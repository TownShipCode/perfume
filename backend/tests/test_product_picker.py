from __future__ import annotations

import asyncio

from src.config import get_settings
from src.db.connection import close_database, connect_database, initialize_database
from src.services.catalog_service import ProductInput, create_product
from src.services.message_templates import build_customer_reply
from src.services.order_flow import handle_text_message
from src.services.whatsapp_buttons import BUTTON_TO_CMD


async def _seed_ambiguous_products(database) -> None:
    """Two products that share an ambiguous short name (SCANDAL men/women)."""
    await create_product(
        database,
        ProductInput(
            product_number=8,
            name="SCANDAL",
            price="30.00",
            gender="men",
            scent_family="woody",
            image_url="https://example.com/scandal-m.svg",
            keywords=["scandal"],
        ),
    )
    await create_product(
        database,
        ProductInput(
            product_number=16,
            name="SCANDAL",
            price="30.00",
            gender="women",
            scent_family="floral",
            image_url="https://example.com/scandal-w.svg",
            keywords=["scandal ladies", "scandal women"],
        ),
    )


def test_ambiguous_partial_name_returns_product_picker(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOCAL_SQLITE_PATH", str(tmp_path / "picker.db"))
    get_settings.cache_clear()

    async def scenario() -> None:
        settings = get_settings()
        database = await connect_database(settings)
        try:
            await initialize_database(database)
            await _seed_ambiguous_products(database)

            # A partial name matching BOTH SCANDAL products must NOT guess.
            result = await handle_text_message(
                database,
                {"message_id": "m1", "from": "27820000000", "type": "text", "text": "scandal", "profile_name": "Alice"},
            )
            assert result["action"] == "product_picker"
            numbers = {c["product_number"] for c in result["candidates"]}
            assert numbers == {8, 16}

            # The reply is a WhatsApp LIST message (tap-to-choose).
            reply = await build_customer_reply(database, result)
            assert reply is not None
            assert reply["type"] == "interactive"
            interactive = reply["payload"]["interactive"]
            assert interactive["type"] == "list"
            rows = interactive["action"]["sections"][0]["rows"]
            assert {r["id"] for r in rows} == {"pick_8", "pick_16"}
            assert "SCANDAL" in rows[0]["title"]

            # Row ids are registered so a tap routes to the product number.
            assert BUTTON_TO_CMD["pick_8"] == "8"
            assert BUTTON_TO_CMD["pick_16"] == "16"
        finally:
            await close_database(database)

    asyncio.run(scenario())
    get_settings.cache_clear()


def test_quantity_prefixed_ambiguous_name_returns_product_picker(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOCAL_SQLITE_PATH", str(tmp_path / "picker-qty.db"))
    get_settings.cache_clear()

    async def scenario() -> None:
        settings = get_settings()
        database = await connect_database(settings)
        try:
            await initialize_database(database)
            await _seed_ambiguous_products(database)

            result = await handle_text_message(
                database,
                {"message_id": "m1", "from": "27820000000", "type": "text", "text": "3 scandal", "profile_name": "Alice"},
            )
            assert result["action"] == "product_picker"
            numbers = {c["product_number"] for c in result["candidates"]}
            assert numbers == {8, 16}
        finally:
            await close_database(database)

    asyncio.run(scenario())
    get_settings.cache_clear()


def test_unique_partial_name_auto_resolves_to_quantity(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOCAL_SQLITE_PATH", str(tmp_path / "picker-unique.db"))
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

            # Only one product matches "shoes" → behaves like typing product 1.
            result = await handle_text_message(
                database,
                {"message_id": "m1", "from": "27820000000", "type": "text", "text": "shoes", "profile_name": "Alice"},
            )
            assert result["action"] == "quantity_selection"
            assert result["product_name"] == "Red Shoes"
        finally:
            await close_database(database)

    asyncio.run(scenario())
    get_settings.cache_clear()


def test_chat_word_does_not_auto_resolve_to_product(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOCAL_SQLITE_PATH", str(tmp_path / "picker-chat.db"))
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
                    name="Good Girl",
                    price="30.00",
                    keywords=["good girl"],
                ),
            )

            # "good" is chat filler — must NOT hijack into a quantity prompt.
            result = await handle_text_message(
                database,
                {"message_id": "m1", "from": "27820000000", "type": "text", "text": "good", "profile_name": "Alice"},
            )
            assert result["action"] in ("interactive_welcome", "unmatched")
        finally:
            await close_database(database)

    asyncio.run(scenario())
    get_settings.cache_clear()


def test_picker_row_tap_selects_the_exact_product(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOCAL_SQLITE_PATH", str(tmp_path / "picker-tap.db"))
    get_settings.cache_clear()

    async def scenario() -> None:
        settings = get_settings()
        database = await connect_database(settings)
        try:
            await initialize_database(database)
            await _seed_ambiguous_products(database)

            # Emulate the webhook mapping a list_reply row id → product number:
            # BUTTON_TO_CMD is populated when the picker is rendered (test above),
            # so a tap on row "pick_8" arrives as text "8".
            from src.services.whatsapp_buttons import BUTTON_TO_CMD
            tapped = BUTTON_TO_CMD.get("pick_8", "8")
            result = await handle_text_message(
                database,
                {"message_id": "m2", "from": "27820000000", "type": "text", "text": tapped, "profile_name": "Alice"},
            )
            # Tapping the men's SCANDAL row must resolve to product #8 (men), not #16.
            assert result["action"] == "quantity_selection"
            assert result["product_name"] == "SCANDAL"
            assert "scandal-m.svg" in (result.get("image_url") or "")
        finally:
            await close_database(database)

    asyncio.run(scenario())
    get_settings.cache_clear()
