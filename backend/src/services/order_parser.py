from __future__ import annotations

import re


ORDER_PATTERN = re.compile(r"^\s*(?P<quantity>\d+)\s+(?P<product>.+?)\s*$", re.IGNORECASE)


def split_quantity_and_name(text: str) -> tuple[int | None, str]:
    """Split an order attempt into (quantity, product_text).

    "5 scandal" → (5, "scandal"); "scandal" → (None, "scandal").
    Returns None quantity when there is no leading digit, so callers can
    drive both the keyword parser and the fuzzy candidate picker.
    """
    raw = (text or "").strip()
    match = ORDER_PATTERN.match(raw)
    if not match:
        return None, raw
    return int(match.group("quantity")), match.group("product").strip()


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


def _product_matches(query: str, target: str) -> bool:
    """Substring match (either direction) with a length floor to avoid noise.

    A 3+ char query may match inside a longer name/keyword (e.g. "million"
    inside "LADY MILLION"); a full/leading keyword may match inside a longer
    query. Two-char tokens (e.g. "si") never drive fuzzy candidates.
    """
    if not query or not target:
        return False
    query_l = query.lower()
    target_l = target.lower()
    if len(query_l) >= 3 and query_l in target_l:
        return True
    if len(target_l) >= 3 and target_l in query_l:
        return True
    return False


def product_candidates(product_text: str, products: list[dict]) -> list[dict]:
    """Return distinct products whose name or keyword fuzzy-matches product_text.

    Powers the ambiguous/partial-name LIST picker (e.g. "scandal" → both the
    men's and women's SCANDAL; "million" → ONE MILLION and LADY MILLION).
    Results are deduped by product id and sorted by product_number.
    """
    query = (product_text or "").strip().lower()
    if len(query) < 2:
        return []

    seen: dict[int, dict] = {}
    for product in products:
        name = (product.get("name") or "").lower()
        keywords = [str(k) for k in (product.get("keywords") or [])]
        if _product_matches(query, name) or any(_product_matches(query, k) for k in keywords):
            pid = product.get("id") or product.get("product_id")
            if pid is not None and pid not in seen:
                seen[pid] = product

    return sorted(seen.values(), key=lambda p: (p.get("product_number") or 0))
