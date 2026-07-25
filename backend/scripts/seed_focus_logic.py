"""Seed Focus Logic product locally or on Railway.

Usage:
    python backend/scripts/seed_focus_logic.py
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import get_settings
from src.db.connection import close_database, connect_database, initialize_database
from src.services.catalog_service import ProductInput, create_product


FOCUS_LOGIC_IMAGE = os.getenv(
    "FOCUS_LOGIC_IMAGE_URL",
    "https://REPLACE-WITH-VERCEL-BLOB-URL",
)


async def seed() -> None:
    settings = get_settings()
    database = await connect_database(settings)
    try:
        await initialize_database(database)
        await create_product(
            database,
            ProductInput(
                product_number=1,
                name="Focus Logic Herbal Blend 1L",
                price="330.00",
                image_url=FOCUS_LOGIC_IMAGE,
                description="Rooibos, Honeybush & Sutherlandia blend. Enriched with grape seed, magnesium, chromium, L-carnitine & B-vitamins. Caffeine-free. 1/4 cup (62.5ml) daily.",
                keywords=[
                    "focus logic", "focus", "logic", "herbal blend",
                    "herbal", "blend", "tonic", "1l", "1 litre",
                    "focus logic 1l",
                ],
            ),
        )
        print("[OK] Focus Logic Herbal Blend 1L seeded")
    finally:
        await close_database(database)


if __name__ == "__main__":
    asyncio.run(seed())
