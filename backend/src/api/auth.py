"""Admin auth — HttpOnly cookie session tokens (wiki pattern)."""
from __future__ import annotations

import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from src.db.connection import Database, execute, fetch_one

router = APIRouter(prefix="/api/auth", tags=["auth"])

SESSION_HOURS = 24
TOKEN_BYTES = 32


def _hash_password(password: str) -> str:
    """PBKDF2-HMAC-SHA256 with random salt."""
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 600_000)
    return salt.hex() + ":" + dk.hex()


def _verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, dk_hex = stored.split(":", 1)
        salt = bytes.fromhex(salt_hex)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 600_000)
        return dk.hex() == dk_hex
    except Exception:
        return False


def _new_token() -> str:
    return secrets.token_urlsafe(TOKEN_BYTES)


async def _get_active_hash(database: Database) -> str | None:
    now_fn = "CURRENT_TIMESTAMP" if database.mode == "sqlite" else "NOW()"
    row = await fetch_one(
        database,
        f"SELECT password_hash FROM _admin_sessions WHERE expires_at > {now_fn} ORDER BY id DESC LIMIT 1",
    )
    return row["password_hash"] if row else None


async def _store_session(database: Database, password_hash: str) -> str:
    token = _new_token()
    expires = datetime.now(timezone.utc) + timedelta(hours=SESSION_HOURS)
    if database.mode == "sqlite":
        await execute(
            database,
            "INSERT INTO _admin_sessions (token, password_hash, expires_at) VALUES (?, ?, ?)",
            token, password_hash, expires.isoformat(),
        )
    else:
        await execute(
            database,
            "INSERT INTO _admin_sessions (token, password_hash, expires_at) VALUES ($1, $2, $3)",
            token, password_hash, expires,
        )
    return token


async def _validate_token(database: Database, token: str) -> bool:
    now_fn = "CURRENT_TIMESTAMP" if database.mode == "sqlite" else "NOW()"
    if database.mode == "sqlite":
        row = await fetch_one(
            database,
            f"SELECT id FROM _admin_sessions WHERE token = ? AND expires_at > {now_fn}",
            token,
        )
    else:
        row = await fetch_one(
            database,
            f"SELECT id FROM _admin_sessions WHERE token = $1 AND expires_at > {now_fn}",
            token,
        )
    return row is not None


async def _clear_token(database: Database, token: str) -> None:
    if database.mode == "sqlite":
        await execute(database, "DELETE FROM _admin_sessions WHERE token = ?", token)
    else:
        await execute(database, "DELETE FROM _admin_sessions WHERE token = $1", token)


@router.post("/login")
async def login(request: Request) -> JSONResponse:
    body = await request.json()
    password = (body or {}).get("password", "")
    if not password:
        raise HTTPException(status_code=400, detail="Password required")

    database: Database = request.app.state.database

    # First-time setup: if no hash exists, use DASHBOARD_API_KEY as initial password
    existing_hash = await _get_active_hash(database)
    if existing_hash is None:
        from src.config import get_settings
        settings = get_settings()
        initial_key = settings.dashboard_api_key
        if not initial_key:
            raise HTTPException(status_code=500, detail="No admin password configured")
        if password != initial_key:
            raise HTTPException(status_code=401, detail="Invalid password")
        password_hash = _hash_password(password)
    else:
        if not _verify_password(password, existing_hash):
            raise HTTPException(status_code=401, detail="Invalid password")
        password_hash = existing_hash

    token = await _store_session(database, password_hash)
    resp = JSONResponse(content={"authenticated": True})
    resp.set_cookie(
        key="session_token",
        value=token,
        max_age=SESSION_HOURS * 3600,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
    )
    return resp


@router.post("/logout")
async def logout(request: Request) -> JSONResponse:
    token = request.cookies.get("session_token") or ""
    database: Database = request.app.state.database
    await _clear_token(database, token)
    resp = JSONResponse(content={"authenticated": False})
    resp.delete_cookie("session_token", path="/")
    return resp


@router.get("/check")
async def check(request: Request) -> dict:
    token = request.cookies.get("session_token") or ""
    database: Database = request.app.state.database
    valid = await _validate_token(database, token)
    return {"authenticated": valid}


@router.post("/set-password")
async def set_password(request: Request) -> JSONResponse:
    body = await request.json()
    current = (body or {}).get("current", "")
    new_password = (body or {}).get("new", "")
    if not current or not new_password:
        raise HTTPException(status_code=400, detail="Current and new password required")

    database: Database = request.app.state.database
    existing_hash = await _get_active_hash(database)
    if existing_hash and not _verify_password(current, existing_hash):
        raise HTTPException(status_code=401, detail="Invalid current password")

    password_hash = _hash_password(new_password)
    await execute(database, "DELETE FROM _admin_sessions")  # invalidate all old tokens
    token = await _store_session(database, password_hash)
    resp = JSONResponse(content={"authenticated": True})
    resp.set_cookie(
        key="session_token",
        value=token,
        max_age=SESSION_HOURS * 3600,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
    )
    return resp
