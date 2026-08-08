from __future__ import annotations

import asyncio
import types

from src.api.flyer import consumer_flyer
from src.config import get_settings
from src.db.connection import close_database, connect_database, initialize_database
from src.services.catalog_service import ProductInput, create_product


class _FakeRequest:
    """Minimal request shim exposing app.state.database + app.state.settings."""

    def __init__(self, database, settings) -> None:
        self.app = types.SimpleNamespace(
            state=types.SimpleNamespace(database=database, settings=settings)
        )


def test_consumer_flyer_renders_from_db_no_hardcoding(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOCAL_SQLITE_PATH", str(tmp_path / "flyer.db"))
    monkeypatch.setenv("ADMIN_PHONE", "+27820000000")
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
                    name="Rose Oud",
                    price="85.00",
                    image_url="https://example.com/rose-oud.jpg",
                    thumbnail_url="https://example.com/rose-oud-thumb.jpg",
                    gender="women",
                    scent_family="oriental",
                    keywords=["rose", "oud"],
                ),
            )
            await create_product(
                database,
                ProductInput(
                    product_number=2,
                    name="Sauvage",
                    price="95.00",
                    image_url=None,
                    gender="men",
                    keywords=["sauvage"],
                ),
            )

            response = await consumer_flyer(_FakeRequest(database, settings))
            html = response.body.decode("utf-8")

            # Edition stamp + validity window (auto-computed, not hardcoded)
            assert "Edition" in html
            assert "Valid from" in html and "Valid until" in html

            # Product names + computed retail prices come from the DB (2× wholesale)
            assert "Rose Oud" in html
            assert "R170.00" in html  # 85 × 2
            assert "Sauvage" in html
            assert "R190.00" in html  # 95 × 2

            # Gender grouping rendered
            assert "Women" in html
            assert "Men" in html

            # No hardcoded image for Sauvage (no image) → initial-letter fallback tile
            assert '<div class="no-img">S</div>' in html

            # WhatsApp CTA built from settings (not hardcoded)
            assert "wa.me/27820000000" in html

            # Image present for Rose Oud (thumbnail preferred)
            assert "rose-oud-thumb.jpg" in html
        finally:
            await close_database(database)

    asyncio.run(scenario())
    get_settings.cache_clear()
