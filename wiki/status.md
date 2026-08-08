# Zen Fragrances — Project Status

**2026-08-08** · 24 tests passing · 15 migrations · Web cart + WhatsApp flow complete · Full GTM + pre-launch strategy documented

## Platform Summary

```
                    WEB STORE                      WHATSAPP
                    (everyone)                     (agents only)
                    ──────────                     ────────────
                    
Browse:      ✅ Catalogue (scent/gender filters)   ✅ PDF flyer (agents share on WA)
Cart:        ✅ Add to Cart from grid/detail       ✅ Type "5 Rose Oud" → confirm
Checkout:    ✅ Address form → Yoco/EFT             ✅ Address prompts → POP
Repeat:      ❌ (use Quick Order)                   ✅ "repeat" restores last order
Discovery:   ✅ Blog (5 SEO articles)               ✅ PDF flyer + "help" + web link
Agents:      ✅ Agent Locator (suburb search)       ✅ "join / recover / agent"
Dashboard:   ✅ 3-tier (Super Admin / Admin-production / Agent)  ❌ (web only)
```

## Session 2026-08-08 — Strategy, Flyer, Tooling (session end)

- **Strategy**: M-Scents researched (13th competitor — 21 KZN stores, R15–R200 price ladder); competitive-geography.md (only overlap = KZN); SWOT + Blue Ocean saved (swot-blue-ocean.md); **GTM Master Plan** (visual mermaid doc); **OWN-BRAND-FIRST** decision (produce under Zen, licensing later); **budget-first launch** (R30 price point, agents 5% off → R28.50, retail ~R60); payment pathways + courier/collection flow; pre-launch plan (8 tracks, gate checklist, weeks −4→0).
- **Build**: click-through **URL buttons** on WhatsApp (no raw URLs in text); **consumer flyer** `GET /flyer` (DB-generated, edition-stamped, gender-grouped); **fixed `create_product`** dropping gender/scent/stock; **Word generator** → `docs/GTM-Strategy-ZenFragrances.docx` (15 sections / 14 tables / 6 charts).
- **Docs added to wiki**: gtm-master-plan, swot-blue-ocean, competitive-geography, launch-plan, distribution-options, flyer-cadence, production-questions, market-entry-strategy. All in index + `/memories/repo/`.

## Today's Session (2026-07-28) — Complete Rebuild

### Branding & Cleanup
- All BioMed references removed → Zen Fragrances
- Config renamed: `account_holder=Zen Fragrances`, `bio_med_email→store_email`
- Wiki: 6 files updated, pricing model corrected (wholesale + agent markup + 5% team commission)

### WhatsApp Flow Redesign
- Catalogue text wall replaced with **PDF flyer + web store link**
- Order confirmation step: [✅ Confirm] [❌ Cancel] before items hit cart
- Product image shown in confirmation prompt
- Streamlined multi-product: type → confirm → type next → checkout
- Cart on demand: `cart` command with line items + buttons
- Quick tips on first item: `stock · cart · checkout · cancel`
- Repeat last order: `repeat` / `reorder` / `same again`
- Web bridge: 🛍️ Browse Store button, web URL in help/product detail/not found
- Agent referral: `agent` / `become an agent` command

### Web Store — 11 Pages
- Landing: correct wholesale pricing, Quick Order CTA, link tiles
- Catalogue: gender chips, scent family filters, Add to Cart buttons
- Product Detail: scent profile card, stock badge, Add to Cart + WhatsApp buttons
- Quick Order: grid with qty ± inputs, floating cart bar, WhatsApp send
- Cart: line items, qty controls, shipping calc, checkout button
- Checkout: address form, Yoco/EFT payment, order creation
- Order Confirmed: success page
- Blog: 5 SEO articles (dupes guide, business 101, EDT vs EDP, top 10 men's, wholesale)
- Agent Locator: suburb search → agent cards with WhatsApp
- Register / Register Agent / Login / Forgot Password
- Dashboards: Admin, Manufacturer, Team, Agent

### Backend
- `POST /api/orders/web` — web checkout endpoint (validates products server-side)
- `GET /api/agent/price-list` — printer-friendly wholesale price list
- `GET /api/agent/search` — agent locator by suburb
- `GET /api/products/scents` — distinct scent families + genders for filters
- `GET /api/products` — `scent_family` query param
- `get_product_by_id` returns all fields (gender, scent, top_notes, stock)
- Migration 015: `suburb`, `is_listed`, `bio`, `profile_image_url` on customers
- `SECURITY.md` with vulnerability reporting policy
- `scripts/monitor_competitors.py` — FFC, Fragrance Boutique, Perfumes for Africa scraper

## Feature Summary

| Feature | Status |
|---------|--------|
| Multi-role (admin, mfg, team, agent, wholesaler, public) | Done |
| WhatsApp ordering (confirmation, cart, checkout, repeat) | Done |
| Web cart + checkout (Yoco/EFT) | Done |
| Product catalog (scent/gender filters, categories) | Done |
| Agent locator (suburb search, public listing) | Done |
| Agent price list (PDF/HTML) | Done |
| Consumer retail flyer (GET /flyer, DB-generated, edition-stamped) | Done |
| Agent referral (WhatsApp command) | Done |
| Order confirmation step | Done |
| Repeat last order | Done |
| Stock management (atomic decrement, low stock threshold) | Done |
| Payment (Yoco checkout + webhook, EFT + POP) | Done |
| Competitor price monitoring | Done |
| Blog (5 SEO articles) | Done |
| Quick Order (grid + bulk WhatsApp send) | Done |
| Manufacturer forwarding (manufacturer format) | Done |
| Rate limiting (4 tiers: webhook, public, auth, dashboard, yoco) | Done |
| Security headers (CSP, HSTS, X-Frame-Options) | Done |
| Dual DB (Postgres/SQLite for local dev) | Done |
| Click-through URL buttons on WhatsApp (no raw URLs) | Done |
| `create_product` persists gender/scent/stock (bug fixed) | Done |
| Consumer retail flyer (GET /flyer) + monthly edition stamp | Done |
| GTM Word doc generator (docs/GTM-Strategy-ZenFragrances.docx) | Done |
| Pre-launch plan (8 tracks, gate checklist) | Done |
| Admin dashboard charts (Flint + Chart.js: revenue line, orders bar) | Done |
| 24 tests passing | Done |

## Config

```env
# Required for production
WHATSAPP_SEND_MODE=live
MANUFACTURER_PHONE=
WHATSAPP_APP_SECRET=
APP_ENV=production
WEB_BASE_URL=https://zenfragrances.vercel.app
STORE_EMAIL=orders@zenfragrances.co.za

# Pricing
SHIPPING_FEE=65.00
FREE_SHIPPING_THRESHOLD=2000.00
COMMISSION_PERCENT=5
COURIER_FEE=65.00
COURIER_NAME=The Courier Guy
MFG_USERNAME=ZenFragrances
```

## Dashboards — 3-tier model (2026-08-08)

Three dashboards, not four. Routes exist for all roles; the product model is **Super Admin → Admin (production) → Agent**, with Team member as an agent sub-role.

| Dashboard | Route | File | Who | Content |
|---|---|---|---|---|
| **Super Admin** | `/dashboard/admin` | `AdminDashboard.jsx` | Owner/operator | Analytics + **Flint charts (revenue line, orders bar)** + management/settings links |
| **Admin (production)** | `/dashboard/manufacturer` | `ManufacturerDashboard.jsx` | Production/manufacturer ops | All orders, confirm POP → mark shipped (production fulfillment) |
| **Agent** | `/dashboard/agent` | `AgentDashboard.jsx` | Reseller agents | Own orders, total sales, pending count, status table |
| *(Team member)* | `/dashboard/team` | `TeamDashboard.jsx` | Agent managers | Their agents + commissions — sub-role of the Agent tier |

Route map (from `web/src/components/DashboardLayout.jsx`): `super_admin → admin`, `manufacturer → manufacturer`, `team_member → team`, `agent → agent`.

**Full role definitions + permissions matrix:** [`roles-permissions.md`](roles-permissions.md)

## Pending for Launch

- [ ] Confirm the **contract manufacturer** can private-label (Zen brand) + hold inventory (launch-critical)
- [ ] Define **Zen own-brand identity**: name/bottle/label/packaging/brand colours
- [ ] Confirm **R30 budget price point + 5% agent discount** mechanics
- [ ] Complete **pre-launch gates** (see gtm-master-plan.md §8): site/WA ready · branding · fast movers · samples/test · activate 50 agents + hawkers · GO LIVE Edition-1
- [ ] Set `FLYER_WHATSAPP` in Railway
- [ ] Product data (20-SKU launch set under Zen brand → seed script)
- [ ] WhatsApp credentials + `MANUFACTURER_PHONE` + `WHATSAPP_APP_SECRET` in Railway
- [ ] Deploy web store to Vercel (`web/dist/` ready, 300KB)
- [ ] Set `WEB_BASE_URL` in Railway
- [ ] Switch `WHATSAPP_SEND_MODE=live` and `APP_ENV=production`
- [ ] Configure Meta WhatsApp catalog → set `WHATSAPP_CATALOG_ID`
- [ ] Enable GitHub security settings (6 from blog post)
- isiZulu template translations (17 templates need text)
- Sentry error tracking (DSN available, not configured)

