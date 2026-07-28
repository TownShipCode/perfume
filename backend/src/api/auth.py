"""Admin auth — HttpOnly cookie session tokens (wiki pattern)."""
from __future__ import annotations

import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from src.db.connection import Database, execute, fetch_one
from src.middleware.auth import require_dashboard_api_key
from src.middleware.rate_limit import auth_rate_limit

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


@router.post("/login", dependencies=[Depends(auth_rate_limit())])
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


@router.post("/set-password", dependencies=[Depends(require_dashboard_api_key)])
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


# ── Phase 7: Role-based auth (login, register, agent registration) ──


@router.post("/login/role", dependencies=[Depends(auth_rate_limit())])
async def login_role(request: Request) -> JSONResponse:
    """Login with email + password, returns role + token for dashboard redirect."""
    body = await request.json()
    email = (body or {}).get("email", "").strip().lower()
    password = (body or {}).get("password", "")
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")

    database: Database = request.app.state.database
    from src.services.customer_service import get_customer_by_email

    customer = await get_customer_by_email(database, email)
    if customer is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    stored_hash = customer.get("password_hash") or ""
    if not _verify_password(password, stored_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = await _store_session(database, stored_hash)
    resp = JSONResponse(content={
        "authenticated": True,
        "role": customer.get("role", "customer"),
        "agent_code": customer.get("agent_code"),
        "name": customer.get("name"),
        "id": customer["id"],
    })
    resp.set_cookie(
        key="session_token", value=token,
        max_age=SESSION_HOURS * 3600, httponly=True, secure=True, samesite="lax", path="/",
    )
    return resp


@router.post("/register", dependencies=[Depends(auth_rate_limit())])
async def register_public(request: Request) -> JSONResponse:
    """Public self-service registration (no approval needed)."""
    body = await request.json() or {}
    email = body.get("email", "").strip().lower()
    phone = body.get("phone", "").strip()
    name = body.get("name", "").strip()
    surname = body.get("surname", "").strip()
    password = body.get("password", "")

    if not email or not phone or not password:
        raise HTTPException(status_code=400, detail="Email, phone, and password required")

    database: Database = request.app.state.database
    from src.services.customer_service import get_customer_by_phone, get_customer_by_email

    if await get_customer_by_email(database, email):
        raise HTTPException(status_code=409, detail="Email already registered")
    if await get_customer_by_phone(database, phone):
        raise HTTPException(status_code=409, detail="Phone number already registered")

    password_hash = _hash_password(password)
    if database.mode == "postgres":
        await execute(
            database,
            """INSERT INTO customers (phone_number, email, name, surname, password_hash, role)
               VALUES ($1, $2, $3, $4, $5, 'customer')""",
            phone, email, name, surname, password_hash,
        )
    else:
        await execute(
            database,
            """INSERT INTO customers (phone_number, email, name, surname, password_hash, role)
               VALUES (?, ?, ?, ?, ?, 'customer')""",
            phone, email, name, surname, password_hash,
        )

    return JSONResponse(content={"registered": True, "email": email}, status_code=201)


@router.post("/register/agent", dependencies=[Depends(auth_rate_limit())])
async def register_agent_web(request: Request) -> JSONResponse:
    """Agent self-registration via web store (with team code)."""
    body = await request.json() or {}
    phone = body.get("phone", "").strip()
    name = body.get("name", "").strip()
    surname = body.get("surname", "").strip()
    team_code = body.get("team_code", "").strip().upper()
    email = body.get("email", "").strip().lower()
    password = body.get("password", "")

    if not phone or not name or not team_code:
        raise HTTPException(status_code=400, detail="Phone, name, and team code required")

    database: Database = request.app.state.database
    from src.services.customer_service import register_agent

    import secrets
    recovery_pin = str(secrets.randbelow(10000)).zfill(4)

    agent = await register_agent(
        database, phone, first_name=name, surname=surname,
        team_code=team_code, recovery_pin=recovery_pin,
    )

    if agent is None:
        raise HTTPException(status_code=400, detail="Team code not found")

    # Set email + password if provided
    if email and password:
        password_hash = _hash_password(password)
        if database.mode == "postgres":
            await execute(
                database,
                "UPDATE customers SET email = $1, password_hash = $2 WHERE id = $3",
                email, password_hash, agent["id"],
            )
        else:
            await execute(
                database,
                "UPDATE customers SET email = ?, password_hash = ? WHERE id = ?",
                email, password_hash, agent["id"],
            )

    return JSONResponse(content={
        "registered": True,
        "agent_code": agent.get("agent_code"),
        "recovery_pin": recovery_pin,
    }, status_code=201)
