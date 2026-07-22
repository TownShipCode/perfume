from __future__ import annotations

import re


ORDER_PATTERN = re.compile(r"^\s*(?P<quantity>\d+)\s+(?P<product>.+?)\s*$", re.IGNORECASE)


def parse_order(text: str, keyword_map: dict[str, dict]) -> dict | None:
    match = ORDER_PATTERN.match(text)
    if not match:
        return None

    quantity = int(match.group("quantity"))
    product_text = match.group("product").strip().lower()

    if quantity <= 0:
        return None

    exact_match = keyword_map.get(product_text)
    if exact_match:
        return _build_result(quantity, product_text, exact_match)

    for keyword, product in keyword_map.items():
        if keyword in product_text:
            return _build_result(quantity, keyword, product)

    return None


def _build_result(quantity: int, keyword: str, product: dict) -> dict:
    return {
        "product_id": product["product_id"],
        "product_number": product["product_number"],
        "product_name": product["name"],
        "quantity": quantity,
        "matched_keyword": keyword,
        "unit_price": product["price"],
    }
