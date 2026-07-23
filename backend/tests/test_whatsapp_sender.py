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
        assert result["recipient"] == "27820000000"
        assert "Hello" in str(result["text"])

    asyncio.run(scenario())
    get_settings.cache_clear()


def test_deliver_reply_live_meta_transport(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOCAL_SQLITE_PATH", str(tmp_path / "sender-live.db"))
    monkeypatch.setenv("WHATSAPP_PROVIDER", "meta")
    monkeypatch.setenv("WHATSAPP_SEND_MODE", "live")
    monkeypatch.setenv("WHATSAPP_API_KEY", "test-key")
    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "123456")
    monkeypatch.setenv("WHATSAPP_API_BASE_URL", "https://example.test/v1")
    get_settings.cache_clear()

    captured: dict[str, object] = {}

    async def fake_meta(settings, to, text, phone_id):
        captured["url"] = f"{settings.whatsapp_api_base_url}/{phone_id}/messages"
        captured["to"] = to
        captured["text"] = text
        return {"status": "sent", "recipient": to, "text": text[:100]}

    monkeypatch.setattr(whatsapp_sender, "_send_meta", fake_meta)

    async def scenario() -> None:
        result = await whatsapp_sender.deliver_reply(
            {"from": "27820000000"},
            {"text": "Reply body"},
        )
        assert result is not None
        assert result["status"] == "sent"
        assert captured["url"] == "https://example.test/v1/123456/messages"
        assert captured["to"] == "27820000000"
        assert captured["text"] == "Reply body"

    asyncio.run(scenario())
    get_settings.cache_clear()
