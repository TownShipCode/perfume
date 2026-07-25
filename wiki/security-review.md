# BioMed — Security Review & Best Practices

**2026-07-24**

## Current Security Posture

### Authentication
| Layer | Implementation | Status |
|---|---|---|
| Dashboard API key | `x-api-key` header or `Authorization: Bearer` | ✅ Active |
| Session cookies | HttpOnly `session_token` cookie (wiki auth pattern) | ✅ Supported |
| Webhook signature | HMAC-SHA256 via `x-hub-signature-256` header | ✅ Active |
| Rate limiting | In-memory sliding window: 60 req/min per IP on webhook | ✅ Active |
| Production gate | `APP_ENV=production` tightens verification | ⚠️ Not yet enabled |

### Endpoint Auth Coverage
| Endpoint | Auth | Risk |
|---|---|---|
| `GET /health` | None | Low — public health check |
| `GET /api/products` | None | Low — public catalog, read-only |
| `GET /api/orders` | `require_dashboard_api_key` | ✅ |
| `POST /api/products` | `require_dashboard_api_key` | ✅ |
| `PUT /api/products/{id}` | `require_dashboard_api_key` | ✅ |
| `DELETE /api/products/{id}` | `require_dashboard_api_key` | ✅ |
| `GET /api/customers` | `require_dashboard_api_key` | ✅ |
| `PUT /api/customers/{phone}/address` | `require_dashboard_api_key` | ✅ |
| `POST /api/orders/{id}/forward` | `require_dashboard_api_key` | ✅ |
| `POST /api/orders/{id}/fl-pop` | `require_dashboard_api_key` | ✅ |
| `POST /api/orders/{id}/fl-pop/confirm` | `require_dashboard_api_key` | ✅ |
| `GET /api/analytics/*` | `require_dashboard_api_key` | ✅ |
| `GET /api/templates` | `require_dashboard_api_key` | ✅ |
| `PUT /api/templates/{key}` | `require_dashboard_api_key` | ✅ |
| `GET /webhook` | None | Low — only verifies challenge |
| `POST /webhook` | HMAC signature + rate limit | ✅ |

### Rate Limiting
- **Webhook**: 60 requests per minute per IP (in-memory, sliding window)
- **API endpoints**: No rate limiting (dashboard only, low volume)
- **Risk**: In-memory limiter resets on deploy. Consider Redis for multi-instance.

### Idempotency
- **Message dedup**: `processed_messages` table by `message_id` — prevents double-processing on Kapso retry
- **Forward dedup**: `forward_delivery_status` check — prevents double-forward to manufacturer

### Data Exposure
- **Database URL**: In `.env` only, not committed (via `.gitignore`)
- **API keys**: Environment variables only, never in code
- **Customer PII**: Phone numbers, names, addresses in PostgreSQL — Railway-managed

## Recommendations

### 🔴 High Priority
1. **Enable `APP_ENV=production`** after WhatsApp keys are set
2. **Verify `DASHBOARD_API_KEY` on Railway** matches local `.env`
3. **Set `WHATSAPP_VERIFY_TOKEN` and `WHATSAPP_APP_SECRET`** on Railway

### 🟠 Medium Priority
4. **Add Sentry error tracking** — DSN available, not configured
5. **Add HTTPS redirect** — Railway handles this, but verify
6. **Rotate API keys periodically** — plan for key rotation
7. **Add request logging** — currently only error logging via `logger`

### 🟡 Low Priority
8. **Redis rate limiting** — for multi-instance deploys
9. **API key scoping** — separate keys for different dashboard roles
10. **Audit log** — who forwarded which order, when

## Questions to Address

| # | Question |
|---|---|
| Q1 | Is the MANUFACTURER_PHONE shared with FL? Any privacy concerns? |
| Q2 | Should customer POP images be stored in Vercel Blob (CDN) vs as raw URLs? |
| Q3 | Do we need multi-user dashboard access (different admin roles)? |
| Q4 | What's the data retention policy for customer orders/addresses? |
| Q5 | Should we encrypt customer PII at rest (postal_code, email, phone)? |
| Q6 | What happens if Kapso API is down? Do we need a retry queue? |
