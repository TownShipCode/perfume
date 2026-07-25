from __future__ import annotations

from decimal import Decimal

from src.config import Settings, get_settings
from src.db.connection import Database
from src.models.cart import CartItem
from src.services.cart_service import add_item_to_cart, build_cart
from src.services.catalog_service import build_catalog_lines, get_keyword_map, get_product_by_number
from src.services.customer_service import get_customer_by_phone, get_or_create_customer, save_customer_profile, set_customer_language
from src.services.order_service import create_order, get_latest_open_order, record_pop_received
from src.services.order_parser import parse_order
from src.services.session_service import get_or_create_session, get_session_by_phone, save_session_state
from src.services.state_machine import State


ADDRESS_STEPS = [
    ("surname", "What is your SURNAME?"),
    ("area", "What is your AREA?"),
    ("street", "What is your STREET and HOUSE NUMBER?"),
    ("city", "What is your CITY?"),
    ("postal_code", "What is your POSTAL CODE?"),
    ("email", "What is your EMAIL address?"),
    ("province", "What is your PROVINCE?"),
]


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

    if session.get("state") == State.LANGUAGE_SELECTION:
        return await _handle_language_selection(database, customer, session, lowered)

    if lowered in settings.whatsapp_greeting_commands:
        if not customer.get("language"):
            updated_session = await save_session_state(database, phone_number, state=State.LANGUAGE_SELECTION, cart=cart_items, current_step=0, temp_address=None)
            return {"action": "language_selection", "state": updated_session["state"]}
        lines = await build_catalog_lines(database)
        return {
            "action": "welcome_catalogue",
            "state": session.get("state", State.IDLE),
            "customer_name": customer.get("name"),
            "catalogue": "\n".join(lines) if lines else "No products available right now.",
        }

    if lowered in settings.whatsapp_catalog_commands:
        lines = await build_catalog_lines(database)
        return {
            "action": "catalogue",
            "state": session.get("state", State.IDLE),
            "catalogue": "\n".join(lines) if lines else "No products available right now.",
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
                "action": "address_confirmation_requested",
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

    keyword_map = await get_keyword_map(database)
    parsed = parse_order(text, keyword_map)
    if parsed is None:
        return {"action": "unmatched", "state": session.get("state", State.IDLE), "text": text}

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
        area=temp_address["area"],
        street=temp_address["street"],
        city=temp_address["city"],
        postal_code=temp_address.get("postal_code", ""),
        email=temp_address.get("email", ""),
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
    return {
        "items": [item.model_dump() for item in cart.items],
        "total": str(cart.total),
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
