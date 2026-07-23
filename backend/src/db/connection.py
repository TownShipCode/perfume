from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.config import Settings, get_settings


MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


@dataclass
class Database:
    pool: object


async def connect_database(settings: Settings | None = None) -> Database:
    settings = settings or get_settings()
    dsn = settings.database_url
    if not dsn or not dsn.startswith("postgres"):
        raise RuntimeError("DATABASE_URL must be a valid PostgreSQL connection string")
    import asyncpg
    pool = await asyncpg.create_pool(dsn=dsn, min_size=1, max_size=5)
    return Database(pool=pool)


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
    assert database.pool is not None
    async with database.pool.acquire() as connection:
        await connection.execute(
            "INSERT INTO _schema_migrations (version, name) VALUES ($1, $2)", version, name,
        )


async def execute_script(database: Database, sql: str) -> None:
    assert database.pool is not None
    async with database.pool.acquire() as connection:
        for statement in sql.split(";"):
            statement = statement.strip()
            if not statement:
                continue
            try:
                await connection.execute(statement)
            except Exception as error:
                if versionless_duplicate_column(error):
                    continue
                raise


async def fetch_all(database: Database, query: str, *params: object) -> list[dict]:
    assert database.pool is not None
    async with database.pool.acquire() as connection:
        rows = await connection.fetch(query, *params)
        return [dict(row) for row in rows]


async def fetch_one(database: Database, query: str, *params: object) -> dict | None:
    assert database.pool is not None
    async with database.pool.acquire() as connection:
        row = await connection.fetchrow(query, *params)
        return dict(row) if row else None


async def execute(database: Database, query: str, *params: object) -> None:
    assert database.pool is not None
    async with database.pool.acquire() as connection:
        await connection.execute(query, *params)


def versionless_duplicate_column(error: Exception) -> bool:
    text = str(error).lower()
    return "duplicate_column" in text or "already exists" in text

