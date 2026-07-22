from __future__ import annotations

from src.db.connection import Database, execute, fetch_one


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
