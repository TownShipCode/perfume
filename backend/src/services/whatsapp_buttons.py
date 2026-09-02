"""
WhatsApp interactive button builders for Zen Fragrances.
Adopts miana's _build_help_buttons / _BUTTON_TO_CMD pattern.
"""

from __future__ import annotations

from typing import Any

# ── Button ID → internal command mapping ──
# When a user taps a button, the webhook receives a button_reply with an ID.
# We map that ID to a text command that the existing order_flow handlers understand.
BUTTON_TO_CMD: dict[str, str] = {
    "catalogue": "catalogue",
    "browse_store": "catalogue",
    "order": "checkout",
    "help": "help",
    "yes": "yes",
    "no": "no",
    "add_more": "catalogue",
    "browse": "catalogue",
    "pay_yoco": "yoco",
    "pay_eft": "eft",
    "confirm_add": "add_confirm",
    "cancel_add": "add_cancel",
    "view_cart": "cart",
    "become_agent": "become agent",
    "shop_now": "catalogue",
}


def build_welcome_buttons(body_text: str, web_url: str) -> dict[str, Any]:
    """
    Welcome buttons shown when a customer says "hi" / "hello".

    Meta/Kapso interactive BUTTON messages only support reply buttons —
    URL buttons ("type": "url") are NOT allowed in a button message and cause
    the whole send to fail with 400/422. Reply buttons map back to commands via
    BUTTON_TO_CMD. Three clear jobs are offered: order/shop (catalogue),
    become an agent, or help. The web-store link is always in the fallback text.
    """
    return {
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body_text},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "shop_now", "title": "🛍️ Shop / Order"}},
                    {"type": "reply", "reply": {"id": "become_agent", "title": "🤝 Become an Agent"}},
                    {"type": "reply", "reply": {"id": "help", "title": "❓ Help"}},
                ]
            },
        },
    }


def build_visit_store_buttons(body_text: str, web_url: str) -> dict[str, Any]:
    """
    A click-through "Visit Store" message to the web store.

    Meta URL buttons cannot be embedded in a regular interactive button message.
    The correct schema is a dedicated cta_url interactive message
    (interactive.type = "cta_url" with action.name = "cta_url" + parameters).
    Verified to send successfully via Kapso (HTTP 200).
    """
    return {
        "type": "interactive",
        "interactive": {
            "type": "cta_url",
            "header": {"type": "text", "text": "Zen Fragrances"},
            "body": {"text": body_text[:1024]},
            "footer": {"text": "Tap the button below to open the store."},
            "action": {
                "name": "cta_url",
                "parameters": {"display_text": "🛍️ Visit Store", "url": web_url},
            },
        },
    }


def build_confirm_buttons(body_text: str) -> dict[str, Any]:
    """
    Yes/No confirmation buttons for address/profile confirmation.
    """
    return {
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body_text},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "yes", "title": "✅ Yes"}},
                    {"type": "reply", "reply": {"id": "no", "title": "❌ No"}},
                ]
            },
        },
    }


def build_quantity_buttons(body_text: str, quantity_options: tuple[int, ...]) -> dict[str, Any]:
    """
    Quantity selection buttons shown after a customer picks a product.
    WhatsApp allows up to 3 buttons — we show the first 3 quantity options.
    """
    buttons = [
        {"type": "reply", "reply": {"id": f"qty_{qty}", "title": str(qty)}}
        for qty in quantity_options[:3]
    ]
    return {
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body_text},
            "action": {"buttons": buttons},
        },
    }


def build_cart_buttons(body_text: str) -> dict[str, Any]:
    """Cart summary buttons — add more items or proceed to checkout."""
    return {
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body_text},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "add_more", "title": "➕ Add More"}},
                    {"type": "reply", "reply": {"id": "order", "title": "🛒 Checkout"}},
                ]
            },
        },
    }


def build_confirm_order_buttons(body_text: str) -> dict[str, Any]:
    """Confirmation buttons before adding to cart."""
    return {
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body_text},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "confirm_add", "title": "✅ Confirm"}},
                    {"type": "reply", "reply": {"id": "cancel_add", "title": "❌ Cancel"}},
                ]
            },
        },
    }


def build_payment_buttons(body_text: str, methods_enabled: tuple[str, ...]) -> dict[str, Any]:
    """Payment selection buttons — Yoco or EFT based on config."""
    buttons: list[dict[str, Any]] = []
    if "yoco" in methods_enabled:
        buttons.append({"type": "reply", "reply": {"id": "pay_yoco", "title": "💳 Pay with Yoco"}})
    if "eft" in methods_enabled:
        buttons.append({"type": "reply", "reply": {"id": "pay_eft", "title": "🏦 EFT / Deposit"}})
    return {
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body_text},
            "action": {"buttons": buttons},
        },
    }


def register_picker_mappings(candidates: list[dict[str, Any]]) -> None:
    """Register LIST row ids (pick_<product_number>) → product-number commands.

    When a user taps a row in the product LIST picker, the webhook receives a
    list_reply whose id we map back to a bare product number, so the existing
    numeric ordering path (quantity prompt → add) resumes seamlessly.
    """
    for product in candidates:
        number = product.get("product_number")
        if number is not None:
            BUTTON_TO_CMD[f"pick_{number}"] = str(number)


def build_product_list_picker(
    body_text: str,
    candidates: list[dict[str, Any]],
    button_label: str = "Select product",
) -> dict[str, Any]:
    """Build a WhatsApp interactive LIST message for ambiguous product names.

    When a partial/ambiguous name matches several products (e.g. "scandal"
    = SCANDAL men OR women; "million" = ONE MILLION OR LADY MILLION), present
    each match as a tappable row instead of guessing. Max 10 rows/section.
    """
    rows: list[dict[str, str]] = []
    for product in candidates[:10]:
        number = product.get("product_number")
        name = str(product.get("name") or "Product")
        gender = str(product.get("gender") or "").capitalize()
        price = product.get("price")
        title = f"{number}. {name}"[:24]
        description = f"R{price} · {gender}"[:72] if price is not None else f"{gender}"[:72]
        rows.append({"id": f"pick_{number}", "title": title, "description": description})

    return {
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {"text": body_text[:1024]},
            "action": {
                "button": button_label[:20],
                "sections": [
                    {"title": "Products", "rows": rows},
                ],
            },
        },
    }
