from __future__ import annotations

from fastapi import APIRouter, Request, status

from src.services.catalog_service import ProductInput, create_product, list_all_products


router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("")
async def get_products(request: Request) -> dict[str, object]:
    products = await list_all_products(request.app.state.database)
    return {"items": products, "count": len(products)}


@router.post("", status_code=status.HTTP_201_CREATED)
async def post_product(request: Request, payload: ProductInput) -> dict[str, object]:
    product = await create_product(request.app.state.database, payload)
    return {"item": product}
