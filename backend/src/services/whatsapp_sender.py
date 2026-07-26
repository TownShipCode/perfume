from __future__ import annotations

import json
from typing import Any

from src.config import Settings, get_settings


async def deliver_reply(event: dict[str, Any], reply: dict[str, Any] | None) -> dict[str, Any] | None:
    if reply is None:
        return None

    settings = get_settings()
    recipient = event.get("from")
    if not recipient:
        return {"status": "skipped", "reason": "missing_recipient"}

    # Interactive messages (buttons, location requests, etc.)
    if reply.get("type") == "interactive":
        payload = reply.get("payload")
        if isinstance(payload, dict):
            result = await send_interactive_message(recipient, payload)
            # Fallback: if interactive fails or is in dry_run/skipped mode, send text instead
            if result.get("status") in ("failed", "dry_run", "skipped") and reply.get("fallback_text"):
                return await send_text_message(recipient, reply["fallback_text"])
            return result
        return {"status": "skipped", "reason": "missing_interactive_payload"}

    image_url = reply.get("image_url")
    if image_url:
        return await send_image_message(recipient, image_url, caption=reply.get("text"))

    return await _send(settings, recipient, reply["text"])


async def send_text_message(recipient: str, text: str) -> dict[str, Any]:
    settings = get_settings()
    return await _send(settings, recipient, text)


async def send_image_message(recipient: str, image_url: str, caption: str | None = None) -> dict[str, Any]:
    settings = get_settings()
    return await _send_image(settings, recipient, image_url, caption)


# Commented out per user request — activate when WHATSAPP_CATALOG_ID is configured.
# async def send_product_message(recipient: str, product_number: int) -> dict[str, Any]:
#     """Send a WhatsApp Product Message — native rich product card.
#
#     Requires WHATSAPP_CATALOG_ID to be set and a Meta Commerce Catalog configured.
#     Falls back to text + image if catalog isn't available.
#     """
#     settings = get_settings()
#     catalog_id = settings.whatsapp_catalog_id
#
#     if not catalog_id:
#         return {"status": "skipped", "reason": "no_catalog_id"}
#
#     if settings.whatsapp_send_mode == "off":
#         return {"status": "skipped", "reason": "send_mode_off"}
#
#     if settings.whatsapp_send_mode != "live":
#         return {"status": "dry_run", "recipient": recipient, "product_number": product_number}
#
#     phone_id = settings.whatsapp_phone_number_id or "1235032529693241"
#     payload = {
#         "messaging_product": "whatsapp",
#         "to": recipient,
#         "type": "product",
#         "product": {
#             "catalog_id": catalog_id,
#             "product_retailer_id": str(product_number),
#         },
#     }
#
#     try:
#         if settings.whatsapp_provider == "kapso":
#             return await _send_product_kapso(settings, recipient, payload, phone_id)
#         else:
#             return await _send_product_meta(settings, recipient, payload, phone_id)
#     except Exception as error:
#         return {"status": "failed", "error": str(error)}
#
#
# async def _send_product_kapso(settings: Settings, to: str, payload: dict, phone_id: str) -> dict[str, Any]:
#     import aiohttp
#     url = f"https://api.kapso.ai/meta/whatsapp/v24.0/{phone_id}/messages"
#     headers = {"X-API-Key": settings.whatsapp_api_key or "", "Content-Type": "application/json"}
#     async with aiohttp.ClientSession() as session:
#         async with session.post(url, json=payload, headers=headers,
#                                 timeout=aiohttp.ClientTimeout(total=15)) as resp:
#             if resp.status in (200, 201):
#                 return {"status": "sent", "recipient": to}
#             body = await resp.text()
#             return {"status": "failed", "http_status": resp.status, "body": body[:200]}
#
#
# async def _send_product_meta(settings: Settings, to: str, payload: dict, phone_id: str) -> dict[str, Any]:
#     import asyncio, json
#     from urllib import request as urllib_request
#     url = f"{settings.whatsapp_api_base_url.rstrip('/')}/{phone_id}/messages"
#     headers = {
#         "Authorization": f"Bearer {settings.whatsapp_api_key}",
#         "Content-Type": "application/json",
#         "User-Agent": "curl/8.0",
#     }
#     body = json.dumps(payload).encode("utf-8")
#     req = urllib_request.Request(url, data=body, headers=headers, method="POST")
#     await asyncio.to_thread(urllib_request.urlopen, req, timeout=30)
#     return {"status": "sent", "recipient": to}



async def send_interactive_message(recipient: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Send an interactive WhatsApp message (buttons, location request, etc.) via Kapso.

    Adopts miana's _send_interactive_via_kapso pattern.
    Falls back to text if interactive send fails.
    """
    settings = get_settings()

    if settings.whatsapp_send_mode == "off":
        return {"status": "skipped", "reason": "send_mode_off"}

    if settings.whatsapp_send_mode != "live":
        return {"status": "dry_run", "recipient": recipient, "payload": payload}

    if not settings.whatsapp_api_key:
        return {"status": "failed", "reason": "missing_api_key"}

    phone_id = settings.whatsapp_phone_number_id or "1235032529693241"

    try:
        if settings.whatsapp_provider == "kapso":
            return await _send_interactive_kapso(settings, recipient, payload, phone_id)
        else:
            return await _send_interactive_meta(settings, recipient, payload, phone_id)
    except Exception as error:
        return {"status": "failed", "error": str(error)}


async def _send_interactive_kapso(settings: Settings, to: str, payload: dict[str, Any], phone_id: str) -> dict[str, Any]:
    """Send interactive message via Kapso gateway."""
    import aiohttp

    url = f"https://api.kapso.ai/meta/whatsapp/v24.0/{phone_id}/messages"
    headers = {"X-API-Key": settings.whatsapp_api_key or "", "Content-Type": "application/json"}
    full_payload: dict[str, object] = {
        "messaging_product": "whatsapp",
        "to": to,
        **payload,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=full_payload, headers=headers,
                                timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status in (200, 201):
                return {"status": "sent", "recipient": to}
            body = await resp.text()
            return {"status": "failed", "http_status": resp.status, "body": body[:200]}


async def _send_interactive_meta(settings: Settings, to: str, payload: dict[str, Any], phone_id: str) -> dict[str, Any]:
    """Send interactive message via Meta WhatsApp Cloud API directly."""
    import asyncio
    from urllib import request as urllib_request

    url = f"{settings.whatsapp_api_base_url.rstrip('/')}/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {settings.whatsapp_api_key}",
        "Content-Type": "application/json",
        "User-Agent": "curl/8.0",
    }
    full_payload = {"messaging_product": "whatsapp", "to": to, **payload}
    body = json.dumps(full_payload).encode("utf-8")
    req = urllib_request.Request(url, data=body, headers=headers, method="POST")
    await asyncio.to_thread(urllib_request.urlopen, req, timeout=30)
    return {"status": "sent", "recipient": to}


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


async def _send_image(settings: Settings, to: str, image_url: str, caption: str | None = None) -> dict[str, Any]:
    if settings.whatsapp_send_mode == "off":
        return {"status": "skipped", "reason": "send_mode_off", "image_url": image_url[:100]}

    if settings.whatsapp_send_mode != "live":
        return {"status": "dry_run", "recipient": to, "image_url": image_url[:100], "caption": caption}

    if not settings.whatsapp_api_key:
        return {"status": "failed", "reason": "missing_api_key"}

    phone_id = settings.whatsapp_phone_number_id or "1102791516242887"

    try:
        if settings.whatsapp_provider == "kapso":
            return await _send_image_kapso(settings, to, image_url, caption, phone_id)
        else:
            return await _send_image_meta(settings, to, image_url, caption, phone_id)
    except Exception as error:
        return {"status": "failed", "error": str(error)}


async def _send_image_kapso(settings: Settings, to: str, image_url: str, caption: str | None, phone_id: str) -> dict[str, Any]:
    import aiohttp

    url = f"https://api.kapso.ai/meta/whatsapp/v24.0/{phone_id}/messages"
    headers = {"X-API-Key": settings.whatsapp_api_key or "", "Content-Type": "application/json"}
    img_payload: dict[str, object] = {"link": image_url}
    if caption:
        img_payload["caption"] = caption
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "image",
        "image": img_payload,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers,
                                timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status in (200, 201):
                return {"status": "sent", "recipient": to, "image_url": image_url[:100]}
            body = await resp.text()
            return {"status": "failed", "http_status": resp.status, "body": body[:200]}


async def _send_image_meta(settings: Settings, to: str, image_url: str, caption: str | None, phone_id: str) -> dict[str, Any]:
    import asyncio
    import json
    from urllib import request as urllib_request

    url = f"{settings.whatsapp_api_base_url.rstrip('/')}/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {settings.whatsapp_api_key}",
        "Content-Type": "application/json",
        "User-Agent": "curl/8.0",
    }
    img_payload: dict[str, object] = {"link": image_url}
    if caption:
        img_payload["caption"] = caption
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "image",
        "image": img_payload,
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib_request.Request(url, data=body, headers=headers, method="POST")
    await asyncio.to_thread(urllib_request.urlopen, req, timeout=30)
    return {"status": "sent", "recipient": to, "image_url": image_url[:100]}
