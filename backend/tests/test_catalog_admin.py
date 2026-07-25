from __future__ import annotations

import asyncio
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from src.config import get_settings
from src.db.connection import Database, close_database, connect_database, initialize_database
from src.services.catalog_service import ProductInput, ProductUpdateInput, create_product, delete_product, get_keyword_map, update_product
from src.services.customer_service import get_or_create_customer, update_customer_address


def test_product_update_delete_and_customer_address_update(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LOCAL_SQLITE_PATH", str(tmp_path / "catalog-admin.db"))
    get_settings.cache_clear()

    async def scenario() -> None:
        settings = get_settings()
        database: Database = await connect_database(settings)
        try:
            await initialize_database(database)
            product: dict[str, Any] = await create_product(
                database,
                ProductInput(
                    product_number=1,
                    name="Red Shoes",
                    price=Decimal("350.00"),
                    image_url="https://example.com/red-shoes.jpg",
                    keywords=["shoe", "shoes"],
                ),
            )
            updated: dict[str, Any] | None = await update_product(
                database,
                product["id"],
                ProductUpdateInput(
                    product_number=9,
                    name="Green Shoes",
                    price=Decimal("390.00"),
                    image_url="https://example.com/green-shoes.jpg",
                    is_active=False,
                    keywords=["green shoe", "sneaker"],
                ),
            )
            assert updated is not None
            assert updated["product_number"] == 9
            assert updated["name"] == "Green Shoes"

            keyword_map: dict[str, dict[str, Any]] = await get_keyword_map(database)
            assert "green shoe" not in keyword_map

            deleted: bool = await delete_product(database, product["id"])
            assert deleted is True

            customer: dict[str, Any] = await get_or_create_customer(database, "27820000000", "Alice")
            address: dict[str, Any] | None = await update_customer_address(
                database,
                customer["phone_number"],
                area="Soweto",
                street="44 Vilakazi Street",
                city="Johannesburg",
            )
            assert address is not None
            assert address["full_address"] == "44 Vilakazi Street, Soweto, Johannesburg"
        finally:
            await close_database(database)

    asyncio.run(scenario())
    get_settings.cache_clear()
