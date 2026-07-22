from __future__ import annotations

from decimal import Decimal

from src.db.connection import Database
from src.models.cart import CartItem
from src.services.cart_service import add_item_to_cart, build_cart
from src.services.catalog_service import get_keyword_map
from src.services.customer_service import get_customer_by_phone, get_or_create_customer, save_customer_address
from src.services.order_service import create_order, get_latest_open_order, record_pop_received
from src.services.order_parser import parse_order
from src.services.session_service import get_or_create_session, get_session_by_phone, save_session_state


ADDRESS_STEPS = [
    ("area", "What is your AREA?"),
    ("street", "What is your STREET and HOUSE NUMBER?"),
    ("city", "What is your CITY?"),
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

    if session.get("state") == "address_collection":
        return await _handle_address_collection(database, customer, session, cart_items, text)

    if session.get("state") == "address_confirmation":
        return await _handle_address_confirmation(database, customer, session, cart_items, lowered)

    if session.get("state") == "pop_waiting":
        return {"action": "awaiting_pop", "state": "pop_waiting"}

    if lowered == "done":
        if not cart_items:
            return {"action": "checkout_blocked", "reason": "empty_cart", "state": session.get("state", "idle")}

        next_state = "address_confirmation" if customer.get("address_verified") and customer.get("full_address") else "address_collection"
        temp_address = None if next_state == "address_confirmation" else {}
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
        if next_state == "address_confirmation":
            return {
                "action": "address_confirmation_requested",
                "state": updated_session["state"],
                "address": customer.get("full_address"),
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
        return {"action": "unmatched", "state": session.get("state", "idle"), "text": text}

    updated_items = add_item_to_cart(cart_items, parsed["product_id"], parsed["quantity"])
    updated_session = await save_session_state(
        database,
        phone_number,
        state="ordering",
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
            state="address_collection",
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

    updated_customer = await save_customer_address(
        database,
        phone_number,
        area=temp_address["area"],
        street=temp_address["street"],
        city=temp_address["city"],
    )
    return await _finalize_order(
        database,
        customer_id=updated_customer["id"],
        phone_number=phone_number,
        cart_items=cart_items,
        full_address=updated_customer["full_address"],
    )


async def _handle_address_confirmation(
    database: Database,
    customer: dict,
    session: dict,
    cart_items: list[CartItem],
    lowered: str,
) -> dict[str, object]:
    phone_number = customer["phone_number"]
    if lowered in {"yes", "y"}:
        return await _finalize_order(
            database,
            customer_id=customer["id"],
            phone_number=phone_number,
            cart_items=cart_items,
            full_address=customer.get("full_address"),
        )

    if lowered in {"no", "n"}:
        updated_session = await save_session_state(
            database,
            phone_number,
            state="address_collection",
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
        "state": session.get("state", "address_confirmation"),
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
    order = await create_order(database, customer_id=customer_id, cart_items=cart_items, total=cart.total)
    updated_session = await save_session_state(
        database,
        phone_number,
        state="pop_waiting",
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
    }


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

    if session.get("state") != "pop_waiting":
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
