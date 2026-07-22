from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from src.middleware.auth import require_dashboard_api_key
from src.services.manufacturer_forwarding import forward_order_to_manufacturer, get_manufacturer_forward_preview
from src.services.catalog_service import get_keyword_map
from src.services.order_parser import parse_order
from src.services.order_service import get_order_by_id, list_orders, update_order_status


router = APIRouter(prefix="/api/orders", tags=["orders"])


class ParseOrderRequest(BaseModel):
    text: str


class UpdateOrderStatusRequest(BaseModel):
    status: str


class ForwardOrderRequest(BaseModel):
    force: bool = False


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
    order = await update_order_status(request.app.state.database, order_id, payload.status)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
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
