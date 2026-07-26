from __future__ import annotations

from src.config import get_settings
from src.db.connection import Database
from src.services.catalog_service import get_products_by_ids
from src.services.message_templates import render_template
from src.services.order_service import get_order_by_id, record_order_forwarding
from src.services.whatsapp_sender import send_image_message, send_text_message


async def get_manufacturer_forward_preview(database: Database, order_id: int) -> dict[str, object] | None:
    order = await get_order_by_id(database, order_id)
    if order is None:
        return None

    recipient, message, line_items = await _build_forward_message(database, order)
    return {
        "recipient": recipient,
        "message": message,
        "line_items": line_items,
        "order": order,
    }


async def forward_order_to_manufacturer(database: Database, order_id: int, *, force: bool = False) -> dict[str, object] | None:
    preview = await get_manufacturer_forward_preview(database, order_id)
    if preview is None:
        return None

    order = preview["order"]

    if order.get("forward_delivery_status") and not force:
        return {
            "action": "forward_skipped",
            "reason": "already_forwarded",
            "recipient": order.get("forwarded_to"),
            "order": order,
        }

    recipient = preview["recipient"]
    if not recipient:
        return {
            "action": "forward_skipped",
            "reason": "manufacturer_phone_missing",
            "order": order,
        }

    message = preview["message"]
    delivery = await send_text_message(recipient, message)
    image_delivery = None
    fl_pop_url = order.get("fl_pop_image_url")
    if fl_pop_url:
        image_delivery = await send_image_message(recipient, str(fl_pop_url), caption=f"POP for order {order.get('order_number')}")
    status = str(delivery.get("status", "unknown"))
    updated = await record_order_forwarding(
        database,
        order_id,
        forwarded_to=recipient or "",
        delivery_status=status,
        message_id=delivery.get("provider_message_id"),
        error=delivery.get("error") or delivery.get("reason"),
        payload=delivery.get("payload"),
        response=delivery.get("provider_response"),
    )
    return {
        "action": "forwarded",
        "recipient": recipient,
        "message": message,
        "line_items": preview.get("line_items", []),
        "delivery": delivery,
        "image_delivery": image_delivery,
        "order": updated,
    }


async def _build_forward_message(database: Database, order: dict[str, object]) -> tuple[str | None, str, list[dict[str, object]]]:
    from datetime import date

    settings = get_settings()
    recipient = settings.manufacturer_phone
    products_by_id = await get_products_by_ids(
        database,
        [int(item.get("product_id", 0)) for item in order.get("items") or []],
    )
    line_items = _build_line_items(order.get("items") or [], products_by_id)

    customer_name = order.get("name") or ""
    phone_number = order.get("phone_number") or ""
    full_address = order.get("full_address") or ""

    from src.services.customer_service import get_customer_by_phone
    customer = await get_customer_by_phone(database, phone_number)
    surname = (customer.get("surname") or "") if customer else ""
    postal_code = (customer.get("postal_code") or "") if customer else ""
    province = (customer.get("province") or "") if customer else ""

    quantities = _format_items(line_items)

    message = await render_template(
        database,
        "manufacturer_forward",
        customer_name=customer_name,
        surname=surname,
        full_address=full_address,
        postal_code=postal_code,
        email=settings.bio_med_email,
        province=province,
        phone_number=phone_number,
        items=quantities,
        fl_username=settings.fl_username,
        new_membership=settings.default_membership,
        repurchase=settings.default_repurchase,
        date_of_payment=date.today().strftime("%d %b %Y"),
        courier_name=settings.courier_name,
        self_pickup=settings.self_pickup_default,
    )
    return recipient, message, line_items


def _format_items(line_items: list[dict[str, object]]) -> str:
    lines = [f"- {item['quantity']}x {item['product_name']}" for item in line_items]
    return "\n".join(lines) if lines else "- No items"


def _build_line_items(items: list[dict], products_by_id: dict[int, dict]) -> list[dict[str, object]]:
    line_items: list[dict[str, object]] = []
    for item in items:
        product_id = int(item.get("product_id", 0))
        product = products_by_id.get(product_id) or {}
        product_name = product.get("name") or f"Product {product_id}"
        line_items.append(
            {
                "product_id": product_id,
                "product_name": product_name,
                "quantity": item.get("quantity", 0),
            }
        )
    return line_items