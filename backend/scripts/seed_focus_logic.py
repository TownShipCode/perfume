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

        products = [
            ProductInput(
                product_number=1,
                name="Focus Logic Herbal Blend 1L",
                price="330.00",
                image_url=FOCUS_LOGIC_IMAGE,
                description="Rooibos, Honeybush & Sutherlandia blend. Enriched with grape seed, magnesium, chromium, L-carnitine & B-vitamins. Caffeine-free. 1/4 cup (62.5ml) daily.",
                keywords=["focus logic", "focus", "logic", "herbal blend", "herbal", "blend", "tonic", "1l", "1 litre", "focus logic 1l"],
            ),
            ProductInput(
                product_number=2,
                name="Immune Booster Syrup 500ml",
                price="180.00",
                image_url=FOCUS_LOGIC_IMAGE,
                description="Elderberry, Echinacea & Vitamin C blend. Supports natural immunity. 2 tablespoons daily. Suitable for all ages.",
                keywords=["immune", "booster", "syrup", "immunity", "elderberry", "echinacea", "500ml", "immune booster", "flu"],
            ),
            ProductInput(
                product_number=3,
                name="Detox Tea Blend 100g",
                price="95.00",
                image_url=FOCUS_LOGIC_IMAGE,
                description="Dandelion, Milk Thistle & Ginger. Supports liver health & natural detox. 1 teaspoon per cup, steep 5 min. 100g loose leaf.",
                keywords=["detox", "tea", "dandelion", "milk thistle", "ginger", "liver", "cleanse", "100g", "detox tea"],
            ),
            ProductInput(
                product_number=4,
                name="Joint & Bone Tonic 1L",
                price="280.00",
                image_url=FOCUS_LOGIC_IMAGE,
                description="Devil's Claw, Turmeric & Glucosamine blend. Supports joint mobility & bone health. 1/4 cup (62.5ml) daily. Caffeine-free.",
                keywords=["joint", "bone", "tonic", "devils claw", "turmeric", "glucosamine", "arthritis", "mobility", "1l", "joint tonic"],
            ),
        ]

        for product in products:
            try:
                await create_product(database, product)
                print(f"[OK] {product.name} seeded")
            except Exception:
                print(f"[SKIP] {product.name} — already exists")

    finally:
        await close_database(database)


if __name__ == "__main__":
    asyncio.run(seed())
