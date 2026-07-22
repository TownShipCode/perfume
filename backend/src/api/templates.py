from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from src.middleware.auth import require_dashboard_api_key
from src.services.message_templates import list_templates, update_template_body


router = APIRouter(prefix="/api/templates", tags=["templates"], dependencies=[Depends(require_dashboard_api_key)])


class UpdateTemplateRequest(BaseModel):
    body: str


@router.get("")
async def get_templates(request: Request) -> dict[str, object]:
    items = await list_templates(request.app.state.database)
    return {"items": items, "count": len(items)}


@router.put("/{template_key}")
async def put_template(request: Request, template_key: str, payload: UpdateTemplateRequest) -> dict[str, object]:
    try:
        item = await update_template_body(request.app.state.database, template_key, payload.body)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=f"Unknown template: {template_key}") from error
    return {"item": item}