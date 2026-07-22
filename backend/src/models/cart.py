from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field


class CartItem(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


class Cart(BaseModel):
    items: list[CartItem] = Field(default_factory=list)
    total: Decimal = Field(default=Decimal("0.00"))
