from __future__ import annotations

from src.db.connection import Database, fetch_all, execute, fetch_one


async def get_customer_by_phone(database: Database, phone_number: str) -> dict | None:
    query = "SELECT * FROM customers WHERE phone_number = $1" if database.mode == "postgres" else "SELECT * FROM customers WHERE phone_number = ?"
    return await fetch_one(database, query, phone_number)


async def get_or_create_customer(database: Database, phone_number: str, name: str | None = None) -> dict:
    existing = await get_customer_by_phone(database, phone_number)
    if existing is not None:
        return existing

    if database.mode == "postgres":
        await execute(
            database,
            "INSERT INTO customers (phone_number, name) VALUES ($1, $2)",
            phone_number,
            name,
        )
    else:
        await execute(
            database,
            "INSERT INTO customers (phone_number, name) VALUES (?, ?)",
            phone_number,
            name,
        )

    created = await get_customer_by_phone(database, phone_number)
    assert created is not None
    return created


async def save_customer_address(
    database: Database,
    phone_number: str,
    *,
    area: str,
    street: str,
    city: str,
) -> dict:
    full_address = f"{street}, {area}, {city}"
    if database.mode == "postgres":
        await execute(
            database,
            """
            UPDATE customers
            SET area = $1, street = $2, city = $3, full_address = $4, address_verified = TRUE, updated_at = NOW()
            WHERE phone_number = $5
            """,
            area,
            street,
            city,
            full_address,
            phone_number,
        )
    else:
        await execute(
            database,
            """
            UPDATE customers
            SET area = ?, street = ?, city = ?, full_address = ?, address_verified = 1, updated_at = CURRENT_TIMESTAMP
            WHERE phone_number = ?
            """,
            area,
            street,
            city,
            full_address,
            phone_number,
        )

    updated = await get_customer_by_phone(database, phone_number)
    assert updated is not None
    return updated


async def list_customers(database: Database) -> list[dict]:
    if database.mode == "postgres":
        return await fetch_all(
            database,
            """
            SELECT c.*, COUNT(o.id) AS order_count
            FROM customers c
            LEFT JOIN orders o ON o.customer_id = c.id
            GROUP BY c.id
            ORDER BY c.created_at DESC, c.id DESC
            """
        )

    return await fetch_all(
        database,
        """
        SELECT c.*, COUNT(o.id) AS order_count
        FROM customers c
        LEFT JOIN orders o ON o.customer_id = c.id
        GROUP BY c.id
        ORDER BY c.created_at DESC, c.id DESC
        """
    )


async def list_customer_orders(database: Database, phone_number: str) -> list[dict]:
    if database.mode == "postgres":
        return await fetch_all(
            database,
            """
             SELECT o.id, o.order_number, o.customer_id, o.items, o.total, o.status, o.pop_image_url, o.tracking_info,
                 o.forwarded_to, o.forwarded_at, o.forward_delivery_status, o.forward_message_id, o.forward_error,
                 o.forward_payload, o.forward_response, o.forward_attempts, o.created_at, o.updated_at
            FROM orders o
            JOIN customers c ON c.id = o.customer_id
            WHERE c.phone_number = $1
            ORDER BY o.created_at DESC, o.id DESC
            """,
            phone_number,
        )

    return await fetch_all(
        database,
        """
         SELECT o.id, o.order_number, o.customer_id, o.items, o.total, o.status, o.pop_image_url, o.tracking_info,
             o.forwarded_to, o.forwarded_at, o.forward_delivery_status, o.forward_message_id, o.forward_error,
             o.forward_payload, o.forward_response, o.forward_attempts, o.created_at, o.updated_at
        FROM orders o
        JOIN customers c ON c.id = o.customer_id
        WHERE c.phone_number = ?
        ORDER BY o.created_at DESC, o.id DESC
        """,
        phone_number,
    )


async def update_customer_address(
    database: Database,
    phone_number: str,
    *,
    area: str,
    street: str,
    city: str,
) -> dict | None:
    existing = await get_customer_by_phone(database, phone_number)
    if existing is None:
        return None
    return await save_customer_address(database, phone_number, area=area, street=street, city=city)


async def set_customer_language(database: Database, phone_number: str, language: str) -> dict | None:
    existing = await get_customer_by_phone(database, phone_number)
    if existing is None:
        return None
    if database.mode == "postgres":
        await execute(database, "UPDATE customers SET language = $1, updated_at = NOW() WHERE phone_number = $2", language, phone_number)
    else:
        await execute(database, "UPDATE customers SET language = ?, updated_at = CURRENT_TIMESTAMP WHERE phone_number = ?", language, phone_number)
    return await get_customer_by_phone(database, phone_number)

