# BioMed — Project Status

**2026-07-25** · 25 tests passing · 11 migrations · Phases 1–4 deployed · Live testing

## Wiki Index

| Document | Description |
|---|---|
| [status.md](status.md) | Project overview, features, config |
| [e2e-test-results.md](e2e-test-results.md) | End-to-end API test results against live Railway |
| [security-review.md](security-review.md) | Auth, rate limiting, endpoint coverage, recommendations |
| [retrospective.md](retrospective.md) | What worked, challenges, questions we should have asked, Kapso debugging post-mortem |
| [kapso-debugging.md](kapso-debugging.md) | Kapso webhook format guide, common mistakes, CLI reference |
| [adding-products.md](adding-products.md) | How to add products: seed script, dashboard, or API |

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
| Address collection (7-step: surname, area, street, city, postal_code, email, province) | Done |
| POP handling + expiry (24h) + order cancellation | Done |
| Admin API (orders, customers, products, templates) | Done |
| Dashboard (React/Vite) with manufacturer msg display | Done |
| Manufacturer forwarding (Focus Logic format) + two-message send | Done |
| FL POP upload + auto-forward (two-POP model) | Done |
| Dashboard FL POP upload + preview + confirm UI | Done |
| Product margin (per-product `bio_med_margin`) | Done |
| All commands configurable (env-driven, no hardcoding) | Done |
| WhatsApp catalogue/menu + greet/welcome + info command | Done |
| Language infrastructure (en/zu, DB-backed templates) | Done |
| Railway deploy (Docker + PostgreSQL) | Done |
| Vercel dashboard deploy | Done |
| Atomic idempotency (race condition fix) | Done |
| Language code guard (en/zu outside selection state) | Done |
| Product image serving (/static via FastAPI) | Done |
| Railway Railpack config (Root Directory = backend) | Done |

## Config

```env
DASHBOARD_API_KEY=bmd-7xp3kqm9wf2rhn8vd4lj
SHIPPING_FEE=109.00
FREE_SHIPPING_THRESHOLD=2000.00
WHATSAPP_SEND_MODE=dry_run
POP_EXPIRY_HOURS=24
DEFAULT_LANGUAGE=en
SUPPORTED_LANGUAGES=en,zu
AUTO_FORWARD_TO_MANUFACTURER=true
DEFAULT_MARGIN=70.00
COURIER_FEE=150.00
COURIER_NAME=The Courier Guy
FL_USERNAME=BioMed_SA
```

## Pending

- WhatsApp credentials + `MANUFACTURER_PHONE` + `WHATSAPP_APP_SECRET` (set in Railway Dashboard)
- **Live test**: verify the atomic dedup + language guard fixes work end-to-end
- isiZulu template translations (17 templates need text)
- Sentry error tracking (DSN available, not configured)
- `APP_ENV=production` (after MANUFACTURER_PHONE and APP_SECRET are set)

