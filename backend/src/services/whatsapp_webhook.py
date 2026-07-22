from __future__ import annotations

import hashlib
import hmac
from typing import Any

from fastapi import HTTPException, status

from src.config import Settings
from src.db.connection import Database, execute, fetch_one


def verify_webhook_challenge(mode: str | None, token: str | None, challenge: str | None, settings: Settings) -> str:
    if mode != "subscribe" or not challenge:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid webhook verification request")

    expected_token = settings.whatsapp_verify_token
    if expected_token and token == expected_token:
        return challenge

    if settings.is_production:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Webhook verification failed")

    if token:
        return challenge

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Webhook verification failed")


def verify_signature(body: bytes, signature: str | None, settings: Settings) -> bool:
    secret = settings.whatsapp_app_secret
    if not secret:
        return not settings.is_production

    if not signature or not signature.startswith("sha256="):
        return False

    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    expected = f"sha256={digest}"
    return hmac.compare_digest(expected, signature)


def extract_message_event(payload: dict[str, Any]) -> dict[str, Any] | None:
    direct_messages = payload.get("messages")
    if isinstance(direct_messages, list) and direct_messages:
        message = direct_messages[0]
        contact = None
        contacts = payload.get("contacts")
        if isinstance(contacts, list) and contacts:
            contact = contacts[0]
        return _normalize_message(message, contact)

    entries = payload.get("entry")
    if not isinstance(entries, list):
        return None

    for entry in entries:
        changes = entry.get("changes")
        if not isinstance(changes, list):
            continue
        for change in changes:
            value = change.get("value", {})
            messages = value.get("messages")
            if not isinstance(messages, list) or not messages:
                continue
            contacts = value.get("contacts")
            contact = contacts[0] if isinstance(contacts, list) and contacts else None
            return _normalize_message(messages[0], contact)

    return None


def _normalize_message(message: dict[str, Any], contact: dict[str, Any] | None) -> dict[str, Any]:
    message_type = message.get("type", "unknown")
    event = {
        "message_id": message.get("id"),
        "from": message.get("from"),
        "type": message_type,
        "profile_name": (contact or {}).get("profile", {}).get("name"),
        "text": None,
        "image_id": None,
        "image_url": None,
        "interactive_id": None,
        "interactive_title": None,
    }

    if message_type == "text":
        event["text"] = ((message.get("text") or {}).get("body") or "").strip()
    elif message_type == "image":
        image = message.get("image") or {}
        event["image_id"] = image.get("id")
        event["image_url"] = image.get("link")
    elif message_type == "interactive":
        interactive = message.get("interactive") or {}
        button_reply = interactive.get("button_reply") or {}
        list_reply = interactive.get("list_reply") or {}
        reply = button_reply or list_reply
        event["interactive_id"] = reply.get("id")
        event["interactive_title"] = reply.get("title")

    return event


async def is_message_processed(database: Database, message_id: str | None) -> bool:
    if not message_id:
        return False

    if database.mode == "postgres":
        row = await fetch_one(
            database,
            "SELECT message_id FROM processed_messages WHERE message_id = $1",
            message_id,
        )
    else:
        row = await fetch_one(
            database,
            "SELECT message_id FROM processed_messages WHERE message_id = ?",
            message_id,
        )

    return row is not None


async def mark_message_processed(database: Database, message_id: str | None) -> None:
    if not message_id:
        return

    if database.mode == "postgres":
        await execute(
            database,
            "INSERT INTO processed_messages (message_id) VALUES ($1) ON CONFLICT (message_id) DO NOTHING",
            message_id,
        )
        return

    await execute(
        database,
        "INSERT OR IGNORE INTO processed_messages (message_id) VALUES (?)",
        message_id,
    )
