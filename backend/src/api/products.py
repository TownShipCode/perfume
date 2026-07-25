from __future__ import annotations

from asyncpg.exceptions import UniqueViolationError
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from src.middleware.auth import require_dashboard_api_key
from src.services.catalog_service import (
    ProductInput,
    ProductUpdateInput,
    create_product,
    delete_product,
    get_product_by_id,
    list_all_products,
    update_product,
)


router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("")
async def get_products(request: Request) -> dict[str, object]:
    products = await list_all_products(request.app.state.database)
    return {"items": products, "count": len(products)}


@router.post("", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_dashboard_api_key)])
async def post_product(request: Request, payload: ProductInput) -> dict[str, object]:
    try:
        product = await create_product(request.app.state.database, payload)
    except UniqueViolationError:
        raise HTTPException(status_code=409, detail=f"Product number {payload.product_number} already exists")
    return {"item": product}


@router.put("/{product_id}", dependencies=[Depends(require_dashboard_api_key)])
async def put_product(request: Request, product_id: int, payload: ProductUpdateInput) -> dict[str, object]:
    product = await update_product(request.app.state.database, product_id, payload)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"item": product}


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_dashboard_api_key)])
async def remove_product(request: Request, product_id: int) -> Response:
    deleted = await delete_product(request.app.state.database, product_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Product not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
