from __future__ import annotations

from src.config import get_settings
from src.db.connection import Database
from src.services.catalog_service import get_products_by_ids
from src.services.message_templates import render_template
from src.services.order_service import get_order_by_id, record_order_forwarding
from src.services.whatsapp_sender import send_text_message


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
        "order": updated,
    }


async def _build_forward_message(database: Database, order: dict[str, object]) -> tuple[str | None, str, list[dict[str, object]]]:
    settings = get_settings()
    recipient = settings.manufacturer_phone
    products_by_id = await get_products_by_ids(
        database,
        [int(item.get("product_id", 0)) for item in order.get("items") or []],
    )
    line_items = _build_line_items(order.get("items") or [], products_by_id)
    message = await render_template(
        database,
        "manufacturer_forward",
        order_number=order["order_number"],
        customer_name=order.get("name") or order.get("phone_number") or "Customer",
        phone_number=order.get("phone_number") or "",
        full_address=order.get("full_address") or "",
        items=_format_items(line_items),
        total=order.get("total") or "0.00",
        currency=settings.store_currency,
        pop_image_url=order.get("pop_image_url") or "not provided",
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