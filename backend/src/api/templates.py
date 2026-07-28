from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from src.middleware.auth import require_dashboard_api_key
from src.services.message_templates import DEFAULT_TEMPLATES


router = APIRouter(prefix="/api/templates", tags=["templates"], dependencies=[Depends(require_dashboard_api_key)])


@router.get("")
async def get_templates(request: Request) -> dict[str, object]:
    items = [{"template_key": k, "body": v} for k, v in sorted(DEFAULT_TEMPLATES.items())]
    return {"items": items, "count": len(items)}