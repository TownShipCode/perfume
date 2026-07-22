from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from src.middleware.auth import require_dashboard_api_key
from src.services.customer_service import get_customer_by_phone, list_customer_orders, list_customers, update_customer_address


router = APIRouter(prefix="/api/customers", tags=["customers"], dependencies=[Depends(require_dashboard_api_key)])


class UpdateCustomerAddressRequest(BaseModel):
    area: str
    street: str
    city: str


@router.get("")
async def get_customers(request: Request) -> dict[str, object]:
    customers = await list_customers(request.app.state.database)
    return {"items": customers, "count": len(customers)}


@router.get("/{phone_number}/orders")
async def get_customer_order_history(request: Request, phone_number: str) -> dict[str, object]:
    customer = await get_customer_by_phone(request.app.state.database, phone_number)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    orders = await list_customer_orders(request.app.state.database, phone_number)
    return {"customer": customer, "items": orders, "count": len(orders)}


@router.put("/{phone_number}/address")
async def put_customer_address(
    request: Request,
    phone_number: str,
    payload: UpdateCustomerAddressRequest,
) -> dict[str, object]:
    customer = await update_customer_address(
        request.app.state.database,
        phone_number,
        area=payload.area,
        street=payload.street,
        city=payload.city,
    )
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"item": customer}
