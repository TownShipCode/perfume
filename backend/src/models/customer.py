from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class Customer(BaseModel):
    id: int | None = None
    phone_number: str
    name: str | None = None
    surname: str | None = None
    area: str | None = None
    street: str | None = None
    city: str | None = None
    postal_code: str | None = None
    email: str | None = None
    province: str | None = None
    full_address: str | None = None
    address_verified: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None
