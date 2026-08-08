# Zen Fragrances — Architecture Reference

**2026-07-29** · For future sessions / new developers

## Stack

| Layer | Tech |
|---|---|
| Backend | Python 3.12, FastAPI, asyncpg (Postgres), sqlite3 (local dev) |
| Database | PostgreSQL on Railway, SQLite for local testing |
| WhatsApp | Kapso gateway → Meta Cloud API v24.0 |
| Web Store | React 19 + Vite 7 + Tailwind CSS, deployed on Vercel |
| Payments | Yoco Checkout API + EFT / POP |
| Deploy | Railway (backend, auto-deploy from GitHub), Vercel (web store) |

## Two-Channel Architecture

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│  WHATSAPP    │────▶│   FASTAPI        │◀────│  WEB STORE   │
│  (agents)    │     │   (same DB)      │     │  (everyone)  │
└──────────────┘     └──────────────────┘     └──────────────┘
                            │
                     ┌──────┴──────┐
                     │  PostgreSQL │
                     │  (Railway)  │
                     └─────────────┘
```

## Key Files — Current

| File | Purpose |
|---|---|
| `src/main.py` | FastAPI app, lifespan, security headers, all routers |
| `src/config.py` | `Settings` dataclass — 40+ env vars, `@lru_cache` |
| `src/api/webhook.py` | WhatsApp webhook — signature verify, event extract, idempotency |
| `src/api/orders.py` | Order API + `POST /api/orders/web` (web checkout) |
| `src/api/products.py` | Product search, categories, scents, detail |
| `src/api/auth.py` | Login, register, forgot password |
| `src/api/agent_tools.py` | Price list PDF, agent locator search, profile |
| `src/services/order_flow.py` | `handle_text_message()` — state router, all WhatsApp commands |
| `src/services/order_service.py` | `create_order()`, stock management, POP, shipping |
| `src/services/message_templates.py` | `build_customer_reply()` — all action → reply mappings |
| `src/services/whatsapp_buttons.py` | Welcome, confirm, cart, quantity, payment buttons |
| `src/services/catalog_service.py` | Products, keywords, search, pagination |
| `src/services/yoco_payment.py` | Yoco checkout + webhook |
| `src/db/connection.py` | Dual Postgres/SQLite, `_sqlite_compat()` DDL translator |
| `scripts/e2e_test.py` | 42-check e2e: WhatsApp + Web + Cross-Channel |

## WhatsApp Commands

| Command | Action |
|---|---|
| `hi`, `hello` | Welcome with [🛍️ Browse Store] [🛒 View Cart] [ℹ️ Help] |
| `5 Rose Oud` | Parse → confirm → add to cart |
| `cart` | Cart summary with [➕ Add More] [🛒 Checkout] |
| `checkout`, `done` | Address collection → order creation |
| `repeat`, `reorder` | Restore last order to cart |
| `stock 1` | Check stock for product #1 |
| `info 1` | Product detail with image + web link |
| `menu`, `catalogue` | **PDF flyer** + web store link (no text wall) — agents share/print the PDF as their catalogue |
| `price list` | Agent wholesale price list URL |
| `agent`, `become an agent` | Agent referral pitch + register link |
| `join AGENT123` | Join under a team member |
| `recover AGENT123` | Lost number recovery |
| `cancel` | Cancel current order |
| `help`, `?` | Web link + quick reference |

## Visit Store Link — Placement Strategy (2026-08-08)

**Rule:** the "Visit Store" web link appears at every *decision point*, never mid-action.

| Priority | Touchpoint | Status | Why |
|---|---|---|---|
| 🏆 Primary | **Welcome message** — `[🛍️ Visit Store]` button (first CTA) | ✅ exists (as "Browse Store") | Front door — seen on every new conversation (agent or consumer) |
| 🥈 Add | **After checkout / order confirmed** | ❌ missing | Repeat/upsell moment — append "browse for your next order" |
| 🥉 Keep | **Product not found / out of stock** | ✅ exists | Recovery — don't lose the sale, redirect to store |
| On-demand | `menu`/`catalogue`, empty cart, `help` | ✅ exists | Explicit request |

**Do NOT place:** during address collection / mid-order (don't interrupt an active purchase), or in the confirm-before-cart prompt (keep it focused).

The link lives at: welcome (front door) → product-not-found (recovery) → post-checkout (upsell) → on-demand (`menu`/`help`).

**IMPLEMENTED 2026-08-08 — all store links are click-through URL buttons, NO raw URLs in text:**
- `whatsapp_buttons.py`: `build_welcome_buttons(body, web_url)` — first button is now `type: url` "🛍️ Visit Store"; new `build_visit_store_buttons(body, web_url)` helper
- `message_templates.py`: new `_visit_store_reply()` helper; `catalogue_web`, `checkout_blocked`, `product_not_found`, `help_menu` all return interactive URL-button replies (fallback_text keeps URL only if interactive send fails); `product_detail` sends text/image + a URL-button follow-up
- `order_flow.py`: `help` → `help_menu` action (URL button); WhatsApp-catalog fallback (no catalog_id) → `catalogue_web`; greeting path passes `web_url`
- **Meta Cloud API URL buttons** (`type: url`) open the browser directly when tapped — true click-through, unlike reply buttons which only webhook back.
- ⚠️ **EXCEPTION — WhatsApp Catalog link (`wa.me/c/...`) stays a TEXT link, NOT a URL button** (2026-08-08):
  - URL buttons CANNOT be forwarded/shared; text links can (customer shares catalog to others)
  - `wa.me/c/...` auto-hyperlinks in WhatsApp → already a click-through link
  - opens INSIDE WhatsApp (data-friendly), not the external browser
  - `catalog_link` reply: text + "_Tap to open, or forward to share with customers._"
- Tests updated: `test_order_flow.py` asserts URL buttons + reply buttons. 23 tests passing.

## Request Flow (WhatsApp message)

```
WhatsApp → Meta → Kapso → Railway /webhook (POST)
                              │
                    verify_signature()
                    extract_message_event()
                    try_claim_message()       ← idempotency gate
                              │
                    handle_text_message()     ← state machine routing
                    handle_image_message()    ← POP handling
                              │
                    build_customer_reply()    ← returns dict or list[dict]
                              │
                    BackgroundTasks           ← fire-and-forget
                    _deliver_reply_safe()
                    deliver_reply()           ← text / image / interactive
                              │
                    send_*_kapso() / send_*_meta()
                              │
                         WhatsApp ← Kapso ← BioMed
```

## State Machine

```
LANGUAGE_SELECTION (disabled, auto-migrates to IDLE)
  → IDLE
    → ORDERING (product selected, waiting for quantity)
    → ADDRESS_COLLECTION (7 sequential prompts: name, surname, area, street, city, postal_code, province)
    → ADDRESS_CONFIRMATION (existing customers — Yes/No interactive buttons)
    → POP_WAITING (order created, waiting for POP image)
    → CONFIRMED (POP received)
```

## Key Files

| File | Purpose |
|---|---|
| `src/main.py` | FastAPI app, lifespan (DB init, background expiry task) |
| `src/config.py` | `Settings` dataclass — all env vars, frozen, `@lru_cache` |
| `src/api/webhook.py` | WhatsApp webhook endpoint — signature verify, event extract, route to handlers |
| `src/services/order_flow.py` | `handle_text_message()` — main state router, `ADDRESS_STEPS`, escape hatches |
| `src/services/message_templates.py` | `DEFAULT_TEMPLATES` dict + `build_customer_reply()` — returns dict or list |
| `src/services/whatsapp_sender.py` | `deliver_reply()`, `send_text_message()`, `send_image_message()`, `send_interactive_message()` |
| `src/services/whatsapp_buttons.py` | `build_welcome_buttons()`, `build_quantity_buttons()`, `build_cart_buttons()`, `build_confirm_buttons()` |
| `src/services/catalog_service.py` | `build_catalog_lines()` (clean one-liner: `🫖 *1.* Product — R330`), `get_product_by_number()` |
| `src/services/manufacturer_forwarding.py` | Manufacturer form — sends text + POP image to `MANUFACTURER_PHONE` |
| `src/services/customer_service.py` | `save_customer_profile()` (7 fields), `save_customer_address()` (backward compat wrapper) |
| `src/services/order_service.py` | POP recording, `update_order_status()`, `cancel_pending_pop_order()` |
| `src/db/connection.py` | Dual Postgres/SQLite — `fetch_all`, `fetch_one`, `execute`, `_sqlite_compat()` DDL translator |

## Message Reply Format

`build_customer_reply()` returns:
- `{"text": "..."}` — plain text message
- `{"text": "...", "image_url": "..."}` — image with text caption
- `{"type": "interactive", "payload": {...}, "fallback_text": "..."}` — interactive buttons
- `[dict1, dict2]` — list of messages (e.g. image then buttons)

## Config Env Vars (key ones)

| Var | Default | Purpose |
|---|---|---|
| `WHATSAPP_SEND_MODE` | `dry_run` | `off` / `dry_run` / `live` |
| `WHATSAPP_PROVIDER` | `kapso` | `kapso` or `meta` |
| `WHATSAPP_API_KEY` | — | Kapso or Meta API key |
| `WHATSAPP_PHONE_NUMBER_ID` | `1235032529693241` | Meta phone ID |
| `MANUFACTURER_PHONE` | — | Manufacturer WhatsApp number |
| `AUTO_FORWARD_TO_MANUFACTURER` | `true` | Auto-forward on manufacturer POP upload |
| `COURIER_NAME` | `The Courier Guy` | Manufacturer form COURIER field |
| `COURIER_FEE` | `150.00` | Shipping fee per order |
| `MFG_USERNAME` | — | Manufacturer form username field |
| `WHATSAPP_CATALOG_ID` | — | Meta catalog ID (not yet configured) |
| `WHATSAPP_QUANTITY_OPTIONS` | `1,2,3,4,5,6` | Comma-separated quantity button values |

## Database Migrations (12 total)

| # | File | What |
|---|---|---|
| 001 | `_schema_migrations` table | Migration tracking |
| 002 | `customers`, `products`, `orders`, `sessions`, `message_templates` | Core tables |
| 003 | `forwarded_to`, `forwarded_at` on orders | Manufacturer forwarding |
| 004 | `forward_delivery_status`, `forward_attempts` on orders | Forward audit |
| 005 | `shipping_fee`, `tracking_info` on orders | Shipping |
| 006 | `description` on products | Product detail |
| 007 | `language` on customers | Multi-language |
| 008 | `admin_sessions` table | Dashboard auth |
| 009 | `surname`, `postal_code`, `email`, `province` on customers | Profile fields |
| 010 | `bio_med_margin` on products | Margin tracking |
| 011 | manufacturer POP fields on orders | POP (two-POP model) |
| 012 | `thumbnail_url` on products | Multi-channel images |

## Gotchas & Pitfalls

1. **Kapso v2 webhook format** — different from Meta standard. See `kapso-debugging.md`.
2. **Kapso phone format** — sometimes sends without `+` prefix. Webhook normalizes with `^\+?\d{10,15}$`.
3. **SQLite DDL compat** — `_sqlite_compat()` regex translates Postgres types. Fragile — keep migration SQL simple.
4. **Decimal JSON serialization** — use `jsonable_encoder()` for webhook responses containing cart totals.
5. **Railway env vars** — must use commas (not spaces) for list-type vars. `_csv_values` splits by comma.
6. **`build_customer_reply` return types** — can return `dict`, `list[dict]`, or `None`. Webhook handler checks `isinstance(replies, list)`.
7. **Test expectations** — 7-step address flow needs 9 text messages before POP. Image message IDs shift accordingly.
8. **`deliver_reply` is now background** — errors are logged but don't block the webhook response. Check logs for delivery failures.
