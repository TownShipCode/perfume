from __future__ import annotations

import asyncio
import hashlib
import hmac

from src.config import get_settings
from src.db.connection import close_database, connect_database, initialize_database
from src.services.catalog_service import ProductInput, create_product
from src.services.order_flow import handle_text_message
from src.services.session_service import get_session_by_phone
from src.config import Settings
from src.services.whatsapp_webhook import extract_message_event, verify_signature, verify_webhook_challenge


def make_settings(**overrides: object) -> Settings:
    values = {
        "app_env": "development",
        "log_level": "INFO",
        "store_name": "Test Store",
        "store_currency": "ZAR",
        "api_base_url": "http://localhost:8000",
        "database_url": None,
        "local_sqlite_path": __import__("pathlib").Path("app.db"),
        "whatsapp_api_base_url": "https://graph.facebook.com/v24.0",
        "whatsapp_send_mode": "dry_run",
        "whatsapp_api_key": None,
        "whatsapp_phone_number_id": None,
        "whatsapp_verify_token": "verify-token",
        "whatsapp_app_secret": "secret-key",
        "dashboard_api_key": None,
        "admin_phone": None,
        "manufacturer_phone": None,
        "whatsapp_greeting_commands": ("hi",),
        "whatsapp_catalog_commands": ("menu",),
        "whatsapp_checkout_commands": ("done",),
        "whatsapp_confirm_commands": ("yes",),
        "whatsapp_reject_commands": ("no",),
        "shipping_fee": __import__("decimal").Decimal("109.00"),
        "free_shipping_threshold": __import__("decimal").Decimal("2000.00"),
        "whatsapp_cancel_commands": ("cancel",),
        "pop_expiry_hours": 24,
        "default_language": "en",
        "supported_languages": ("en", "zu"),
        "cors_origins": ("http://localhost:5173",),
        "sentry_dsn": None,
    }
    values.update(overrides)
    return Settings(**values)


def test_verify_webhook_challenge_accepts_valid_token() -> None:
    settings = make_settings()
    assert verify_webhook_challenge("subscribe", "verify-token", "12345", settings) == "12345"


def test_verify_signature_accepts_matching_sha256_header() -> None:
    settings = make_settings()
    body = b'{"hello":"world"}'
    signature = "sha256=" + hmac.new(b"secret-key", body, hashlib.sha256).hexdigest()
    assert verify_signature(body, signature, settings) is True


def test_extract_message_event_supports_meta_payload_shape() -> None:
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "contacts": [{"profile": {"name": "Alice"}}],
                            "messages": [
                                {
                                    "id": "wamid.1",
                                    "from": "27820000000",
                                    "type": "text",
                                    "text": {"body": "2 shoes"},
                                }
                            ],
                        }
                    }
                ]
            }
        ]
    }

    event = extract_message_event(payload)
    assert event is not None
    assert event["message_id"] == "wamid.1"
    assert event["text"] == "2 shoes"
    assert event["profile_name"] == "Alice"


def test_webhook_text_message_updates_session_state(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOCAL_SQLITE_PATH", str(tmp_path / "webhook-test.db"))
    monkeypatch.setenv("WHATSAPP_APP_SECRET", "secret-key")
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "verify-token")
    get_settings.cache_clear()

    async def scenario() -> None:
        settings = get_settings()
        database = await connect_database(settings)
        try:
            await initialize_database(database)
            await create_product(
                database,
                ProductInput(
                    product_number=1,
                    name="Red Shoes",
                    price="350.00",
                    image_url="https://example.com/red-shoes.jpg",
                    keywords=["shoe", "shoes", "red shoe"],
                ),
            )

            result = await handle_text_message(
                database,
                {
                    "message_id": "wamid.200",
                    "from": "27820000000",
                    "type": "text",
                    "text": "2 shoes",
                    "profile_name": "Alice",
                },
            )

            assert result["action"] == "cart_updated"
            assert result["state"] == "ordering"
            assert result["cart"]["items"][0]["quantity"] == 2
            assert result["cart"]["total"] == "700.00"

            stored_session = await get_session_by_phone(database, "27820000000")
            assert stored_session is not None
            assert stored_session["state"] == "ordering"
            assert stored_session["cart"][0]["quantity"] == 2
        finally:
            await close_database(database)

    asyncio.run(scenario())

    get_settings.cache_clear()
