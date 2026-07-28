# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownParameterType=false, reportAttributeAccessIssue=false

from __future__ import annotations

import logging
from decimal import Decimal

from src.config import Settings, get_settings
from src.db.connection import Database, execute, fetch_one
from src.models.cart import CartItem
from src.services.cart_service import add_item_to_cart, build_cart
from src.services.catalog_service import build_catalog_lines, get_keyword_map, get_product_by_number, list_active_products, search_products
from src.services.customer_service import get_customer_by_phone, get_or_create_customer, save_customer_profile, set_customer_language
from src.services.order_service import create_order, get_latest_open_order, record_pop_received
from src.services.order_parser import parse_order
from src.services.session_service import get_or_create_session, get_session_by_phone, save_session_state
from src.services.state_machine import State


ADDRESS_STEPS = [
    ("name", "� *Let's get your order to you!*\n\nTo make sure your products reach you safely, please share a few delivery details.\n\n👤 What is your FIRST NAME?"),
    ("surname", "📝 What is your SURNAME?"),
    ("area", "📍 What is your AREA?"),
    ("street", "🏠 Now send your STREET and HOUSE NUMBER."),
    ("city", "🏙️ Now send your CITY."),
    ("postal_code", "📮 Now send your POSTAL CODE."),
    ("province", "🗺️ Now send your PROVINCE."),
]

logger = logging.getLogger(__name__)


async def _get_catalogue_image_url(database: Database) -> str | None:
    products = await list_active_products(database)
    for product in products:
        image_url = product.get("image_url")
        if image_url:
            return str(image_url)
    return None


async def handle_text_message(database: Database, event: dict) -> dict[str, object]:
    try:
        return await _handle_text_message_impl(database, event)
    except Exception as exc:
        logger.exception("handle_text_message_fatal | phone=%s error=%s",
                         (event.get("from") or "?")[-4:], exc)
        return {"action": "internal_error", "text": "Something went wrong. Please try again."}


async def _handle_text_message_impl(database: Database, event: dict) -> dict[str, object]:
    phone_number = event.get("from")
    if not phone_number:
        return {"action": "ignored", "reason": "missing_phone_number"}

    customer = await get_or_create_customer(database, phone_number, event.get("profile_name"))
    session = await get_or_create_session(database, phone_number)
    cart_items = [CartItem.model_validate(item) for item in session.get("cart", [])]

    # ── Agent detection (Phase 3) ──
    # If customer is an agent, stamp agent_code + team_member_id on the session
    # so all orders from this session get commission tracking.
    agent_code = customer.get("agent_code")
    team_member_id = customer.get("registered_by")
    if agent_code:
        session["agent_code"] = agent_code
        session["team_member_id"] = team_member_id

    text = (event.get("text") or "").strip()
    lowered = text.lower()
    settings = get_settings()

    logger.info(
        "handle_text_message | phone=%s state=%s text=%s lang=%s",
        phone_number[-4:], session.get("state"), text[:60],
        customer.get("language") or "(none)",
    )

    # ── LANGUAGE_SELECTION disabled — default language auto-assigned ──
    # Safety net: users who might still have LANGUAGE_SELECTION in DB
    # get auto-migrated to IDLE with default language.
    if session.get("state") == State.LANGUAGE_SELECTION:
        await set_customer_language(database, phone_number, settings.default_language)
        await save_session_state(
            database, phone_number,
            state=State.IDLE, cart=session.get("cart", []),
            current_step=0, temp_address=session.get("temp_address"),
        )

    if lowered in settings.whatsapp_catalog_commands:
        web_url = settings.web_base_url.rstrip("/")
        return {
            "action": "catalogue_web",
            "state": session.get("state", State.IDLE),
            "web_url": f"{web_url}/catalogue",
        }

    # Language codes: auto-set language, then show catalogue
    if lowered in settings.supported_languages:
        if not customer.get("language") or customer.get("language") != lowered:
            await set_customer_language(database, phone_number, lowered)
            customer["language"] = lowered
        lines = await build_catalog_lines(database)
        customer_name = customer.get("name") or ""
        return {
            "action": "welcome_catalogue",
            "state": session.get("state", State.IDLE),
            "customer_name": customer_name,
            "catalogue": "\n".join(lines) if lines else "No products available right now.",
        }

    # ── Confirmation step: agent confirmed/cancelled a pending order ──
    temp = session.get("temp_address") or {}
    pending_order = temp.get("__pending_order__")
    if pending_order and lowered in ("add_confirm", "add_cancel"):
        if lowered == "add_confirm":
            # Add pending to cart
            updated_items = add_item_to_cart(cart_items, pending_order["product_id"], pending_order["quantity"])
            temp.pop("__pending_order__", None)
            await save_session_state(
                database, phone_number,
                state=State.ORDERING, cart=updated_items,
                current_step=session.get("current_step", 0),
                temp_address=temp,
            )
            price_map = await _build_price_map(database)
            cart = build_cart(updated_items, price_map)
            return {
                "action": "order_confirmed",
                "state": State.ORDERING,
                "product_name": pending_order["product_name"],
                "quantity": pending_order["quantity"],
                "cart": _serialize_cart(cart),
            }
        else:
            # Cancel pending — clear it
            temp.pop("__pending_order__", None)
            await save_session_state(
                database, phone_number,
                state=State.IDLE, cart=cart_items,
                current_step=0, temp_address=temp,
            )
            return {"action": "order_cancelled_pending", "state": State.IDLE}

    if session.get("state") == State.ADDRESS_COLLECTION:
        return await _handle_address_collection(database, customer, session, cart_items, text)

    # info N: show product detail
    if lowered.startswith("info ") or lowered.startswith("details "):
        num_text = lowered.split(maxsplit=1)[1] if " " in lowered else ""
        if num_text.isdigit():
            product = await get_product_by_number(database, int(num_text))
            if product:
                web_url = settings.web_base_url.rstrip("/")
                return {"action": "product_detail", "product_name": product["name"], "description": product.get("description") or "No description available.", "price": str(product["price"]), "image_url": product.get("image_url"), "product_url": f"{web_url}/product/{product['product_number']}"}
        return {"action": "unmatched", "state": session.get("state", State.IDLE), "text": text}

    if session.get("state") == State.ADDRESS_CONFIRMATION:
        return await _handle_profile_confirmation(database, customer, session, cart_items, lowered)

    if lowered in settings.whatsapp_cancel_commands:
        await _cancel_order(database, phone_number)
        return {"action": "order_cancelled", "state": State.IDLE}

    # ── Agent registration: JOIN <team_code> (Phase 4) ──
    if lowered.startswith("join "):
        return await _handle_agent_join(database, phone_number, customer, text)

    # ── Lost number recovery: RECOVER <agent_code> [pin] (Phase 4) ──
    if lowered.startswith("recover "):
        return await _handle_agent_recovery(database, phone_number, customer, session, lowered)

    # ── Stock check: stock <product_number or name> (Phase 8) ──
    if lowered.startswith("stock "):
        return await _handle_stock_check(database, lowered)

    # ── Agent price list: "price list" or "pricelist" ──
    if lowered in ("price list", "pricelist", "prices"):
        return {
            "action": "price_list",
            "state": session.get("state", State.IDLE),
            "url": f"{settings.api_base_url}/api/agent/price-list",
        }

    # ── WhatsApp catalog link ──
    if lowered in ("catalog link", "share catalog", "wa catalog"):
        catalog_id = settings.whatsapp_catalog_id
        if catalog_id:
            return {
                "action": "catalog_link",
                "state": session.get("state", State.IDLE),
                "catalog_url": f"https://wa.me/c/{catalog_id}",
            }
        return {"action": "text", "text": "📋 View our catalogue here:\n{}/catalogue".format(settings.api_base_url.replace("/api", ""))}

    # ── Agent referral: customer can become an agent ──
    if lowered == "agent" or lowered == "become agent" or lowered == "become an agent":
        if customer.get("role") == "agent":
            return {"action": "text", "text": "✨ You're already a Zen Fragrances agent! Use your dashboard to manage orders and track commissions."}
        return {
            "action": "become_agent",
            "state": session.get("state", State.IDLE),
            "customer_name": customer.get("name") or "",
            "register_url": f"{settings.api_base_url.replace('/api', '')}/register-agent",
        }

    # ── Recovery challenge active? (Phase 4) ──
    if temp.get("recovery_agent_code"):
        return await _handle_recovery_challenge(database, phone_number, session, text)

    # In POP_WAITING, handle payment method selection + cancel/checkout
    if session.get("state") == State.POP_WAITING:
        if lowered == "yoco" and "yoco" in settings.payment_methods_enabled:
            return await _handle_yoco_payment(database, session, settings)
        if lowered == "eft" and "eft" in settings.payment_methods_enabled:
            return await _handle_eft_payment(session)
        # Let them browse catalogue while waiting
        if lowered in settings.whatsapp_catalog_commands:
            web_url = settings.web_base_url.rstrip("/")
            return {
                "action": "catalogue_web",
                "state": State.POP_WAITING,
                "web_url": f"{web_url}/catalogue",
            }
        return {"action": "awaiting_pop", "state": State.POP_WAITING}

    # ── Cart view: show current cart on demand ──
    if lowered in ("cart", "view cart", "my cart"):
        if not cart_items:
            return {"action": "text", "text": "🛒 Your cart is empty.\n\nType a product name to add items, e.g. _\"5 Rose Oud\"_."}
        price_map = await _build_price_map(database)
        cart = build_cart(cart_items, price_map)
        return {
            "action": "cart_summary",
            "state": State.ORDERING,
            "cart": _serialize_cart(cart),
        }

    # ── Repeat last order: restore previous order to cart ──
    if lowered in ("repeat", "reorder", "repeat last", "same again"):
        from src.services.order_service import get_latest_order
        last = await get_latest_order(database, phone_number)
        if not last or not last.get("items"):
            return {"action": "text", "text": "📭 No previous orders found.\n\nType a product name to start, e.g. _\"5 Rose Oud\"_."}
        items = last["items"]
        restored = []
        for it in items:
            pid = it.get("product_id")
            qty = it.get("quantity", 1)
            if pid:
                restored.append(CartItem(product_id=pid, quantity=qty))
        if not restored:
            return {"action": "text", "text": "📭 Couldn't restore your last order.\n\nType a product name to start fresh."}
        await save_session_state(
            database, phone_number,
            state=State.ORDERING, cart=restored,
            current_step=0, temp_address=temp,
        )
        price_map = await _build_price_map(database)
        cart = build_cart(restored, price_map)
        item_names = [f"{it.get('quantity', 1)}× {it.get('product_name', '?')}" for it in cart.get("items", [])]
        return {
            "action": "repeat_order",
            "state": State.ORDERING,
            "cart": _serialize_cart(cart),
            "item_list": "\n".join(f"  {n}" for n in item_names),
            "total": cart.get("total", "0"),
        }

    if lowered in settings.whatsapp_checkout_commands:
        # Auto-confirm any pending order before checkout
        if pending_order:
            updated_items = add_item_to_cart(cart_items, pending_order["product_id"], pending_order["quantity"])
            temp.pop("__pending_order__", None)
            cart_items = updated_items
            await save_session_state(
                database, phone_number,
                state=State.ORDERING, cart=cart_items,
                current_step=0, temp_address=temp,
            )
            session["cart"] = [item.model_dump() for item in cart_items]

        if not cart_items:
            return {"action": "checkout_blocked", "reason": "empty_cart", "state": session.get("state", State.IDLE)}

        next_state = State.ADDRESS_CONFIRMATION if customer.get("address_verified") and customer.get("full_address") else State.ADDRESS_COLLECTION
        temp_address = None if next_state == State.ADDRESS_CONFIRMATION else {}
        updated_session = await save_session_state(
            database,
            phone_number,
            state=next_state,
            cart=cart_items,
            current_step=0,
            temp_address=temp_address,
        )
        price_map = await _build_price_map(database)
        cart = build_cart(cart_items, price_map)
        if next_state == State.ADDRESS_CONFIRMATION:
            return {
                "action": "interactive_address_confirm",
                "state": updated_session["state"],
                "customer_name": customer.get("name", ""),
                "surname": customer.get("surname", ""),
                "address": customer.get("full_address"),
                "email": customer.get("email", ""),
                "province": customer.get("province", ""),
                "cart": _serialize_cart(cart),
            }
        return {
            "action": "address_collection_started",
            "state": updated_session["state"],
            "prompt": ADDRESS_STEPS[0][1],
            "cart": _serialize_cart(cart),
        }

    # Help command — show useful info with web store link
    if lowered in ("help", "?"):
        web_url = settings.web_base_url.rstrip("/")
        return {
            "action": "text",
            "text": f"💡 *{settings.store_name}*\n\n🛍️ Browse & order online:\n{web_url}/catalogue\n\n⚡ Quick order via WhatsApp:\n• Type product name: e.g. _\"5 Rose Oud\"_\n• Check stock: _\"stock 1\"_\n• View cart: _\"cart\"_\n• Checkout: _\"checkout\"_\n• Cancel: _\"cancel\"_",
        }

    # Bare number shortcut or quantity input
    if text.isdigit():
        qty = int(text)
        # Check if user is responding to a quantity prompt
        pending_raw = session.get("temp_address")
        if isinstance(pending_raw, dict) and pending_raw.get("__pending_product__"):
            pending = pending_raw["__pending_product__"]
            return await _add_pending_to_cart(database, phone_number, session, cart_items, pending, qty)

        # New product selection: save pending, ask for quantity
        product = await get_product_by_number(database, int(text))
        if product:
            await save_session_state(
                database, phone_number,
                state=State.ORDERING, cart=cart_items,
                current_step=0,
                temp_address={"__pending_product__": {"id": product["id"], "name": product["name"], "price": str(product["price"])}},
            )
            return {
                "action": "quantity_selection",
                "product_name": product["name"],
                "price": str(product["price"]),
                "description": product.get("description", ""),
                "image_url": product.get("image_url"),
            }
        # Product number doesn't exist — suggest web store
        web_url = settings.web_base_url.rstrip("/")
        return {
            "action": "product_not_found",
            "state": session.get("state", State.IDLE),
            "attempted_number": int(text),
            "web_url": f"{web_url}/catalogue",
        }

    keyword_map = await get_keyword_map(database)
    parsed = parse_order(text, keyword_map)
    if parsed is None:
        logger.warning(
            "handle_text_message | UNMATCHED→WELCOME phone=%s state=%s text=%s",
            phone_number[-4:], session.get("state"), text[:60],
        )
        # Any unrecognized text triggers interactive welcome — no gatekeeping
        if not customer.get("language"):
            await set_customer_language(database, phone_number, settings.default_language)
            customer["language"] = settings.default_language
        customer_name = customer.get("name") or ""
        greeting = f" {customer_name}" if customer_name else ""
        web_url = settings.web_base_url.rstrip("/")
        return {
            "action": "interactive_welcome",
            "state": session.get("state", State.IDLE),
            "customer_name": customer_name,
            "greeting": f"👋 Hi{greeting}! Welcome to Zen Fragrances. What would you like to do?",
            "web_url": f"{web_url}/catalogue",
        }

    # ── Confirmation: ask agent to confirm before adding to cart ──
    unit_total = parsed["quantity"] * float(parsed["unit_price"])
    temp["__pending_order__"] = {
        "product_id": parsed["product_id"],
        "product_name": parsed["product_name"],
        "quantity": parsed["quantity"],
        "unit_price": str(parsed["unit_price"]),
    }
    await save_session_state(
        database, phone_number,
        state=State.ORDERING, cart=cart_items,
        current_step=0, temp_address=temp,
    )
    # Look up product image for visual confirmation
    product_detail = await get_product_by_number(database, parsed["product_number"])
    result: dict[str, object] = {
        "action": "confirm_order",
        "state": State.ORDERING,
        "product_name": parsed["product_name"],
        "quantity": parsed["quantity"],
        "unit_price": str(parsed["unit_price"]),
        "unit_total": f"{unit_total:,.2f}",
    }
    if product_detail and product_detail.get("image_url"):
        result["image_url"] = product_detail["image_url"]
    return result


async def _handle_language_selection(
    database: Database,
    customer: dict,
    session: dict,
    lowered: str,
) -> dict[str, object]:
    settings = get_settings()
    if lowered in settings.supported_languages:
        await set_customer_language(database, customer["phone_number"], lowered)
        await save_session_state(
            database, customer["phone_number"],
            state=State.IDLE, cart=session.get("cart", []),
            current_step=0, temp_address=session.get("temp_address"),
        )
        lines = await build_catalog_lines(database)
        catalogue = "\n".join(lines) if lines else "No products available right now."
        customer_name = customer.get("name") or ""
        return {
            "action": "language_set",
            "language": lowered,
            "state": State.IDLE,
            "customer_name": customer_name,
            "catalogue": catalogue,
        }
    return {"action": "language_selection", "state": State.LANGUAGE_SELECTION}


async def _handle_address_collection(
    database: Database,
    customer: dict,
    session: dict,
    cart_items: list[CartItem],
    text: str,
) -> dict[str, object]:
    phone_number = customer["phone_number"]
    settings = get_settings()
    lowered = text.strip().lower()

    # ── Escape hatches: allow cancel, help, catalogue while collecting address ──
    if lowered in settings.whatsapp_cancel_commands:
        await save_session_state(
            database, phone_number,
            state=State.IDLE, cart=cart_items,
            current_step=0, temp_address={},
        )
        return {"action": "order_cancelled", "state": State.IDLE}

    if lowered in ("help", "?"):
        return {
            "action": "address_collection_progress",
            "state": session.get("state"),
            "current_step": int(session.get("current_step", 0)),
            "prompt": "ℹ️ You're providing your delivery details.\n\nReply *CANCEL* to start over, or continue answering the questions.",
        }

    if lowered in settings.whatsapp_catalog_commands:
        return {
            "action": "address_collection_progress",
            "state": session.get("state"),
            "current_step": int(session.get("current_step", 0)),
            "prompt": "📋 Please finish providing your delivery details first — then you can browse the catalogue.\n\nReply *CANCEL* to start over.",
        }

    if lowered in settings.whatsapp_greeting_commands:
        _prompt = ADDRESS_STEPS[min(int(session.get("current_step", 0)), len(ADDRESS_STEPS) - 1)][1]
        return {
            "action": "address_collection_progress",
            "state": session.get("state"),
            "current_step": int(session.get("current_step", 0)),
            "prompt": f"👋 You're in the middle of providing your delivery details.\n\n{_prompt}\n\n_Type CANCEL to start over._",
        }

    step_index = int(session.get("current_step", 0))
    temp_address = dict(session.get("temp_address") or {})
    key, _prompt = ADDRESS_STEPS[min(step_index, len(ADDRESS_STEPS) - 1)]
    value = text.strip()
    if len(value) < 2:
        return {"action": "address_collection_progress", "state": session.get("state"), "current_step": step_index, "prompt": f"⚠️ Please enter a valid {key.replace('_', ' ')}.\n\n{_prompt}"}
    temp_address[key] = value

    if step_index < len(ADDRESS_STEPS) - 1:
        next_step = step_index + 1
        updated_session = await save_session_state(
            database,
            phone_number,
            state=State.ADDRESS_COLLECTION,
            cart=cart_items,
            current_step=next_step,
            temp_address=temp_address,
        )
        return {
            "action": "address_collection_progress",
            "state": updated_session["state"],
            "current_step": updated_session["current_step"],
            "prompt": ADDRESS_STEPS[next_step][1],
        }

    updated_customer = await save_customer_profile(
        database,
        phone_number,
        name=temp_address.get("name", ""),
        area=temp_address["area"],
        street=temp_address["street"],
        city=temp_address["city"],
        postal_code=temp_address.get("postal_code", ""),
        province=temp_address.get("province", ""),
        surname=temp_address.get("surname", ""),
    )
    return await _finalize_order(
        database,
        customer_id=updated_customer["id"],
        phone_number=phone_number,
        cart_items=cart_items,
        full_address=updated_customer["full_address"],
        session=session,
    )


async def _handle_profile_confirmation(
    database: Database,
    customer: dict,
    session: dict,
    cart_items: list[CartItem],
    lowered: str,
) -> dict[str, object]:
    phone_number = customer["phone_number"]
    settings = get_settings()
    if lowered in settings.whatsapp_confirm_commands:
        return await _finalize_order(
            database,
            customer_id=customer["id"],
            phone_number=phone_number,
            cart_items=cart_items,
            full_address=customer.get("full_address"),
            session=session,
        )

    if lowered in settings.whatsapp_reject_commands:
        updated_session = await save_session_state(
            database,
            phone_number,
            state=State.ADDRESS_COLLECTION,
            cart=cart_items,
            current_step=0,
            temp_address={},
        )
        return {
            "action": "address_collection_started",
            "state": updated_session["state"],
            "prompt": ADDRESS_STEPS[0][1],
        }

    return {
        "action": "address_confirmation_pending",
        "state": session.get("state", State.ADDRESS_CONFIRMATION),
        "address": customer.get("full_address"),
    }


async def _finalize_order(
    database: Database,
    *,
    customer_id: int,
    phone_number: str,
    cart_items: list[CartItem],
    full_address: str | None,
    session: dict | None = None,
) -> dict[str, object]:
    price_map = await _build_price_map(database)
    cart = build_cart(cart_items, price_map)
    settings = get_settings()
    applied_shipping = await _compute_shipping(settings, cart.total)

    # ── Commission calculation (Phase 3) ──
    agent_code_val: str | None = None
    team_member_id_val: int | None = None
    commission = Decimal("0")
    if session:
        agent_code_val = session.get("agent_code")
        team_member_id_val = session.get("team_member_id")
        if agent_code_val and team_member_id_val:
            commission = (cart.total + applied_shipping) * settings.commission_percent / Decimal("100")

    order = await create_order(
        database,
        customer_id=customer_id,
        cart_items=cart_items,
        total=cart.total + applied_shipping,
        shipping_fee=applied_shipping,
        agent_code=agent_code_val,
        team_member_id=team_member_id_val,
        commission_amount=commission,
    )
    updated_session = await save_session_state(
        database,
        phone_number,
        state=State.POP_WAITING,
        cart=[],
        current_step=0,
        temp_address={"order_number": order["order_number"]},
    )
    return {
        "action": "order_created",
        "state": updated_session["state"],
        "order_number": order["order_number"],
        "address": full_address,
        "cart": _serialize_cart(cart),
        "shipping_fee": str(applied_shipping),
    }


async def _handle_yoco_payment(database: Database, session: dict, settings) -> dict[str, object]:
    """Create Yoco checkout session and return payment link."""
    from src.services.order_service import get_latest_order
    from src.services.yoco_payment import create_checkout_session

    phone = session.get("phone_number", "")
    order = await get_latest_order(database, phone)
    if not order:
        return {"action": "payment_selection", "state": State.POP_WAITING}

    total = order.get("total", 0)
    amount_cents = int(float(str(total)) * 100)
    result = await create_checkout_session(
        str(order.get("order_number", "")), amount_cents,
        agent_code=order.get("agent_code"),
        team_member_id=order.get("team_member_id"),
    )

    if result:
        # Store payment method
        await execute(
            database,
            "UPDATE orders SET payment_method = 'yoco', yoco_checkout_id = $1, updated_at = NOW() WHERE id = $2",
            result["checkout_id"],
            order["id"],
        )
        return {
            "action": "yoco_payment_link",
            "checkout_url": result["checkout_url"],
        }
    return {
        "action": "bank_details",
        "order_number": order.get("order_number", ""),
    }


async def _handle_eft_payment(session: dict) -> dict[str, object]:
    """Show bank details for EFT payment."""
    temp = session.get("temp_address") or {}
    return {
        "action": "bank_details",
        "order_number": str(temp.get("order_number", "")),
    }


async def _compute_shipping(settings: Settings, subtotal: Decimal) -> Decimal:
    if settings.free_shipping_threshold > 0 and subtotal >= settings.free_shipping_threshold:
        return Decimal("0")
    return settings.shipping_fee


async def _build_price_map(database: Database) -> dict[int, Decimal]:
    keyword_map = await get_keyword_map(database)
    prices: dict[int, Decimal] = {}
    for product in keyword_map.values():
        product_id = int(product["product_id"])
        if product_id not in prices:
            prices[product_id] = Decimal(str(product["price"]))
    return prices


def _serialize_cart(cart) -> dict[str, object]:
    items = []
    for item in cart.items:
        if hasattr(item, "model_dump"):
            items.append(item.model_dump())
        elif isinstance(item, dict):
            items.append(item)
        else:
            items.append(str(item))
    return {
        "items": items,
        "total": str(cart.total),
    }


async def _add_pending_to_cart(
    database: Database,
    phone_number: str,
    session: dict,
    cart_items: list[CartItem],
    pending: dict,
    quantity: int,
) -> dict[str, object]:
    """Add pending product to cart with specified quantity, then clear pending state."""
    settings = get_settings()
    if quantity <= 0:
        await save_session_state(
            database, phone_number,
            state=State.IDLE, cart=cart_items,
            current_step=0, temp_address=None,
        )
        return {
            "action": "interactive_welcome",
            "customer_name": "",
            "greeting": f"👋 *Welcome to {settings.store_name}!* 🫖\n\nYour natural health store on WhatsApp.\nWhat would you like to do?",
        }

    if quantity > settings.max_quantity:
        return {
            "action": "quantity_selection",
            "product_name": pending["name"],
            "price": pending["price"],
        }

    updated_items = add_item_to_cart(cart_items, pending["id"], quantity)
    updated_session = await save_session_state(
        database, phone_number,
        state=State.ORDERING, cart=updated_items,
        current_step=0, temp_address=None,
    )
    price_map = await _build_price_map(database)
    cart = build_cart(updated_items, price_map)
    return {
        "action": "cart_summary",
        "state": updated_session["state"],
        "matched_item": {
            "product_id": pending["id"],
            "product_name": pending["name"],
            "quantity": quantity,
            "matched_keyword": "quantity_select",
            "unit_price": pending["price"],
        },
        "cart": _serialize_cart(cart),
    }


async def _cancel_order(database: Database, phone_number: str) -> None:
    """Cancel any pending POP order and reset session."""
    from src.services.order_service import cancel_pending_pop_order

    await cancel_pending_pop_order(database, phone_number)
    await save_session_state(
        database, phone_number,
        state=State.IDLE, cart=[],
        current_step=0, temp_address=None,
    )


# ── Phase 4: Agent registration & recovery ──


async def _handle_agent_join(
    database: Database, phone_number: str, customer: dict, text: str
) -> dict[str, object]:
    """Handle JOIN <team_code> command for agent self-registration."""
    import secrets
    from src.services.customer_service import get_customer_by_agent_code, register_agent

    parts = text.strip().split()
    if len(parts) < 2:
        return {"action": "error", "text": "Usage: JOIN <team-code>\n\nAsk your team member for their code."}

    team_code = parts[1].strip().upper()

    # Check if already an agent
    if customer.get("role") == "agent" and customer.get("agent_code"):
        return {
            "action": "already_agent",
            "text": f"⚠️ You're already registered as agent *{customer['agent_code']}*.\nType CATALOGUE to start ordering.",
        }

    # Validate team code
    team_member = await get_customer_by_agent_code(database, team_code)
    if team_member is None or team_member.get("role") != "team_member":
        return {"action": "error", "text": "❌ Team code not found. Check with your team member."}

    # Generate recovery PIN
    recovery_pin = str(secrets.randbelow(10000)).zfill(4)

    # Register agent (reuse existing customer record by phone)
    agent = await register_agent(
        database, phone_number,
        first_name=customer.get("name") or "",
        surname=customer.get("surname") or "",
        team_code=team_code,
        recovery_pin=recovery_pin,
    )

    if agent is None:
        return {"action": "error", "text": "❌ Registration failed. Please try again or contact support."}

    agent_code_val = agent.get("agent_code", "")
    return {
        "action": "agent_registered",
        "text": (
            f"✅ *Welcome to Zen Fragrances!*\n\n"
            f"Your agent code: *{agent_code_val}*\n"
            f"🔐 Recovery PIN: *{recovery_pin}* — save this!\n\n"
            f"Type *CATALOGUE* to browse, *STOCK <number>* to check availability, "
            f"or reply with a product number to order."
        ),
    }


async def _handle_agent_recovery(
    database: Database, new_phone: str, customer: dict, session: dict, lowered: str
) -> dict[str, object]:
    """Handle RECOVER <agent_code> [pin] for lost number recovery."""
    from src.services.customer_service import get_customer_by_agent_code, migrate_phone_number

    parts = lowered.strip().split()

    # RECOVER <agent_code>
    if len(parts) < 2:
        return {"action": "error", "text": "Usage: RECOVER <your-agent-code> [pin]\n\nIf you don't know your code, contact your team member."}

    agent_code_input = parts[1].strip().upper()
    agent = await get_customer_by_agent_code(database, agent_code_input)

    if agent is None:
        return {"action": "error", "text": "❌ Agent code not found."}

    # If PIN provided: direct recovery
    if len(parts) >= 3:
        pin_input = parts[2].strip()
        stored_pin = agent.get("recovery_pin") or ""
        if pin_input == stored_pin:
            await migrate_phone_number(database, agent["phone_number"], new_phone)
            return {
                "action": "agent_recovered",
                "text": "✅ Your account is now linked to this number. Type CATALOGUE to start ordering.",
            }
        return {"action": "error", "text": "❌ Incorrect PIN. If you forgot it, contact your team member for help."}

    # Challenge mode: ask for last order total
    session["recovery_agent_code"] = agent_code_input
    session["recovery_attempts"] = 0
    await save_session_state(
        database, new_phone,
        state=State.IDLE, cart=session.get("cart", []),
        current_step=0,
        temp_address={"recovery_agent_code": agent_code_input, "recovery_attempts": 0},
    )
    return {
        "action": "recovery_challenge",
        "text": "🔐 To verify your identity, what was the total of your last order? (e.g. R990)",
    }


async def _handle_recovery_challenge(
    database: Database, phone_number: str, session: dict, text: str
) -> dict[str, object]:
    """Verify recovery challenge answer."""
    from src.services.customer_service import get_customer_by_agent_code, migrate_phone_number

    temp = session.get("temp_address") or {}
    agent_code_val = temp.get("recovery_agent_code", "")
    attempts = int(temp.get("recovery_attempts", 0))

    agent = await get_customer_by_agent_code(database, agent_code_val)
    if agent is None:
        return {"action": "error", "text": "Recovery session expired. Start again with RECOVER <code>."}

    # Get last order total for this agent
    if database.mode == "postgres":
        from src.db.connection import fetch_one
        last_order = await fetch_one(
            database,
            "SELECT total FROM orders WHERE agent_code = $1 ORDER BY created_at DESC LIMIT 1",
            agent_code_val,
        )
    else:
        from src.db.connection import fetch_one
        last_order = await fetch_one(
            database,
            "SELECT total FROM orders WHERE agent_code = ? ORDER BY created_at DESC LIMIT 1",
            agent_code_val,
        )

    expected = str(last_order["total"]) if last_order else ""
    if text.strip().replace("R", "").replace("r", "") == expected.replace("R", "").replace("r", ""):
        old_phone = agent["phone_number"]
        await migrate_phone_number(database, old_phone, phone_number)
        # Clear recovery state
        await save_session_state(
            database, phone_number,
            state=State.IDLE, cart=[], current_step=0, temp_address=None,
        )
        return {
            "action": "agent_recovered",
            "text": f"✅ Verified! Your account is now on this number. Type CATALOGUE to order.",
        }

    attempts += 1
    if attempts >= 3:
        await save_session_state(
            database, phone_number,
            state=State.IDLE, cart=[], current_step=0, temp_address=None,
        )
        return {"action": "error", "text": "❌ Too many failed attempts. Contact your team member or use RECOVER <code> <pin>."}

    await save_session_state(
        database, phone_number,
        state=State.IDLE, cart=session.get("cart", []),
        current_step=0,
        temp_address={"recovery_agent_code": agent_code_val, "recovery_attempts": attempts},
    )
    return {"action": "recovery_challenge", "text": f"❌ Not correct. Try again or contact your team member. ({3 - attempts} attempts left)"}


# ── Phase 8: Stock check ──


async def _handle_stock_check(database: Database, lowered: str) -> dict[str, object]:
    """Handle STOCK <product_number> or STOCK <name> command."""
    from src.services.catalog_service import get_product_by_number, get_product_detail

    query = lowered.replace("stock", "", 1).replace(":", "").strip()

    # Try by product number
    if query.isdigit():
        product = await get_product_by_number(database, int(query))
        if product is None:
            # Try as product ID
            pid = int(query)
            product = await get_product_detail(database, pid)
    else:
        # Search by name
        result = await search_products(database, query, page=1, page_size=1)
        products = result.get("products", [])
        product = products[0] if products else None

    if product is None:
        return {"action": "stock_not_found", "text": f"❌ Product not found: {query}"}

    name = product.get("name", query)
    stock = product.get("stock_quantity")

    if stock is None:
        return {"action": "stock_info", "text": f"📦 *{name}*: In stock ✅"}
    elif stock > 5:
        return {"action": "stock_info", "text": f"📦 *{name}*: {stock} in stock ✅"}
    elif stock > 0:
        return {"action": "stock_info", "text": f"⚠️ *{name}*: only *{stock}* left! Order soon."}
    else:
        return {"action": "stock_info", "text": f"❌ *{name}* is out of stock."}


async def handle_image_message(database: Database, event: dict) -> dict[str, object]:
    phone_number = event.get("from")
    if not phone_number:
        return {"action": "ignored", "reason": "missing_phone_number"}

    customer = await get_customer_by_phone(database, phone_number)
    session = await get_session_by_phone(database, phone_number)
    if customer is None or session is None:
        return {"action": "unexpected_image", "reason": "unknown_customer"}

    if session.get("state") != State.POP_WAITING:
        return {"action": "unexpected_image", "reason": "not_waiting_for_pop", "state": session.get("state")}

    order = await get_latest_open_order(database, customer["id"])
    if order is None:
        return {"action": "unexpected_image", "reason": "no_active_order"}

    media_reference = event.get("image_url") or event.get("image_id")
    if not media_reference:
        return {"action": "unexpected_image", "reason": "missing_media_reference"}

    updated_order = await record_pop_received(database, order["id"], media_reference)
    updated_session = await save_session_state(
        database,
        phone_number,
        state="confirmed",
        cart=[],
        current_step=0,
        temp_address=None,
    )
    return {
        "action": "pop_received",
        "state": updated_session["state"],
        "order_number": updated_order["order_number"],
        "media_reference": media_reference,
    }
