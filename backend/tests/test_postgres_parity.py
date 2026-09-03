"""Postgres parity tests — the suite's SQLite safety net can't catch PG-only bugs.

Why this file exists
--------------------
The main test suite runs every migration against a fresh SQLite file through
`_sqlite_compat`, which TRANSLATES AWAY Postgres specifics (partial-index
`WHERE` clauses, `LOWER()` expression indexes, type coercion, `IF NOT EXISTS`
semantics). That translation is why commit `84eb402`'s migration passed 39/39
on SQLite yet broke production Postgres: migration 014's FULL unique index on
`LOWER(email)` + migration 009's `email NOT NULL DEFAULT ''` meant only ONE
customer could ever have an empty email, so every NEW WhatsApp number crashed
with `UniqueViolationError` (fixed by migration 017 → partial unique index).

These tests run the REAL migration runner against a REAL Postgres so the
schema is validated on the engine production uses. They are skipped unless
`TEST_DATABASE_URL` is set (a throwaway Postgres — never point this at the
production database; the test DROPs the public schema it runs against).

Run locally against a disposable Postgres:
    set TEST_DATABASE_URL=postgresql://postgres:pass@localhost:5432/zen_test
    set PYTHONPATH=...\\backend
    .\\.venv\\Scripts\\python -m pytest backend\\tests\\test_postgres_parity.py -q
"""
from __future__ import annotations

import asyncio
import os

import pytest

from src.config import get_settings
from src.db.connection import (
    Database,
    close_database,
    connect_database,
    execute,
    fetch_one,
    initialize_database,
)
from src.services.customer_service import get_or_create_customer

TEST_URL = os.getenv("TEST_DATABASE_URL", "").strip()

pytestmark = pytest.mark.skipif(
    not TEST_URL,
    reason="TEST_DATABASE_URL not set — Postgres parity tests skipped",
)


async def _open_test_db() -> Database:
    """Connect to the Postgres pointed at by TEST_DATABASE_URL.

    `connect_database`/`get_settings` read `DATABASE_URL`, so point it at the
    test URL (and clear the settings cache) before connecting.
    """
    os.environ["DATABASE_URL"] = TEST_URL
    os.environ["LOCAL_SQLITE_PATH"] = "/tmp/zen-parity-not-used.db"
    get_settings.cache_clear()
    settings = get_settings()
    database = await connect_database(settings)
    if database.mode != "postgres":
        raise RuntimeError(f"TEST_DATABASE_URL did not yield a Postgres connection: {TEST_URL}")
    return database


async def _reset_schema(database: Database) -> None:
    """Drop and recreate the public schema for a clean, repeatable run.

    Only ever runs when TEST_DATABASE_URL is set (test-only database).
    """
    await execute(database, "DROP SCHEMA public CASCADE")
    await execute(database, "CREATE SCHEMA public")


def test_migrations_apply_cleanly_on_postgres() -> None:
    """The full migration chain (incl. 017) applies on real Postgres."""

    async def scenario() -> None:
        db = await _open_test_db()
        try:
            await _reset_schema(db)
            await initialize_database(db)

            # Migration 017 must be recorded
            row = await fetch_one(
                db, "SELECT version, name FROM _schema_migrations WHERE version = 17"
            )
            assert row is not None, "migration 017 was not applied"
            assert row["name"] == "017_fix_customers_email_unique.sql"
        finally:
            await close_database(db)

    asyncio.run(scenario())


def test_new_whatsapp_customer_insert_succeeds_on_postgres() -> None:
    """Regression: a brand-new phone number must be able to register.

    This is the exact INSERT that failed on production before migration 017
    (UNIQUE violation on LOWER(email)='' for every new customer).
    """

    async def scenario() -> None:
        db = await _open_test_db()
        try:
            await _reset_schema(db)
            await initialize_database(db)

            # First new number (occupies the empty-email slot if the bug existed)
            a = await get_or_create_customer(db, "27830000011", "First")
            assert a["email"] == ""

            # Second + third new numbers — the actual regression
            b = await get_or_create_customer(db, "27830000022", "Second")
            c = await get_or_create_customer(db, "27830000033", "Third")
            assert b["email"] == ""
            assert c["email"] == ""

            # Cleanup test rows
            for phone in ("27830000011", "27830000022", "27830000033"):
                await execute(db, "DELETE FROM customers WHERE phone_number = $1", phone)
        finally:
            await close_database(db)

    asyncio.run(scenario())


def test_duplicate_real_email_still_rejected_on_postgres() -> None:
    """017 must keep blocking duplicate REAL emails (case-insensitive)."""

    async def scenario() -> None:
        db = await _open_test_db()
        try:
            await _reset_schema(db)
            await initialize_database(db)

            await execute(
                db,
                "INSERT INTO customers (phone_number, name, email) VALUES ($1, $2, $3)",
                "27830000044", "Carol", "CAROL@X.COM",
            )
            # Same email, different case → must violate the partial unique index
            from asyncpg.exceptions import UniqueViolationError
            with pytest.raises(UniqueViolationError):
                await execute(
                    db,
                    "INSERT INTO customers (phone_number, name, email) VALUES ($1, $2, $3)",
                    "27830000055", "Carol2", "carol@x.com",
                )

            await execute(db, "DELETE FROM customers WHERE phone_number = $1", "27830000044")
        finally:
            await close_database(db)

    asyncio.run(scenario())


def test_email_unique_index_is_partial_on_postgres() -> None:
    """The email unique index must be PARTIAL (WHERE email <> '') on Postgres.

    A full unique index on LOWER(email) with a NOT NULL DEFAULT '' column is
    the root cause of the silent-bot bug — assert the schema stays partial.
    """

    async def scenario() -> None:
        db = await _open_test_db()
        try:
            await _reset_schema(db)
            await initialize_database(db)

            indexdef_row = await fetch_one(
                db,
                "SELECT indexdef FROM pg_indexes "
                "WHERE schemaname = 'public' AND indexname = 'idx_customers_email_unique'",
            )
            assert indexdef_row is not None, "email unique index not found"
            indexdef = indexdef_row["indexdef"]
            assert "WHERE" in indexdef and "email" in indexdef, (
                f"email index is NOT partial — root cause regression. Got: {indexdef}"
            )
            assert "UNIQUE" in indexdef.upper(), "email index lost its UNIQUE constraint"
        finally:
            await close_database(db)

    asyncio.run(scenario())
