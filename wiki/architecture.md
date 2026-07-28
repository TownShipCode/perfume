# Zen Fragrances — Architecture Reference

**2026-07-26** · For future sessions / new developers

## Stack

| Layer | Tech |
|---|---|
| Backend | Python 3.12, FastAPI, asyncpg (Postgres), sqlite3 (local dev) |
| Database | PostgreSQL on Railway, SQLite for local testing |
| WhatsApp | Kapso gateway → Meta Cloud API v24.0, phone_id=1235032529693241 |
| Dashboard | React + Vite, deployed on Vercel |
| Deploy | Railway (backend, auto-deploy from GitHub), Vercel (dashboard) |

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
| `src/services/manufacturer_forwarding.py` | FL 14-field form — sends text + POP image to `MANUFACTURER_PHONE` |
| `src/services/customer_service.py` | `save_customer_profile()` (7 fields), `save_customer_address()` (backward compat wrapper) |
| `src/services/order_service.py` | `record_fl_pop()`, `update_order_status()`, `cancel_pending_pop_order()` |
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
| `MANUFACTURER_PHONE` | — | Focus Logic WhatsApp number |
| `AUTO_FORWARD_TO_MANUFACTURER` | `true` | Auto-forward on FL POP upload |
| `COURIER_NAME` | `The Courier Guy` | FL form COURIER field |
| `COURIER_FEE` | `150.00` | Shipping fee per order |
| `FL_USERNAME` | — | FL form FL USERNAME field |
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
| 011 | `fl_pop_image_url`, `fl_pop_uploaded_at`, `fl_amount` on orders | FL POP (two-POP model) |
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
