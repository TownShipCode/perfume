from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


class SettingsError(RuntimeError):
    pass


@dataclass(frozen=True)
class Settings:
    app_env: str
    log_level: str
    store_name: str
    store_currency: str
    api_base_url: str
    database_url: str | None
    local_sqlite_path: Path
    whatsapp_api_key: str | None
    whatsapp_phone_number_id: str | None
    whatsapp_verify_token: str | None
    whatsapp_app_secret: str | None
    dashboard_api_key: str | None
    admin_phone: str | None
    manufacturer_phone: str | None
    cors_origins: tuple[str, ...]
    sentry_dsn: str | None

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def database_mode(self) -> str:
        return "postgres" if self.database_url else "sqlite"


def _optional(name: str) -> str | None:
    value = os.getenv(name)
    return value.strip() if value and value.strip() else None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    raw_sqlite_path = os.getenv("LOCAL_SQLITE_PATH", "backend/data/app.db")
    local_sqlite_path = (PROJECT_ROOT / raw_sqlite_path).resolve()
    cors_origins = tuple(
        origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if origin.strip()
    )

    settings = Settings(
        app_env=os.getenv("APP_ENV", "development").lower(),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        store_name=os.getenv("STORE_NAME", "Example Store"),
        store_currency=os.getenv("STORE_CURRENCY", "ZAR"),
        api_base_url=os.getenv("API_BASE_URL", "http://localhost:8000"),
        database_url=_optional("DATABASE_URL"),
        local_sqlite_path=local_sqlite_path,
        whatsapp_api_key=_optional("WHATSAPP_API_KEY"),
        whatsapp_phone_number_id=_optional("WHATSAPP_PHONE_NUMBER_ID"),
        whatsapp_verify_token=_optional("WHATSAPP_VERIFY_TOKEN"),
        whatsapp_app_secret=_optional("WHATSAPP_APP_SECRET"),
        dashboard_api_key=_optional("DASHBOARD_API_KEY"),
        admin_phone=_optional("ADMIN_PHONE"),
        manufacturer_phone=_optional("MANUFACTURER_PHONE"),
        cors_origins=cors_origins,
        sentry_dsn=_optional("SENTRY_DSN"),
    )
    validate_settings(settings)
    return settings


def validate_settings(settings: Settings) -> None:
    if settings.is_production:
        missing = [
            name
            for name, value in {
                "DATABASE_URL": settings.database_url,
                "WHATSAPP_API_KEY": settings.whatsapp_api_key,
                "WHATSAPP_PHONE_NUMBER_ID": settings.whatsapp_phone_number_id,
                "WHATSAPP_VERIFY_TOKEN": settings.whatsapp_verify_token,
                "WHATSAPP_APP_SECRET": settings.whatsapp_app_secret,
                "DASHBOARD_API_KEY": settings.dashboard_api_key,
            }.items()
            if not value
        ]
        if missing:
            raise SettingsError(
                "Missing required production configuration: " + ", ".join(missing)
            )

    settings.local_sqlite_path.parent.mkdir(parents=True, exist_ok=True)
