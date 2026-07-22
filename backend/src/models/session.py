from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from src.models.cart import CartItem


class Session(BaseModel):
    id: int | None = None
    phone_number: str
    state: str = "idle"
    cart: list[CartItem] = Field(default_factory=list)
    temp_address: dict[str, str] | None = None
    current_step: int = 0
    updated_at: datetime | None = None
