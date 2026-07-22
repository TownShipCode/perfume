from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from src.models.cart import CartItem


class Order(BaseModel):
    id: int | None = None
    order_number: str
    customer_id: int = Field(gt=0)
    items: list[CartItem] = Field(default_factory=list)
    total: Decimal
    status: str = "pending"
    pop_image_url: str | None = None
    tracking_info: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
