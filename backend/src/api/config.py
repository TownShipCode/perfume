from fastapi import APIRouter

from src.config import get_settings

router = APIRouter(prefix="/api", tags=["config"])


@router.get("/config")
async def get_public_config() -> dict:
    """Public site configuration so the frontend never hardcodes business values."""
    settings = get_settings()
    return {
        "store_name": settings.store_name,
        "store_currency": settings.store_currency,
        "shipping_fee": str(settings.shipping_fee),
        "free_shipping_threshold": str(settings.free_shipping_threshold),
        "courier_fee": str(settings.courier_fee),
        "commission_percent": str(settings.commission_percent),
        "payment_methods_enabled": list(settings.payment_methods_enabled),
        "bank_name": settings.bank_name,
        "account_holder": settings.account_holder,
        "web_base_url": settings.web_base_url,
    }
