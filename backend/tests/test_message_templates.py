from __future__ import annotations

import asyncio

from src.config import get_settings
from src.db.connection import close_database, connect_database, initialize_database
from src.services.message_templates import build_customer_reply, list_templates, update_template_body


def test_build_customer_reply_uses_defaults_when_templates_missing(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOCAL_SQLITE_PATH", str(tmp_path / "reply-defaults.db"))
    get_settings.cache_clear()

    async def scenario() -> None:
        settings = get_settings()
        database = await connect_database(settings)
        try:
            await initialize_database(database)
            reply = await build_customer_reply(
                database,
                {
                    "action": "cart_updated",
                    "matched_item": {"quantity": 2, "product_name": "Red Shoes"},
                    "cart": {"total": "700.00"},
                },
            )
            assert reply is not None
            assert "2x Red Shoes" in reply["text"]
            assert "700.00" in reply["text"]
        finally:
            await close_database(database)

    asyncio.run(scenario())
    get_settings.cache_clear()


def test_template_listing_and_update(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOCAL_SQLITE_PATH", str(tmp_path / "template-admin.db"))
    get_settings.cache_clear()

    async def scenario() -> None:
        settings = get_settings()
        database = await connect_database(settings)
        try:
            await initialize_database(database)
            templates = await list_templates(database)
            manufacturer = next(item for item in templates if item["template_key"] == "manufacturer_forward")
            assert manufacturer["is_customized"] is False

            updated = await update_template_body(database, "manufacturer_forward", "Forward {order_number}")
            assert updated["body"] == "Forward {order_number}"
            assert updated["is_customized"] is True

            refreshed = await list_templates(database)
            manufacturer = next(item for item in refreshed if item["template_key"] == "manufacturer_forward")
            assert manufacturer["body"] == "Forward {order_number}"
            assert manufacturer["is_customized"] is True
        finally:
            await close_database(database)

    asyncio.run(scenario())
    get_settings.cache_clear()


def test_build_customer_reply_uses_stored_template(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOCAL_SQLITE_PATH", str(tmp_path / "reply-db.db"))
    get_settings.cache_clear()

    async def scenario() -> None:
        settings = get_settings()
        database = await connect_database(settings)
        try:
            await initialize_database(database)
            database.connection.execute(
                "INSERT INTO message_templates (template_key, body) VALUES (?, ?)",
                ("pop_received", "Custom POP reply."),
            )
            database.connection.commit()
            reply = await build_customer_reply(database, {"action": "pop_received"})
            assert reply == {"text": "Custom POP reply."}
        finally:
            await close_database(database)

    asyncio.run(scenario())
    get_settings.cache_clear()
