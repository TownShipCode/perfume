from __future__ import annotations

from src.config import get_settings


def _settings_with(**env) -> None:
    import os
    from src.config import get_settings
    for key, value in env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = str(value)
    get_settings.cache_clear()


def test_live_payment_methods_hides_eft_placeholder_account(monkeypatch) -> None:
    monkeypatch.setenv("PAYMENT_METHODS_ENABLED", "eft")
    monkeypatch.setenv("ACCOUNT_NUMBER", "0000000000")
    monkeypatch.delenv("YOCO_SECRET_KEY", raising=False)
    _settings_with(PAYMENT_METHODS_ENABLED="eft", ACCOUNT_NUMBER="0000000000")
    try:
        settings = get_settings()
        assert settings.live_payment_methods == ()
    finally:
        get_settings.cache_clear()


def test_live_payment_methods_exposes_eft_with_real_account(monkeypatch) -> None:
    monkeypatch.setenv("PAYMENT_METHODS_ENABLED", "eft")
    monkeypatch.setenv("ACCOUNT_NUMBER", "1234567890")
    monkeypatch.delenv("YOCO_SECRET_KEY", raising=False)
    _settings_with(PAYMENT_METHODS_ENABLED="eft", ACCOUNT_NUMBER="1234567890")
    try:
        settings = get_settings()
        assert settings.live_payment_methods == ("eft",)
    finally:
        get_settings.cache_clear()


def test_live_payment_methods_hides_yoco_without_secret(monkeypatch) -> None:
    monkeypatch.setenv("PAYMENT_METHODS_ENABLED", "yoco,eft")
    monkeypatch.setenv("ACCOUNT_NUMBER", "0000000000")
    monkeypatch.delenv("YOCO_SECRET_KEY", raising=False)
    _settings_with(PAYMENT_METHODS_ENABLED="yoco,eft", ACCOUNT_NUMBER="0000000000")
    try:
        settings = get_settings()
        assert settings.live_payment_methods == ()
    finally:
        get_settings.cache_clear()


def test_live_payment_methods_yoco_with_secret(monkeypatch) -> None:
    monkeypatch.setenv("PAYMENT_METHODS_ENABLED", "yoco,eft")
    monkeypatch.setenv("ACCOUNT_NUMBER", "1234567890")
    monkeypatch.setenv("YOCO_SECRET_KEY", "sk_test_123")
    _settings_with(PAYMENT_METHODS_ENABLED="yoco,eft", ACCOUNT_NUMBER="1234567890", YOCO_SECRET_KEY="sk_test_123")
    try:
        settings = get_settings()
        assert set(settings.live_payment_methods) == {"yoco", "eft"}
    finally:
        get_settings.cache_clear()
