from __future__ import annotations

import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = PROJECT_ROOT / "backend"


def check(label: str, condition: bool, detail: str) -> bool:
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}: {detail}")
    return condition


def main() -> int:
    ok = True

    py = sys.version_info
    ok &= check("Python", py >= (3, 11), f"{py.major}.{py.minor}.{py.micro} detected")
    ok &= check("Backend dir", BACKEND_DIR.exists(), str(BACKEND_DIR))
    ok &= check("pyproject", (BACKEND_DIR / "pyproject.toml").exists(), "backend/pyproject.toml")
    ok &= check("Env template", (PROJECT_ROOT / ".env.example").exists(), ".env.example")
    ok &= check(
        "Migration files",
        (BACKEND_DIR / "src" / "db" / "migrations" / "001_schema_migrations.sql").exists()
        and (BACKEND_DIR / "src" / "db" / "migrations" / "002_core_tables.sql").exists(),
        "001_schema_migrations.sql + 002_core_tables.sql",
    )

    required_in_production = [
        "DATABASE_URL",
        "WHATSAPP_API_KEY",
        "WHATSAPP_PHONE_NUMBER_ID",
        "WHATSAPP_VERIFY_TOKEN",
        "WHATSAPP_APP_SECRET",
        "DASHBOARD_API_KEY",
    ]
    app_env = os.getenv("APP_ENV", "development").lower()
    if app_env == "production":
        missing = [name for name in required_in_production if not os.getenv(name)]
        ok &= check("Production env vars", not missing, ", ".join(missing) or "all present")
    else:
        print("[INFO] Development mode detected; production-only env validation skipped")

    if ok:
        print("[PASS] Phase 1 foundation checks passed")
        return 0

    print("[FAIL] Phase 1 foundation checks failed")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
