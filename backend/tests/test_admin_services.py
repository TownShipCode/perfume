from __future__ import annotations

import asyncio

from src.config import get_settings
from src.db.connection import close_database, connect_database, initialize_database
from src.services.catalog_service import ProductInput, create_product
from src.services.customer_service import list_customer_orders, list_customers
from src.services.manufacturer_forwarding import forward_order_to_manufacturer
from src.services.order_flow import handle_image_message, handle_text_message
from src.services.order_service import get_order_by_id, list_orders, update_order_status


def test_admin_service_queries_and_status_update(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOCAL_SQLITE_PATH", str(tmp_path / "admin-services.db"))
    monkeypatch.setenv("MANUFACTURER_PHONE", "27829990000")
    monkeypatch.setenv("WHATSAPP_SEND_MODE", "dry_run")
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

            await handle_image_message(
                database,
                {"message_id": "m6", "from": "27820000000", "type": "image", "image_id": "media-123", "image_url": None},
            )

            orders = await list_orders(database)
            assert len(orders) == 1
            assert orders[0]["phone_number"] == "27820000000"
            assert orders[0]["status"] == "pop_received"

            filtered = await list_orders(database, "pop_received")
            assert len(filtered) == 1

            not_forwarded = await list_orders(database, forward_status="not_sent")
            assert len(not_forwarded) == 1
            assert not_forwarded[0]["id"] == orders[0]["id"]

            order = await get_order_by_id(database, orders[0]["id"])
            assert order is not None
            assert order["order_number"].startswith("ORD-")
            assert len(order["items"]) == 1

            forwarded = await forward_order_to_manufacturer(database, order["id"])
            assert forwarded is not None
            assert forwarded["action"] == "forwarded"

            forwarded_only = await list_orders(database, forward_status="dry_run")
            assert len(forwarded_only) == 1
            assert forwarded_only[0]["id"] == order["id"]

            no_longer_not_sent = await list_orders(database, forward_status="not_sent")
            assert len(no_longer_not_sent) == 0

            combined_filter = await list_orders(database, status="pop_received", forward_status="dry_run")
            assert len(combined_filter) == 1
            assert combined_filter[0]["id"] == order["id"]

            updated = await update_order_status(database, order["id"], "confirmed")
            assert updated is not None
            assert updated["status"] == "confirmed"

            confirmed_and_forwarded = await list_orders(database, status="confirmed", forward_status="dry_run")
            assert len(confirmed_and_forwarded) == 1
            assert confirmed_and_forwarded[0]["id"] == order["id"]

            customers = await list_customers(database)
            assert len(customers) == 1
            assert customers[0]["phone_number"] == "27820000000"
            assert customers[0]["order_count"] == 1

            history = await list_customer_orders(database, "27820000000")
            assert len(history) == 1
            assert history[0]["order_number"] == order["order_number"]
        finally:
            await close_database(database)

    asyncio.run(scenario())
    get_settings.cache_clear()
