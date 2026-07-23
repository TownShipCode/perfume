from __future__ import annotations

import asyncio

from src.config import get_settings
from src.db.connection import close_database, connect_database, fetch_one, initialize_database
from src.services.catalog_service import ProductInput, create_product
from src.services.customer_service import get_customer_by_phone
from src.services.message_templates import build_customer_reply
from src.services.order_flow import handle_image_message, handle_text_message
from src.services.session_service import get_session_by_phone


def test_order_flow_collects_address_and_creates_order(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOCAL_SQLITE_PATH", str(tmp_path / "order-flow.db"))
    monkeypatch.setenv("SHIPPING_FEE", "109.00")
    monkeypatch.setenv("FREE_SHIPPING_THRESHOLD", "2000.00")
    get_settings.cache_clear()

    async def scenario() -> None:
        settings = get_settings()
        database = await connect_database(settings)
        try:
            await initialize_database(database)
            await create_product(
                database,
                ProductInput(
                    product_number=1,
                    name="Red Shoes",
                    price="350.00",
                    image_url="https://example.com/red-shoes.jpg",
                    keywords=["shoe", "shoes", "red shoe"],
                ),
            )

            added = await handle_text_message(
                database,
                {"message_id": "m1", "from": "27820000000", "type": "text", "text": "2 shoes", "profile_name": "Alice"},
            )
            assert added["action"] == "cart_updated"
            assert added["cart"]["total"] == "700.00"

            done = await handle_text_message(
                database,
                {"message_id": "m2", "from": "27820000000", "type": "text", "text": "done", "profile_name": "Alice"},
            )
            assert done["action"] == "address_collection_started"
            assert done["state"] == "address_collection"

            area = await handle_text_message(
                database,
                {"message_id": "m3", "from": "27820000000", "type": "text", "text": "Khayelitsha", "profile_name": "Alice"},
            )
            assert area["action"] == "address_collection_progress"
            assert area["current_step"] == 1

            street = await handle_text_message(
                database,
                {"message_id": "m4", "from": "27820000000", "type": "text", "text": "12 Main Road", "profile_name": "Alice"},
            )
            assert street["action"] == "address_collection_progress"
            assert street["current_step"] == 2

            city = await handle_text_message(
                database,
                {"message_id": "m5", "from": "27820000000", "type": "text", "text": "Cape Town", "profile_name": "Alice"},
            )
            assert city["action"] == "order_created"
            assert city["state"] == "pop_waiting"
            assert city["address"] == "12 Main Road, Khayelitsha, Cape Town"
            assert city["order_number"].startswith("ORD-")

            session = await get_session_by_phone(database, "27820000000")
            assert session is not None
            assert session["state"] == "pop_waiting"
            assert session["cart"] == []

            customer = await get_customer_by_phone(database, "27820000000")
            assert customer is not None
            assert customer["address_verified"] in (1, True)
            assert customer["full_address"] == "12 Main Road, Khayelitsha, Cape Town"

            query = "SELECT order_number, status, total FROM orders WHERE customer_id = ?"
            order = await fetch_one(database, query, customer["id"])
            assert order is not None
            assert order["status"] == "pending"
        finally:
            await close_database(database)

    asyncio.run(scenario())
    get_settings.cache_clear()


def test_order_flow_marks_pop_received_and_confirms_session(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOCAL_SQLITE_PATH", str(tmp_path / "pop-flow.db"))
    monkeypatch.setenv("SHIPPING_FEE", "109.00")
    monkeypatch.setenv("FREE_SHIPPING_THRESHOLD", "2000.00")
    get_settings.cache_clear()

    async def scenario() -> None:
        settings = get_settings()
        database = await connect_database(settings)
        try:
            await initialize_database(database)
            await create_product(
                database,
                ProductInput(
                    product_number=1,
                    name="Red Shoes",
                    price="350.00",
                    image_url="https://example.com/red-shoes.jpg",
                    keywords=["shoe", "shoes", "red shoe"],
                ),
            )

            for message_id, text in [
                ("m1", "2 shoes"),
                ("m2", "done"),
                ("m3", "Khayelitsha"),
                ("m4", "12 Main Road"),
                ("m5", "Cape Town"),
            ]:
                await handle_text_message(
                    database,
                    {"message_id": message_id, "from": "27820000000", "type": "text", "text": text, "profile_name": "Alice"},
                )

            result = await handle_image_message(
                database,
                {
                    "message_id": "m6",
                    "from": "27820000000",
                    "type": "image",
                    "image_id": "media-123",
                    "image_url": None,
                    "profile_name": "Alice",
                },
            )
            assert result["action"] == "pop_received"
            assert result["state"] == "confirmed"
            assert result["media_reference"] == "media-123"

            session = await get_session_by_phone(database, "27820000000")
            assert session is not None
            assert session["state"] == "confirmed"

            customer = await get_customer_by_phone(database, "27820000000")
            assert customer is not None
            order = await fetch_one(database, "SELECT status, pop_image_url FROM orders WHERE customer_id = ?", customer["id"])
            assert order is not None
            assert order["status"] == "pop_received"
            assert order["pop_image_url"] == "media-123"
        finally:
            await close_database(database)

    asyncio.run(scenario())
    get_settings.cache_clear()


def test_order_flow_returns_catalogue_for_menu_command(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOCAL_SQLITE_PATH", str(tmp_path / "catalogue-flow.db"))
    get_settings.cache_clear()

    async def scenario() -> None:
        settings = get_settings()
        database = await connect_database(settings)
        try:
            await initialize_database(database)
            await create_product(
                database,
                ProductInput(
                    product_number=1,
                    name="Red Shoes",
                    price="350.00",
                    image_url="https://example.com/red-shoes.jpg",
                    keywords=["shoe", "shoes", "red shoe"],
                ),
            )
            await create_product(
                database,
                ProductInput(
                    product_number=2,
                    name="Blue Hat",
                    price="120.00",
                    image_url="https://example.com/blue-hat.jpg",
                    keywords=["hat", "blue hat"],
                ),
            )

            result = await handle_text_message(
                database,
                {"message_id": "m1", "from": "27820000000", "type": "text", "text": "menu", "profile_name": "Alice"},
            )
            assert result["action"] == "catalogue"
            assert "1. Red Shoes - R350" in result["catalogue"]
            assert "2. Blue Hat - R120" in result["catalogue"]

            reply = await build_customer_reply(database, result)
            assert reply is not None
            assert "Available products:" in reply["text"]
            assert "Reply with something like: 2 shoes" in reply["text"]

            session = await get_session_by_phone(database, "27820000000")
            assert session is not None
            assert session["state"] == "idle"
        finally:
            await close_database(database)

    asyncio.run(scenario())
    get_settings.cache_clear()


def test_order_flow_uses_configured_catalogue_commands(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOCAL_SQLITE_PATH", str(tmp_path / "catalogue-command-config.db"))
    monkeypatch.setenv("WHATSAPP_CATALOG_COMMANDS", "shop,list")
    get_settings.cache_clear()

    async def scenario() -> None:
        settings = get_settings()
        database = await connect_database(settings)
        try:
            await initialize_database(database)
            await create_product(
                database,
                ProductInput(
                    product_number=1,
                    name="Red Shoes",
                    price="350.00",
                    image_url="https://example.com/red-shoes.jpg",
                    keywords=["shoe", "shoes", "red shoe"],
                ),
            )

            configured = await handle_text_message(
                database,
                {"message_id": "m1", "from": "27820000000", "type": "text", "text": "shop", "profile_name": "Alice"},
            )
            assert configured["action"] == "catalogue"

            default_menu = await handle_text_message(
                database,
                {"message_id": "m2", "from": "27820000000", "type": "text", "text": "menu", "profile_name": "Alice"},
            )
            assert default_menu["action"] == "unmatched"
        finally:
            await close_database(database)

    asyncio.run(scenario())
    get_settings.cache_clear()


def test_order_flow_returns_welcome_catalogue_for_greeting(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOCAL_SQLITE_PATH", str(tmp_path / "greeting-flow.db"))
    get_settings.cache_clear()

    async def scenario() -> None:
        settings = get_settings()
        database = await connect_database(settings)
        try:
            await initialize_database(database)
            await create_product(
                database,
                ProductInput(
                    product_number=1,
                    name="Red Shoes",
                    price="350.00",
                    image_url="https://example.com/red-shoes.jpg",
                    keywords=["shoe", "shoes", "red shoe"],
                ),
            )

            result = await handle_text_message(
                database,
                {"message_id": "m1", "from": "27820000000", "type": "text", "text": "hi", "profile_name": "Alice"},
            )
            assert result["action"] == "welcome_catalogue"
            assert "1. Red Shoes - R350" in result["catalogue"]
            assert result["customer_name"] == "Alice"

            reply = await build_customer_reply(database, result)
            assert reply is not None
            assert "Hi Alice!" in reply["text"]
            assert "Here is our catalogue:" in reply["text"]
        finally:
            await close_database(database)

    asyncio.run(scenario())
    get_settings.cache_clear()


def test_order_flow_calculates_shipping(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOCAL_SQLITE_PATH", str(tmp_path / "shipping.db"))
    monkeypatch.setenv("SHIPPING_FEE", "109.00")
    monkeypatch.setenv("FREE_SHIPPING_THRESHOLD", "2000.00")
    get_settings.cache_clear()

    async def scenario() -> None:
        settings = get_settings()
        database = await connect_database(settings)
        try:
            await initialize_database(database)
            await create_product(
                database,
                ProductInput(
                    product_number=1, name="Red Shoes", price="350.00",
                    image_url="https://example.com/red-shoes.jpg",
                    keywords=["shoe", "shoes", "red shoe"],
                ),
            )
            for message_id, text in [("m1", "2 shoes"), ("m2", "done"), ("m3", "Khayelitsha"), ("m4", "12 Main Road"), ("m5", "Cape Town")]:
                await handle_text_message(database, {"message_id": message_id, "from": "27820000001", "type": "text", "text": text, "profile_name": "Bob"})
            order = await fetch_one(database, "SELECT total, shipping_fee FROM orders WHERE customer_id = (SELECT id FROM customers WHERE phone_number = ?)", "27820000001")
            assert order is not None
            assert float(order["total"]) == 809.00
            assert float(order["shipping_fee"]) == 109.00
        finally:
            await close_database(database)

    asyncio.run(scenario())
    get_settings.cache_clear()


def test_order_flow_waives_shipping_above_threshold(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOCAL_SQLITE_PATH", str(tmp_path / "shipping-free.db"))
    monkeypatch.setenv("SHIPPING_FEE", "109.00")
    monkeypatch.setenv("FREE_SHIPPING_THRESHOLD", "500.00")
    get_settings.cache_clear()

    async def scenario() -> None:
        settings = get_settings()
        database = await connect_database(settings)
        try:
            await initialize_database(database)
            await create_product(
                database,
                ProductInput(
                    product_number=1, name="Red Shoes", price="350.00",
                    image_url="https://example.com/red-shoes.jpg",
                    keywords=["shoe", "shoes", "red shoe"],
                ),
            )
            for message_id, text in [("m1", "2 shoes"), ("m2", "done"), ("m3", "Khayelitsha"), ("m4", "12 Main Road"), ("m5", "Cape Town")]:
                await handle_text_message(database, {"message_id": message_id, "from": "27820000002", "type": "text", "text": text, "profile_name": "Carol"})
            order = await fetch_one(database, "SELECT total, shipping_fee FROM orders WHERE customer_id = (SELECT id FROM customers WHERE phone_number = ?)", "27820000002")
            assert order is not None
            assert float(order["total"]) == 700.00
            assert float(order["shipping_fee"]) == 0
        finally:
            await close_database(database)

    asyncio.run(scenario())
    get_settings.cache_clear()


def test_order_flow_cancel_clears_cart_and_session(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOCAL_SQLITE_PATH", str(tmp_path / "cancel.db"))
    monkeypatch.setenv("SHIPPING_FEE", "109.00")
    monkeypatch.setenv("FREE_SHIPPING_THRESHOLD", "2000.00")
    get_settings.cache_clear()

    async def scenario() -> None:
        database = await connect_database(get_settings())
        try:
            await initialize_database(database)
            await create_product(
                database,
                ProductInput(product_number=1, name="Red Shoes", price="350.00", image_url="https://example.com/red-shoes.jpg", keywords=["shoe"]),
            )
            await handle_text_message(database, {"message_id": "m1", "from": "27820000010", "type": "text", "text": "2 shoes", "profile_name": "Dave"})
            result = await handle_text_message(database, {"message_id": "m2", "from": "27820000010", "type": "text", "text": "cancel", "profile_name": "Dave"})
            assert result["action"] == "order_cancelled"
            assert result["state"] == "idle"
            session = await get_session_by_phone(database, "27820000010")
            assert session is not None
            assert session["state"] == "idle"
            assert session["cart"] == []
        finally:
            await close_database(database)

    asyncio.run(scenario())
    get_settings.cache_clear()