# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false

"""Yoco Checkout API integration — single-merchant payment processing."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from typing import Any

import aiohttp

from src.config import Settings, get_settings

logger = logging.getLogger(__name__)


async def create_checkout_session(
    order_number: str,
    amount_cents: int,
    currency: str = "ZAR",
    agent_code: str | None = None,
    team_member_id: int | None = None,
) -> dict[str, Any] | None:
    """Call Yoco Checkout API to create a payment session.

    Returns dict with checkout_url and checkout_id, or None on failure.
    amount_cents: amount in cents (R480.00 = 48000).
    """
    settings = get_settings()
    if not settings.yoco_secret_key:
        return None

    metadata: dict[str, Any] = {"order_number": order_number}
    if agent_code:
        metadata["agent_code"] = agent_code
    if team_member_id:
        metadata["team_member_id"] = str(team_member_id)

    payload = {
        "amount": amount_cents,
        "currency": currency,
        "metadata": metadata,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{settings.yoco_base_url}/charges/",
                json=payload,
                headers={
                    "Authorization": f"Bearer {settings.yoco_secret_key}",
                    "Content-Type": "application/json",
                },
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                body = await resp.json()
                if resp.status in (200, 201):
                    return {
                        "checkout_url": body.get("redirect_url", ""),
                        "checkout_id": body.get("id", ""),
                    }
                logger.warning("YOCO checkout_failed | status=%s body=%s", resp.status, body)
                return None
    except Exception as exc:
        logger.error("YOCO checkout_error | %s", exc)
        return None


def verify_yoco_signature(body: bytes, signature: str | None, settings: Settings) -> bool:
    """Verify Yoco webhook HMAC-SHA256 signature."""
    secret = settings.yoco_webhook_secret
    if not secret:
        return not settings.is_production

    if not signature or not signature.startswith("sha256="):
        return False

    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    expected = f"sha256={digest}"
    return hmac.compare_digest(expected, signature)


async def is_yoco_event_duplicate(database, yoco_event_id: str) -> bool:
    """Check if a Yoco event has already been processed (idempotency gate)."""
    from src.db.connection import fetch_one

    if database.mode == "postgres":
        row = await fetch_one(
            database,
            "SELECT yoco_event_id FROM orders WHERE yoco_event_id = $1 LIMIT 1",
            yoco_event_id,
        )
    else:
        row = await fetch_one(
            database,
            "SELECT yoco_event_id FROM orders WHERE yoco_event_id = ? LIMIT 1",
            yoco_event_id,
        )
    return row is not None


async def record_yoco_payment(
    database,
    order_number: str,
    yoco_event_id: str,
    payment_status: str,
) -> dict | None:
    """Update order with Yoco payment result. Returns updated order or None."""
    from src.db.connection import execute, fetch_one

    if database.mode == "postgres":
        await execute(
            database,
            """UPDATE orders SET payment_status = $1, yoco_event_id = $2, updated_at = NOW()
               WHERE order_number = $3 AND payment_method = 'yoco'""",
            payment_status, yoco_event_id, order_number,
        )
    else:
        await execute(
            database,
            """UPDATE orders SET payment_status = ?, yoco_event_id = ?, updated_at = CURRENT_TIMESTAMP
               WHERE order_number = ? AND payment_method = 'yoco'""",
            payment_status, yoco_event_id, order_number,
        )

    if database.mode == "postgres":
        return await fetch_one(
            database,
            "SELECT id, order_number FROM orders WHERE order_number = $1",
            order_number,
        )
    return await fetch_one(
        database,
        "SELECT id, order_number FROM orders WHERE order_number = ?",
        order_number,
    )
