from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Header, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from src.config import get_settings
from src.middleware.rate_limit import webhook_rate_limit
from src.services.message_templates import build_customer_reply
from src.services.order_flow import handle_image_message, handle_text_message
from src.services.order_service import expire_stale_pop_orders
from src.services.whatsapp_sender import deliver_reply
from src.services.whatsapp_webhook import (
    extract_message_event,
    try_claim_message,
    verify_signature,
    verify_webhook_challenge,
)


logger = logging.getLogger(__name__)
router = APIRouter(tags=["webhook"])


@router.get("/webhook")
async def verify_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
) -> str:
    settings = get_settings()
    return verify_webhook_challenge(hub_mode, hub_verify_token, hub_challenge, settings)


@router.post("/webhook", dependencies=[Depends(webhook_rate_limit())])
async def receive_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None),
) -> JSONResponse:
    settings = get_settings()

    # Verify payload signature (Kapso forwards Meta's HMAC)
    raw_body = await request.body()
    if not verify_signature(raw_body, x_hub_signature_256, settings):
        return JSONResponse(status_code=200, content={"status": "rejected", "reason": "invalid_signature"})

    # Parse the webhook payload
    payload = await request.json()
    # Log the raw payload structure for debugging
    has_messages = bool(payload.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages"))
    has_statuses = bool(payload.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("statuses"))
    logger.warning("WEBHOOK payload_structure | keys=%s batch=%s messages=%s statuses=%s",
                list(payload.keys()), payload.get("batch"), has_messages, has_statuses)
    event = extract_message_event(payload)

    # Status update callbacks (delivered/read/sent receipts) — log and acknowledge
    if event is None:
        statuses = payload.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("statuses", [])
        if statuses:
            for s in statuses:
                logger.warning("WEBHOOK status_update | msg=%s status=%s", s.get("id"), s.get("status"))
        return JSONResponse(status_code=200, content={"status": "acknowledged", "reason": "status_update"})

    # Idempotency: atomically claim this message_id.
    # try_claim_message inserts + checks in a single DB round-trip so
    # concurrent duplicate requests cannot both slip through the gate.
    try:
        if not await try_claim_message(request.app.state.database, event["message_id"]):
            return JSONResponse(status_code=200, content={"status": "duplicate", "message_id": event["message_id"]})
    except Exception as exc:
        logger.error("WEBHOOK claim_message_failed | %s", exc)
        return JSONResponse(status_code=503, content={"status": "retry", "reason": "db_unavailable"})

    # Process message with transient/permanent error classification
    try:
        await expire_stale_pop_orders(request.app.state.database, settings.pop_expiry_hours)
        result: dict[str, object] | None = None
        if event.get("type") == "text":
            result = await handle_text_message(request.app.state.database, event)
        elif event.get("type") == "image":
            result = await handle_image_message(request.app.state.database, event)
        reply = await build_customer_reply(request.app.state.database, result)
        delivery = await deliver_reply(event, reply)
        logger.warning("WEBHOOK processed | action=%s reply=%s delivery=%s",
                    result.get("action") if result else "none",
                    "yes" if reply else "no",
                    delivery.get("status") if delivery else "none")
        return JSONResponse(status_code=200, content=jsonable_encoder({
            "status": "accepted", "event": event, "result": result,
            "reply": reply, "delivery": delivery,
        }))
    except Exception as exc:
        logger.error("WEBHOOK processing_error | %s", exc)
        if _is_transient(exc):
            return JSONResponse(status_code=503, content={"status": "retry", "reason": "transient_error"})
        # Permanent error — acknowledge so Kapso doesn't retry forever
        return JSONResponse(status_code=200, content={"status": "error", "reason": "permanent_error"})


def _is_transient(exc: Exception) -> bool:
    """Classify exceptions: transient (Kapso should retry) vs permanent (dead letter)."""
    error_str = str(exc).lower()
    transient_markers = [
        "connection", "timeout", "unavailable", "pool", "too many",
        "server closed", "cannot connect", "connection refused",
    ]
    return any(marker in error_str for marker in transient_markers)

