from __future__ import annotations

import asyncio

from src.config import get_settings
from src.db.connection import connect_database, initialize_database


PRODUCTS = [
    {"product_number": 1, "name": "Red Shoes", "price": 350.00, "image_url": "https://example.com/products/red-shoes.jpg"},
    {"product_number": 2, "name": "Blue Hat", "price": 120.00, "image_url": "https://example.com/products/blue-hat.jpg"},
    {"product_number": 3, "name": "Black Bag", "price": 280.00, "image_url": "https://example.com/products/black-bag.jpg"},
    {"product_number": 4, "name": "White T-Shirt", "price": 160.00, "image_url": "https://example.com/products/white-tshirt.jpg"},
]

PRODUCT_KEYWORDS = {
    1: ["shoe", "shoes", "sneaker", "red shoe", "red shoes"],
    2: ["hat", "cap", "blue hat"],
    3: ["bag", "black bag", "backpack"],
    4: ["tshirt", "t-shirt", "shirt", "white tshirt"],
}

MESSAGE_TEMPLATES = {
    "welcome": "Welcome to {store_name}. Reply with a quantity and product name, for example: 2 shoes.",
    "cart_update": "Added {quantity}x {product_name}. Total: {total} {currency}.",
    "address_request": "I need your delivery address. First: what is your area?",
    "address_confirmation": "Address saved: {full_address}. Is this correct?",
    "order_final": "Order {order_number} confirmed. Total: {total} {currency}. Please send your POP image.",
    "pop_received": "POP received. We will confirm your order shortly.",
    "address_request_street": "Thanks. Now send your STREET and HOUSE NUMBER.",
    "address_request_city": "Thanks. Now send your CITY.",
    "checkout_blocked": "Your cart is empty. Add a product first, for example: 2 shoes.",
    "unmatched": "I could not match that product. Try something like: 2 shoes or 1 hat.",
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
                    INSERT INTO products (product_number, name, price, image_url)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (product_number) DO UPDATE
                    SET name = EXCLUDED.name,
                        price = EXCLUDED.price,
                        image_url = EXCLUDED.image_url,
                        updated_at = NOW()
                    """,
                    product["product_number"],
                    product["name"],
                    product["price"],
                    product["image_url"],
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
                INSERT INTO products (product_number, name, price, image_url)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(product_number) DO UPDATE SET
                    name = excluded.name,
                    price = excluded.price,
                    image_url = excluded.image_url,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (product["product_number"], product["name"], product["price"], product["image_url"]),
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
