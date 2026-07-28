"""
WhatsApp interactive button builders for BioMed.
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
}


def register_quantity_mappings(quantity_options: tuple[int, ...]) -> None:
    """Register quantity button IDs → quantity values in BUTTON_TO_CMD.

    Called at startup so the webhook knows that tapping [3] means quantity 3.
    """
    for qty in quantity_options:
        BUTTON_TO_CMD[f"qty_{qty}"] = str(qty)


def build_welcome_buttons(body_text: str) -> dict[str, Any]:
    """
    Welcome buttons shown when a customer says "hi" / "hello".
    WhatsApp allows up to 3 buttons per interactive message.
    """
    return {
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body_text},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "browse_store", "title": "🛍️ Browse Store"}},
                    {"type": "reply", "reply": {"id": "view_cart", "title": "🛒 View Cart"}},
                    {"type": "reply", "reply": {"id": "help", "title": "ℹ️ Help"}},
                ]
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
