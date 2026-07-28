# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false

"""Payment endpoints — Yoco webhook + checkout link generation."""

from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from src.config import get_settings
from src.middleware.auth import require_dashboard_api_key
from src.middleware.rate_limit import webhook_rate_limit
from src.services.yoco_payment import (
    create_checkout_session,
    is_yoco_event_duplicate,
    record_yoco_payment,
    verify_yoco_signature,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["payments"])


@router.post("/api/payments/checkout/{order_id}", dependencies=[Depends(require_dashboard_api_key)])
async def generate_checkout_link(request: Request, order_id: int) -> dict[str, object]:
    """Manually generate a Yoco checkout link for an order (admin resend)."""
    from src.services.order_service import get_order_by_id

    order = await get_order_by_id(request.app.state.database, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    total = order.get("total", 0)
    amount_cents = int(float(str(total)) * 100)
    result = await create_checkout_session(str(order.get("order_number", "")), amount_cents)
    if not result:
        raise HTTPException(status_code=502, detail="Yoco checkout creation failed")

    return {"checkout_url": result["checkout_url"], "checkout_id": result["checkout_id"]}


@router.post("/webhooks/yoco", dependencies=[Depends(webhook_rate_limit())])
async def yoco_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_yoco_signature: str | None = Header(default=None),
) -> JSONResponse:
    """Yoco webhook — receives payment status events."""
    settings = get_settings()
    raw_body = await request.body()

    if not verify_yoco_signature(raw_body, x_yoco_signature, settings):
        return JSONResponse(status_code=200, content={"status": "rejected", "reason": "invalid_signature"})

    try:
        payload = await request.json()
        event_type = payload.get("type", "")
        event_id = payload.get("id", "")
        status = payload.get("status", "")
        metadata = payload.get("metadata", {})
        order_number = metadata.get("order_number", "")

        if not order_number or not event_id:
            return JSONResponse(status_code=200, content={"status": "ignored", "reason": "missing_data"})

        database = request.app.state.database

        # Idempotency: skip if already processed
        if await is_yoco_event_duplicate(database, event_id):
            logger.warning("YOCO duplicate_event | id=%s", event_id)
            return JSONResponse(status_code=200, content={"status": "duplicate"})

        if status == "successful":
            order = await record_yoco_payment(database, order_number, event_id, "paid")
            if order:
                # Fire-and-forget: notify customer + auto-forward
                background_tasks.add_task(
                    _notify_payment_success,
                    database,
                    order,
                )
                logger.warning("YOCO payment_success | order=%s", order_number)
        elif status in ("failed", "cancelled"):
            await record_yoco_payment(database, order_number, event_id, status)
            logger.warning("YOCO payment_%s | order=%s", status, order_number)

        return JSONResponse(status_code=200, content={"status": "received"})
    except Exception as exc:
        logger.error("YOCO webhook_error | %s", exc)
        return JSONResponse(status_code=200, content={"status": "error"})


async def _notify_payment_success(database, order: dict) -> None:
    """Background task: notify customer and auto-forward to manufacturer."""
    from src.services.manufacturer_forwarding import forward_order_to_manufacturer
    from src.services.message_templates import render_template
    from src.services.whatsapp_sender import send_text_message

    settings = get_settings()
    phone = order.get("phone_number")

    # Notify customer
    if phone:
        message = await render_template(
            database,
            "payment_received",
            order_number=order.get("order_number", ""),
        )
        await send_text_message(phone, message)

    # Auto-forward to manufacturer
    if settings.auto_forward_to_manufacturer:
        try:
            await forward_order_to_manufacturer(database, order["id"])
        except Exception as exc:
            logger.error("YOCO auto_forward_failed | order=%s error=%s", order.get("order_number"), exc)
