from __future__ import annotations

import asyncio

from src.config import get_settings
from src.db.connection import close_database, connect_database, initialize_database
from src.services.catalog_service import (
    ProductInput,
    build_recent_catalogue_text,
    create_product,
    invalidate_catalogue_cache,
)


def test_recent_catalogue_returns_products_in_chat(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOCAL_SQLITE_PATH", str(tmp_path / "recent-catalogue.db"))
    get_settings.cache_clear()
    invalidate_catalogue_cache()

    async def scenario() -> None:
        settings = get_settings()
        database = await connect_database(settings)
        try:
            await initialize_database(database)
            await create_product(
                database,
                ProductInput(product_number=1, name="RED SHOES", price="350.00", keywords=["shoe"]),
            )
            await create_product(
                database,
                ProductInput(product_number=2, name="BLACK OPIUM", price="30.00", keywords=["opium"]),
            )

            text = await build_recent_catalogue_text(database)
            assert "RED SHOES" in text
            assert "BLACK OPIUM" in text
            assert "1" in text  # product number present for in-chat ordering
        finally:
            await close_database(database)

    asyncio.run(scenario())
    get_settings.cache_clear()
    invalidate_catalogue_cache()


def test_recent_catalogue_invalidates_on_product_create(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOCAL_SQLITE_PATH", str(tmp_path / "recent-catalogue-invalidate.db"))
    get_settings.cache_clear()
    invalidate_catalogue_cache()

    async def scenario() -> None:
        settings = get_settings()
        database = await connect_database(settings)
        try:
            await initialize_database(database)
            await create_product(
                database,
                ProductInput(product_number=1, name="RED SHOES", price="350.00", keywords=["shoe"]),
            )

            # First render caches the one-product list.
            first = await build_recent_catalogue_text(database)
            assert "RED SHOES" in first
            assert "BLUE HAT" not in first

            # Add a product → create_product invalidates the cache → next render includes it.
            await create_product(
                database,
                ProductInput(product_number=2, name="BLUE HAT", price="120.00", keywords=["hat"]),
            )
            second = await build_recent_catalogue_text(database)
            assert "RED SHOES" in second
            assert "BLUE HAT" in second
        finally:
            await close_database(database)

    asyncio.run(scenario())
    get_settings.cache_clear()
    invalidate_catalogue_cache()
