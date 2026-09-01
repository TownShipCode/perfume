from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from src.config import get_settings
from src.middleware.auth import require_dashboard_api_key
from src.services.manufacturer_forwarding import forward_order_to_manufacturer, get_manufacturer_forward_preview
from src.services.catalog_service import get_keyword_map, get_products_by_ids
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


class WebOrderItem(BaseModel):
    product_id: int
    quantity: int


class WebOrderRequest(BaseModel):
    items: list[WebOrderItem]
    name: str
    surname: str = ""
    email: str = ""
    phone: str = ""
    area: str = ""
    street: str = ""
    city: str = ""
    postal_code: str = ""
    province: str = ""
    payment_method: str = "yoco"  # yoco or eft


@router.post("/parse")
async def parse_order_preview(request: Request, payload: ParseOrderRequest) -> dict[str, object]:
    keyword_map = await get_keyword_map(request.app.state.database)
    result = parse_order(payload.text, keyword_map)
    if result is None:
        raise HTTPException(status_code=422, detail="Unable to match product from message")
    return {"item": result}


@router.get("")
async def get_orders(
    request: Request,
    status: str | None = None,
    forward_status: str | None = None,
) -> dict[str, object]:
    orders = await list_orders(request.app.state.database, status, forward_status)
    return {"items": orders, "count": len(orders)}


@router.get("/track")
async def track_order(request: Request, phone: str = "") -> dict[str, object]:
    """Public: look up a customer's recent orders by phone number (no auth).
    Returns only safe fields, never internal forwarding data.
    """
    if not phone:
        raise HTTPException(status_code=400, detail="Phone number required")

    normalized = phone.strip()
    if not normalized.startswith("+"):
        normalized = "+" + normalized

    from src.db.connection import fetch_all as _fetch_all

    db = request.app.state.database
    if db.mode == "postgres":
        rows = await _fetch_all(
            db,
            """
            SELECT o.id, o.order_number, o.items, o.total, o.status, o.tracking_info, o.created_at
            FROM orders o
            JOIN customers c ON c.id = o.customer_id
            WHERE c.phone_number = $1
            ORDER BY o.created_at DESC
            LIMIT 10
            """,
            normalized,
        )
    else:
        rows = await _fetch_all(
            db,
            """
            SELECT o.id, o.order_number, o.items, o.total, o.status, o.tracking_info, o.created_at
            FROM orders o
            JOIN customers c ON c.id = o.customer_id
            WHERE c.phone_number = ?
            ORDER BY o.created_at DESC
            LIMIT 10
            """,
            normalized,
        )

    items = []
    for row in rows:
        items.append({
            "id": row["id"],
            "order_number": row["order_number"],
            "items": row["items"],
            "total": str(row["total"]),
            "status": row["status"],
            "tracking_info": row.get("tracking_info"),
            "created_at": str(row["created_at"]),
        })
    return {"items": items, "count": len(items)}


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
    """Upload the manufacturer's POP — shows preview, does NOT forward."""
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

    # Notify customer — only if forwarding succeeded
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


# ── Web Store Checkout ──


@router.post("/web")
async def create_web_order(request: Request, payload: WebOrderRequest) -> dict[str, object]:
    """Public: create an order from the web store. Returns order + Yoco checkout URL."""
    from src.models.cart import CartItem
    from src.services.customer_service import get_or_create_customer
    from src.services.order_service import create_order
    from src.services.yoco_payment import create_checkout_session
    from src.services.catalog_service import get_products_by_ids

    db = request.app.state.database
    settings = get_settings()

    if not payload.items:
        raise HTTPException(status_code=400, detail="No items in order")

    # Get product prices from DB (don't trust client prices)
    product_ids = [it.product_id for it in payload.items]
    price_map = await get_products_by_ids(db, product_ids)
    if not price_map:
        raise HTTPException(status_code=400, detail="No valid products found")

    cart_items: list[CartItem] = []
    subtotal = Decimal("0")
    for it in payload.items:
        product = price_map.get(it.product_id)
        if not product:
            continue
        qty = max(1, min(it.quantity, 99))
        cart_items.append(CartItem(product_id=it.product_id, quantity=qty))
        subtotal += Decimal(str(product["price"])) * qty

    if not cart_items:
        raise HTTPException(status_code=400, detail="No valid items after validation")

    # Calculate shipping
    shipping = settings.shipping_fee if subtotal < settings.free_shipping_threshold else Decimal("0")
    total = subtotal + shipping

    # Get or create customer
    phone = payload.phone.strip() if payload.phone else "27820000000"
    if not phone.startswith("+"):
        phone = f"+{phone}" if not phone.startswith("+") else phone
    customer = await get_or_create_customer(db, phone, payload.name)

    # Build address
    address_parts = [p for p in [payload.street, payload.area, payload.city, payload.postal_code, payload.province] if p]
    full_address = ", ".join(address_parts) if address_parts else None

    # Create order
    order = await create_order(
        db,
        customer_id=customer["id"],
        cart_items=cart_items,
        total=total,
        shipping_fee=shipping,
    )

    # Yoco checkout
    checkout_url = None
    if payload.payment_method == "yoco" and settings.yoco_secret_key:
        try:
            checkout = await create_checkout_session(
                db, order, total, phone,
                agent_code=customer.get("agent_code"),
                team_member_id=customer.get("registered_by"),
            )
            checkout_url = checkout.get("checkout_url")
        except Exception:
            pass  # Fall through — order created, payment can be done manually

    return {
        "order": order,
        "checkout_url": checkout_url,
        "payment_method": payload.payment_method,
    }
