from __future__ import annotations

import logging
from decimal import Decimal

from src.config import Settings, get_settings
from src.db.connection import Database
from src.models.cart import CartItem
from src.services.cart_service import add_item_to_cart, build_cart
from src.services.catalog_service import build_catalog_lines, get_keyword_map, get_product_by_number, list_active_products
from src.services.customer_service import get_customer_by_phone, get_or_create_customer, save_customer_profile, set_customer_language
from src.services.order_service import create_order, get_latest_open_order, record_pop_received
from src.services.order_parser import parse_order
from src.services.session_service import get_or_create_session, get_session_by_phone, save_session_state
from src.services.state_machine import State


ADDRESS_STEPS = [
    ("name", "👤 *Step 1/7* — What is your FIRST NAME?"),
    ("surname", "📝 *Step 2/7* — What is your SURNAME?"),
    ("area", "📍 *Step 3/7* — What is your AREA?"),
    ("street", "🏠 *Step 4/7* — Now send your STREET and HOUSE NUMBER."),
    ("city", "🏙️ *Step 5/7* — Now send your CITY."),
    ("postal_code", "📮 *Step 6/7* — Now send your POSTAL CODE."),
    ("province", "🗺️ *Step 7/7* — Now send your PROVINCE."),
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
    phone_number = event.get("from")
    if not phone_number:
        return {"action": "ignored", "reason": "missing_phone_number"}

    customer = await get_or_create_customer(database, phone_number, event.get("profile_name"))
    session = await get_or_create_session(database, phone_number)
    cart_items = [CartItem.model_validate(item) for item in session.get("cart", [])]

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
        lines = await build_catalog_lines(database)
        image_url = await _get_catalogue_image_url(database)
        return {
            "action": "catalogue",
            "state": session.get("state", State.IDLE),
            "catalogue": "\n".join(lines) if lines else "No products available right now.",
            "image_url": image_url,
        }

    # Language codes: auto-set language, then show catalogue
    if lowered in settings.supported_languages:
        if not customer.get("language") or customer.get("language") != lowered:
            await set_customer_language(database, phone_number, lowered)
            customer["language"] = lowered
        lines = await build_catalog_lines(database)
        image_url = await _get_catalogue_image_url(database)
        customer_name = customer.get("name") or ""
        return {
            "action": "welcome_catalogue",
            "state": session.get("state", State.IDLE),
            "customer_name": customer_name,
            "catalogue": "\n".join(lines) if lines else "No products available right now.",
            "image_url": image_url,
        }

    if session.get("state") == State.ADDRESS_COLLECTION:
        return await _handle_address_collection(database, customer, session, cart_items, text)

    # info N: show product detail
    if lowered.startswith("info ") or lowered.startswith("details "):
        num_text = lowered.split(maxsplit=1)[1] if " " in lowered else ""
        if num_text.isdigit():
            product = await get_product_by_number(database, int(num_text))
            if product:
                return {"action": "product_detail", "product_name": product["name"], "description": product.get("description") or "No description available.", "price": str(product["price"])}
        return {"action": "unmatched", "state": session.get("state", State.IDLE), "text": text}

    if session.get("state") == State.ADDRESS_CONFIRMATION:
        return await _handle_profile_confirmation(database, customer, session, cart_items, lowered)

    if session.get("state") == State.POP_WAITING:
        return {"action": "awaiting_pop", "state": State.POP_WAITING}

    if lowered in settings.whatsapp_cancel_commands:
        updated_session = await save_session_state(
            database,
            phone_number,
            state=State.IDLE,
            cart=[],
            current_step=0,
            temp_address=None,
        )
        return {"action": "order_cancelled", "state": updated_session["state"]}

    if lowered in settings.whatsapp_checkout_commands:
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
                "province": customer.get("province", ""),
                "cart": _serialize_cart(cart),
            }
        return {
            "action": "address_collection_started",
            "state": updated_session["state"],
            "prompt": ADDRESS_STEPS[0][1],
            "cart": _serialize_cart(cart),
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
            }
        # Product number doesn't exist — show what IS available
        lines = await build_catalog_lines(database)
        return {
            "action": "product_not_found",
            "state": session.get("state", State.IDLE),
            "attempted_number": int(text),
            "catalogue": "\n".join(lines) if lines else "No products available right now.",
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
        return {
            "action": "interactive_welcome",
            "state": session.get("state", State.IDLE),
            "customer_name": customer_name,
            "greeting": f"👋 Hi{greeting}! Welcome to BioMed. What would you like to do?",
        }

    updated_items = add_item_to_cart(cart_items, parsed["product_id"], parsed["quantity"])
    updated_session = await save_session_state(
        database,
        phone_number,
        state=State.ORDERING,
        cart=updated_items,
        current_step=session.get("current_step", 0),
        temp_address=session.get("temp_address"),
    )
    price_map = await _build_price_map(database)
    cart = build_cart(updated_items, price_map)
    return {
        "action": "cart_updated",
        "state": updated_session["state"],
        "matched_item": parsed,
        "cart": _serialize_cart(cart),
    }


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
        image_url = await _get_catalogue_image_url(database)
        customer_name = customer.get("name") or ""
        return {
            "action": "language_set",
            "language": lowered,
            "state": State.IDLE,
            "customer_name": customer_name,
            "catalogue": catalogue,
            "image_url": image_url,
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
    step_index = int(session.get("current_step", 0))
    temp_address = dict(session.get("temp_address") or {})
    key, _prompt = ADDRESS_STEPS[min(step_index, len(ADDRESS_STEPS) - 1)]
    temp_address[key] = text.strip()

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
) -> dict[str, object]:
    price_map = await _build_price_map(database)
    cart = build_cart(cart_items, price_map)
    settings = get_settings()
    applied_shipping = await _compute_shipping(settings, cart.total)
    order = await create_order(
        database,
        customer_id=customer_id,
        cart_items=cart_items,
        total=cart.total + applied_shipping,
        shipping_fee=applied_shipping,
    )
    updated_session = await save_session_state(
        database,
        phone_number,
        state=State.POP_WAITING,
        cart=[],
        current_step=0,
        temp_address=None,
    )
    return {
        "action": "order_created",
        "state": updated_session["state"],
        "order_number": order["order_number"],
        "address": full_address,
        "cart": _serialize_cart(cart),
        "shipping_fee": str(applied_shipping),
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
    if quantity <= 0:
        # Invalid quantity — clear pending, show welcome
        await save_session_state(
            database, phone_number,
            state=State.IDLE, cart=cart_items,
            current_step=0, temp_address=None,
        )
        return {
            "action": "interactive_welcome",
            "customer_name": "",
            "greeting": "👋 Welcome to BioMed. What would you like to do?",
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
        "action": "cart_updated",
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
