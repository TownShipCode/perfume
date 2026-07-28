# Zen Fragrances — Outstanding Fixes

**Generated:** 2026-07-28 · **Source:** Full security + UX audit

---

## ✅ Week 1 Fixes — COMPLETED

| # | Fix | Status |
|---|------|:---:|
| 1 | Add `GET /api/products/{id}` route | ✅ |
| 2 | Fix `get_customer_by_email()` function | ✅ |
| 3 | Rename 013_yoco.sql → 014_yoco.sql | ✅ |
| 4 | Apply `auth_rate_limit` to login/register | ✅ |
| 5 | Fix `_adjust_stock` NULL guard → stock always tracked | ✅ |
| 6 | Fix stock race condition (prevent negative stock) | ✅ |
| 7 | Fix Yoco SQLite crash (add database.mode branching) | ✅ |
| 8 | Add `customers.email` index + UNIQUE constraint | ✅ |

---

## 🔴 Week 2 — Security (Must Fix)

| # | What | File | Fix |
|---|------|------|-----|
| S1 | Token in localStorage — XSS vector | `web/src/api.js:4` | HttpOnly cookies set by backend |
| S2 | DASHBOARD_API_KEY exposed in wiki | `wiki/status.md:4` | Remove from wiki |
| S3 | No password confirmation on register | `web/src/pages/Register.jsx` | Add `confirmPassword` field |
| S4 | Recovery PIN shown in plain text | `web/src/pages/RegisterAgent.jsx:27` | Mask or show once with warning |
| S5 | Hardcoded WhatsApp numbers | `web/src/pages/ProductDetail.jsx:17`, `Layout.jsx:37` | Move to env/config |
| S6 | No CSP headers, X-Content-Type-Options, X-Frame-Options | `main.py` middleware | Add security headers |
| S7 | `/api/health` reads DB state — violates wiki pattern | `main.py:115` | Make DB-independent |
| S8 | No ErrorBoundary wrapping React app | `web/src/App.jsx` | Add ErrorBoundary component |

## 🟠 Week 3 — Resilience (Should Fix)

| # | What | Fix |
|---|------|-----|
| R1 | Outbound message failures silently lost | Add dead-letter queue / retry |
| R2 | `handle_text_message` no try/except | Wrap in try/except, classify transient errors |
| R3 | Manufacturer dashboard wrong API URL | Use `PUT /api/orders/${id}/status` |
| R4 | Admin dashboard stats key mismatch | Fix `total_revenue` → `revenue` |
| R5 | No forgot-password flow | Add reset via email |
| R6 | `ProductInput` missing `gender/scent_family/top_notes/stock_quantity` | Update Pydantic model |

## 🟡 Week 4 — UX + Polish

| # | What | Fix |
|---|------|-----|
| U1 | No debounce on catalogue search | Add 300ms debounce |
| U2 | `alert()` for errors in dashboard | Use inline error display |
| U3 | API base URL hardcoded to `biomed-production` | Use `VITE_API_URL` env var everywhere |
| U4 | Template body no length limit | Add validation |
| U5 | No onboarding for new agents | Add welcome guide / first steps |
| U6 | No "reseller kit" download in agent dashboard | Build Phase 11 feature |

## 🔵 Accessibility

| # | What |
|---|------|
| A1 | No skip-to-content link |
| A2 | No aria-label on nav links |
| A3 | No focus-visible styles |
| A4 | No lang attribute in index.html |

## 🔮 Future (Phase 2+)

| # | What |
|---|------|
| F1 | Multi-tenant org_id (before second brand) |
| F2 | API versioning (/v1/ prefix) |
| F3 | LLM: product recommendations engine |
| F4 | LLM: natural language order intent |
| F5 | Customer purchase history analytics |
| F6 | JSONB product attributes (scent notes, longevity) |
| F7 | Audit log table |
| F8 | Soft-delete (archived_at) pattern |

---

## Tags

#outstanding #fixes #audit #zen-fragrances
