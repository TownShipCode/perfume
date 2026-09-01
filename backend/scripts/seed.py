from __future__ import annotations

import asyncio

from src.config import get_settings
from src.db.connection import connect_database, initialize_database


PRODUCTS = [
    # BUDGET PERFUMES — R30 wholesale (placeholder SVG label images)
    # Men
    {"product_number": 1, "name": "212 VIP", "price": 30.00, "gender": "men", "scent_family": "woody", "top_notes": "Citrus, bergamot", "description": "Inspired by the designer night-out scent.", "image_url": "/static/labels/212-vip.svg"},
    {"product_number": 2, "name": "DESIRE", "price": 30.00, "gender": "men", "scent_family": "woody", "top_notes": "Spices, amber", "description": "Inspired by the designer desire scent.", "image_url": "/static/labels/desire.svg"},
    {"product_number": 3, "name": "INVICTUS", "price": 30.00, "gender": "men", "scent_family": "aquatic", "top_notes": "Grapefruit, sea notes", "description": "Inspired by the designer sporty scent.", "image_url": "/static/labels/invictus.svg"},
    {"product_number": 4, "name": "L'EAU D'ISSEY", "price": 30.00, "gender": "men", "scent_family": "aquatic", "top_notes": "Yuzu, marine notes", "description": "Inspired by the designer fresh aquatic scent.", "image_url": "/static/labels/leau-dissey.svg"},
    {"product_number": 5, "name": "LEGEND", "price": 30.00, "gender": "men", "scent_family": "fresh", "top_notes": "Lavender, mint", "description": "Inspired by the designer bold scent.", "image_url": "/static/labels/legend.svg"},
    {"product_number": 6, "name": "ONE MILLION", "price": 30.00, "gender": "men", "scent_family": "sweet", "top_notes": "Cinnamon, leather", "description": "Inspired by the designer sweet leather scent.", "image_url": "/static/labels/one-million.svg"},
    {"product_number": 7, "name": "ONLY THE BRAVE", "price": 30.00, "gender": "men", "scent_family": "fresh", "top_notes": "Citrus, amber", "description": "Inspired by the designer daring scent.", "image_url": "/static/labels/only-the-brave.svg"},
    {"product_number": 8, "name": "SCANDAL", "price": 30.00, "gender": "men", "scent_family": "woody", "top_notes": "Spices, woods", "description": "Inspired by the designer bold masculine scent.", "image_url": "/static/labels/scandal-m.svg"},
    # Women
    {"product_number": 9, "name": "ARMANI SI", "price": 30.00, "gender": "women", "scent_family": "floral", "top_notes": "Mandarin, vanilla", "description": "Inspired by the designer elegant scent.", "image_url": "/static/labels/armani-si.svg"},
    {"product_number": 10, "name": "BLACK OPIUM", "price": 30.00, "gender": "women", "scent_family": "floral", "top_notes": "Coffee, vanilla", "description": "Inspired by the designer intense scent.", "image_url": "/static/labels/black-opium.svg"},
    {"product_number": 11, "name": "CHANNEL NO 5", "price": 30.00, "gender": "women", "scent_family": "floral", "top_notes": "Aldehydes, jasmine", "description": "Inspired by the designer classic scent.", "image_url": "/static/labels/channel-no-5.svg"},
    {"product_number": 12, "name": "GOOD GIRL", "price": 30.00, "gender": "women", "scent_family": "floral", "top_notes": "Almond, tuberose", "description": "Inspired by the designer chic scent.", "image_url": "/static/labels/good-girl.svg"},
    {"product_number": 13, "name": "GUCCI RUSH", "price": 30.00, "gender": "women", "scent_family": "floral", "top_notes": "Peach, vanilla", "description": "Inspired by the designer vibrant scent.", "image_url": "/static/labels/gucci-rush.svg"},
    {"product_number": 14, "name": "LADY MILLION", "price": 30.00, "gender": "women", "scent_family": "floral", "top_notes": "Orange blossom, honey", "description": "Inspired by the designer sparkling scent.", "image_url": "/static/labels/lady-million.svg"},
    {"product_number": 15, "name": "NARCISO RODRIGUEZ", "price": 30.00, "gender": "women", "scent_family": "floral", "top_notes": "Musk, jasmine", "description": "Inspired by the designer musky scent.", "image_url": "/static/labels/narciso-rodriguez.svg"},
    {"product_number": 16, "name": "SCANDAL", "price": 30.00, "gender": "women", "scent_family": "floral", "top_notes": "Honey, gardenia", "description": "Inspired by the designer bold feminine scent.", "image_url": "/static/labels/scandal-w.svg"},
    # Add-on / bundle SKUs
    {"product_number": 17, "name": "DISCOVERY SET (10ML x 3)", "price": 45.00, "gender": "unisex", "scent_family": "mix", "top_notes": "Three mini samples to explore", "description": "A low-risk way to try three scents before committing. Swap them in store.", "image_url": "/static/labels/discovery-set.svg"},
    {"product_number": 18, "name": "GIFT SET (2 x 30ML BOXED)", "price": 55.00, "gender": "unisex", "scent_family": "mix", "top_notes": "Two 30ml bottles in a gift box", "description": "Two popular 30ml bottles in a ready-to-gift box. Perfect for gifting.", "image_url": "/static/labels/gift-set.svg"},
]

PRODUCT_KEYWORDS = {
    1: ["212", "212 vip", "vip"],
    2: ["desire"],
    3: ["invictus"],
    4: ["issey", "l'eau d'issey", "eau dissey"],
    5: ["legend"],
    6: ["one million", "million"],
    7: ["only the brave", "brave"],
    8: ["scandal"],
    9: ["armani si", "si"],
    10: ["black opium", "opium"],
    11: ["channel no 5", "no 5", "channel 5", "chanel no 5"],
    12: ["good girl"],
    13: ["gucci rush", "rush"],
    14: ["lady million"],
    15: ["narciso rodriguez", "narciso"],
    16: ["scandal ladies", "scandal women"],
    17: ["discovery set", "samples", "mini", "sampler"],
    18: ["gift set", "gift", "boxed", "gift box"],
}

MESSAGE_TEMPLATES = {
    "welcome": "Welcome to {store_name}. Reply with a quantity and product name, for example: 1 FL 1L.",
    "cart_update": "Added {quantity}x {product_name}. Total: {total} {currency}.",
    "address_request": "I need your delivery address. First: what is your area?",
    "address_confirmation": "Address saved: {full_address}. Is this correct?",
    "order_final": "Order {order_number} confirmed. Total: {total} {currency}. Please send your POP image.",
    "pop_received": "POP received. We will confirm your order shortly.",
    "address_request_street": "Thanks. Now send your STREET and HOUSE NUMBER.",
    "address_request_city": "Thanks. Now send your CITY.",
    "checkout_blocked": "Your cart is empty. Add a product first, for example: 1 FL 1L.",
    "unmatched": "I could not match that product. Try something like: 1 FL 1L or 1 focus logic.",
    "awaiting_pop": "Your order is waiting for POP. Please send your POP image.",
    "address_confirmation_pending": "Please reply YES to use your saved address, or NO to enter a new one.",
    "manufacturer_forward": "NEW ORDER {order_number}\nCustomer: {customer_name}\nPhone: {phone_number}\nAddress: {full_address}\nItems:\n{items}\nTotal: {total} {currency}\nPOP: {pop_image_url}",
}


async def main() -> None:
    settings = get_settings()
    database = await connect_database(settings)
    await initialize_database(database)

    if database.mode == "postgres":
        assert database.pool is not None
        async with database.pool.acquire() as connection:
            for product in PRODUCTS:
                await connection.execute(
                    """
                    INSERT INTO products (product_number, name, price, image_url, description, gender, scent_family, top_notes)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (product_number) DO UPDATE
                    SET name = EXCLUDED.name,
                        price = EXCLUDED.price,
                        image_url = EXCLUDED.image_url,
                        description = EXCLUDED.description,
                        gender = EXCLUDED.gender,
                        scent_family = EXCLUDED.scent_family,
                        top_notes = EXCLUDED.top_notes,
                        updated_at = NOW()
                    """,
                    product["product_number"],
                    product["name"],
                    product["price"],
                    product["image_url"],
                    product.get("description"),
                    product.get("gender"),
                    product.get("scent_family"),
                    product.get("top_notes"),
                )

            for product_number, keywords in PRODUCT_KEYWORDS.items():
                product_id = await connection.fetchval(
                    "SELECT id FROM products WHERE product_number = $1",
                    product_number,
                )
                for keyword in keywords:
                    await connection.execute(
                        "INSERT INTO product_keywords (product_id, keyword) VALUES ($1, $2) ON CONFLICT (keyword) DO NOTHING",
                        product_id,
                        keyword,
                    )

            for key, body in MESSAGE_TEMPLATES.items():
                await connection.execute(
                    """
                    INSERT INTO message_templates (template_key, body)
                    VALUES ($1, $2)
                    ON CONFLICT (template_key) DO UPDATE
                    SET body = EXCLUDED.body,
                        updated_at = NOW()
                    """,
                    key,
                    body,
                )
    else:
        assert database.connection is not None
        connection = database.connection
        for product in PRODUCTS:
            connection.execute(
                """
                INSERT INTO products (product_number, name, price, image_url, description, gender, scent_family, top_notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(product_number) DO UPDATE SET
                    name = excluded.name,
                    price = excluded.price,
                    image_url = excluded.image_url,
                    description = excluded.description,
                    gender = excluded.gender,
                    scent_family = excluded.scent_family,
                    top_notes = excluded.top_notes,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (product["product_number"], product["name"], product["price"], product["image_url"],
                 product.get("description"), product.get("gender"), product.get("scent_family"), product.get("top_notes")),
            )

        for product_number, keywords in PRODUCT_KEYWORDS.items():
            row = connection.execute(
                "SELECT id FROM products WHERE product_number = ?",
                (product_number,),
            ).fetchone()
            if row is None:
                continue
            for keyword in keywords:
                connection.execute(
                    "INSERT OR IGNORE INTO product_keywords (product_id, keyword) VALUES (?, ?)",
                    (row[0], keyword),
                )

        for key, body in MESSAGE_TEMPLATES.items():
            connection.execute(
                """
                INSERT INTO message_templates (template_key, body)
                VALUES (?, ?)
                ON CONFLICT(template_key) DO UPDATE SET
                    body = excluded.body,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (key, body),
            )

        connection.commit()

    print(f"Seed complete using {settings.database_mode} mode")


if __name__ == "__main__":
    asyncio.run(main())
