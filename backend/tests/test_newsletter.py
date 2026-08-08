from __future__ import annotations

import asyncio
import types

import pytest
from fastapi import HTTPException

from src.api.newsletter import subscribe
from src.config import get_settings
from src.db.connection import close_database, connect_database, initialize_database


class _FakeRequest:
    def __init__(self, database, settings) -> None:
        self.app = types.SimpleNamespace(
            state=types.SimpleNamespace(database=database, settings=settings)
        )


class _Payload:
    def __init__(self, email: str) -> None:
        self.email = email


def test_newsletter_subscribe_and_idempotent(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOCAL_SQLITE_PATH", str(tmp_path / "newsletter.db"))
    get_settings.cache_clear()

    async def scenario() -> None:
        settings = get_settings()
        database = await connect_database(settings)
        try:
            await initialize_database(database)
            req = _FakeRequest(database, settings)

            res = await subscribe(req, _Payload("  Alice@Example.com "))
            assert res["ok"] is True
            assert res["email"] == "alice@example.com"

            # Duplicate is idempotent (no error)
            res2 = await subscribe(req, _Payload("alice@example.com"))
            assert res2["ok"] is True

            with pytest.raises(HTTPException) as exc:
                await subscribe(req, _Payload("not-an-email"))
            assert exc.value.status_code == 422
        finally:
            await close_database(database)

    asyncio.run(scenario())
    get_settings.cache_clear()
