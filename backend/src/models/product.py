from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class Product(BaseModel):
    id: int | None = None
    product_number: int = Field(gt=0)
    name: str
    price: Decimal
    bio_med_margin: Decimal = Decimal("0")
    image_url: str | None = None
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None
