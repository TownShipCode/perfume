#!/usr/bin/env python3
"""Zen Fragrances — Startup Configuration Check

Run before deploying to production:
  python startup_check.py

Exits with code 0 if all checks pass, 1 if any critical checks fail.
"""
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))


def check(ok: bool, label: str, severity: str = "error"):
    icon = "[PASS]" if ok else ("[WARN]" if severity == "warn" else "[FAIL]")
    print(f"  {icon} {label}")
    return ok


def main():
    errors = 0
    warnings = 0

    print("=" * 60)
    print("Zen Fragrances — Startup Configuration Check")
    print("=" * 60)

    # ── 1. Environment Variables ──
    print("\n[ENV] Environment Variables")
    required = {
        "DASHBOARD_API_KEY": os.getenv("DASHBOARD_API_KEY"),
        "DATABASE_URL": os.getenv("DATABASE_URL"),
    }
    for key, val in required.items():
        if check(bool(val), f"{key} is set"):
            pass
        else:
            errors += 1

    optional = {
        "WHATSAPP_API_KEY": os.getenv("WHATSAPP_API_KEY"),
        "WHATSAPP_PHONE_NUMBER_ID": os.getenv("WHATSAPP_PHONE_NUMBER_ID"),
        "WHATSAPP_APP_SECRET": os.getenv("WHATSAPP_APP_SECRET"),
        "WHATSAPP_VERIFY_TOKEN": os.getenv("WHATSAPP_VERIFY_TOKEN"),
        "MANUFACTURER_PHONE": os.getenv("MANUFACTURER_PHONE"),
        "YOCO_SECRET_KEY": os.getenv("YOCO_SECRET_KEY"),
        "YOCO_WEBHOOK_SECRET": os.getenv("YOCO_WEBHOOK_SECRET"),
    }
    for key, val in optional.items():
        if not check(bool(val), f"{key} is set", "warn"):
            warnings += 1

    # ── 2. Config Validation ──
    print("\n[CONFIG] Configuration")
    try:
        from src.config import get_settings
        settings = get_settings()
        check(settings.store_name != "Example Store", f"STORE_NAME is set: {settings.store_name}")
        check(settings.whatsapp_provider in ("kapso", "meta"), f"WHATSAPP_PROVIDER: {settings.whatsapp_provider}")
        check(settings.whatsapp_send_mode in ("dry_run", "live", "off"), f"WHATSAPP_SEND_MODE: {settings.whatsapp_send_mode}")
        check(settings.courier_fee >= 0, f"COURIER_FEE: R{settings.courier_fee}")
        check(settings.commission_percent >= 0, f"COMMISSION_PERCENT: {settings.commission_percent}%")

        if settings.whatsapp_send_mode == "live":
            if not check(bool(settings.whatsapp_api_key), "WHATSAPP_API_KEY is set for live mode", "error"):
                errors += 1
            else:
                pass
        else:
            check(True, f"Send mode '{settings.whatsapp_send_mode}' — safe for testing")

        if settings.app_env == "production":
            check(settings.whatsapp_verify_token is not None, "WHATSAPP_VERIFY_TOKEN set for production")
            check(settings.whatsapp_app_secret is not None, "WHATSAPP_APP_SECRET set for production")
            check(settings.dashboard_api_key is not None, "DASHBOARD_API_KEY set for production")
        else:
            check(True, f"APP_ENV='{settings.app_env}' — relaxed security")

    except Exception as e:
        print(f"  [FAIL] Config failed: {e}")
        errors += 1

    # ── 3. Security Headers (production only) ──
    print("\n[SEC] Security")
    check(os.getenv("APP_ENV") != "production" or os.getenv("ENFORCE_HTTPS") == "true",
          "ENFORCE_HTTPS=true in production", "warn")
    check(not os.getenv("DASHBOARD_API_KEY") or len(os.getenv("DASHBOARD_API_KEY", "")) > 12,
          "DASHBOARD_API_KEY > 12 chars", "warn")

    # ── 4. Database Connection ──
    print("\n[DB] Database")
    try:
        import asyncio
        from src.db.connection import connect_database, close_database, initialize_database

        async def test_db():
            db = await connect_database()
            await initialize_database(db)
            check(True, f"Connected: {db.mode}")
            await close_database(db)

        asyncio.run(test_db())
    except Exception as e:
        print(f"  [FAIL] DB connection failed: {e}")
        errors += 1

    # ── 5. Migration Count ──
    print("\n[MIG] Migrations")
    migrations_dir = PROJECT_ROOT / "backend" / "src" / "db" / "migrations"
    migration_files = sorted(f.name for f in migrations_dir.glob("*.sql"))
    check(len(migration_files) >= 14, f"{len(migration_files)} migration files found (expected >= 14)")

    # Detect duplicate version prefixes
    prefixes = [f[:3] for f in migration_files if f[0].isdigit()]
    duplicates = [p for p in prefixes if prefixes.count(p) > 1]
    for dup in set(duplicates):
        check(False, f"Duplicate migration prefix: {dup}", "error")
        errors += 1

    # ── 6. Static Files ──
    print("\n[FILE] Static Files")
    static_dir = PROJECT_ROOT / "backend" / "static"
    check(static_dir.is_dir(), "backend/static/ directory exists", "warn")

    # ── 7. Web Store Build ──
    print("\n[WEB] Web Store")
    web_dist = PROJECT_ROOT / "web" / "dist" / "index.html"
    if web_dist.exists():
        check(True, "web/dist/ build exists")
    else:
        check(False, "web/dist/ not built — run: cd web && npm run build", "warn")
        warnings += 1

    # ── Summary ──
    print("\n" + "=" * 60)
    if errors == 0 and warnings == 0:
        print("[OK] All checks passed - ready to deploy!")
    elif errors == 0:
        print(f"[WARN] {warnings} warning(s) - safe to deploy but review above")
    else:
        print(f"[FAIL] {errors} error(s), {warnings} warning(s) - fix errors before deploying")

    return 1 if errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main())

