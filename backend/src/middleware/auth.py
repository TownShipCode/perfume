from __future__ import annotations

from fastapi import HTTPException, Request, status

from src.config import get_settings


async def require_dashboard_api_key(request: Request) -> None:
    settings = get_settings()
    expected = settings.dashboard_api_key
    if not expected:
        if settings.is_production:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Dashboard API key is not configured")
        return

    provided = request.headers.get("x-api-key")
    if provided == expected:
        return

    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer ") and auth_header.removeprefix("Bearer ") == expected:
        return

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
