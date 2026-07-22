from __future__ import annotations

from decimal import Decimal

from src.models.cart import Cart, CartItem


def add_item_to_cart(cart_items: list[CartItem], product_id: int, quantity: int) -> list[CartItem]:
    updated: list[CartItem] = []
    matched = False
    for item in cart_items:
        if item.product_id == product_id:
            updated.append(CartItem(product_id=product_id, quantity=item.quantity + quantity))
            matched = True
        else:
            updated.append(item)

    if not matched:
        updated.append(CartItem(product_id=product_id, quantity=quantity))

    return updated


def calculate_cart_total(cart_items: list[CartItem], product_prices: dict[int, Decimal]) -> Decimal:
    total = Decimal("0.00")
    for item in cart_items:
        total += product_prices.get(item.product_id, Decimal("0.00")) * item.quantity
    return total.quantize(Decimal("0.01"))


def build_cart(cart_items: list[CartItem], product_prices: dict[int, Decimal]) -> Cart:
    return Cart(items=cart_items, total=calculate_cart_total(cart_items, product_prices))
