from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from src.config import get_settings
from src.middleware.auth import require_dashboard_api_key
from src.services.manufacturer_forwarding import forward_order_to_manufacturer, get_manufacturer_forward_preview
from src.services.catalog_service import get_keyword_map
from src.services.order_parser import parse_order
from src.services.order_service import get_order_by_id, list_orders, record_fl_pop, update_order_status


router = APIRouter(prefix="/api/orders", tags=["orders"])


class ParseOrderRequest(BaseModel):
    text: str


class UpdateOrderStatusRequest(BaseModel):
    status: str
    tracking_info: str | None = None


class ForwardOrderRequest(BaseModel):
    force: bool = False


class FlPopRequest(BaseModel):
    fl_pop_image_url: str
    fl_amount: Decimal | None = None


class FlPopConfirmRequest(BaseModel):
    fl_pop_image_url: str
    fl_amount: Decimal | None = None
    confirm: bool = True


@router.post("/parse")
async def parse_order_preview(request: Request, payload: ParseOrderRequest) -> dict[str, object]:
    keyword_map = await get_keyword_map(request.app.state.database)
    result = parse_order(payload.text, keyword_map)
    if result is None:
        raise HTTPException(status_code=422, detail="Unable to match product from message")
    return {"item": result}


@router.get("", dependencies=[Depends(require_dashboard_api_key)])
async def get_orders(
    request: Request,
    status: str | None = None,
    forward_status: str | None = None,
) -> dict[str, object]:
    orders = await list_orders(request.app.state.database, status, forward_status)
    return {"items": orders, "count": len(orders)}


@router.get("/{order_id}", dependencies=[Depends(require_dashboard_api_key)])
async def get_order(request: Request, order_id: int) -> dict[str, object]:
    order = await get_order_by_id(request.app.state.database, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    preview = await get_manufacturer_forward_preview(request.app.state.database, order_id)
    return {"item": order, "manufacturer_forward_preview": preview}


@router.put("/{order_id}/status", dependencies=[Depends(require_dashboard_api_key)])
async def put_order_status(request: Request, order_id: int, payload: UpdateOrderStatusRequest) -> dict[str, object]:
    from src.services.order_service import update_order_tracking
    from src.services.whatsapp_sender import send_text_message
    from src.services.message_templates import render_template

    if payload.tracking_info:
        await update_order_tracking(request.app.state.database, order_id, payload.tracking_info)

    order = await update_order_status(request.app.state.database, order_id, payload.status)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    # Notify customer when shipped
    if payload.status == "shipped" and order.get("phone_number"):
        settings = get_settings()
        tracking = order.get("tracking_info") or payload.tracking_info or "Pending"
        message = await render_template(
            request.app.state.database,
            "order_shipped",
            order_number=order["order_number"],
            tracking_info=tracking,
            tracking_url=settings.courier_tracking_url,
            full_address=order.get("full_address") or "Your address",
        )
        await send_text_message(order["phone_number"], message)

    return {"item": order}


@router.post("/{order_id}/confirm", dependencies=[Depends(require_dashboard_api_key)])
async def confirm_order(request: Request, order_id: int) -> dict[str, object]:
    order = await update_order_status(request.app.state.database, order_id, "confirmed")
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"item": order}


@router.post("/{order_id}/forward", dependencies=[Depends(require_dashboard_api_key)])
async def forward_order(request: Request, order_id: int, payload: ForwardOrderRequest) -> dict[str, object]:
    result = await forward_order_to_manufacturer(request.app.state.database, order_id, force=payload.force)
    if result is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return result


@router.post("/{order_id}/fl-pop", dependencies=[Depends(require_dashboard_api_key)])
async def upload_fl_pop(request: Request, order_id: int, payload: FlPopRequest) -> dict[str, object]:
    """Upload BioMed's POP to Focus Logic — shows preview, does NOT forward."""
    order = await get_order_by_id(request.app.state.database, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    preview = await get_manufacturer_forward_preview(request.app.state.database, order_id)
    settings = get_settings()

    return {
        "order": order,
        "fl_pop_preview": {
            "fl_pop_image_url": payload.fl_pop_image_url,
            "fl_amount": str(payload.fl_amount) if payload.fl_amount else str(settings.default_margin),
            "forward_preview": preview.get("message") if preview else None,
            "recipient": preview.get("recipient") if preview else None,
        },
    }


@router.post("/{order_id}/fl-pop/confirm", dependencies=[Depends(require_dashboard_api_key)])
async def confirm_fl_pop_and_forward(request: Request, order_id: int, payload: FlPopConfirmRequest) -> dict[str, object]:
    """Save FL POP, auto-forward to manufacturer, then notify customer."""
    from src.services.whatsapp_sender import send_text_message
    from src.services.message_templates import render_template

    order = await get_order_by_id(request.app.state.database, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    fl_amount = payload.fl_amount or get_settings().default_margin
    updated = await record_fl_pop(request.app.state.database, order_id, payload.fl_pop_image_url, fl_amount)
    if updated is None:
        raise HTTPException(status_code=404, detail="Order not found")

    forward_result = None
    if get_settings().auto_forward_to_manufacturer:
        forward_result = await forward_order_to_manufacturer(request.app.state.database, order_id)

    # Notify customer their order is confirmed
    customer_phone = updated.get("phone_number")
    if customer_phone and forward_result and forward_result.get("action") == "forwarded":
        items = updated.get("items") or []
        item_lines = "\n".join(f"• {i.get('quantity', 0)}x {i.get('product_name', 'item')}" for i in items)
        confirmation = await render_template(
            request.app.state.database,
            "order_confirmed",
            order_number=updated["order_number"],
            customer_name=updated.get("name") or "Customer",
            items=item_lines or "Your order",
            total=str(updated.get("total", "0.00")),
            courier=get_settings().courier_name,
        )
        await send_text_message(customer_phone, confirmation)

    return {
        "order": updated,
        "forward_result": forward_result,
    }
