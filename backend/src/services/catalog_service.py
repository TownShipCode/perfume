from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from src.db.connection import Database, execute, fetch_all, fetch_one


class ProductInput(BaseModel):
    product_number: int = Field(gt=0)
    name: str
    price: Decimal = Field(ge=0)
    bio_med_margin: Decimal = Field(default=Decimal("0"), ge=0)
    image_url: str | None = None
    description: str | None = None
    is_active: bool = True
    keywords: list[str] = Field(default_factory=list)


class ProductUpdateInput(BaseModel):
    product_number: int = Field(gt=0)
    name: str
    price: Decimal = Field(ge=0)
    bio_med_margin: Decimal = Field(default=Decimal("0"), ge=0)
    image_url: str | None = None
    description: str | None = None
    is_active: bool = True
    keywords: list[str] = Field(default_factory=list)


async def list_active_products(database: Database) -> list[dict]:
    mode = database.mode
    where_clause = "WHERE is_active = TRUE" if mode == "postgres" else "WHERE is_active = 1"
    rows = await fetch_all(
        database,
        f"""
        SELECT id, product_number, name, price, bio_med_margin, image_url, description, is_active, created_at, updated_at
        FROM products
        {where_clause}
        ORDER BY product_number
        """,
    )
    return await _attach_keywords(database, rows)


async def build_catalog_lines(database: Database) -> list[str]:
    products = await list_active_products(database)
    lines: list[str] = []
    for product in products:
        num = product["product_number"]
        name = product["name"]
        price = product["price"]
        desc = (product.get("description") or "").strip()

        lines.append(f"*{num}.* {name}")
        if desc:
            short_desc = desc[:80] + "…" if len(desc) > 80 else desc
            lines.append(f"    _{short_desc}_")
        lines.append(f"    💰 R{price}")
    return lines


async def list_all_products(database: Database) -> list[dict]:
    rows = await fetch_all(
        database,
        """
        SELECT id, product_number, name, price, bio_med_margin, image_url, description, is_active, created_at, updated_at
        FROM products
        ORDER BY product_number
        """,
    )
    return await _attach_keywords(database, rows)


async def _attach_keywords(database: Database, products: list[dict]) -> list[dict]:
    if not products:
        return products
    product_ids = [p["id"] for p in products]
    if database.mode == "postgres":
        kw_rows = await fetch_all(
            database,
            "SELECT product_id, keyword FROM product_keywords WHERE product_id = ANY($1) ORDER BY product_id, keyword",
            product_ids,
        )
    else:
        placeholders = ",".join("?" for _ in product_ids)
        kw_rows = await fetch_all(
            database,
            f"SELECT product_id, keyword FROM product_keywords WHERE product_id IN ({placeholders}) ORDER BY product_id, keyword",
            *product_ids,
        )
    kw_map: dict[int, list[str]] = {pid: [] for pid in product_ids}
    for row in kw_rows:
        kw_map[row["product_id"]].append(row["keyword"])
    for product in products:
        product["keywords"] = kw_map.get(product["id"], [])
    return products


async def get_keyword_map(database: Database) -> dict[str, dict[str, Any]]:
    mode = database.mode
    where_clause = "WHERE p.is_active = TRUE" if mode == "postgres" else "WHERE p.is_active = 1"
    rows = await fetch_all(
        database,
        f"""
        SELECT pk.keyword, p.id AS product_id, p.product_number, p.name, p.price, p.bio_med_margin, p.image_url, p.description, p.is_active
        FROM product_keywords pk
        JOIN products p ON p.id = pk.product_id
        {where_clause}
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
            "description": row["description"],
            "is_active": row["is_active"],
        }
        for row in rows
    }


async def create_product(database: Database, payload: ProductInput) -> dict[str, Any]:
    normalized_keywords = _normalize_keywords(payload.keywords)

    if database.mode == "postgres":
        row = await fetch_one(
            database,
            """
            INSERT INTO products (product_number, name, price, bio_med_margin, image_url, description, is_active)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id, product_number, name, price, bio_med_margin, image_url, description, is_active, created_at, updated_at
            """,
            payload.product_number,
            payload.name,
            payload.price,
            payload.bio_med_margin,
            payload.image_url,
            payload.description,
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
        INSERT INTO products (product_number, name, price, bio_med_margin, image_url, description, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        payload.product_number,
        payload.name,
        str(payload.price),
        str(payload.bio_med_margin),
        payload.image_url,
        payload.description,
        1 if payload.is_active else 0,
    )
    row = await fetch_one(
        database,
        """
        SELECT id, product_number, name, price, bio_med_margin, image_url, is_active, created_at, updated_at
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


async def get_product_by_number(database: Database, product_number: int) -> dict | None:
    if database.mode == "postgres":
        return await fetch_one(
            database,
            "SELECT id, product_number, name, price, bio_med_margin, image_url, description, is_active FROM products WHERE product_number = $1 AND is_active = TRUE",
            product_number,
        )
    return await fetch_one(
        database,
        "SELECT id, product_number, name, price, bio_med_margin, image_url, description, is_active FROM products WHERE product_number = ? AND is_active = 1",
        product_number,
    )


async def get_product_by_id(database: Database, product_id: int) -> dict | None:
    if database.mode == "postgres":
        return await fetch_one(
            database,
            """
            SELECT id, product_number, name, price, bio_med_margin, image_url, description, is_active, created_at, updated_at
            FROM products
            WHERE id = $1
            """,
            product_id,
        )

    return await fetch_one(
        database,
        """
        SELECT id, product_number, name, price, bio_med_margin, image_url, description, is_active, created_at, updated_at
        FROM products
        WHERE id = ?
        """,
        product_id,
    )


async def get_products_by_ids(database: Database, product_ids: list[int]) -> dict[int, dict]:
    unique_ids = sorted({product_id for product_id in product_ids if product_id > 0})
    if not unique_ids:
        return {}

    if database.mode == "postgres":
        placeholders = ", ".join(f"${index}" for index in range(1, len(unique_ids) + 1))
        rows = await fetch_all(
            database,
            f"""
            SELECT id, product_number, name, price, bio_med_margin, image_url, description, is_active, created_at, updated_at
            FROM products
            WHERE id IN ({placeholders})
            ORDER BY product_number
            """,
            *unique_ids,
        )
    else:
        placeholders = ", ".join("?" for _ in unique_ids)
        rows = await fetch_all(
            database,
            f"""
            SELECT id, product_number, name, price, bio_med_margin, image_url, description, is_active, created_at, updated_at
            FROM products
            WHERE id IN ({placeholders})
            ORDER BY product_number
            """,
            *unique_ids,
        )

    return {row["id"]: row for row in rows}


async def update_product(database: Database, product_id: int, payload: ProductUpdateInput) -> dict[str, Any] | None:
    existing = await get_product_by_id(database, product_id)
    if existing is None:
        return None

    normalized_keywords = _normalize_keywords(payload.keywords)

    if database.mode == "postgres":
        await execute(
            database,
            """
            UPDATE products
            SET product_number = $1, name = $2, price = $3, bio_med_margin = $4, image_url = $5, description = $6, is_active = $7, updated_at = NOW()
            WHERE id = $8
            """,
            payload.product_number,
            payload.name,
            payload.price,
            payload.bio_med_margin,
            payload.image_url,
            payload.description,
            payload.is_active,
            product_id,
        )
        await execute(database, "DELETE FROM product_keywords WHERE product_id = $1", product_id)
        for keyword in normalized_keywords:
            await execute(
                database,
                "INSERT INTO product_keywords (product_id, keyword) VALUES ($1, $2) ON CONFLICT (keyword) DO UPDATE SET product_id = EXCLUDED.product_id",
                product_id,
                keyword,
            )
    else:
        await execute(
            database,
            """
            UPDATE products
            SET product_number = ?, name = ?, price = ?, bio_med_margin = ?, image_url = ?, description = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            payload.product_number,
            payload.name,
            str(payload.price),
            str(payload.bio_med_margin),
            payload.image_url,
            payload.description,
            1 if payload.is_active else 0,
            product_id,
        )
        await execute(database, "DELETE FROM product_keywords WHERE product_id = ?", product_id)
        for keyword in normalized_keywords:
            await execute(
                database,
                "INSERT OR REPLACE INTO product_keywords (id, product_id, keyword) VALUES ((SELECT id FROM product_keywords WHERE keyword = ?), ?, ?)",
                keyword,
                product_id,
                keyword,
            )

    return await get_product_by_id(database, product_id)


async def delete_product(database: Database, product_id: int) -> bool:
    existing = await get_product_by_id(database, product_id)
    if existing is None:
        return False

    if database.mode == "postgres":
        await execute(database, "DELETE FROM products WHERE id = $1", product_id)
    else:
        await execute(database, "DELETE FROM products WHERE id = ?", product_id)
    return True


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
