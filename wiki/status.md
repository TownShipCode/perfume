# BioMed — Project Status

**2026-07-23** · 25 tests passing · Deployed · 7 migrations

## URLs

| Service | URL |
|---------|-----|
| API | `https://biomed-production.up.railway.app` |
| Dashboard | `https://biomed-dashboard-five.vercel.app` |
| Repo | `https://github.com/TownShipCode/BioMed` |

## Feature Summary

| Feature | Status |
|---------|--------|
| Backend scaffold, config, migrations (7) | Done |
| Product catalog + keyword matching + description | Done |
| Order parsing + cart + shipping (R109, free over R2000) | Done |
| WhatsApp webhook + signature + idempotency + rate limiter | Done |
| Address collection (3-step) + confirmation | Done |
| POP handling + expiry (24h) + order cancellation | Done |
| Admin API (orders, customers, products, templates) | Done |
| Dashboard (React/Vite) with manufacturer msg display | Done |
| Manufacturer forwarding + audit trail | Done |
| All commands configurable (env-driven, no hardcoding) | Done |
| WhatsApp catalogue/menu + greet/welcome + info command | Done |
| Language infrastructure (en/zu, DB-backed templates) | Done |
| Railway deploy (Docker + PostgreSQL) | Done |
| Vercel dashboard deploy | Done |

## Config

```env
DASHBOARD_API_KEY=bmd-wz9a4n2xk7qpf3vc8hjm
SHIPPING_FEE=109.00
FREE_SHIPPING_THRESHOLD=2000.00
WHATSAPP_SEND_MODE=dry_run
POP_EXPIRY_HOURS=24
DEFAULT_LANGUAGE=en
SUPPORTED_LANGUAGES=en,zu
```

## Pending

- WhatsApp credentials (user has them, needs `railway variables set`)
- isiZulu template translations (infrastructure ready, 13 templates need text)
- `APP_ENV=production` after WhatsApp keys are set
- Product image upload (Vercel Blob recommended)
- Sentry error tracking (DSN available, not configured)

