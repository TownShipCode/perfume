# Zen Fragrances — Learnings & Session Log

**Last updated:** 2026-07-29
**Global wiki reference:** [`TownShipCode/wiki`](https://github.com/TownShipCode/wiki)

---

## Key Takeaways from Build (2026-07-24 to 2026-07-29)

### What Worked Well
- **Database abstraction** — Dual Postgres/SQLite via `connection.py` made local testing fast
- **State machine design** — `State` enum made extending flow trivial
- **Template-driven messages** — All replies are DB-backed, editable via dashboard
- **Env-driven config** — Every business rule is an env var, no hardcoded values
- **Fire-and-forget replies** — `BackgroundTasks` cut webhook latency by ~50%
- **Two-channel architecture** — WhatsApp + Web share same DB, orders, stock. No sync needed.
- **Confirmation step** — Catching mis-matches before cart eliminated silent wrong orders
- **Web bridge** — WhatsApp links to web for discovery, WhatsApp for fast reorder. Clean separation.

### Biggest Wastes
- **Kapso webhook debugging: ~3 hours** — Kapso v2 format is different from Meta's. See [kapso-debugging.md](kapso-debugging.md)
- **Inline Python in PowerShell: ~30 min** — Escaping issues. Write `.py` files instead.
- **Railway CLI timeouts: ~20 min** — Use GitHub auto-deploy, not `railway up`
- **Multi-replace tool failures: ~15 min** — `multi_replace_string_in_file` frequently fails. Use individual `replace_string_in_file` instead.

### 2026-07-28/29 Session — Key Decisions
- **WhatsApp = agents only, Web = everyone** — Public buys on web, agents can use both
- **Catalogue on WhatsApp = PDF flyer (2026-08-08 decision)** — text wall removed. `menu`/`catalogue` now sends a shareable, printable PDF flyer + web store link. The PDF is the primary distribution weapon (agents forward it, print as flyers); the web catalogue is the discovery/SEO engine. Discovery is NOT web-only anymore.
- **Confirmation before cart** — "5 Rose Oud at R85 = R425. [✅ Confirm] [❌ Cancel]"
- **Repeat order** — `repeat` command restores last order. Uses `get_products_by_ids` for names.
- **CartItem is Pydantic** — `product_id` not `product_name`. Must look up names from DB.
- **Email UNIQUE constraint** — Empty emails break SQLite. Seed scripts need unique emails.
- **create_product doesn't save new fields** — gender, scent_family, stock_quantity. Use raw SQL or update the function.

### Errors Found & Fixed (2026-07-28/29)
| Error | Root Cause | Fix |
|---|---|---|
| `CartItem` has no `product_name` | Pydantic model only has `product_id`, `quantity` | Look up names via `get_products_by_ids` |
| `Cart` object has no `get` | Cart is a Pydantic model, not dict | Use attribute access: `cart.items`, `cart.total` |
| repeat_order returns text | `get_latest_order` doesn't return `items` field | Use `list_orders` instead |
| UNIQUE constraint on email | Empty string emails collide in SQLite | Seed unique emails per customer |
| Scent families query returns 0 | `create_product` doesn't save gender/scent/stock | Raw SQL for e2e seeding |
| Multi-replace oldString mismatch | Complex patterns with emojis/backticks fail | Use individual replace_string_in_file |

---

## Global Wiki Patterns Applied

These patterns from `TownShipCode/wiki` are baked into this project:

| Pattern | Where Applied |
|---------|--------------|
| **Webhook signature verification** | `src/api/webhook.py` — HMAC-SHA256 |
| **Idempotency keys** | `processed_messages` table — `ON CONFLICT DO NOTHING` |
| **Rate limiting** | `src/middleware/rate_limit.py` — 60 req/min per IP |
| **Healthcheck independence** | `/health` returns without DB dependency |
| **Bootstrap order** | `main.py` lifespan: DB pool → migrations → HTTP + jobs |
| **Migration idempotency** | All migrations use `IF NOT EXISTS` |
| **Env-driven config** | `src/config.py` — frozen dataclass, fail-fast on missing vars |
| **No secrets in code** | All credentials via env vars, `.env` in `.gitignore` |

---

## Session Log

### 2026-08-08 (SESSION END) — Full GTM package complete
This session produced the complete go-to-market package. Key outputs:
- **Strategy**: M-Scents researched (13th competitor — 21 KZN stores, price ladder) → competitive-geography.md; SWOT + Blue Ocean saved (swot-blue-ocean.md); GTM Master Plan (visual mermaid, gtm-master-plan.md); **OWN-BRAND-FIRST** decision; **budget-first launch** (R30, agents 5% off → R28.50, retail ~R60); payment pathways + courier/collection flow; pre-launch gantt + gate checklist (8 tracks, weeks −4→0).
- **Build**: click-through URL buttons on WhatsApp (no raw URLs; wa.me/c link stays shareable text); consumer flyer GET /flyer (DB-generated, edition-stamped); fixed create_product dropping gender/scent/stock (also fixed list_active_products SELECT); docx generator → docs/GTM-Strategy-ZenFragrances.docx (15 sections, 14 tables, 6 charts).
- **Docs**: 8 new wiki files added + all registered in index + mirrored in /memories/repo/. Tests: 24 passing.
- **Next session pre-flight**: read gtm-master-plan.md §8 (pre-launch gates) + status.md pending list. First real tasks: confirm the contract manufacturer private-label + inventory; pick brand colours.

### 2026-08-08 — Competitive Intelligence: M-Scents + Distribution Revisit
- Researched **M-Scents** (m-scents.co.za): branded distributor, 241 products, R15–R200 price ladder, starter packs R800–R3,750, **21 physical stores ALL in KZN**
- M-Scents **Mthatha (EC) store reported but unverified** — not on their store locator. TODO verify.
- Created `wiki/competitive-geography.md`: FFC (national 15 warehouses) vs M-Scents (local 21 KZN stores) — **only overlap = KZN (Durban + PMB)**
- Strategy note: enter **Gauteng townships** first (FFC city-warehouse only, M-Scents absent), Eastern Cape second (both thin; Mthatha signal), avoid KZN (saturated)
- **Zero-capital distribution rule**: model depends on manufacturer holding inventory + dropship. Validate the contract manufacturer holds stock.
- **3-tier brand portfolio decision (CORRECTED 2026-08-08)**: OWN BRAND FIRST — produce + sell under Zen brand from day 1 (contract manufacture); licensing Motala/P2D/Parfumo is LATER/optional, not launch. Own label: Zen Budget (R30–50) / Zen Signature (R80–150) / Zen Premium Oud (R150–200). Full margin, stronger moat; must build Zen brand trust (packaging quality non-negotiable).
- Pre-production market entry questions saved to `/memories/repo/market-entry-questions.md`
- Landing page `/register/agent` enhanced: hero, how-it-works, FFC comparison table, earnings calculator, FAQ
- Created `wiki/production-questions.md`: 27 questions on brand width/perfume types, pricing points, and **store customer profile (dual model: individuals + resellers)** with 7 critical assumptions (incl. township consumers pay R150–300 retail; sizes 15ml–200ml matter; gift sets are high-margin; township/peri-urban is the core engine)
- Created `wiki/launch-plan.md`: 20 SKUs, 3-tier ladder (R30-50 / R80-100 / R150-200), first-wave GP townships then EC. Budget tier = acquisition tool, NEVER shipped solo (courier = 186% of value).
- Created `wiki/distribution-options.md` + folded into `gtm-strategy.md` §4.2: **Option 1 agent-hub** (zero capital; Zen absorbs courier on consolidated ≥R2,000; no-money-handling flow: Hawker→Zen→(commission)→Agent) + **Option 2 DCs** (L1 hub agent R0 → L3 Zen DC R50-150K, revenue-funded). Penetration ladder L0→L4.
- **Click-through URL buttons (implemented)**: ALL WhatsApp store links are now `type: url` buttons (open browser directly), NO raw URLs in text. Changed `whatsapp_buttons.py` (welcome first button = Visit Store URL button; new `build_visit_store_buttons`), `message_templates.py` (`_visit_store_reply` helper; catalogue_web/checkout_blocked/product_not_found/catalog_link/help_menu), `order_flow.py` (help → help_menu; catalog fallback → catalogue_web; greeting passes web_url). Tests updated, 23 passing.
- **EXCEPTION (2026-08-08): WhatsApp Catalog `wa.me/c/...` link is a TEXT link, not a URL button** — URL buttons can't be forwarded/shared, and text links keep the customer in WhatsApp (data-friendly). Reverted `catalog_link` to tappable text with "_forward to share_" hint.
- **Monthly edition model (2026-08-08)**: catalogue prices change monthly → implemented Edition stamp + validity window on `agent_tools.py` price list (`Edition 2026-08`, valid from/until, auto-computed). Canonical URL always regenerates. Planned: monthly 1st-of-month WhatsApp broadcast with change summary. Doc: `wiki/flyer-cadence.md`.
- **Consumer retail flyer built (2026-08-08)**: `GET /flyer` in `backend/src/api/flyer.py` — DB-generated (zero hardcoding): retail 2× pricing, gender-grouped (Men/Women/Unisex), images with initial-letter fallback, WhatsApp CTA (`FLYER_WHATSAPP`→`ADMIN_PHONE`), featured via `FLYER_FEATURED_IDS` (default first 4), edition + validity stamp. **Fixed documented bug**: `create_product` now persists `gender`/`scent_family`/`top_notes`/`stock_quantity` (previously dropped) — also fixed `list_active_products` SELECT. New `flyer_whatsapp` + `flyer_featured_ids` settings. Test: `test_flyer.py`. 24 tests passing.
- **GTM Master Plan (visual edition)**: created `wiki/gtm-master-plan.md` — consolidates all strategy into one doc with **Mermaid charts** (strategy canvas, price ladder, courier economics, penetration ladder, payment flow, gantt, tier pie) + tables. Renders in VS Code preview + GitHub. Flyer styling to be refined once **brand colours** are chosen.
- **Editable .docx generated (2026-08-08)**: `backend/scripts/generate_gtm_docx.py` → `docs/GTM-Strategy-ZenFragrances.docx` (224KB, 10 sections, 7 tables, 5 matplotlib charts: strategy canvas, price ladder, courier, tier mix, launch timeline). Re-run script after data changes. Requires `python-docx` + `matplotlib` (installed in .venv).
- **SWOT + Blue Ocean finally saved (2026-08-08)**: `wiki/swot-blue-ocean.md` created — it had only lived in chat. 10/10/10/10 SWOT, ERRC grid, 3 tiers of non-customers, 8 blue-ocean initiatives, brand portfolio (OWN BRAND FIRST, licensing later), geography, SWOT→action matrix. Also added production question #24: **2-month buyer cycle** (loyalty vs switching, reorder timing/payday, retention, tier step-up).
- **GTM master plan expanded (2026-08-08)**: added §11 GTM approaches considered (7 options + strengths/weaknesses + verdict), §12 readable SWOT, §13 factual competitor landscape, §14 **OWNING THE VERTICAL** — distributing third-party brands is a BRIDGE, not the end-game; destination = Zen private-label vertical (Phase 2+, revenue-funded). Owning the vertical changes moat/brand/margin/manufacturer-dependency/data assumptions but NOT zero-capital launch.
- **CORRECTION + REGEN (2026-08-08)**: strategy corrected to **OWN BRAND FIRST** — produce + sell under Zen brand from day 1; licensing Motala/P2D is LATER/optional. **Initial launch = BUDGET tier, R30 price point, agents get 5% off (R28.50), retail ~R60.** Payment pathways + collection/courier clarified (Yoco/EFT+PayShap/cash-exception → Courier Guy or Pargo/Pudo pickup). Regenerated `docs/GTM-Strategy-ZenFragrances.docx` (15 sections, 13 tables, 5 charts) + synced wiki gtm-master-plan.md. KPI budget share updated to <60%/<40%/<20% (budget-first normalizing).
- **PRE-LAUNCH GANTT + checklist (2026-08-08)**: 8-track pre-launch plan (site & WA ready · branding plan · branding · fast movers · samples/test · activate agents · activate hawkers · GO LIVE) as a Gantt (mermaid in wiki §8 + matplotlib chart in docx §7) + gate-based checklist with exit criteria (weeks −4→0, 2026-08-10→2026-09-07). Docx now 14 tables / 6 charts.
- **UI/UX resources (2026-08-08)**: created `wiki/ui-ux.md` — curated resources mapped to the Zen web store. Top picks: **checklist.design** (audit pre-launch pages/flows), **tasteskill.dev** (anti-slop frontend skill + brandkit once colours chosen), **Microsoft Flint** (50 chart types, Excel-native charts — upgrade admin dashboard + docx charts), **transitions.dev** (UI polish), **no-ai-slop** (authentic copy). Tied to pre-launch gates. yerd.app (PHP) skipped — not relevant.
- **Leftover BioMed branding cleaned (2026-08-08)**: fixed "Your natural health store on WhatsApp" greeting (order_flow.py), health emojis in `_product_emoji` (🫖🛡️🍵🦴 → 🌹🌊🌿🫧 fallback 🧴), and BioMed/Focus Logic docstrings (orders.py, whatsapp_buttons.py). 24 tests passing.
- **Website improvements implemented (2026-08-08)**: from the zenfragrances.com (namesake, Canada) benchmark — **Landing value strip** ("Inspired by, not a dupe · Oil-based · Alcohol-free · Long-lasting · Skin-friendly"), **email capture** (new `POST /api/newsletter` + migration 016 `newsletter_subscribers`, public, idempotent + test), **ProductDetail "inspired by, not a dupe"** note, **Cart free-shipping progress bar** (R2,000 threshold). 25 tests passing. Note: Tailwind v4 style-lint hints (flex-shrink-0, bg-gradient-to-b) are pre-existing, not errors.
- **FAQ block added to store Landing (2026-08-08)** + **name-change tally created** (`wiki/name-change-tally.md`) — 71 matches / 31 files where "Zen Fragrances" appears, grouped by runtime code, web strings, scripts/artifacts, domains/envs, wiki. Rename procedure included. ⚠️ Do NOT rename competitors.md #14 (the Canadian namesake) or applied migration comments.
- **Microsoft Flint dashboard charts (2026-08-08)**: installed `flint-chart` + `chart.js` (free, MIT). Built `web/src/components/FlintChart.jsx` using `assembleChartjs`; Admin dashboard renders **revenue line** + **orders bar** from `/api/analytics/daily`. `npm run build` passes. Note: bundle ~945KB (Flint+Chart.js heavy — lazy-load dashboard later).
- **Three-dashboard model (2026-08-08, close-out)**: the product has **THREE dashboards — Super Admin, Admin (production), Agent** (team member = agent sub-role). Code has 4 routes; mapping documented in `wiki/status.md`. Do NOT redesign as 4 equal dashboards — keep the 3-tier hierarchy in mind for future UI work.
- **Roles defined (2026-08-08, close-out)**: created `wiki/roles-permissions.md` — full role model for the current dashboards: `super_admin` (overview + Flint charts + management/settings), `manufacturer` (Admin-production: all orders, POP-waiting → confirm → shipped), `agent` (own orders + sales + pending), `team_member` (agent sub-role: recruits + 5% commission), `customer` (default/public), `wholesaler` (planned bulk tier, no dashboard). Includes permissions matrix + **enforcement reality**: frontend gates by `ROLE_PATH`; backend auth is session-cookie/x-api-key (authentication, NOT per-role authorization) — role-scoped server-side guards are a known gap (next steps listed in the doc). Registered in `_index.md`.
- **SESSION CLOSE 2026-08-08**: user confirmed the **4-tier model stands as-is** (Super Admin → Admin-production → Agent, Team = agent sub-role) — no redesign. All changes this session uncommitted (see `git status`): flyer + newsletter endpoints + migration 016, Flint dashboard charts, website improvements (value strip, email capture, FAQ, free-shipping bar), 8 new wiki docs + roles-permissions.md, docx generator + docs/. **Next session pre-flight**: read `gtm-master-plan.md` §8 gates + `status.md` pending list; confirm contract manufacturer private-label + inventory; pick brand colours (unblocks flyer styling + Flint theme); decide on server-side RBAC (outstanding-fixes U0 FL rename still open).
- **Flint theme caveat**: `theme_spec` applies to Vega-Lite output only, not Chart.js backend — dashboard uses default styling until brand colours decided.

### 2026-07-28 — Wiki Setup & Global Best Practices Integration
- Created `wiki/_index.md` (navigation hub)
- Created `wiki/learnings.md` (this file)
- Created `.github/copilot-instructions.md` (session pre-flight with wiki reference)
- Set up repo memory at `/memories/repo/session-start.md`
- Incorporated global `TownShipCode/wiki` best practices:
  - Pre-flight checklist (read wiki before any code)
  - Token waste prevention rules
  - Wiki pointer pattern (don't duplicate rules across repos)

### 2026-07-26 PM — UX Polish + Performance
- Step counters removed, warm address intro
- Fire-and-forget replies, background expiry task
- Address collection escape hatches
- Multi-message support (image + buttons as separate messages)
- 15 errors found & fixed

### 2026-07-24/25 — Build + Live Testing
- Full platform build (Phases 1-4)
- Live flow test with Thandi (13-step journey)
- Kapso webhook debugging (3 hours — format mismatch)
- E2E API tests against live Railway

---

## Token Waste Prevention (from Global Wiki)

**Read these BEFORE touching any code.** From `TownShipCode/wiki/learnings/token-waste-patterns.md`:

- [ ] Read project wiki first (~200 tokens, saves 12K+)
- [ ] Check CWD before `cd` commands
- [ ] Batch edits with `multi_replace_string_in_file`
- [ ] One final verification, not per-edit
- [ ] No temp verify files — use inline `python -c` or permanent tests
- [ ] Use `grep_search` + line-range reads instead of full-file re-reads
- [ ] Todo list: max 1 per 5 turns
- [ ] Single `tokencrusher log` at session end

---

## Tags

#learnings #biomed #session-log
