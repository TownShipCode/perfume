from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from src.services.catalog_service import get_keyword_map
from src.services.order_parser import parse_order


router = APIRouter(prefix="/api/orders", tags=["orders"])


class ParseOrderRequest(BaseModel):
    text: str


@router.post("/parse")
async def parse_order_preview(request: Request, payload: ParseOrderRequest) -> dict[str, object]:
    keyword_map = await get_keyword_map(request.app.state.database)
    result = parse_order(payload.text, keyword_map)
    if result is None:
        raise HTTPException(status_code=422, detail="Unable to match product from message")
    return {"item": result}
