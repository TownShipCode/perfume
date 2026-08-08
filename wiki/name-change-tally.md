# Name-Change Tally — where "Zen Fragrances" appears

**Created:** 2026-08-08
**Purpose:** If we rename the brand (the Canadian company owns `zenfragrances.com`), this is the complete checklist of every place the name appears. Work through it mechanically.
**Search:** `zenfragrance|Zen Fragrance|zen_fragrances|zen\.fragrances|ZenFragrance|ZEN FRAGRANCE` (71 matches / 31 files when tallied)

---

## 1. RUNTIME CODE / CONFIG (must rename — shown to users at runtime)

| File | Line | Where |
|---|---|---|
| `backend/src/config.py` | 123 | `account_holder` default `"Zen Fragrances"` |
| `backend/src/services/message_templates.py` | 37, 38 | `order_confirmed`, `order_shipped` templates ("Thank you for choosing Zen Fragrances") |
| `backend/src/services/message_templates.py` | 133, 135 | Welcome greeting + fallback |
| `backend/src/services/message_templates.py` | 405 | Agent-pitch message ("Become a Zen Fragrances Agent") |
| `backend/src/services/order_flow.py` | 178, 363, 793 | "already a Zen Fragrances agent" · welcome greeting · success welcome |
| `backend/src/api/agent_tools.py` | 84 | Price-list footer "Powered by Zen Fragrances" |
| `backend/src/services/whatsapp_buttons.py` | 2 | Module docstring (cosmetic) |
| `backend/src/db/migrations/013_multi_role.sql` | 2 | Comment (cosmetic — do NOT edit applied migrations) |

## 2. WEB STORE — visible strings

| File | Line | Where |
|---|---|---|
| `web/index.html` | 7 | `<title>Zen Fragrances</title>` |
| `web/src/components/Layout.jsx` | 12, 41 | Header brand + footer |
| `web/src/components/DashboardLayout.jsx` | 33 | Sidebar brand link |
| `web/src/pages/Landing.jsx` | 24, 74 | H1 + "Find a Zen Fragrances agent" |
| `web/src/pages/RegisterAgent.jsx` | 112, 118 | "Why agents choose Zen Fragrances" + comparison header |
| `web/src/pages/AgentLocator.jsx` | 24 | "Find a Zen Fragrances agent near you" |
| `web/src/pages/BlogPost.jsx` | 55 | "Sign up as a Zen Fragrances agent" |

## 3. SCRIPTS / ARTIFACTS / SECURITY

| File | Line | Where |
|---|---|---|
| `scripts/e2e_test.py` | 59, 69 | Banner + `STORE_NAME="Zen Fragrances"` |
| `backend/scripts/generate_gtm_docx.py` | 3, 28, 208, 214, 494 | Doc title + output filename |
| `docs/GTM-Strategy-ZenFragrances.docx` | — | Filename (regenerate to rename) |
| `SECURITY.md` | 1, 7 | Title + `security@zenfragrances.co.za` |

## 4. DOMAINS / ENVS / EMAILS

| Item | Value | Where referenced |
|---|---|---|
| `WEB_BASE_URL` | `https://zenfragrances.vercel.app` | `wiki/status.md` config + Vercel project slug |
| `STORE_EMAIL` | `orders@zenfragrances.co.za` | `wiki/status.md` config |
| `MFG_USERNAME` | `ZenFragrances` | `wiki/status.md` config |
| `.env.example` | `STORE_NAME=Example Store` | generic — no change needed (already neutral) |
| `wiki/adding-products.md` | `https://zenfragrances.vercel.app/static/...` | example image URLs |

## 5. WIKI / DOCS — brand in headers & body (optional to rename, low risk)

- `wiki/_index.md` · `architecture.md` · `competitors.md` · `e2e-test-results.md` · `gtm-master-plan.md` · `gtm-strategy.md` · `learnings.md` · `outstanding-fixes.md` · `retrospective.md` · `security-review.md` · `status.md` · `swot-blue-ocean.md` · `ui-ux.md` · `flyer-cadence.md` · `launch-plan.md` · `distribution-options.md` · `production-questions.md` · `market-entry-strategy.md` · `competitive-geography.md` (titles + prose)

## ⚠️ DO NOT RENAME (they refer to the OTHER company)

- `wiki/competitors.md` **#14** — the NAMESAKE (Canadian `zenfragrances.com`). Keep the old name there; add a note "(now '[New Name]')".
- Social handles `zen.fragrances` (IG/TikTok) — belong to the Canadian brand, not us.

## ⚠️ DO NOT EDIT (applied migrations)
- `backend/src/db/migrations/013_multi_role.sql` — comment only; don't modify applied migration files.

## Rename procedure (when decided)
1. Pick the new name → search `Zen Fragrance|zenfragrance|zenfragrances` across repo
2. Rename runtime config first (`config.py` default + envs + `STORE_NAME`) → re-test (25 tests)
3. Rename web visible strings → rebuild `web/dist`
4. Update `SECURITY.md` email + domain envs in Railway/Vercel
5. Rename `docs/*.docx` + regenerate
6. Wiki: global find-replace, but preserve competitors.md #14 (namesake) wording
