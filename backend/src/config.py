from __future__ import annotations

import os
from dataclasses import dataclass
from decimal import Decimal
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
    web_base_url: str
    database_url: str | None
    local_sqlite_path: Path
    whatsapp_provider: str
    whatsapp_api_base_url: str
    whatsapp_send_mode: str
    whatsapp_api_key: str | None
    whatsapp_phone_number_id: str | None
    whatsapp_verify_token: str | None
    whatsapp_app_secret: str | None
    whatsapp_catalog_id: str | None
    dashboard_api_key: str | None
    yoco_secret_key: str | None
    yoco_webhook_secret: str | None
    admin_phone: str | None
    manufacturer_phone: str | None
    flyer_whatsapp: str | None
    flyer_featured_ids: tuple[int, ...]
    shipping_fee: Decimal
    free_shipping_threshold: Decimal
    whatsapp_greeting_commands: tuple[str, ...]
    whatsapp_catalog_commands: tuple[str, ...]
    whatsapp_checkout_commands: tuple[str, ...]
    whatsapp_confirm_commands: tuple[str, ...]
    whatsapp_reject_commands: tuple[str, ...]
    whatsapp_cancel_commands: tuple[str, ...]
    pop_expiry_hours: int
    cors_origins: tuple[str, ...]
    sentry_dsn: str | None
    auto_forward_to_manufacturer: bool
    default_margin: Decimal
    courier_fee: Decimal
    courier_name: str
    courier_tracking_url: str
    commission_percent: Decimal
    low_stock_threshold: int
    quantity_options: tuple[int, ...]
    max_quantity: int
    yoco_base_url: str
    bank_name: str
    account_holder: str
    account_number: str
    branch_code: str
    payment_methods_enabled: tuple[str, ...]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def database_mode(self) -> str:
        return "postgres" if self.database_url else "sqlite"


def _optional(name: str) -> str | None:
    value = os.getenv(name)
    return value.strip() if value and value.strip() else None


def _csv_values(raw_value: str) -> tuple[str, ...]:
    values = tuple(item.strip().lower() for item in raw_value.split(",") if item.strip())
    return values


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    raw_sqlite_path = os.getenv("LOCAL_SQLITE_PATH", "backend/data/app.db")
    local_sqlite_path = (PROJECT_ROOT / raw_sqlite_path).resolve()
    cors_origins = tuple(
        origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if origin.strip()
    )
    whatsapp_greeting_commands = _csv_values(os.getenv("WHATSAPP_GREETING_COMMANDS", "hi,hello,hey,start"))
    whatsapp_catalog_commands = _csv_values(os.getenv("WHATSAPP_CATALOG_COMMANDS", "menu,catalogue,catalog,products"))
    whatsapp_checkout_commands = _csv_values(os.getenv("WHATSAPP_CHECKOUT_COMMANDS", "done,checkout,order"))
    whatsapp_confirm_commands = _csv_values(os.getenv("WHATSAPP_CONFIRM_COMMANDS", "yes,y,ok,correct"))
    whatsapp_reject_commands = _csv_values(os.getenv("WHATSAPP_REJECT_COMMANDS", "no,n"))

    shipping_fee = Decimal(os.getenv("SHIPPING_FEE", "109.00") or "109.00")
    free_shipping_threshold = Decimal(os.getenv("FREE_SHIPPING_THRESHOLD", "2000.00") or "2000.00")
    whatsapp_cancel_commands = _csv_values(os.getenv("WHATSAPP_CANCEL_COMMANDS", "cancel,stop"))
    pop_expiry_hours = int(os.getenv("POP_EXPIRY_HOURS", "24") or "24")
    default_language = os.getenv("DEFAULT_LANGUAGE", "en").strip().lower() or "en"
    supported_languages = _csv_values(os.getenv("SUPPORTED_LANGUAGES", "en,zu"))
    default_margin = Decimal(os.getenv("DEFAULT_MARGIN", "70.00") or "70.00")
    courier_fee = Decimal(os.getenv("COURIER_FEE", "65.00") or "65.00")
    commission_percent = Decimal(os.getenv("COMMISSION_PERCENT", "5") or "5")
    low_stock_threshold = int(os.getenv("LOW_STOCK_THRESHOLD", "5") or "5")
    courier_name = os.getenv("COURIER_NAME", "The Courier Guy").strip()
    courier_tracking_url = os.getenv("COURIER_TRACKING_URL", "https://thecourierguy.co.za/track").strip()
    auto_forward = os.getenv("AUTO_FORWARD_TO_MANUFACTURER", "true").strip().lower() in ("true", "1", "yes")
    quantity_options = tuple(
        int(v.strip()) for v in os.getenv("WHATSAPP_QUANTITY_OPTIONS", "1,2,3,4,5,6").split(",") if v.strip().isdigit()
    )
    max_quantity = int(os.getenv("MAX_QUANTITY", "99") or "99")
    yoco_base_url = os.getenv("YOCO_BASE_URL", "https://online.yoco.com/v1").strip()
    bank_name = os.getenv("BANK_NAME", "Standard Bank").strip()
    account_holder = os.getenv("ACCOUNT_HOLDER", "Zen Fragrances").strip()
    account_number = os.getenv("ACCOUNT_NUMBER", "").strip()
    branch_code = os.getenv("BRANCH_CODE", "").strip()
    payment_methods_enabled = _csv_values(os.getenv("PAYMENT_METHODS_ENABLED", "yoco,eft"))

    settings = Settings(
        app_env=os.getenv("APP_ENV", "development").lower(),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        store_name=os.getenv("STORE_NAME", "Example Store"),
        store_currency=os.getenv("STORE_CURRENCY", "ZAR"),
        api_base_url=os.getenv("API_BASE_URL", "http://localhost:8000"),
        web_base_url=os.getenv("WEB_BASE_URL", "http://localhost:5173"),
        database_url=_optional("DATABASE_URL"),
        local_sqlite_path=local_sqlite_path,
        whatsapp_provider=os.getenv("WHATSAPP_PROVIDER", "meta").lower(),
        whatsapp_api_base_url=os.getenv("WHATSAPP_API_BASE_URL", "https://graph.facebook.com/v24.0"),
        whatsapp_send_mode=os.getenv("WHATSAPP_SEND_MODE", "dry_run").lower(),
        whatsapp_api_key=_optional("WHATSAPP_API_KEY"),
        whatsapp_phone_number_id=_optional("WHATSAPP_PHONE_NUMBER_ID"),
        whatsapp_verify_token=_optional("WHATSAPP_VERIFY_TOKEN"),
        whatsapp_app_secret=_optional("WHATSAPP_APP_SECRET"),
        whatsapp_catalog_id=_optional("WHATSAPP_CATALOG_ID"),
        yoco_secret_key=_optional("YOCO_SECRET_KEY"),
        yoco_webhook_secret=_optional("YOCO_WEBHOOK_SECRET"),
        dashboard_api_key=_optional("DASHBOARD_API_KEY"),
        admin_phone=_optional("ADMIN_PHONE"),
        manufacturer_phone=_optional("MANUFACTURER_PHONE"),
        flyer_whatsapp=_optional("FLYER_WHATSAPP"),
        flyer_featured_ids=tuple(
            int(v.strip()) for v in os.getenv("FLYER_FEATURED_IDS", "").split(",") if v.strip().isdigit()
        ),
        whatsapp_greeting_commands=whatsapp_greeting_commands,
        whatsapp_catalog_commands=whatsapp_catalog_commands,
        whatsapp_checkout_commands=whatsapp_checkout_commands,
        whatsapp_confirm_commands=whatsapp_confirm_commands,
        whatsapp_reject_commands=whatsapp_reject_commands,
        shipping_fee=shipping_fee,
        free_shipping_threshold=free_shipping_threshold,
        whatsapp_cancel_commands=whatsapp_cancel_commands,
        pop_expiry_hours=pop_expiry_hours,
        cors_origins=cors_origins,
        sentry_dsn=_optional("SENTRY_DSN"),
        auto_forward_to_manufacturer=auto_forward,
        default_margin=default_margin,
        courier_fee=courier_fee,
        courier_name=courier_name,
        courier_tracking_url=courier_tracking_url,
        commission_percent=commission_percent,
        low_stock_threshold=low_stock_threshold,
        quantity_options=quantity_options,
        max_quantity=max_quantity,
        yoco_base_url=yoco_base_url,
        bank_name=bank_name,
        account_holder=account_holder,
        account_number=account_number,
        branch_code=branch_code,
        payment_methods_enabled=payment_methods_enabled,
    )
    validate_settings(settings)
    return settings


def validate_settings(settings: Settings) -> None:
    if settings.whatsapp_provider not in {"meta", "kapso"}:
        raise SettingsError("WHATSAPP_PROVIDER must be 'meta' or 'kapso'")
    if settings.is_production:
        if settings.whatsapp_send_mode == "live" and not settings.whatsapp_api_key:
            raise SettingsError("WHATSAPP_API_KEY is required when send_mode=live in production")
        if "yoco" in settings.payment_methods_enabled and not settings.yoco_secret_key:
            raise SettingsError("YOCO_SECRET_KEY is required when yoco payment method is enabled in production")
        if not settings.account_number:
            raise SettingsError("ACCOUNT_NUMBER is required in production")

    if settings.is_production:
        required = {
            "DATABASE_URL": settings.database_url,
            "DASHBOARD_API_KEY": settings.dashboard_api_key,
        }
        if settings.whatsapp_provider == "meta":
            required.update({
                "WHATSAPP_API_KEY": settings.whatsapp_api_key,
                "WHATSAPP_PHONE_NUMBER_ID": settings.whatsapp_phone_number_id,
                "WHATSAPP_VERIFY_TOKEN": settings.whatsapp_verify_token,
                "WHATSAPP_APP_SECRET": settings.whatsapp_app_secret,
            })
        elif settings.whatsapp_provider == "kapso":
            required.update({
                "WHATSAPP_API_KEY": settings.whatsapp_api_key,
            })
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise SettingsError(
                "Missing required production configuration: " + ", ".join(missing)
            )

    if settings.whatsapp_send_mode not in {"dry_run", "live", "off"}:
        raise SettingsError("WHATSAPP_SEND_MODE must be one of: dry_run, live, off")

    if not settings.whatsapp_catalog_commands:
        raise SettingsError("WHATSAPP_CATALOG_COMMANDS must include at least one command")

    if not settings.whatsapp_greeting_commands:
        raise SettingsError("WHATSAPP_GREETING_COMMANDS must include at least one command")

    if not settings.whatsapp_checkout_commands:
        raise SettingsError("WHATSAPP_CHECKOUT_COMMANDS must include at least one command")

    if not settings.whatsapp_confirm_commands:
        raise SettingsError("WHATSAPP_CONFIRM_COMMANDS must include at least one command")

    if not settings.whatsapp_reject_commands:
        raise SettingsError("WHATSAPP_REJECT_COMMANDS must include at least one command")

    if settings.shipping_fee < 0:
        raise SettingsError("SHIPPING_FEE must be >= 0")

    if settings.free_shipping_threshold < 0:
        raise SettingsError("FREE_SHIPPING_THRESHOLD must be >= 0")

    if not settings.whatsapp_cancel_commands:
        raise SettingsError("WHATSAPP_CANCEL_COMMANDS must include at least one command")

    if settings.pop_expiry_hours < 1:
        raise SettingsError("POP_EXPIRY_HOURS must be >= 1")

    settings.local_sqlite_path.parent.mkdir(parents=True, exist_ok=True)

