# BioMed

WhatsApp Order Platform backend scaffold for low-literacy customer ordering over WhatsApp.

## Current Scope

- product catalog API
- keyword-based order parsing
- webhook verification and signature checking
- cart and session persistence
- guided address collection
- order creation and POP receipt handling
- admin read/update service layer for orders and customers
- template-driven customer reply generation for webhook actions
- React/Vite dashboard scaffold for orders, products, and customers
- manufacturer forwarding endpoint and dashboard action with forwarding audit metadata
- template admin endpoints and dashboard editing for customer/manufacturer message bodies

## Local Setup

1. Create a local env file from `.env.example`.
2. Use the existing virtual environment at `.venv`.
3. Install the backend package:

```powershell
.\.venv\Scripts\python -m pip install -e .\backend pytest
```

4. Run the test suite:

```powershell
.\.venv\Scripts\python -m pytest backend\tests
```

5. Start the API:

```powershell
$env:PYTHONPATH = "C:\Users\Sanel\Desktop\BioMed\backend"
.\.venv\Scripts\python -m uvicorn src.main:app --host 127.0.0.1 --port 8000
```

6. Verify health:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

## Secrets

- keep `.env` local only
- `.gitignore` excludes `.env`, `.venv`, local DB files, and Python caches
- production secrets must be supplied through environment variables

## WhatsApp Delivery Modes

- `WHATSAPP_SEND_MODE=dry_run` returns composed outbound payloads without calling the provider
- `WHATSAPP_SEND_MODE=live` sends replies to the configured provider endpoint
- `WHATSAPP_SEND_MODE=off` disables outbound delivery while preserving backend state changes
- `WHATSAPP_GREETING_COMMANDS` controls which greeting messages return the welcome catalogue
- `WHATSAPP_CATALOG_COMMANDS` controls which inbound customer commands show the product catalogue
- `WHATSAPP_CHECKOUT_COMMANDS` controls which words trigger checkout from the cart
- `WHATSAPP_CONFIRM_COMMANDS` controls which words confirm a saved address
- `WHATSAPP_REJECT_COMMANDS` controls which words trigger new address entry

## Admin API Auth

- use `x-api-key: <DASHBOARD_API_KEY>`
- or `Authorization: Bearer <DASHBOARD_API_KEY>`
- if `DASHBOARD_API_KEY` is unset, admin auth is relaxed only in non-production mode
