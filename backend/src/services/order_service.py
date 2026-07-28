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
o.forward_payload, o.forward_response, o.forward_attempts, o.shipping_fee,
o.agent_code, o.team_member_id, o.commission_amount, o.created_at, o.updated_at,
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
    agent_code: str | None = None,
    team_member_id: int | None = None,
    commission_amount: Decimal = Decimal("0"),
) -> dict:
    order_number = _generate_order_number()
    items_payload = json.dumps([item.model_dump() for item in cart_items])

    if database.mode == "postgres":
        row = await fetch_one(
            database,
            """
            INSERT INTO orders (order_number, customer_id, items, total, status, shipping_fee,
                                agent_code, team_member_id, commission_amount)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id, order_number, customer_id, items, total, status, pop_image_url, tracking_info,
                      forwarded_to, forwarded_at, forward_delivery_status, forward_message_id, forward_error,
                      forward_payload, forward_response, forward_attempts, agent_code, team_member_id,
                      commission_amount, created_at, updated_at
            """,
            order_number, customer_id, items_payload, total, "pending", shipping_fee,
            agent_code, team_member_id, commission_amount,
        )
        assert row is not None
        # Stock decrement
        for item in cart_items:
            await _adjust_stock(database, item.product_id, -item.quantity)
        return _decode_order(row)

    await execute(
        database,
        """
        INSERT INTO orders (order_number, customer_id, items, total, status, shipping_fee,
                            agent_code, team_member_id, commission_amount)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        order_number, customer_id, items_payload, str(total), "pending", str(shipping_fee),
        agent_code, str(team_member_id) if team_member_id else None,
        str(commission_amount),
    )
    row = await fetch_one(
        database,
        """
         SELECT id, order_number, customer_id, items, total, status, pop_image_url, tracking_info,
             forwarded_to, forwarded_at, forward_delivery_status, forward_message_id, forward_error,
             forward_payload, forward_response, forward_attempts, agent_code, team_member_id,
             commission_amount, created_at, updated_at
        FROM orders
        WHERE order_number = ?
        """,
        order_number,
    )
    assert row is not None

    # ── Stock decrement (Phase 8) ──
    await _decrement_stock_for_order(database, cart_items)

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


async def get_latest_order(database: Database, phone_number: str) -> dict | None:
    """Get the most recent order for a customer by phone number."""
    if database.mode == "postgres":
        row = await fetch_one(
            database,
            """SELECT o.id, o.order_number, o.total, o.status, o.payment_method
               FROM orders o
               JOIN customers c ON c.id = o.customer_id
               WHERE c.phone_number = $1
               ORDER BY o.created_at DESC LIMIT 1""",
            phone_number,
        )
    else:
        row = await fetch_one(
            database,
            """SELECT o.id, o.order_number, o.total, o.status, o.payment_method
               FROM orders o
               JOIN customers c ON c.id = o.customer_id
               WHERE c.phone_number = ?
               ORDER BY o.created_at DESC LIMIT 1""",
            phone_number,
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


async def update_order_tracking(database: Database, order_id: int, tracking_info: str) -> dict | None:
    if database.mode == "postgres":
        await execute(
            database,
            "UPDATE orders SET tracking_info = $1, updated_at = NOW() WHERE id = $2",
            tracking_info,
            order_id,
        )
    else:
        await execute(
            database,
            "UPDATE orders SET tracking_info = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            tracking_info,
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


async def cancel_pending_pop_order(database: Database, phone_number: str) -> None:
    """Cancel the latest pop_waiting order for a customer, if any. Restore stock."""
    # First get the order to restore stock
    order = await fetch_one(
        database,
        "SELECT * FROM orders WHERE customer_id = (SELECT id FROM customers WHERE phone_number = $1) AND status = 'pop_waiting' ORDER BY created_at DESC LIMIT 1"
        if database.mode == "postgres"
        else "SELECT * FROM orders WHERE customer_id = (SELECT id FROM customers WHERE phone_number = ?) AND status = 'pop_waiting' ORDER BY created_at DESC LIMIT 1",
        phone_number,
    )
    if order:
        await _increment_stock_for_order(database, order)

    if database.mode == "postgres":
        await execute(
            database,
            """
            UPDATE orders SET status = 'cancelled', updated_at = NOW()
            WHERE customer_id = (SELECT id FROM customers WHERE phone_number = $1)
              AND status = 'pop_waiting'
              AND id = (SELECT id FROM orders WHERE customer_id = (SELECT id FROM customers WHERE phone_number = $1) AND status = 'pop_waiting' ORDER BY created_at DESC LIMIT 1)
            """,
            phone_number,
        )
    else:
        await execute(
            database,
            """
            UPDATE orders SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP
            WHERE customer_id = (SELECT id FROM customers WHERE phone_number = ?)
              AND status = 'pop_waiting'
              AND id = (SELECT id FROM orders WHERE customer_id = (SELECT id FROM customers WHERE phone_number = ?) AND status = 'pop_waiting' ORDER BY created_at DESC LIMIT 1)
            """,
            phone_number,
            phone_number,
        )


async def expire_stale_pop_orders(database: Database, pop_expiry_hours: int) -> int:
    """Expire stale POP orders. Restore stock for each."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=pop_expiry_hours)

    # Get expired orders to restore stock
    if database.mode == "postgres":
        expired = await fetch_all(
            database,
            "SELECT * FROM orders WHERE status = 'pop_waiting' AND created_at < $1",
            cutoff,
        )
        await execute(
            database,
            "UPDATE orders SET status = 'expired', updated_at = NOW() WHERE status = 'pop_waiting' AND created_at < $1",
            cutoff,
        )
    else:
        expired = await fetch_all(
            database,
            "SELECT * FROM orders WHERE status = 'pop_waiting' AND created_at < ?",
            cutoff.isoformat(),
        )
        await execute(
            database,
            "UPDATE orders SET status = 'expired', updated_at = CURRENT_TIMESTAMP WHERE status = 'pop_waiting' AND created_at < ?",
            cutoff.isoformat(),
        )

    for order in expired:
        await _increment_stock_for_order(database, order)

    return len(expired)


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


# ── Stock management helpers (Phase 8) ──


async def _adjust_stock(database: Database, product_id: int, delta: int) -> None:
    """Adjust stock_quantity for a product by delta (negative = decrement)."""
    if database.mode == "postgres":
        await execute(
            database,
            "UPDATE products SET stock_quantity = COALESCE(stock_quantity, 0) + $1, updated_at = NOW() WHERE id = $2 AND stock_quantity IS NOT NULL",
            delta, product_id,
        )
    else:
        await execute(
            database,
            "UPDATE products SET stock_quantity = COALESCE(stock_quantity, 0) + ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND stock_quantity IS NOT NULL",
            delta, product_id,
        )


async def _decrement_stock_for_order(database: Database, cart_items: list[CartItem]) -> None:
    """Decrement stock for each item in the order."""
    for item in cart_items:
        await _adjust_stock(database, item.product_id, -item.quantity)


async def _increment_stock_for_order(database: Database, order: dict) -> None:
    """Increment stock for each item in a cancelled/expired order."""
    items = order.get("items", [])
    if isinstance(items, str):
        items = json.loads(items or "[]")
    for item in items:
        pid = item.get("product_id") or item.get("id", 0)
        qty = item.get("quantity", 0)
        if pid and qty:
            await _adjust_stock(database, int(pid), int(qty))


async def record_fl_pop(
    database: Database,
    order_id: int,
    fl_pop_url: str,
    fl_amount: Decimal | None = None,
) -> dict | None:
    """Record BioMed's POP paid to Focus Logic."""
    now = datetime.now(timezone.utc)
    if database.mode == "postgres":
        row = await fetch_one(
            database,
            """
            UPDATE orders
            SET fl_pop_image_url = $1, fl_pop_uploaded_at = $2, fl_amount = $3, updated_at = $4
            WHERE id = $5
            RETURNING id, order_number, customer_id, items, total, status, pop_image_url, tracking_info,
                      forwarded_to, forwarded_at, forward_delivery_status, forward_message_id, forward_error,
                      forward_payload, forward_response, forward_attempts,
                      fl_pop_image_url, fl_pop_uploaded_at, fl_amount,
                      created_at, updated_at
            """,
            fl_pop_url,
            now,
            fl_amount,
            now,
            order_id,
        )
    else:
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")
        await execute(
            database,
            """
            UPDATE orders
            SET fl_pop_image_url = ?, fl_pop_uploaded_at = ?, fl_amount = ?, updated_at = ?
            WHERE id = ?
            """,
            fl_pop_url,
            now_str,
            str(fl_amount) if fl_amount else None,
            now_str,
            order_id,
        )
        row = await fetch_one(
            database,
            "SELECT id, order_number, customer_id, items, total, status, pop_image_url, tracking_info, forwarded_to, forwarded_at, forward_delivery_status, forward_message_id, forward_error, forward_payload, forward_response, forward_attempts, fl_pop_image_url, fl_pop_uploaded_at, fl_amount, created_at, updated_at FROM orders WHERE id = ?",
            order_id,
        )

    if row is None:
        return None
    return _decode_order(row)
