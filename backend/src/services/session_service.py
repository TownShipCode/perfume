from __future__ import annotations

import json
from typing import Any

from src.db.connection import Database, execute, fetch_one
from src.models.cart import CartItem


async def get_session_by_phone(database: Database, phone_number: str) -> dict | None:
    query = "SELECT * FROM sessions WHERE phone_number = $1" if database.mode == "postgres" else "SELECT * FROM sessions WHERE phone_number = ?"
    session = await fetch_one(database, query, phone_number)
    if session is None:
        return None
    return _decode_session(session)


async def get_or_create_session(database: Database, phone_number: str) -> dict:
    existing = await get_session_by_phone(database, phone_number)
    if existing is not None:
        return existing

    if database.mode == "postgres":
        await execute(database, "INSERT INTO sessions (phone_number) VALUES ($1)", phone_number)
    else:
        await execute(database, "INSERT INTO sessions (phone_number) VALUES (?)", phone_number)

    created = await get_session_by_phone(database, phone_number)
    assert created is not None
    return created


async def save_session_state(
    database: Database,
    phone_number: str,
    *,
    state: str,
    cart: list[CartItem],
    current_step: int,
    temp_address: dict[str, str] | None = None,
) -> dict:
    cart_payload = json.dumps([item.model_dump() for item in cart])
    address_payload = json.dumps(temp_address) if temp_address is not None else None

    if database.mode == "postgres":
        await execute(
            database,
            """
            UPDATE sessions
            SET state = $1, cart = $2, temp_address = $3, current_step = $4, updated_at = NOW()
            WHERE phone_number = $5
            """,
            state,
            cart_payload,
            address_payload,
            current_step,
            phone_number,
        )
    else:
        await execute(
            database,
            """
            UPDATE sessions
            SET state = ?, cart = ?, temp_address = ?, current_step = ?, updated_at = CURRENT_TIMESTAMP
            WHERE phone_number = ?
            """,
            state,
            cart_payload,
            address_payload,
            current_step,
            phone_number,
        )

    updated = await get_session_by_phone(database, phone_number)
    assert updated is not None
    return updated


def _decode_session(session: dict[str, Any]) -> dict[str, Any]:
    decoded = dict(session)
    cart_value = decoded.get("cart")
    if isinstance(cart_value, str):
        decoded["cart"] = json.loads(cart_value or "[]")
    temp_address = decoded.get("temp_address")
    if isinstance(temp_address, str) and temp_address:
        decoded["temp_address"] = json.loads(temp_address)
    return decoded
