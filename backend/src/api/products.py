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
    get_product_categories,
    get_product_detail,
    list_all_products,
    search_products,
    update_product,
)


router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("")
async def get_products(
    request: Request,
    search: str = "",
    page: int = 1,
    page_size: int = 20,
    category: str = "",
    gender: str = "",
    sort: str = "number",
) -> dict[str, object]:
    """Paginated + filtered product search for WhatsApp + web store."""
    if search or category or gender:
        return await search_products(
            request.app.state.database, search,
            page=page, page_size=page_size,
            category=category or None, gender=gender or None, sort=sort,
        )
    products = await list_all_products(request.app.state.database)
    return {"items": products, "count": len(products)}


@router.get("/categories")
async def get_categories(request: Request) -> dict[str, object]:
    """Return all product categories."""
    cats = await get_product_categories(request.app.state.database)
    return {"items": cats}


@router.get("/scents")
async def get_scents(request: Request) -> dict[str, object]:
    """Return distinct scent families and genders for filter chips."""
    from src.db.connection import fetch_all
    rows = await fetch_all(
        request.app.state.database,
        "SELECT DISTINCT scent_family FROM products WHERE scent_family IS NOT NULL AND is_active = TRUE ORDER BY scent_family"
        if request.app.state.database.mode == "postgres"
        else "SELECT DISTINCT scent_family FROM products WHERE scent_family IS NOT NULL AND is_active = 1 ORDER BY scent_family",
    )
    scent_families = [r["scent_family"] for r in rows if r["scent_family"]]
    gender_rows = await fetch_all(
        request.app.state.database,
        "SELECT DISTINCT gender FROM products WHERE gender IS NOT NULL AND is_active = TRUE ORDER BY gender"
        if request.app.state.database.mode == "postgres"
        else "SELECT DISTINCT gender FROM products WHERE gender IS NOT NULL AND is_active = 1 ORDER BY gender",
    )
    genders = [r["gender"] for r in gender_rows if r["gender"]]
    return {"scent_families": scent_families, "genders": genders}


@router.get("/{product_id}")
async def get_product(request: Request, product_id: int) -> dict[str, object]:
    """Get a single product by ID (public — used by web store)."""
    from src.services.catalog_service import get_product_detail
    product = await get_product_detail(request.app.state.database, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


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
