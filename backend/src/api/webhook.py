from __future__ import annotations

from fastapi import APIRouter, Header, Request

from src.config import get_settings
from src.services.order_flow import handle_image_message, handle_text_message
from src.services.whatsapp_webhook import (
    extract_message_event,
    is_message_processed,
    mark_message_processed,
    verify_signature,
    verify_webhook_challenge,
)


router = APIRouter(tags=["webhook"])


@router.get("/webhook")
async def verify_webhook(
    hub_mode: str | None = None,
    hub_verify_token: str | None = None,
    hub_challenge: str | None = None,
) -> str:
    settings = get_settings()
    return verify_webhook_challenge(hub_mode, hub_verify_token, hub_challenge, settings)


@router.post("/webhook")
async def receive_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None),
) -> dict[str, object]:
    settings = get_settings()
    raw_body = await request.body()
    if not verify_signature(raw_body, x_hub_signature_256, settings):
        return {"status": "rejected", "reason": "invalid_signature"}

    payload = await request.json()
    event = extract_message_event(payload)
    if event is None:
        return {"status": "ignored", "reason": "no_message"}

    if await is_message_processed(request.app.state.database, event["message_id"]):
        return {"status": "duplicate", "message_id": event["message_id"]}

    await mark_message_processed(request.app.state.database, event["message_id"])
    result: dict[str, object] | None = None
    if event.get("type") == "text":
        result = await handle_text_message(request.app.state.database, event)
    elif event.get("type") == "image":
        result = await handle_image_message(request.app.state.database, event)
    return {"status": "accepted", "event": event, "result": result}
