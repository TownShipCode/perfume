from __future__ import annotations

import asyncio
from decimal import Decimal

from src.config import get_settings
from src.db.connection import close_database, connect_database, initialize_database
from src.models.cart import CartItem
from src.services.cart_service import add_item_to_cart, build_cart
from src.services.customer_service import get_or_create_customer, save_customer_address
from src.services.session_service import get_or_create_session, save_session_state


def test_cart_service_merges_duplicates_and_totals() -> None:
    cart = []
    cart = add_item_to_cart(cart, product_id=1, quantity=2)
    cart = add_item_to_cart(cart, product_id=1, quantity=1)
    cart = add_item_to_cart(cart, product_id=2, quantity=1)
    built = build_cart(cart, {1: Decimal("350.00"), 2: Decimal("120.00")})
    assert len(built.items) == 2
    assert built.items[0].quantity == 3
    assert built.total == Decimal("1170.00")


def test_customer_and_session_helpers_round_trip(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOCAL_SQLITE_PATH", str(tmp_path / "persistence-test.db"))
    get_settings.cache_clear()

    async def scenario() -> None:
        settings = get_settings()
        database = await connect_database(settings)
        try:
            await initialize_database(database)
            customer = await get_or_create_customer(database, "27820000000", "Alice")
            assert customer["phone_number"] == "27820000000"

            updated_customer = await save_customer_address(
                database,
                "27820000000",
                area="Khayelitsha",
                street="12 Main Road",
                city="Cape Town",
            )
            assert updated_customer["full_address"] == "12 Main Road, Khayelitsha, Cape Town"

            session = await get_or_create_session(database, "27820000000")
            assert session["state"] == "idle"

            updated_session = await save_session_state(
                database,
                "27820000000",
                state="ordering",
                cart=[CartItem(product_id=1, quantity=2)],
                current_step=1,
                temp_address={"area": "Khayelitsha"},
            )
            assert updated_session["state"] == "ordering"
            assert updated_session["cart"][0]["quantity"] == 2
            assert updated_session["temp_address"]["area"] == "Khayelitsha"
        finally:
            await close_database(database)

    asyncio.run(scenario())
    get_settings.cache_clear()
