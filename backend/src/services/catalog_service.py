from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field

from src.db.connection import Database, execute, fetch_all, fetch_one


class ProductInput(BaseModel):
    product_number: int = Field(gt=0)
    name: str
    price: Decimal = Field(ge=0)
    image_url: str | None = None
    is_active: bool = True
    keywords: list[str] = Field(default_factory=list)


async def list_active_products(database: Database) -> list[dict]:
    return await fetch_all(
        database,
        """
        SELECT id, product_number, name, price, image_url, is_active, created_at, updated_at
        FROM products
        WHERE is_active = 1 OR is_active = TRUE
        ORDER BY product_number
        """,
    )


async def list_all_products(database: Database) -> list[dict]:
    return await fetch_all(
        database,
        """
        SELECT id, product_number, name, price, image_url, is_active, created_at, updated_at
        FROM products
        ORDER BY product_number
        """,
    )


async def get_keyword_map(database: Database) -> dict[str, dict]:
    rows = await fetch_all(
        database,
        """
        SELECT pk.keyword, p.id AS product_id, p.product_number, p.name, p.price, p.image_url, p.is_active
        FROM product_keywords pk
        JOIN products p ON p.id = pk.product_id
        WHERE p.is_active = 1 OR p.is_active = TRUE
        ORDER BY LENGTH(pk.keyword) DESC, pk.keyword ASC
        """,
    )
    return {
        row["keyword"].strip().lower(): {
            "product_id": row["product_id"],
            "product_number": row["product_number"],
            "name": row["name"],
            "price": row["price"],
            "image_url": row["image_url"],
            "is_active": row["is_active"],
        }
        for row in rows
    }


async def create_product(database: Database, payload: ProductInput) -> dict:
    normalized_keywords = _normalize_keywords(payload.keywords)

    if database.mode == "postgres":
        row = await fetch_one(
            database,
            """
            INSERT INTO products (product_number, name, price, image_url, is_active)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, product_number, name, price, image_url, is_active, created_at, updated_at
            """,
            payload.product_number,
            payload.name,
            payload.price,
            payload.image_url,
            payload.is_active,
        )
        assert row is not None
        for keyword in normalized_keywords:
            await execute(
                database,
                "INSERT INTO product_keywords (product_id, keyword) VALUES ($1, $2) ON CONFLICT (keyword) DO NOTHING",
                row["id"],
                keyword,
            )
        return row

    await execute(
        database,
        """
        INSERT INTO products (product_number, name, price, image_url, is_active)
        VALUES (?, ?, ?, ?, ?)
        """,
        payload.product_number,
        payload.name,
        str(payload.price),
        payload.image_url,
        1 if payload.is_active else 0,
    )
    row = await fetch_one(
        database,
        """
        SELECT id, product_number, name, price, image_url, is_active, created_at, updated_at
        FROM products
        WHERE product_number = ?
        """,
        payload.product_number,
    )
    assert row is not None
    for keyword in normalized_keywords:
        await execute(
            database,
            "INSERT OR IGNORE INTO product_keywords (product_id, keyword) VALUES (?, ?)",
            row["id"],
            keyword,
        )
    return row


def _normalize_keywords(keywords: list[str]) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for keyword in keywords:
        value = keyword.strip().lower()
        if not value or value in seen:
            continue
        seen.add(value)
        normalized.append(value)
    return normalized
