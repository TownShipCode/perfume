"""Newsletter signup — captures emails for launch announcements + retargeting.

Public, no auth. Idempotent (duplicate emails are ignored).
- Web: POST /api/newsletter
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from src.db.connection import execute

router = APIRouter(prefix="/api/newsletter", tags=["newsletter"])


class NewsletterSubscribe(BaseModel):
    email: str


@router.post("")
async def subscribe(request: Request, payload: NewsletterSubscribe) -> dict[str, object]:
    """Save an email address for launch updates. Returns 409 on duplicate."""
    email = (payload.email or "").strip().lower()
    if len(email) < 5 or "@" not in email or "." not in email:
        raise HTTPException(status_code=422, detail="Please enter a valid email address.")

    database = request.app.state.database
    if database.mode == "postgres":
        await execute(
            database,
            "INSERT INTO newsletter_subscribers (email) VALUES ($1) ON CONFLICT (email) DO NOTHING",
            email,
        )
    else:
        await execute(
            database,
            "INSERT OR IGNORE INTO newsletter_subscribers (email) VALUES (?)",
            email,
        )
    return {"ok": True, "email": email, "message": "Thanks for signing up!"}
