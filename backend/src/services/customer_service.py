from __future__ import annotations

from typing import Any

from src.db.connection import Database, fetch_all, execute, fetch_one


async def get_customer_by_phone(database: Database, phone_number: str) -> dict[str, Any] | None:
    query = "SELECT * FROM customers WHERE phone_number = $1" if database.mode == "postgres" else "SELECT * FROM customers WHERE phone_number = ?"
    return await fetch_one(database, query, phone_number)


async def get_or_create_customer(database: Database, phone_number: str, name: str | None = None) -> dict[str, Any]:
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


async def save_customer_profile(
    database: Database,
    phone_number: str,
    *,
    name: str = "",
    area: str,
    street: str,
    city: str,
    postal_code: str = "",
    email: str = "",
    province: str = "",
    surname: str = "",
) -> dict:
    parts = [street, area, city, postal_code] if postal_code else [street, area, city]
    full_address = ", ".join(p for p in parts if p)
    if database.mode == "postgres":
        await execute(
            database,
            """
            UPDATE customers
            SET name = COALESCE(NULLIF($1, ''), name),
                area = $2, street = $3, city = $4, postal_code = $5, email = $6,
                province = $7, surname = $8, full_address = $9, address_verified = TRUE, updated_at = NOW()
            WHERE phone_number = $10
            """,
            name,
            area,
            street,
            city,
            postal_code,
            email,
            province,
            surname,
            full_address,
            phone_number,
        )
    else:
        await execute(
            database,
            """
            UPDATE customers
            SET name = CASE WHEN ? != '' THEN ? ELSE name END,
                area = ?, street = ?, city = ?, postal_code = ?, email = ?,
                province = ?, surname = ?, full_address = ?, address_verified = 1, updated_at = CURRENT_TIMESTAMP
            WHERE phone_number = ?
            """,
            name,
            name,
            area,
            street,
            city,
            postal_code,
            email,
            province,
            surname,
            full_address,
            phone_number,
        )

    updated = await get_customer_by_phone(database, phone_number)
    assert updated is not None
    return updated


async def save_customer_address(
    database: Database,
    phone_number: str,
    *,
    area: str,
    street: str,
    city: str,
) -> dict:
    return await save_customer_profile(
        database,
        phone_number,
        area=area,
        street=street,
        city=city,
    )


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
) -> dict[str, Any] | None:
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


# ── Agent & Role functions (Phase 1-4) ──


async def get_customer_by_agent_code(database: Database, agent_code: str) -> dict[str, Any] | None:
    """Look up a customer by their agent code."""
    query = (
        "SELECT * FROM customers WHERE agent_code = $1"
        if database.mode == "postgres"
        else "SELECT * FROM customers WHERE agent_code = ?"
    )
    return await fetch_one(database, query, agent_code)


async def get_customer_by_email(database: Database, email: str) -> dict[str, Any] | None:
    """Look up a customer by email (for web store login)."""
    query = (
        "SELECT * FROM customers WHERE LOWER(email) = LOWER($1)"
        if database.mode == "postgres"
        else "SELECT * FROM customers WHERE LOWER(email) = LOWER(?)"
    )
    return await fetch_one(database, query, email.strip().lower())


async def register_agent(
    database: Database,
    phone_number: str,
    first_name: str,
    surname: str,
    team_code: str,
    recovery_pin: str,
) -> dict[str, Any] | None:
    """Register a new agent under a team member."""
    import secrets

    # Validate team member exists
    team_member = await get_customer_by_agent_code(database, team_code)
    if team_member is None or team_member.get("role") != "team_member":
        return None

    # Generate agent code
    suffix = secrets.token_hex(2).upper()[:4]
    agent_code = f"{team_code}-{suffix}"

    if database.mode == "postgres":
        await execute(
            database,
            """INSERT INTO customers (phone_number, name, surname, role, agent_code, registered_by, recovery_pin)
               VALUES ($1, $2, $3, 'agent', $4, $5, $6)
               ON CONFLICT (phone_number) DO UPDATE
               SET role = 'agent', agent_code = $4, registered_by = $5, recovery_pin = $6,
                   name = $2, surname = $3, updated_at = NOW()""",
            phone_number, first_name, surname, agent_code, team_member["id"], recovery_pin,
        )
    else:
        await execute(
            database,
            """INSERT INTO customers (phone_number, name, surname, role, agent_code, registered_by, recovery_pin)
               VALUES (?, ?, ?, 'agent', ?, ?, ?)
               ON CONFLICT (phone_number) DO UPDATE
               SET role = 'agent', agent_code = ?, registered_by = ?, recovery_pin = ?,
                   name = ?, surname = ?, updated_at = CURRENT_TIMESTAMP""",
            phone_number, first_name, surname, agent_code, team_member["id"], recovery_pin,
            agent_code, team_member["id"], recovery_pin, first_name, surname,
        )

    return await get_customer_by_phone(database, phone_number)


async def migrate_phone_number(
    database: Database,
    old_phone: str,
    new_phone: str,
) -> dict[str, Any] | None:
    """Migrate a customer account to a new phone number. Tracks old number."""
    import json as _json

    customer = await get_customer_by_phone(database, old_phone)
    if customer is None:
        return None

    old_phones = _json.loads(customer.get("previous_phone_numbers") or "[]")
    old_phones.append(old_phone)

    if database.mode == "postgres":
        await execute(
            database,
            """UPDATE customers SET phone_number = $1, previous_phone_numbers = $2, updated_at = NOW()
               WHERE id = $3""",
            new_phone, _json.dumps(old_phones), customer["id"],
        )
    else:
        await execute(
            database,
            """UPDATE customers SET phone_number = ?, previous_phone_numbers = ?, updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            new_phone, _json.dumps(old_phones), customer["id"],
        )

    return await get_customer_by_phone(database, new_phone)


async def list_customers_by_role(database: Database, role: str) -> list[dict]:
    """List all customers with a specific role."""
    if database.mode == "postgres":
        return await fetch_all(
            database,
            "SELECT * FROM customers WHERE role = $1 ORDER BY created_at DESC",
            role,
        )
    return await fetch_all(
        database,
        "SELECT * FROM customers WHERE role = ? ORDER BY created_at DESC",
        role,
    )


async def list_agents_by_team_member(database: Database, team_member_id: int) -> list[dict]:
    """List all agents registered by a specific team member."""
    if database.mode == "postgres":
        return await fetch_all(
            database,
            "SELECT * FROM customers WHERE registered_by = $1 AND role = 'agent' ORDER BY created_at DESC",
            team_member_id,
        )
    return await fetch_all(
        database,
        "SELECT * FROM customers WHERE registered_by = ? AND role = 'agent' ORDER BY created_at DESC",
        team_member_id,
    )

