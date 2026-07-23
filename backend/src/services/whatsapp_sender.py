from __future__ import annotations

import json
from typing import Any

from src.config import Settings, get_settings


async def deliver_reply(event: dict[str, Any], reply: dict[str, str] | None) -> dict[str, Any] | None:
    if reply is None:
        return None

    settings = get_settings()
    recipient = event.get("from")
    if not recipient:
        return {"status": "skipped", "reason": "missing_recipient"}

    return await _send(settings, recipient, reply["text"])


async def send_text_message(recipient: str, text: str) -> dict[str, Any]:
    settings = get_settings()
    return await _send(settings, recipient, text)


async def _send(settings: Settings, to: str, text: str) -> dict[str, Any]:
    if settings.whatsapp_send_mode == "off":
        return {"status": "skipped", "reason": "send_mode_off", "text": text[:100]}

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }

    if settings.whatsapp_send_mode != "live":
        return {"status": "dry_run", "recipient": to, "text": text[:100], "payload": payload}

    if not settings.whatsapp_api_key:
        return {"status": "failed", "reason": "missing_api_key"}

    phone_id = settings.whatsapp_phone_number_id or "1102791516242887"

    try:
        if settings.whatsapp_provider == "kapso":
            return await _send_kapso(settings, to, text, phone_id)
        else:
            return await _send_meta(settings, to, text, phone_id)
    except Exception as error:
        return {"status": "failed", "error": str(error)}


async def _send_kapso(settings: Settings, to: str, text: str, phone_id: str) -> dict[str, Any]:
    """Send via Kapso gateway — mirrors miana's _send_via_kapso pattern."""
    import aiohttp

    url = f"https://api.kapso.ai/meta/whatsapp/v24.0/{phone_id}/messages"
    headers = {"X-API-Key": settings.whatsapp_api_key or "", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers,
                                timeout=aiohttp.ClientTimeout(total=15)) as resp:
            body = await resp.text()
            if resp.status in (200, 201):
                return {"status": "sent", "recipient": to, "text": text[:100]}
            return {"status": "failed", "http_status": resp.status, "body": body[:200]}


async def _send_meta(settings: Settings, to: str, text: str, phone_id: str) -> dict[str, Any]:
    """Send via Meta WhatsApp Cloud API directly."""
    import asyncio
    from urllib import request as urllib_request

    url = f"{settings.whatsapp_api_base_url.rstrip('/')}/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {settings.whatsapp_api_key}",
        "Content-Type": "application/json",
        "User-Agent": "curl/8.0",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib_request.Request(url, data=body, headers=headers, method="POST")
    result = await asyncio.to_thread(urllib_request.urlopen, req, timeout=30)
    return {"status": "sent", "recipient": to, "text": text[:100]}
