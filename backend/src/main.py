from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.customers import router as customer_routes
from src.api.orders import router as order_routes
from src.api.products import router as product_routes
from src.api.templates import router as template_routes
from src.api.webhook import router as webhook_routes
from src.config import get_settings
from src.db.connection import close_database, connect_database, initialize_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    database = await connect_database(settings)
    await initialize_database(database)
    app.state.settings = settings
    app.state.database = database
    try:
        yield
    finally:
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

app.include_router(product_routes)
app.include_router(order_routes)
app.include_router(customer_routes)
app.include_router(template_routes)
app.include_router(webhook_routes)


@app.get("/")
async def root() -> dict[str, object]:
    settings = get_settings()
    return {
        "name": "WhatsApp Order Platform API",
        "environment": settings.app_env,
        "database_mode": settings.database_mode,
        "status": "bootstrapped",
    }


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/health")
async def api_health() -> dict[str, str]:
    return {"status": "ok"}
