from __future__ import annotations

from src.config import get_settings
from src.db.connection import Database, execute, fetch_all, fetch_one


DEFAULT_TEMPLATES = {
    "catalogue": "Available products:\n{catalogue}\n\nReply with something like: 2 shoes",
    "welcome_catalogue": "Hi{customer_name}! Here is our catalogue:\n{catalogue}\n\nReply with something like: 2 shoes",
    "cart_update": "Added {quantity}x {product_name}. Total: {total} {currency}.",
    "address_request": "I need your delivery address. First: what is your area?",
    "address_request_street": "Thanks. Now send your STREET and HOUSE NUMBER.",
    "address_request_city": "Thanks. Now send your CITY.",
    "address_confirmation": "Address saved: {full_address}. Is this correct?",
    "address_confirmation_pending": "Please reply YES to use your saved address, or NO to enter a new one.",
    "order_final": "Order {order_number} confirmed. Total: {total} {currency}. Please send your POP image.",
    "pop_received": "POP received. We will confirm your order shortly.",
    "checkout_blocked": "Your cart is empty. Add a product first, for example: 2 shoes.",
    "unmatched": "I could not match that product. Try something like: 2 shoes or 1 hat.",
    "awaiting_pop": "Your order is waiting for POP. Please send your POP image.",
    "manufacturer_forward": "NEW ORDER {order_number}\nCustomer: {customer_name}\nPhone: {phone_number}\nAddress: {full_address}\nItems:\n{items}\nTotal: {total} {currency}\nPOP: {pop_image_url}",
}


async def build_customer_reply(database: Database, result: dict[str, object] | None) -> dict[str, str] | None:
    if result is None:
        return None

    settings = get_settings()
    action = result.get("action")
    if action == "cart_updated":
        matched = result.get("matched_item") or {}
        cart = result.get("cart") or {}
        text = await render_template(
            database,
            "cart_update",
            quantity=matched.get("quantity", 0),
            product_name=matched.get("product_name", "item"),
            total=cart.get("total", "0.00"),
            currency=settings.store_currency,
        )
        return {"text": text}

    if action == "catalogue":
        return {
            "text": await render_template(
                database,
                "catalogue",
                catalogue=result.get("catalogue", "No products available right now."),
            )
        }

    if action == "welcome_catalogue":
        customer_name = result.get("customer_name") or ""
        prefix = f" {customer_name}" if customer_name else ""
        return {
            "text": await render_template(
                database,
                "welcome_catalogue",
                customer_name=prefix,
                catalogue=result.get("catalogue", "No products available right now."),
            )
        }

    if action == "address_collection_started":
        prompt = result.get("prompt") or await render_template(database, "address_request")
        return {"text": prompt}

    if action == "address_collection_progress":
        current_step = result.get("current_step")
        key = "address_request_street" if current_step == 1 else "address_request_city"
        return {"text": await render_template(database, key)}

    if action == "address_confirmation_requested":
        return {
            "text": await render_template(
                database,
                "address_confirmation",
                full_address=result.get("address", ""),
            )
        }

    if action == "address_confirmation_pending":
        return {"text": await render_template(database, "address_confirmation_pending")}

    if action == "order_created":
        cart = result.get("cart") or {}
        return {
            "text": await render_template(
                database,
                "order_final",
                order_number=result.get("order_number", ""),
                total=cart.get("total", "0.00"),
                currency=settings.store_currency,
            )
        }

    if action == "pop_received":
        return {"text": await render_template(database, "pop_received")}

    if action == "checkout_blocked":
        return {"text": await render_template(database, "checkout_blocked")}

    if action == "unmatched":
        return {"text": await render_template(database, "unmatched")}

    if action == "awaiting_pop":
        return {"text": await render_template(database, "awaiting_pop")}

    return None


async def render_template(database: Database, template_key: str, **context: object) -> str:
    template = await get_template_body(database, template_key)
    return template.format(**context)


async def get_template_body(database: Database, template_key: str) -> str:
    if database.mode == "postgres":
        row = await fetch_one(database, "SELECT body FROM message_templates WHERE template_key = $1", template_key)
    else:
        row = await fetch_one(database, "SELECT body FROM message_templates WHERE template_key = ?", template_key)

    if row and row.get("body"):
        return row["body"]
    return DEFAULT_TEMPLATES[template_key]


async def list_templates(database: Database) -> list[dict[str, str | bool]]:
    if database.mode == "postgres":
        rows = await fetch_all(database, "SELECT template_key, body FROM message_templates")
    else:
        rows = await fetch_all(database, "SELECT template_key, body FROM message_templates")

    stored = {row["template_key"]: row["body"] for row in rows}
    items: list[dict[str, str | bool]] = []
    for template_key in sorted(DEFAULT_TEMPLATES):
        default_body = DEFAULT_TEMPLATES[template_key]
        body = stored.get(template_key, default_body)
        items.append(
            {
                "template_key": template_key,
                "body": body,
                "default_body": default_body,
                "is_customized": body != default_body,
            }
        )
    return items


async def update_template_body(database: Database, template_key: str, body: str) -> dict[str, str | bool]:
    if template_key not in DEFAULT_TEMPLATES:
        raise KeyError(template_key)

    default_body = DEFAULT_TEMPLATES[template_key]
    normalized_body = body.strip()

    if database.mode == "postgres":
        await execute(
            database,
            """
            INSERT INTO message_templates (template_key, body)
            VALUES ($1, $2)
            ON CONFLICT (template_key)
            DO UPDATE SET body = EXCLUDED.body, updated_at = NOW()
            """,
            template_key,
            normalized_body,
        )
    else:
        await execute(
            database,
            """
            INSERT INTO message_templates (template_key, body)
            VALUES (?, ?)
            ON CONFLICT(template_key)
            DO UPDATE SET body = excluded.body, updated_at = CURRENT_TIMESTAMP
            """,
            template_key,
            normalized_body,
        )

    return {
        "template_key": template_key,
        "body": normalized_body,
        "default_body": default_body,
        "is_customized": normalized_body != default_body,
    }
