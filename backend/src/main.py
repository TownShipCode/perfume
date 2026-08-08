from __future__ import annotations

import asyncio
import logging
import subprocess
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.api.agent_tools import router as agent_tools_routes
from src.api.analytics import router as analytics_routes
from src.api.auth import router as auth_routes
from src.api.customers import router as customer_routes
from src.api.flyer import router as flyer_routes
from src.api.newsletter import router as newsletter_routes
from src.api.orders import router as order_routes
from src.api.payments import router as payment_routes
from src.api.products import router as product_routes
from src.api.templates import router as template_routes
from src.api.webhook import router as webhook_routes
from src.config import get_settings
from src.db.connection import close_database, connect_database, initialize_database

logger = logging.getLogger(__name__)


async def _expire_stale_orders_loop(database, pop_expiry_hours: int, interval: int = 600):
    """Background task: expire stale POP orders every `interval` seconds."""
    from src.services.order_service import expire_stale_pop_orders
    while True:
        try:
            await expire_stale_pop_orders(database, pop_expiry_hours)
        except Exception as exc:
            logger.warning("background_expiry_error | %s", exc)
        await asyncio.sleep(interval)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    database = await connect_database(settings)
    await initialize_database(database)
    app.state.settings = settings
    app.state.database = database

    # Register quantity button → command mappings
    from src.services.whatsapp_buttons import register_quantity_mappings
    register_quantity_mappings(settings.quantity_options)

    # Background task: expire stale POP orders every 10 minutes
    expiry_task = asyncio.create_task(
        _expire_stale_orders_loop(database, settings.pop_expiry_hours)
    )

    try:
        yield
    finally:
        expiry_task.cancel()
        await close_database(database)


app = FastAPI(
    title="WhatsApp Order Platform API",
    version="0.1.0",
    lifespan=lifespan,
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' https: data:; style-src 'self' 'unsafe-inline'; script-src 'self'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if settings.is_production or os.getenv("ENFORCE_HTTPS") == "true":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

app.include_router(agent_tools_routes)
app.include_router(analytics_routes)
app.include_router(auth_routes)
app.include_router(product_routes)
app.include_router(order_routes)
app.include_router(payment_routes)
app.include_router(customer_routes)
app.include_router(flyer_routes)
app.include_router(newsletter_routes)
app.include_router(template_routes)
app.include_router(webhook_routes)

# Serve static files (product images, etc.)
_static_dir = Path(__file__).resolve().parent.parent / "static"
if _static_dir.is_dir():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


@app.get("/")
async def root() -> dict[str, object]:
    settings = get_settings()
    return {
        "name": "WhatsApp Order Platform API",
        "environment": settings.app_env,
        "database_mode": settings.database_mode,
        "status": "bootstrapped",
    }


GIT_SHA = ""
try:
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        capture_output=True, text=True, timeout=5,
        cwd=Path(__file__).resolve().parents[2],
    )
    if result.returncode == 0:
        GIT_SHA = result.stdout.strip()
except Exception:
    pass

if not GIT_SHA:
    # Fallback: read SHA from file baked into Docker image
    sha_file = Path("/app/git_sha.txt")
    if sha_file.exists():
        GIT_SHA = sha_file.read_text(encoding="utf-8").strip()
        if GIT_SHA == "unknown":
            GIT_SHA = ""


@app.get("/health")
async def health() -> dict[str, object]:
    return {
        "status": "ok",
        "version": "0.1.0",
        "commit": GIT_SHA,
    }


@app.get("/api/health")
async def api_health(request: Request) -> dict[str, object]:
    return {
        "status": "ok",
        "version": "0.1.0",
        "commit": GIT_SHA,
        "db": request.app.state.database.mode,
    }
