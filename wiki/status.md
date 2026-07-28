# Zen Fragrances — Project Status

**2026-07-28** · 25 tests passing · 15 migrations · Web cart + WhatsApp flow complete

## Platform Summary

```
                    WEB STORE                      WHATSAPP
                    (everyone)                     (agents only)
                    ──────────                     ────────────
                    
Browse:      ✅ Catalogue (scent/gender filters)   ❌ (web only)
Cart:        ✅ Add to Cart from grid/detail       ✅ Type "5 Rose Oud" → confirm
Checkout:    ✅ Address form → Yoco/EFT             ✅ Address prompts → POP
Repeat:      ❌ (use Quick Order)                   ✅ "repeat" restores last order
Discovery:   ✅ Blog (5 SEO articles)               ✅ "help" + web link
Agents:      ✅ Agent Locator (suburb search)       ✅ "join / recover / agent"
Dashboard:   ✅ Admin / Mfg / Team / Agent          ❌ (web only)
```

## Today's Session (2026-07-28) — Complete Rebuild

### Branding & Cleanup
- All BioMed references removed → Zen Fragrances
- Config renamed: `fl_username=ZenFragrances`, `account_holder=Zen Fragrances`, `bio_med_email→store_email`
- Wiki: 6 files updated, pricing model corrected (wholesale + agent markup + 5% team commission)

### WhatsApp Flow Redesign
- Catalogue text wall replaced with web store link
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
| Agent referral (WhatsApp command) | Done |
| Order confirmation step | Done |
| Repeat last order | Done |
| Stock management (atomic decrement, low stock threshold) | Done |
| Payment (Yoco checkout + webhook, EFT + POP) | Done |
| Competitor price monitoring | Done |
| Blog (5 SEO articles) | Done |
| Quick Order (grid + bulk WhatsApp send) | Done |
| Manufacturer forwarding (Focus Logic format) | Done |
| Rate limiting (4 tiers: webhook, public, auth, dashboard, yoco) | Done |
| Security headers (CSP, HSTS, X-Frame-Options) | Done |
| Dual DB (Postgres/SQLite for local dev) | Done |
| 25 tests passing | Done |

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
FL_USERNAME=ZenFragrances
```

## Pending for Launch

- [ ] Product data (99 SKU CSV → seed script)
- [ ] WhatsApp credentials + `MANUFACTURER_PHONE` + `WHATSAPP_APP_SECRET` in Railway
- [ ] Deploy web store to Vercel (`web/dist/` ready, 300KB)
- [ ] Set `WEB_BASE_URL` in Railway
- [ ] Switch `WHATSAPP_SEND_MODE=live` and `APP_ENV=production`
- [ ] Configure Meta WhatsApp catalog → set `WHATSAPP_CATALOG_ID`
- [ ] Enable GitHub security settings (6 from blog post)
- isiZulu template translations (17 templates need text)
- Sentry error tracking (DSN available, not configured)
- `APP_ENV=production` (after MANUFACTURER_PHONE and APP_SECRET are set)

