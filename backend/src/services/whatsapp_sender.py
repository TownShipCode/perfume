from __future__ import annotations

import asyncio
import json
from typing import Any
from urllib import request as urllib_request

from src.config import Settings, get_settings


async def deliver_reply(event: dict[str, Any], reply: dict[str, str] | None) -> dict[str, Any] | None:
    if reply is None:
        return None

    settings = get_settings()
    recipient = event.get("from")
    if not recipient:
        return {"status": "skipped", "reason": "missing_recipient"}

    payload = {
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "text",
        "text": {"body": reply["text"]},
    }

    return await _send_payload(settings, payload)


async def send_text_message(recipient: str, text: str) -> dict[str, Any]:
    settings = get_settings()
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "text",
        "text": {"body": text},
    }

    return await _send_payload(settings, payload)


async def _send_payload(settings: Settings, payload: dict[str, Any]) -> dict[str, Any]:
    if settings.whatsapp_send_mode == "off":
        return {"status": "skipped", "reason": "send_mode_off", "payload": payload}

    if settings.whatsapp_send_mode != "live":
        return {"status": "dry_run", "payload": payload}

    if not settings.whatsapp_api_key or not settings.whatsapp_phone_number_id:
        if settings.is_production:
            return {"status": "failed", "reason": "missing_provider_configuration", "payload": payload}
        return {"status": "skipped", "reason": "missing_provider_configuration", "payload": payload}

    try:
        response = await _post_whatsapp_message(settings, payload)
    except Exception as error:
        return {
            "status": "failed",
            "error": str(error),
            "payload": payload,
        }

    return {
        "status": "sent",
        "payload": payload,
        "provider_response": response,
        "provider_message_id": _extract_provider_message_id(response),
    }


def _extract_provider_message_id(response: dict[str, Any]) -> str | None:
    messages = response.get("messages")
    if not isinstance(messages, list) or not messages:
        return None
    first = messages[0]
    if not isinstance(first, dict):
        return None
    value = first.get("id")
    return value if isinstance(value, str) and value else None


async def _post_whatsapp_message(settings: Settings, payload: dict[str, Any]) -> dict[str, Any]:
    url = f"{settings.whatsapp_api_base_url.rstrip('/')}/{settings.whatsapp_phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {settings.whatsapp_api_key}",
        "Content-Type": "application/json",
        "User-Agent": "curl/8.0",
    }
    return await asyncio.to_thread(_send_request, url, headers, payload)


def _send_request(url: str, headers: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib_request.Request(url, data=body, headers=headers, method="POST")
    with urllib_request.urlopen(req, timeout=30) as response:
        text = response.read().decode("utf-8")
    return json.loads(text) if text else {"ok": True}
