from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.config import Settings, get_settings


MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


@dataclass
class Database:
    mode: str
    connection: sqlite3.Connection | None = None
    pool: Any = None


async def connect_database(settings: Settings | None = None) -> Database:
    settings = settings or get_settings()
    if settings.database_url and settings.database_url.startswith("postgres"):
        import asyncpg
        pool = await asyncpg.create_pool(dsn=settings.database_url, min_size=1, max_size=5)
        return Database(mode="postgres", pool=pool)

    connection = sqlite3.connect(settings.local_sqlite_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return Database(mode="sqlite", connection=connection)


async def close_database(database: Database) -> None:
    if database.pool is not None:
        await database.pool.close()


async def initialize_database(database: Database) -> None:
    for migration in sorted(MIGRATIONS_DIR.glob("*.sql")):
        version = int(migration.name.split("_", 1)[0])
        if await migration_applied(database, version):
            continue
        sql = migration.read_text(encoding="utf-8")
        await execute_script(database, sql)
        await record_migration(database, version, migration.name)


async def migration_applied(database: Database, version: int) -> bool:
    if database.mode == "sqlite":
        connection = database.connection
        assert connection is not None
        connection.execute(
            "CREATE TABLE IF NOT EXISTS _schema_migrations (version INTEGER PRIMARY KEY, name TEXT NOT NULL, applied_at TEXT DEFAULT (datetime('now')))"
        )
        cursor = connection.execute(
            "SELECT version FROM _schema_migrations WHERE version = ?", (version,),
        )
        return cursor.fetchone() is not None

    assert database.pool is not None
    async with database.pool.acquire() as connection:
        await connection.execute(
            "CREATE TABLE IF NOT EXISTS _schema_migrations (version INTEGER PRIMARY KEY, name TEXT NOT NULL, applied_at TIMESTAMPTZ DEFAULT NOW())"
        )
        value = await connection.fetchval(
            "SELECT version FROM _schema_migrations WHERE version = $1", version,
        )
        return value is not None


async def record_migration(database: Database, version: int, name: str) -> None:
    if database.mode == "sqlite":
        connection = database.connection
        assert connection is not None
        connection.execute(
            "INSERT INTO _schema_migrations (version, name) VALUES (?, ?)", (version, name),
        )
        connection.commit()
        return

    assert database.pool is not None
    async with database.pool.acquire() as connection:
        await connection.execute(
            "INSERT INTO _schema_migrations (version, name) VALUES ($1, $2)", version, name,
        )


async def execute_script(database: Database, sql: str) -> None:
    if database.mode == "sqlite":
        connection = database.connection
        assert connection is not None
        sql = _sqlite_compat(sql)
        for statement in sql.split(";"):
            statement = statement.strip()
            if not statement:
                continue
            connection.execute(statement)
        connection.commit()
        return

    assert database.pool is not None
    async with database.pool.acquire() as connection:
        for statement in sql.split(";"):
            statement = statement.strip()
            if not statement:
                continue
            try:
                await connection.execute(statement)
            except AttributeError:
                # asyncpg 0.31.0 raises AttributeError: 'NoneType' object
                # has no attribute 'decode' for some DDL statements that
                # return no result rows (e.g., IF NOT EXISTS with pre-existing objects).
                # The statement succeeded — the error is in asyncpg's result handling.
                pass
            except Exception as error:
                if versionless_duplicate_column(error):
                    continue
                raise


async def fetch_all(database: Database, query: str, *params: object) -> list[dict[str, Any]]:
    if database.mode == "sqlite":
        connection = database.connection
        assert connection is not None
        cursor = connection.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    assert database.pool is not None
    async with database.pool.acquire() as connection:
        rows = await connection.fetch(query, *params)
        return [dict(row) for row in rows]


async def fetch_one(database: Database, query: str, *params: object) -> dict[str, Any] | None:
    if database.mode == "sqlite":
        connection = database.connection
        assert connection is not None
        cursor = connection.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None

    assert database.pool is not None
    async with database.pool.acquire() as connection:
        row = await connection.fetchrow(query, *params)
        return dict(row) if row else None


async def execute(database: Database, query: str, *params: object) -> None:
    if database.mode == "sqlite":
        connection = database.connection
        assert connection is not None
        connection.execute(query, params)
        connection.commit()
        return

    assert database.pool is not None
    async with database.pool.acquire() as connection:
        await connection.execute(query, *params)


def versionless_duplicate_column(error: Exception) -> bool:
    text = str(error).lower()
    return "duplicate_column" in text or "already exists" in text


def _sqlite_compat(sql: str) -> str:
    """Translate Postgres DDL syntax to SQLite-compatible equivalents."""
    import re
    # Column types
    sql = re.sub(r'\bTIMESTAMPTZ\b', 'TEXT', sql)
    sql = re.sub(r'\bJSONB\b', 'TEXT', sql)
    sql = re.sub(r'\bBOOLEAN\b', 'INTEGER', sql)
    sql = re.sub(r'\bSERIAL\b', 'INTEGER', sql)
    # Default values
    sql = re.sub(r'DEFAULT NOW\(\)', "DEFAULT (datetime('now'))", sql)
    sql = re.sub(r'DEFAULT TRUE', 'DEFAULT 1', sql)
    sql = re.sub(r'DEFAULT FALSE', 'DEFAULT 0', sql)
    # GENERATED BY DEFAULT AS IDENTITY → SQLite AUTOINCREMENT handled by INTEGER PRIMARY KEY
    sql = re.sub(r'INTEGER\s+PRIMARY\s+KEY\s+GENERATED\s+BY\s+DEFAULT\s+AS\s+IDENTITY', 'INTEGER PRIMARY KEY AUTOINCREMENT', sql)
    sql = re.sub(r'INTEGER\s+GENERATED\s+BY\s+DEFAULT\s+AS\s+IDENTITY\s+PRIMARY\s+KEY', 'INTEGER PRIMARY KEY AUTOINCREMENT', sql)
    # DECIMAL → REAL (SQLite has no DECIMAL, use REAL for float-like storage)
    sql = re.sub(r'\bDECIMAL\(\d+,\s*\d+\)', 'REAL', sql)
    # Strip IF NOT EXISTS from ALTER TABLE ADD COLUMN (SQLite doesn't support it)
    sql = re.sub(r'ALTER TABLE (\w+) ADD COLUMN IF NOT EXISTS', r'ALTER TABLE \1 ADD COLUMN', sql)
    return sql

