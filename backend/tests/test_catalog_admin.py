from __future__ import annotations

import asyncio

from src.config import get_settings
from src.db.connection import close_database, connect_database, initialize_database
from src.services.catalog_service import ProductInput, ProductUpdateInput, create_product, delete_product, get_keyword_map, update_product
from src.services.customer_service import get_or_create_customer, update_customer_address


def test_product_update_delete_and_customer_address_update(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOCAL_SQLITE_PATH", str(tmp_path / "catalog-admin.db"))
    get_settings.cache_clear()

    async def scenario() -> None:
        settings = get_settings()
        database = await connect_database(settings)
        try:
            await initialize_database(database)
            product = await create_product(
                database,
                ProductInput(
                    product_number=1,
                    name="Red Shoes",
                    price="350.00",
                    image_url="https://example.com/red-shoes.jpg",
                    keywords=["shoe", "shoes"],
                ),
            )
            updated = await update_product(
                database,
                product["id"],
                ProductUpdateInput(
                    product_number=9,
                    name="Green Shoes",
                    price="390.00",
                    image_url="https://example.com/green-shoes.jpg",
                    is_active=False,
                    keywords=["green shoe", "sneaker"],
                ),
            )
            assert updated is not None
            assert updated["product_number"] == 9
            assert updated["name"] == "Green Shoes"

            keyword_map = await get_keyword_map(database)
            assert "green shoe" not in keyword_map

            deleted = await delete_product(database, product["id"])
            assert deleted is True

            customer = await get_or_create_customer(database, "27820000000", "Alice")
            address = await update_customer_address(
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
