# Zen Fragrances — Roles & Dashboard Model

**Status:** Current as of 2026-08-08
**Applies to:** `backend/src` (role stored on `customers.role`) + `web/src` (dashboard routing)

---

## 1. Product model: 3 dashboards (not 4)

The user-facing product model is **Super Admin → Admin (production) → Agent**. The
`team_member` route exists but is an **Agent-tier sub-role** (an agent who also recruits
and manages other agents), not a fourth tier.

| # | Dashboard | Route | Component | Who it serves |
|---|---|---|---|---|
| 1 | **Super Admin** | `/dashboard/admin` | `AdminDashboard.jsx` | Owner / operator |
| 2 | **Admin (production)** | `/dashboard/manufacturer` | `ManufacturerDashboard.jsx` | Production / contract-manufacturer ops |
| 3 | **Agent** | `/dashboard/agent` | `AgentDashboard.jsx` | Reseller agents |
| — | *Team member (sub-role)* | `/dashboard/team` | `TeamDashboard.jsx` | Agent managers |

Route map (`web/src/components/DashboardLayout.jsx`):
```
super_admin → admin   ·   manufacturer → manufacturer   ·   team_member → team   ·   agent → agent
```

---

## 2. Role definitions (code value → `customers.role`)

### `super_admin` — Super Admin Dashboard
- **Identity:** The owner/operator (single person or small ops team).
- **Sees:** Whole business — `/api/analytics/summary` (total orders, revenue, active agents, team members) + `/api/analytics/daily` Flint charts (revenue line, orders bar).
- **Does:** Strategic oversight + management/settings links (team members, products, all orders, message templates, configure store).
- **Cannot:** Nothing (top tier).

### `manufacturer` — Admin (production) Dashboard
- **Identity:** The production operator — our contract manufacturer (own-brand-first model) or the ops person running fulfilment.
- **Sees:** All orders (`GET /api/orders`).
- **Does:** Fulfilment state machine — **POP waiting → confirm → mark shipped**; receives forwarded orders (`manufacturer_forward` message format) + POP uploads; agent + total per order.
- **Cannot:** See analytics/Charts, manage products/templates/team (that's Super Admin).

### `agent` — Agent Dashboard
- **Identity:** Reseller agents (R30 wholesale price point, 5% off → R28.50).
- **Sees:** **Own** orders only (`GET /api/orders?agent_code=<own>`), own total sales, pending count, status table.
- **Does:** Share store/flyer, take WhatsApp orders, collect from agent hub / courier.
- **Cannot:** See other agents' data, all orders, analytics, or production controls.

### `team_member` — Team Dashboard (Agent sub-role)
- **Identity:** An agent who also recruits/manages other agents (their `registered_by` links to them).
- **Sees:** Their recruited agents (`GET /api/customers?role=agent` filtered by `registered_by`) + those agents' orders (`GET /api/orders?team_member_id=me`).
- **Does:** Recruit agents (WhatsApp `agent` / `become an agent` command stamps `team_member_id`), earn **5% team commission**.
- **Cannot:** See their agents' orders details? *(frontend lists count + names only; detail access not built)*.

### `customer` — default / public
- **Identity:** WhatsApp buyer or web shopper. No dashboard.
- **Does:** Browse catalogue, buy, become an agent.

### `wholesaler` — planned / hybrid
- Listed in status "Multi-role (admin, mfg, team, agent, wholesaler, public)" — a **bulk-buyer tier** (GTM docx "Wholesalers tier open"): R0 subscription, free-ship, bulk volume. **No dashboard yet** — future Agent-tier variant or separate B2B portal.

---

## 3. Permissions matrix

| Action | `customer` | `agent` | `team_member` | `manufacturer` | `super_admin` |
|---|:---:|:---:|:---:|:---:|:---:|
| Browse store / buy | ✅ | ✅ | ✅ | ✅ | ✅ |
| Agent dashboard (own orders) | — | ✅ | ✅ | — | — |
| Recruit agents / 5% commission | — | — | ✅ | — | — |
| See all orders | — | — | — | ✅ | ✅ |
| Confirm / ship orders (production) | — | — | — | ✅ | ✅ |
| Analytics + Flint charts | — | — | — | — | ✅ |
| Manage products / templates / store | — | — | — | — | ✅ |
| Public APIs (price list, flyer, agent locator, newsletter) | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## 4. Enforcement reality (2026-08-08)

- **Frontend:** Dashboard routing is gated by `ROLE_PATH` in `DashboardLayout.jsx`; `useAuth` redirects unauthenticated → `/login`. Unknown role falls back to `agent` route.
- **Backend:** Endpoints use `require_dashboard_api_key` middleware — **session cookie** (`session_token`, HttpOnly) or `x-api-key`/Bearer fallback. This is **authentication**, not per-role authorization.
- **Role field:** `customers.role` (migration 013) is set on register (`customer`), agent registration (`agent` + `team_member` linkage), and admin/manufacturer seeding. `agent_tools.py` filters `c.role = 'agent'` for the locator.
- **Gap (KNOWN):** Most order/analytics endpoints do **not** yet enforce role-scoped authorization server-side (e.g. any authenticated session could in principle read the full orders list if the endpoint allows it). Agent scoping is by query param (`agent_code`, `team_member_id`) on the client side, not a hard server-side filter tied to the session role.

## 5. Next steps (when roles get hardened)

- [ ] Server-side role guard: enforce `role == 'agent'` → only own `agent_code` orders; `manufacturer`/`super_admin` → all orders
- [ ] `wholesaler` tier: pricing view + bulk order flow (or fold into Agent tier)
- [ ] Super Admin-only guard on `/api/analytics/*`, products, templates, store config
- [ ] Decide Team-member detail access (names+counts today vs full order view)
