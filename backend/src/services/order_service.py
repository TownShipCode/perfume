from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from src.db.connection import Database, execute, fetch_one
from src.models.cart import CartItem


async def create_order(
    database: Database,
    *,
    customer_id: int,
    cart_items: list[CartItem],
    total: Decimal,
) -> dict:
    order_number = _generate_order_number()
    items_payload = json.dumps([item.model_dump() for item in cart_items])

    if database.mode == "postgres":
        row = await fetch_one(
            database,
            """
            INSERT INTO orders (order_number, customer_id, items, total, status)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, order_number, customer_id, items, total, status, pop_image_url, tracking_info, created_at, updated_at
            """,
            order_number,
            customer_id,
            items_payload,
            total,
            "pending",
        )
        assert row is not None
        return row

    await execute(
        database,
        """
        INSERT INTO orders (order_number, customer_id, items, total, status)
        VALUES (?, ?, ?, ?, ?)
        """,
        order_number,
        customer_id,
        items_payload,
        str(total),
        "pending",
    )
    row = await fetch_one(
        database,
        """
        SELECT id, order_number, customer_id, items, total, status, pop_image_url, tracking_info, created_at, updated_at
        FROM orders
        WHERE order_number = ?
        """,
        order_number,
    )
    assert row is not None
    return row


def _generate_order_number() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    suffix = uuid4().hex[:6].upper()
    return f"ORD-{stamp}-{suffix}"


async def get_latest_open_order(database: Database, customer_id: int) -> dict | None:
    if database.mode == "postgres":
        return await fetch_one(
            database,
            """
            SELECT id, order_number, customer_id, items, total, status, pop_image_url, tracking_info, created_at, updated_at
            FROM orders
            WHERE customer_id = $1 AND status IN ('pending', 'pop_waiting', 'address_pending')
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            customer_id,
        )

    return await fetch_one(
        database,
        """
        SELECT id, order_number, customer_id, items, total, status, pop_image_url, tracking_info, created_at, updated_at
        FROM orders
        WHERE customer_id = ? AND status IN ('pending', 'pop_waiting', 'address_pending')
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """,
        customer_id,
    )


async def record_pop_received(database: Database, order_id: int, media_reference: str) -> dict:
    if database.mode == "postgres":
        await execute(
            database,
            """
            UPDATE orders
            SET pop_image_url = $1, status = $2, updated_at = NOW()
            WHERE id = $3
            """,
            media_reference,
            "pop_received",
            order_id,
        )
        row = await fetch_one(
            database,
            "SELECT id, order_number, customer_id, items, total, status, pop_image_url, tracking_info, created_at, updated_at FROM orders WHERE id = $1",
            order_id,
        )
        assert row is not None
        return row

    await execute(
        database,
        """
        UPDATE orders
        SET pop_image_url = ?, status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        media_reference,
        "pop_received",
        order_id,
    )
    row = await fetch_one(
        database,
        "SELECT id, order_number, customer_id, items, total, status, pop_image_url, tracking_info, created_at, updated_at FROM orders WHERE id = ?",
        order_id,
    )
    assert row is not None
    return row
