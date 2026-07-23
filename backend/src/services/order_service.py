from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from uuid import uuid4

from src.db.connection import Database, execute, fetch_all, fetch_one
from src.models.cart import CartItem


ORDER_SELECT_COLUMNS = """
o.id, o.order_number, o.customer_id, o.items, o.total, o.status, o.pop_image_url, o.tracking_info,
o.forwarded_to, o.forwarded_at, o.forward_delivery_status, o.forward_message_id, o.forward_error,
o.forward_payload, o.forward_response, o.forward_attempts, o.shipping_fee, o.created_at, o.updated_at,
c.phone_number, c.full_address, c.name
""".strip()

ORDER_SINGLE_COLUMNS = """
id, order_number, customer_id, items, total, status, pop_image_url, tracking_info,
forwarded_to, forwarded_at, forward_delivery_status, forward_message_id, forward_error,
forward_payload, forward_response, forward_attempts, created_at, updated_at
""".strip()


async def create_order(
    database: Database,
    *,
    customer_id: int,
    cart_items: list[CartItem],
    total: Decimal,
    shipping_fee: Decimal = Decimal("0"),
) -> dict:
    order_number = _generate_order_number()
    items_payload = json.dumps([item.model_dump() for item in cart_items])

    if database.mode == "postgres":
        row = await fetch_one(
            database,
            """
            INSERT INTO orders (order_number, customer_id, items, total, status, shipping_fee)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id, order_number, customer_id, items, total, status, pop_image_url, tracking_info,
                      forwarded_to, forwarded_at, forward_delivery_status, forward_message_id, forward_error,
                      forward_payload, forward_response, forward_attempts, created_at, updated_at
            """,
            order_number,
            customer_id,
            items_payload,
            total,
            "pending",
            shipping_fee,
        )
        assert row is not None
        return _decode_order(row)

    await execute(
        database,
        """
        INSERT INTO orders (order_number, customer_id, items, total, status, shipping_fee)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        order_number,
        customer_id,
        items_payload,
        str(total),
        "pending",
        str(shipping_fee),
    )
    row = await fetch_one(
        database,
        """
         SELECT id, order_number, customer_id, items, total, status, pop_image_url, tracking_info,
             forwarded_to, forwarded_at, forward_delivery_status, forward_message_id, forward_error,
             forward_payload, forward_response, forward_attempts, created_at, updated_at
        FROM orders
        WHERE order_number = ?
        """,
        order_number,
    )
    assert row is not None
    return _decode_order(row)


def _generate_order_number() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    suffix = uuid4().hex[:6].upper()
    return f"ORD-{stamp}-{suffix}"


async def get_latest_open_order(database: Database, customer_id: int) -> dict | None:
    if database.mode == "postgres":
        row = await fetch_one(
            database,
            """
                 SELECT id, order_number, customer_id, items, total, status, pop_image_url, tracking_info,
                     forwarded_to, forwarded_at, forward_delivery_status, forward_message_id, forward_error,
                     forward_payload, forward_response, forward_attempts, created_at, updated_at
            FROM orders
            WHERE customer_id = $1 AND status IN ('pending', 'pop_waiting', 'address_pending')
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            customer_id,
        )
        return _decode_order(row)

    row = await fetch_one(
        database,
        """
         SELECT id, order_number, customer_id, items, total, status, pop_image_url, tracking_info,
             forwarded_to, forwarded_at, forward_delivery_status, forward_message_id, forward_error,
             forward_payload, forward_response, forward_attempts, created_at, updated_at
        FROM orders
        WHERE customer_id = ? AND status IN ('pending', 'pop_waiting', 'address_pending')
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """,
        customer_id,
    )
    return _decode_order(row)


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
            "SELECT id, order_number, customer_id, items, total, status, pop_image_url, tracking_info, forwarded_to, forwarded_at, forward_delivery_status, forward_message_id, forward_error, forward_payload, forward_response, forward_attempts, created_at, updated_at FROM orders WHERE id = $1",
            order_id,
        )
        assert row is not None
        return _decode_order(row)

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
        "SELECT id, order_number, customer_id, items, total, status, pop_image_url, tracking_info, forwarded_to, forwarded_at, forward_delivery_status, forward_message_id, forward_error, forward_payload, forward_response, forward_attempts, created_at, updated_at FROM orders WHERE id = ?",
        order_id,
    )
    assert row is not None
    return _decode_order(row)


async def list_orders(
    database: Database,
    status: str | None = None,
    forward_status: str | None = None,
) -> list[dict]:
    query, params = _build_list_orders_query(database.mode, status, forward_status)
    rows = await fetch_all(database, query, *params)
    return [_decode_order(row) for row in rows]


async def get_order_by_id(database: Database, order_id: int) -> dict | None:
    if database.mode == "postgres":
        row = await fetch_one(
            database,
            """
            SELECT o.id, o.order_number, o.customer_id, o.items, o.total, o.status, o.pop_image_url, o.tracking_info,
                     o.forwarded_to, o.forwarded_at, o.forward_delivery_status, o.forward_message_id, o.forward_error,
                     o.forward_payload, o.forward_response, o.forward_attempts, o.created_at, o.updated_at,
                     c.phone_number, c.full_address, c.name
            FROM orders o
            JOIN customers c ON c.id = o.customer_id
            WHERE o.id = $1
            """,
            order_id,
        )
    else:
        row = await fetch_one(
            database,
            """
            SELECT o.id, o.order_number, o.customer_id, o.items, o.total, o.status, o.pop_image_url, o.tracking_info,
                     o.forwarded_to, o.forwarded_at, o.forward_delivery_status, o.forward_message_id, o.forward_error,
                     o.forward_payload, o.forward_response, o.forward_attempts, o.created_at, o.updated_at,
                     c.phone_number, c.full_address, c.name
            FROM orders o
            JOIN customers c ON c.id = o.customer_id
            WHERE o.id = ?
            """,
            order_id,
        )
    return _decode_order(row)


async def update_order_status(database: Database, order_id: int, status: str) -> dict | None:
    if database.mode == "postgres":
        await execute(
            database,
            "UPDATE orders SET status = $1, updated_at = NOW() WHERE id = $2",
            status,
            order_id,
        )
    else:
        await execute(
            database,
            "UPDATE orders SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            status,
            order_id,
        )
    return await get_order_by_id(database, order_id)


async def record_order_forwarding(
    database: Database,
    order_id: int,
    *,
    forwarded_to: str,
    delivery_status: str,
    message_id: str | None = None,
    error: str | None = None,
    payload: dict | None = None,
    response: dict | None = None,
) -> dict | None:
    payload_text = json.dumps(payload) if payload is not None else None
    response_text = json.dumps(response) if response is not None else None

    if database.mode == "postgres":
        await execute(
            database,
            """
            UPDATE orders
            SET forwarded_to = $1, forwarded_at = NOW(), forward_delivery_status = $2, forward_message_id = $3,
                forward_error = $4, forward_payload = $5, forward_response = $6,
                forward_attempts = forward_attempts + 1, updated_at = NOW()
            WHERE id = $7
            """,
            forwarded_to,
            delivery_status,
            message_id,
            error,
            payload_text,
            response_text,
            order_id,
        )
    else:
        await execute(
            database,
            """
            UPDATE orders
            SET forwarded_to = ?, forwarded_at = CURRENT_TIMESTAMP, forward_delivery_status = ?, forward_message_id = ?,
                forward_error = ?, forward_payload = ?, forward_response = ?,
                forward_attempts = forward_attempts + 1, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            forwarded_to,
            delivery_status,
            message_id,
            error,
            payload_text,
            response_text,
            order_id,
        )
    return await get_order_by_id(database, order_id)


async def expire_stale_pop_orders(database: Database, pop_expiry_hours: int) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=pop_expiry_hours)
    if database.mode == "postgres":
        await execute(
            database,
            "UPDATE orders SET status = 'expired', updated_at = NOW() WHERE status = 'pop_waiting' AND created_at < $1",
            cutoff,
        )
    else:
        await execute(
            database,
            "UPDATE orders SET status = 'expired', updated_at = CURRENT_TIMESTAMP WHERE status = 'pop_waiting' AND created_at < ?",
            cutoff.isoformat(),
        )
    return 0


def _build_list_orders_query(mode: str, status: str | None, forward_status: str | None) -> tuple[str, tuple[object, ...]]:
    clauses: list[str] = []
    params: list[object] = []

    def placeholder() -> str:
        if mode == "postgres":
            return f"${len(params) + 1}"
        return "?"

    if status:
        clauses.append(f"o.status = {placeholder()}")
        params.append(status)

    if forward_status == "not_sent":
        clauses.append("(o.forward_delivery_status IS NULL OR o.forward_delivery_status = '')")
    elif forward_status:
        clauses.append(f"o.forward_delivery_status = {placeholder()}")
        params.append(forward_status)

    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    query = f"""
    SELECT {ORDER_SELECT_COLUMNS}
    FROM orders o
    JOIN customers c ON c.id = o.customer_id
    {where}
    ORDER BY o.created_at DESC, o.id DESC
    """
    return query, tuple(params)


def _decode_order(row: dict | None) -> dict | None:
    if row is None:
        return None
    decoded = dict(row)
    items_value = decoded.get("items")
    if isinstance(items_value, str):
        decoded["items"] = json.loads(items_value or "[]")
    for key in ("forward_payload", "forward_response"):
        raw_value = decoded.get(key)
        if isinstance(raw_value, str) and raw_value:
            decoded[key] = json.loads(raw_value)
    return decoded
