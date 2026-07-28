from __future__ import annotations

import asyncio

from src.config import get_settings
from src.db.connection import close_database, connect_database, initialize_database
from src.services.catalog_service import ProductInput, create_product
from src.services.manufacturer_forwarding import forward_order_to_manufacturer, get_manufacturer_forward_preview
from src.services.order_flow import handle_image_message, handle_text_message
from src.services import whatsapp_sender


def test_forward_order_to_manufacturer_records_audit_fields(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOCAL_SQLITE_PATH", str(tmp_path / "forwarding.db"))
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
                ("m1b", "add_confirm"),
                ("m2", "done"),
                ("m3", "Alice"),
                ("m4", "Dlamini"),
                ("m5", "Khayelitsha"),
                ("m6", "12 Main Road"),
                ("m7", "Cape Town"),
                ("m8", "7784"),
                ("m9", "Western Cape"),
            ]:
                await handle_text_message(
                    database,
                    {"message_id": message_id, "from": "27820000000", "type": "text", "text": text, "profile_name": "Alice"},
                )
            await handle_image_message(
                database,
                {"message_id": "m10", "from": "27820000000", "type": "image", "image_id": "media-123", "image_url": None},
            )

            preview = await get_manufacturer_forward_preview(database, 1)
            assert preview is not None
            assert preview["recipient"] == "27829990000"
            assert "New Order" in preview["message"]
            assert "2x Red Shoes" in preview["message"]
            assert preview["line_items"] == [{"product_id": 1, "product_name": "Red Shoes", "quantity": 2}]

            result = await forward_order_to_manufacturer(database, 1)
            assert result is not None
            assert result["action"] == "forwarded"
            assert result["recipient"] == "27829990000"
            assert result["delivery"]["status"] == "dry_run"
            assert "New Order" in result["message"]
            assert "2x Red Shoes" in result["message"]
            assert result["order"]["forwarded_to"] == "27829990000"
            assert result["order"]["forward_delivery_status"] == "dry_run"
            assert result["order"]["forwarded_at"] is not None
            assert result["order"]["forward_attempts"] == 1
            assert result["order"]["forward_payload"] is not None
            assert result["order"]["forward_error"] is None

            repeated = await forward_order_to_manufacturer(database, 1)
            assert repeated is not None
            assert repeated["action"] == "forward_skipped"
            assert repeated["reason"] == "already_forwarded"
            assert repeated["recipient"] == "27829990000"

            retried = await forward_order_to_manufacturer(database, 1, force=True)
            assert retried is not None
            assert retried["action"] == "forwarded"
            assert retried["recipient"] == "27829990000"
            assert retried["order"]["forward_attempts"] == 2
        finally:
            await close_database(database)

    asyncio.run(scenario())
    get_settings.cache_clear()
