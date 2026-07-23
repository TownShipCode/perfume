# BioMed — Project Status

**2026-07-23** · 24 tests passing · Deployed

## URLs

| Service | URL |
|---------|-----|
| API | `https://biomed-production.up.railway.app` |
| Dashboard | `https://biomed-dashboard-five.vercel.app` |
| Repo | `https://github.com/TownShipCode/BioMed` |

## Quick Start

```powershell
# Backend
Set-Location backend
$env:PYTHONPATH = "."
.\.venv\Scripts\python.exe -m uvicorn src.main:app --host 127.0.0.1 --port 8000

# Dashboard
Set-Location dashboard
npm run dev
```

## Config

```env
DASHBOARD_API_KEY=bmd-7xp3kqm9wf2rhn8vd4lj
SHIPPING_FEE=109.00
FREE_SHIPPING_THRESHOLD=2000.00
WHATSAPP_SEND_MODE=dry_run
```

## Architecture

```
WhatsApp → /webhook → order_flow.py (state machine)
                    → catalog_service.py (keyword match)
                    → cart_service.py (cart merge)
                    → order_service.py (persist)
                    → message_templates.py (reply)
                    → whatsapp_sender.py (deliver)

Admin → Vercel dashboard → /api/* → DASHBOARD_API_KEY auth
```

## State Machine

```
idle → ordering → address_collection → address_confirmation → pop_waiting → confirmed
```

## Migrations

| # | Purpose |
|---|---------|
| 001 | Schema tracking |
| 002 | Core tables (products, customers, orders, sessions, templates) |
| 003 | Forwarding audit (forwarded_to, forwarded_at, forward_delivery_status) |
| 004 | Forwarding audit depth (message_id, error, payload, response, attempts) |
| 005 | Shipping fee column |

## Tests

```
24 passed — test_order_flow (7), test_message_templates (3), test_whatsapp_webhook (4),
test_order_parser (3), test_persistence_helpers (2), test_whatsapp_sender (2),
test_admin_services (1), test_catalog_admin (1), test_manufacturer_forwarding (1)
```

## Known Gaps

- WhatsApp credentials not set (user has them, pending entry)
- No real end-to-end test with WhatsApp sandbox
- Dashboard not auto-deploying from GitHub
- Product image hosting not decided yet
- No error alerting/monitoring (Sentry ready but not configured)

## Pre-Mortem Resolutions (2026-07-23)

| Risk | Status |
|------|--------|
| SQLite data loss | Resolved — Railway PostgreSQL provisioned, DATABASE_URL linked |
| WhatsApp webhook unverified | Pending — user has Meta credentials |
| DASHBOARD_API_KEY exposed | Resolved — rotated to `bmd-wz9a...` |
| SHIPPING_FEE not on Railway | Resolved — set to 109.00 |
| No order cancellation | Resolved — `cancel`/`stop` commands, clears cart, resets session |
| No POP expiry | Resolved — `POP_EXPIRY_HOURS=24`, auto-expires stale waiting orders |
| Dashboard missing forward message | Resolved — manufacturer message preview shown in order detail |
| Hardcoded ADDRESS_STEPS | Deferred — prompt text is content, not logic; all commands env-driven |
| Rate limiter only on webhook | Accepted — admin API is authenticated, low risk |
