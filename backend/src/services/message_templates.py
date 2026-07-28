# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownParameterType=false, reportUnknownLambdaType=false, reportReturnType=false, reportAttributeAccessIssue=false

from __future__ import annotations

from decimal import Decimal
from typing import Any

from src.config import get_settings
from src.db.connection import Database, execute, fetch_all, fetch_one


DEFAULT_TEMPLATES = {
    "catalogue": "📋 *Available Products*\n\n{catalogue}\n\n💡 Type a number to order, or *info 1* for details & image.",
    "welcome_catalogue": "👋 Hi{customer_name}! Here is our catalogue:\n\n{catalogue}\n\n💡 Type a number to order, or *info 1* for details & image.",
    "product_detail": "{product_name}\n{description}\nPrice: R{price}\n\n_Reply with \"1 {product_name}\" to order._",
    "language_selection": "🌍 Please choose your language:\n🇬🇧 Reply: en for English\n🇿🇦 Reply: zu for isiZulu",
    "language_set": "✅ Language set to {lang}.\n\n👋 Hi{customer_name}! Here is our catalogue:\n\n{catalogue}\n\n_Reply with a number to order, e.g. \"1\" for 1x FL 1L._",
    "cart_update": "🛒 Added {quantity}x *{product_name}*\nTotal: R{total}",
    "address_request_name": "👤 What is your FIRST NAME?",
    "address_request_surname": "📝 What is your SURNAME?",
    "address_request": "📍 What is your AREA?",
    "address_request_street": "🏠 Now send your STREET and HOUSE NUMBER.",
    "address_request_city": "🏙️ Now send your CITY.",
    "address_request_postal_code": "📮 Now send your POSTAL CODE.",
    "address_request_province": "🗺️ Now send your PROVINCE.",
    "address_collection_intro": "🚚 *Let's get your order to you!*\n\nTo make sure your products reach you safely, please share a few delivery details.",
    "profile_confirmation": "📋 *Your Profile*\n\n👤 Name: {customer_name}\n📝 Surname: {surname}\n📍 Address: {full_address}\n📧 Email: {email}\n🗺️ Province: {province}\n\nIs this correct?",
    "address_confirmation": "✅ Address saved: {full_address}. Is this correct?",
    "address_confirmation_pending": "Please reply *YES* to use your saved address, or *NO* to enter a new one.",
    "order_final": "✅ *Order #{order_number}*\n\nSubtotal: R{subtotal}\nDelivery: {shipping_line}\n*Total: R{total}*\n\nHow would you like to pay?",
    "payment_selection": "",
    "bank_details": "🏦 *EFT / Bank Deposit*\n\nBank: {bank_name}\nAccount: {account_number}\nHolder: {account_holder}\nBranch: {branch_code}\nReference: *{order_number}*\n\n📸 Please send your POP once paid.\n🗑️ Type *CANCEL* to cancel.",
    "yoco_payment_link": "💳 *Pay securely with Yoco*\n\nTap the link to complete your payment:\n{checkout_url}\n\nYour order will be confirmed automatically.",
    "payment_received": "✅ *Payment received — thank you!* 🙏\n\nOrder #{order_number} is confirmed. We'll notify you once your order is on the way.",
    "payment_declined": "❌ *Payment declined*\n\nPlease try again or use EFT / Bank Deposit instead.\n\nType *CATALOGUE* to browse or *CHECKOUT* to try again.",
    "pop_received": "📸 *POP received — thank you!* 🙏\n\nWe'll review your payment and confirm your order shortly.\nYou'll receive a notification once your order is on the way.",
    "order_confirmed": "✅ *Order #{order_number} Confirmed!* 🎉\n\nHi {customer_name}, your order has been processed and sent to our fulfilment team.\n\n🛒 {items}\n💰 Total: R{total}\n🚚 Delivery: {courier}\n\nWe'll notify you once your order is on the way. Thank you for choosing Zen Fragrances! ✨",
    "order_shipped": "🚚 *Your order is on the way!*\n\nOrder #{order_number}\n📦 Waybill: {tracking_info}\n🔗 Track your order: {tracking_url}\n\n📍 Delivery to:\n{full_address}\n\nThank you for choosing Zen Fragrances! ✨",
    "checkout_blocked": "🛒 Your cart is empty. Add a product first — reply with a number like *1*.",
    "unmatched": "❓ I couldn't match that.\n\nType *CATALOGUE* to see products, or a product number like *1* to start ordering.",
    "awaiting_pop": "⏳ Your order is waiting for POP (proof of payment).\n\n📸 Please send your POP image to confirm.\n🗑️ Type *CANCEL* to cancel this order.\n\n_Your order will expire in {expiry_hours}h if no POP is received._",
    "order_cancelled": "🗑️ Order cancelled.\n\nWhenever you're ready, just say *Hi* to start a new order. We're here for you! ✨",
    "manufacturer_forward": "📦 *New Order #{order_number}*\n\n👤 {customer_name}\n📞 {phone_number}\n📍 {full_address}\n\n🛒 Items:\n{items}\n\n🚚 Courier: {courier_name}",
}


async def build_customer_reply(database: Database, result: dict[str, object] | None) -> dict[str, Any] | None:
    if result is None:
        return None

    settings = get_settings()
    action = result.get("action")
    if action == "cart_summary":
        # On-demand cart view with line items + add more / checkout buttons
        from src.services.whatsapp_buttons import build_cart_buttons
        cart = result.get("cart") or {}
        items = cart.get("items", [])
        item_lines = "\n".join(f"  {it.get('quantity', 0)}× {it.get('product_name', '?')} — R{it.get('subtotal', '0')}" for it in items) if items else "(empty)"
        body = f"🛒 *Your Cart*\n\n{item_lines}\n\n💴 Total: R{cart.get('total', '0.00')}\n\nWhat would you like to do?"
        return {
            "type": "interactive",
            "payload": build_cart_buttons(body),
            "fallback_text": f"🛒 Cart total: R{cart.get('total', '0.00')}. Type CHECKOUT to order or type a product name to add more.",
        }

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

    if action == "catalogue_web":
        web_url = result.get("web_url", "")
        return {"text": f"🛍️ *Browse Our Catalogue*\n\nView all fragrances with images, filters & scent notes:\n\n🔗 {web_url}\n\n⚡ Or order directly here — type a product name, e.g. _\"5 Rose Oud\"_."}

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

    if action == "interactive_welcome":
        # Send tappable WhatsApp buttons instead of plain text
        from src.services.whatsapp_buttons import build_welcome_buttons
        customer_name = result.get("customer_name") or ""
        greeting = f" {customer_name}" if customer_name else ""
        body = result.get("greeting") or f"👋 *Welcome to Zen Fragrances!* ✨\n\nWholesale perfumes for agents.\nType a product name to order — e.g. \"5 Rose Oud\"\n\nWhat would you like to do?"
        web_url = result.get("web_url", "")
        fallback = f"👋 Hi{greeting}! Welcome to Zen Fragrances.\n\n⚡ Type a product name to order (e.g. \"5 Rose Oud\")\n🛍️ Browse catalogue: {web_url}\n📋 Type HELP for all commands."
        return {
            "type": "interactive",
            "payload": build_welcome_buttons(body),
            "fallback_text": fallback,
        }

    if action == "quantity_selection":
        # Send quantity buttons after product selection.
        # If image_url is present, send two messages: image + description, then buttons.
        from src.services.whatsapp_buttons import build_quantity_buttons
        settings = get_settings()
        product_name = result.get("product_name", "item")
        price = result.get("price", "0")
        description = result.get("description", "")
        image_url = result.get("image_url")

        if image_url and description:
            caption = f"🛒 *{product_name}* — R{price}\n\n{description}"
            buttons_body = f"How many {product_name}?"
            return [
                {"image_url": image_url, "text": caption},
                {
                    "type": "interactive",
                    "payload": build_quantity_buttons(buttons_body, settings.quantity_options),
                    "fallback_text": f"🛒 *{product_name}* — R{price}\n\nHow many? Type a number (e.g. 2).",
                },
            ]

        body = f"🛒 *{product_name}* — R{price}\n\nHow many would you like?\nType a number or tap:"
        return {
            "type": "interactive",
            "payload": build_quantity_buttons(body, settings.quantity_options),
            "fallback_text": f"🛒 *{product_name}* — R{price}\n\nHow many? Type a number (e.g. 2).",
        }

    if action == "address_collection_started":
        prompt = result.get("prompt") or await render_template(database, "address_request_name")
        return {"text": prompt}

    if action == "address_collection_progress":
        if "prompt" in result:
            return {"text": str(result["prompt"])}
        current_step = result.get("current_step")
        step_key_map = {
            0: "address_request_name",
            1: "address_request_surname",
            2: "address_request",
            3: "address_request_street",
            4: "address_request_city",
            5: "address_request_postal_code",
            6: "address_request_province",
        }
        key = step_key_map.get(current_step, "address_request")
        return {"text": await render_template(database, key)}

    if action == "interactive_address_confirm":
        # Send Yes/No buttons for address confirmation (miana pattern)
        from src.services.whatsapp_buttons import build_confirm_buttons
        body = await render_template(
            database,
            "profile_confirmation",
            customer_name=result.get("customer_name", ""),
            surname=result.get("surname", ""),
            full_address=result.get("address", ""),
            email=result.get("email", ""),
            province=result.get("province", ""),
        )
        return {
            "type": "interactive",
            "payload": build_confirm_buttons(body),
            "fallback_text": body + "\n\nReply YES or NO.",
        }

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
        shipping_line = "FREE" if shipping_fee == 0 else f"R{shipping_fee}"
        total = str(subtotal + shipping_fee)
        order_number = result.get("order_number", "")

        # Send payment selection buttons
        from src.services.whatsapp_buttons import build_payment_buttons
        settings = get_settings()
        body = f"✅ *Order #{order_number}*\n\nSubtotal: R{subtotal}\nDelivery: {shipping_line}\n*Total: R{total}*\n\nHow would you like to pay?"
        return {
            "type": "interactive",
            "payload": build_payment_buttons(body, settings.payment_methods_enabled),
            "fallback_text": f"✅ Order #{order_number} — R{total}. Reply YOCO to pay online or EFT for bank details.",
        }

    if action == "pop_received":
        return {"text": await render_template(database, "pop_received")}

    if action == "checkout_blocked":
        settings = get_settings()
        web_url = settings.web_base_url.rstrip("/")
        return {"text": f"🛒 *Your cart is empty!*\n\n🛍️ Browse our catalogue online:\n{web_url}/catalogue\n\nOr type a product name here, e.g. _\"5 Rose Oud\"_."}

    if action == "product_not_found":
        attempted = result.get("attempted_number", "?")
        settings = get_settings()
        web_url = settings.web_base_url.rstrip("/")
        return {"text": f"❓ Product #{attempted} not found.\n\n🛍️ Browse our full catalogue online:\n{web_url}/catalogue\n\nOr type a product name directly, e.g. _\"5 Rose Oud\"_."}

    if action == "unmatched":
        return {"text": await render_template(database, "unmatched")}

    if action == "awaiting_pop":
        return {"text": await render_template(database, "awaiting_pop", expiry_hours=str(settings.pop_expiry_hours))}

    if action == "order_cancelled":
        return {"text": await render_template(database, "order_cancelled")}

    if action == "product_detail":
        image_url = result.get("image_url")
        product_url = result.get("product_url", "")
        web_link = f"\n\n🔗 View online: {product_url}" if product_url else ""
        return {
            "text": await render_template(
                database,
                "product_detail",
                product_name=result.get("product_name", ""),
                description=result.get("description", ""),
                price=result.get("price", "0"),
                currency=settings.store_currency,
            ) + web_link,
            **(({"image_url": image_url} if image_url else {})),
        }

    if action == "confirm_order":
        from src.services.whatsapp_buttons import build_confirm_order_buttons
        body = f"🛒 *Confirm your order*\n\n{result.get('quantity', '?')}× *{result.get('product_name', 'item')}*\nR{result.get('unit_price', '0')} each = R{result.get('unit_total', '0')}\n\nAdd to cart?"
        reply = {
            "type": "interactive",
            "payload": build_confirm_order_buttons(body),
            "fallback_text": f"🛒 Adding {result.get('quantity', '?')}× {result.get('product_name', 'item')} at R{result.get('unit_total', '0')}. Reply YES to confirm or type CANCEL.",
        }
        if result.get("image_url"):
            return [{"image_url": result["image_url"], "text": f"*{result.get('product_name', 'item')}*"}, reply]
        return reply

    if action == "order_confirmed":
        cart = result.get("cart") or {}
        total = cart.get("total", "0")
        item_count = len(cart.get("items", []))
        tips = "\n\n💡 *Tips:* `stock Rose Oud` · `cart` · `checkout` · `cancel`" if item_count == 1 else ""
        return {"text": f"✅ *{result.get('quantity', '?')}× {result.get('product_name', 'item')} added!*\n\n🛒 Cart: {item_count} item{'s' if item_count != 1 else ''} · R{total}\n\nType another product or *CHECKOUT* when ready.{tips}"}

    if action == "order_cancelled_pending":
        return {"text": "❌ Order cancelled.\n\nType a product name to start again, or *HELP* for options."}

    if action == "repeat_order":
        item_list = result.get("item_list", "")
        total = result.get("total", "0")
        return {"text": f"🔄 *Last order restored!*\n\n{item_list}\n\n💰 Total: R{total}\n\nType *CHECKOUT* to order or add more products.\nType *CANCEL* to clear."}

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

    if action == "payment_selection":
        from src.services.whatsapp_buttons import build_payment_buttons
        settings = get_settings()
        body = f"✅ *Order #{result.get('order_number', '')}*\n\nSubtotal: R{result.get('subtotal', '0')}\nDelivery: {result.get('shipping_line', '')}\n*Total: R{result.get('total', '0')}*\n\nHow would you like to pay?"
        return {
            "type": "interactive",
            "payload": build_payment_buttons(body, settings.payment_methods_enabled),
            "fallback_text": f"✅ Order #{result.get('order_number', '')} confirmed — R{result.get('total', '0')}. Reply YOCO to pay online or EFT for bank details.",
        }

    if action == "bank_details":
        settings = get_settings()
        return {
            "text": await render_template(
                database,
                "bank_details",
                bank_name=settings.bank_name,
                account_number=settings.account_number,
                account_holder=settings.account_holder,
                branch_code=settings.branch_code,
                order_number=result.get("order_number", ""),
            ),
        }

    if action == "yoco_payment_link":
        return {
            "text": await render_template(
                database,
                "yoco_payment_link",
                checkout_url=result.get("checkout_url", ""),
            ),
        }

    if action == "payment_received":
        return {
            "text": await render_template(
                database,
                "payment_received",
                order_number=result.get("order_number", ""),
            ),
        }

    if action == "payment_declined":
        return {"text": await render_template(database, "payment_declined")}

    if action == "price_list":
        url = result.get("url", "")
        return {"text": f"📋 *Agent Wholesale Price List*\n\nDownload or print our current wholesale price list:\n{url}\n\n_Share this with your customers. Suggested retail: 2× wholesale._"}

    if action == "catalog_link":
        catalog_url = result.get("catalog_url", "")
        return {"text": f"🛍️ *WhatsApp Catalog*\n\nBrowse our full product catalog on WhatsApp:\n{catalog_url}\n\nTap the link to view all fragrances with images and prices."}

    if action == "become_agent":
        customer_name = result.get("customer_name", "")
        greeting = f" {customer_name}" if customer_name else ""
        register_url = result.get("register_url", "")
        return {"text": f"🚀 *Become a Zen Fragrances Agent!*\n\nHi{greeting}! Ready to start your own perfume business?\n\n✨ *Why become an agent?*\n• Buy at wholesale prices (R40-100/bottle)\n• Sell at your own retail price (~2× markup)\n• No starter pack required\n• Order via WhatsApp — no website needed\n• Earn commission by building your own team\n\n📝 Register here:\n{register_url}\n\nAlready registered? Just start ordering — your agent discount is automatic!"}

    if action == "internal_error":
        return {"text": result.get("text", "Something went wrong. Please try again.")}

    if action == "text":
        return {"text": str(result.get("text", ""))}

    return None


async def render_template(database: Database, template_key: str, language: str = "en", **context: object) -> str:
    """Render a template from DEFAULT_TEMPLATES. Database + language params kept for backward compat."""
    return DEFAULT_TEMPLATES[template_key].format(**context)
