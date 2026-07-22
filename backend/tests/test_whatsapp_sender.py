from __future__ import annotations

import asyncio

from src.config import get_settings
from src.services import whatsapp_sender


def test_deliver_reply_dry_run(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOCAL_SQLITE_PATH", str(tmp_path / "sender.db"))
    monkeypatch.setenv("WHATSAPP_SEND_MODE", "dry_run")
    get_settings.cache_clear()

    async def scenario() -> None:
        result = await whatsapp_sender.deliver_reply(
            {"from": "27820000000"},
            {"text": "Hello"},
        )
        assert result is not None
        assert result["status"] == "dry_run"
        assert result["payload"]["to"] == "27820000000"
        assert result["payload"]["text"]["body"] == "Hello"

    asyncio.run(scenario())
    get_settings.cache_clear()


def test_deliver_reply_live_uses_provider_transport(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOCAL_SQLITE_PATH", str(tmp_path / "sender-live.db"))
    monkeypatch.setenv("WHATSAPP_SEND_MODE", "live")
    monkeypatch.setenv("WHATSAPP_API_KEY", "test-key")
    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "123456")
    monkeypatch.setenv("WHATSAPP_API_BASE_URL", "https://example.test/v1")
    get_settings.cache_clear()

    captured: dict[str, object] = {}

    async def fake_post(settings, payload):
        captured["url"] = f"{settings.whatsapp_api_base_url}/{settings.whatsapp_phone_number_id}/messages"
        captured["payload"] = payload
        return {"messages": [{"id": "msg-1"}]}

    monkeypatch.setattr(whatsapp_sender, "_post_whatsapp_message", fake_post)

    async def scenario() -> None:
        result = await whatsapp_sender.deliver_reply(
            {"from": "27820000000"},
            {"text": "Reply body"},
        )
        assert result is not None
        assert result["status"] == "sent"
        assert result["provider_message_id"] == "msg-1"
        assert captured["url"] == "https://example.test/v1/123456/messages"
        assert captured["payload"]["text"]["body"] == "Reply body"

    asyncio.run(scenario())
    get_settings.cache_clear()
