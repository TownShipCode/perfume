from src.services.order_parser import parse_order


KEYWORD_MAP = {
    "shoe": {"product_id": 1, "product_number": 1, "name": "Red Shoes", "price": "350.00"},
    "shoes": {"product_id": 1, "product_number": 1, "name": "Red Shoes", "price": "350.00"},
    "red shoe": {"product_id": 1, "product_number": 1, "name": "Red Shoes", "price": "350.00"},
    "hat": {"product_id": 2, "product_number": 2, "name": "Blue Hat", "price": "120.00"},
}


def test_parse_order_exact_keyword() -> None:
    result = parse_order("2 shoes", KEYWORD_MAP)
    assert result is not None
    assert result["product_id"] == 1
    assert result["quantity"] == 2
    assert result["matched_keyword"] == "shoes"


def test_parse_order_partial_keyword() -> None:
    result = parse_order("1 red shoe please", KEYWORD_MAP)
    assert result is not None
    assert result["product_number"] == 1
    assert result["quantity"] == 1


def test_parse_order_returns_none_for_unknown_product() -> None:
    assert parse_order("3 socks", KEYWORD_MAP) is None
