from __future__ import annotations

import asyncio

from src.config import get_settings
from src.db.connection import close_database, connect_database, initialize_database
from src.services.message_templates import build_customer_reply, DEFAULT_TEMPLATES


def test_build_customer_reply_uses_defaults(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOCAL_SQLITE_PATH", str(tmp_path / "reply-defaults.db"))
    get_settings.cache_clear()

    async def scenario() -> None:
        settings = get_settings()
        database = await connect_database(settings)
        try:
            await initialize_database(database)
            # Test that build_customer_reply works with defaults
            reply = await build_customer_reply(
                database,
                {"action": "text", "text": "Hello world"},
            )
            assert reply is not None
            assert reply["text"] == "Hello world"

            # Verify DEFAULT_TEMPLATES has core keys
            assert "catalogue" in DEFAULT_TEMPLATES
            assert "cart_update" in DEFAULT_TEMPLATES
            assert "order_cancelled" in DEFAULT_TEMPLATES
            assert "manufacturer_forward" in DEFAULT_TEMPLATES
        finally:
            await close_database(database)

    asyncio.run(scenario())
    get_settings.cache_clear()
