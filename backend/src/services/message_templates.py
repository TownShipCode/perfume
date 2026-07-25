from __future__ import annotations

from decimal import Decimal

from src.config import get_settings
from src.db.connection import Database, execute, fetch_all, fetch_one


DEFAULT_TEMPLATES = {
    "catalogue": "Available products:\n{catalogue}\n\nReply with a number to order, e.g. \"1\" for 1x FL 1L.",
    "welcome_catalogue": "Hi{customer_name}! Here is our catalogue:\n{catalogue}\n\nReply with a number to order, e.g. \"1\" for 1x FL 1L.",
    "product_detail": "{product_name}\n{description}\nPrice: {price} {currency}\n\nReply with \"1 {product_name}\" to order.",
    "language_selection": "Please choose your language:\nReply: en for English\nReply: zu for isiZulu",
    "language_set": "Language set to {lang}.\n\nHi{customer_name}! Here is our catalogue:\n{catalogue}\n\nReply with a number to order, e.g. \"1\" for 1x FL 1L.",
    "cart_update": "Added {quantity}x {product_name}. Total: {total} {currency}.",
    "address_request_surname": "What is your SURNAME?",
    "address_request": "What is your AREA?",
    "address_request_street": "Thanks. Now send your STREET and HOUSE NUMBER.",
    "address_request_city": "Thanks. Now send your CITY.",
    "address_request_postal_code": "Thanks. Now send your POSTAL CODE.",
    "address_request_email": "Thanks. Now send your EMAIL address.",
    "address_request_province": "Thanks. Now send your PROVINCE.",
    "profile_confirmation": "Your profile:\nName: {customer_name}\nSurname: {surname}\nAddress: {full_address}\nEmail: {email}\nProvince: {province}\n\nIs this correct?",
    "address_confirmation": "Address saved: {full_address}. Is this correct?",
    "address_confirmation_pending": "Please reply YES to use your saved address, or NO to enter a new one.",
    "order_final": "Order {order_number} confirmed.\nSubtotal: {subtotal} {currency}\nDelivery: {shipping_line}\nTotal: {total} {currency}\nPlease send your POP image.",
    "pop_received": "POP received. We will confirm your order shortly.",
    "checkout_blocked": "Your cart is empty. Add a product first, for example: 1 FL 1L.",
    "unmatched": "I could not match that product. Try something like: 1 FL 1L or 1 focus logic.",
    "awaiting_pop": "Your order is waiting for POP. Please send your POP image.",
    "order_cancelled": "Your order has been cancelled. Reply with anything to start again.",
    "manufacturer_forward": "*FOCUS LOGIC ELECTRONIC FORM*\n\n➡️ *NAME:* {customer_name}\n➡️ *ADDRESS:* {full_address}\n➡️ *CELL NO:* {phone_number}\n➡️ *QUANTITY:*\n{items}\n➡️ *FL USERNAME:* {fl_username}\n➡️ *NEW MEMBERSHIP:* {new_membership}\n➡️ *REPURCHASE:* {repurchase}\n➡️ *COURIER:* {courier_name}\n\nOrder: {order_number}\nTotal: {total} {currency}\nBioMed payment: R{fl_amount}\nPOP: {fl_pop_url}",
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
        image_url = result.get("image_url")
        text = await render_template(
            database,
            "catalogue",
            catalogue=result.get("catalogue", "No products available right now."),
        )
        return {
            "text": text,
            **({"image_url": image_url} if image_url else {}),
        }

    if action == "welcome_catalogue":
        customer_name = result.get("customer_name") or ""
        prefix = f" {customer_name}" if customer_name else ""
        image_url = result.get("image_url")
        text = await render_template(
            database,
            "welcome_catalogue",
            customer_name=prefix,
            catalogue=result.get("catalogue", "No products available right now."),
        )
        return {
            "text": text,
            **({"image_url": image_url} if image_url else {}),
        }

    if action == "address_collection_started":
        prompt = result.get("prompt") or await render_template(database, "address_request_surname")
        return {"text": prompt}

    if action == "address_collection_progress":
        current_step = result.get("current_step")
        step_key_map = {
            0: "address_request_surname",
            1: "address_request",
            2: "address_request_street",
            3: "address_request_city",
            4: "address_request_postal_code",
            5: "address_request_email",
            6: "address_request_province",
        }
        key = step_key_map.get(current_step, "address_request")
        return {"text": await render_template(database, key)}

    if action == "address_confirmation_requested":
        return {
            "text": await render_template(
                database,
                "profile_confirmation",
                customer_name=result.get("customer_name", ""),
                surname=result.get("surname", ""),
                full_address=result.get("address", ""),
                email=result.get("email", ""),
                province=result.get("province", ""),
            )
        }

    if action == "address_confirmation_pending":
        return {"text": await render_template(database, "address_confirmation_pending")}

    if action == "order_created":
        cart = result.get("cart") or {}
        shipping_fee = Decimal(result.get("shipping_fee") or "0")
        subtotal = Decimal(cart.get("total") or "0")
        shipping_line = "FREE" if shipping_fee == 0 else f"{shipping_fee} {settings.store_currency}"
        return {
            "text": await render_template(
                database,
                "order_final",
                order_number=result.get("order_number", ""),
                subtotal=str(subtotal),
                shipping_line=shipping_line,
                total=str(subtotal + shipping_fee),
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

    if action == "order_cancelled":
        return {"text": await render_template(database, "order_cancelled")}

    if action == "product_detail":
        return {
            "text": await render_template(
                database,
                "product_detail",
                product_name=result.get("product_name", ""),
                description=result.get("description", ""),
                price=result.get("price", "0"),
                currency=settings.store_currency,
            )
        }

    if action == "language_selection":
        return {"text": await render_template(database, "language_selection")}

    if action == "language_set":
        customer_name = result.get("customer_name") or ""
        prefix = f" {customer_name}" if customer_name else ""
        image_url = result.get("image_url")
        text = await render_template(
            database,
            "language_set",
            lang=result.get("language", "en"),
            customer_name=prefix,
            catalogue=result.get("catalogue", "No products available right now."),
        )
        return {"text": text, **({"image_url": image_url} if image_url else {})}

    return None


async def render_template(database: Database, template_key: str, language: str = "en", **context: object) -> str:
    template = await get_template_body(database, template_key, language)
    return template.format(**context)


async def get_template_body(database: Database, template_key: str, language: str = "en") -> str:
    if database.mode == "postgres":
        row = await fetch_one(database, "SELECT body FROM message_templates WHERE template_key = $1 AND language = $2", template_key, language)
    else:
        row = await fetch_one(database, "SELECT body FROM message_templates WHERE template_key = ? AND language = ?", template_key, language)

    if row and row.get("body"):
        return row["body"]

    # Fallback to English
    if language != "en":
        if database.mode == "postgres":
            row = await fetch_one(database, "SELECT body FROM message_templates WHERE template_key = $1 AND language = 'en'", template_key)
        else:
            row = await fetch_one(database, "SELECT body FROM message_templates WHERE template_key = ? AND language = 'en'", template_key)
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
