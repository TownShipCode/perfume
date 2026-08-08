# UI/UX Resources & Website Recommendations

**Created:** 2026-08-08
**Purpose:** Curated design/UI tools mapped to the Zen Fragrances web store (React 19 + Vite + Tailwind). Use these to polish the store, avoid "template" UI, and audit before launch.

---

## Resource library (mapped to Zen)

| Resource | What it is | Applies to Zen | Priority |
|---|---|---|---|
| [checklist.design](https://checklist.design) | 110+ UI/UX quality checklists (website, web app, mobile, design system, flows) + Figma plugin | **Audit our key pages pre-launch** — Catalogue, Product Detail, Cart, Checkout, Register/Login, dashboards, 404, Blog | 🔴 High |
| [tasteskill.dev](https://tasteskill.dev) | Anti-slop frontend skill for AI agents (design-taste-frontend); also `brandkit`, `redesign-skill`, `soft/minimalist/brutalist` style skills | **Install as a skill** so future AI UI work stops producing "template purple". `brandkit` → generate brand kit (logo/colour/typography) once brand colours chosen; `redesign-skill` → audit-first pass | 🔴 High |
| [microsoft.github.io/flint-chart](https://microsoft.github.io/flint-chart/) | Microsoft Research charting language — 50 chart types, 5 backends (Vega-Lite/ECharts/Chart.js/Plotly/**Excel**), pro themes (NYT, Economist, Swiss, McKinsey) | **Upgrade the admin dashboard** with professional charts; Flint can emit **native editable Excel charts** — upgrade the GTM .docx from matplotlib images to real Excel charts | 🔴 High |
| [transitions.dev](https://transitions.dev) | Open-source copy-paste UI transitions (card resize, modal, toast, tooltip, skeleton, error shake) | Polish on the React store: cart toasts, product card hover, modal transitions, skeleton loaders, form error shake | 🟠 Medium |
| [04.colorion.co](https://04.colorion.co) | Open-source 404 CSS animations with prompts | Branded 404 page (we have a 404 route) | 🟡 Low |
| [codeshots.dev](https://codeshots.dev) | Free animated code-screenshot generator | Social/blog content — animated platform screenshots for marketing | 🟡 Low |
| [orbs.jakubantalik.com](https://orbs.jakubantalik.com) | Free animated "thinking orb" components | Loading/agent-processing states (e.g., while order processes on WhatsApp/web) | 🟡 Low |
| [github.com/petergyang/no-ai-slop](https://github.com/petergyang/no-ai-slop) | Agent skill that removes 20+ AI-slop writing patterns (preserves voice) | **All web + blog + WhatsApp copy** — keeps the brand sounding human, not AI-generated | 🟠 Medium |
| [mattpocock/skills](https://github.com/mattpocock/skills) | TypeScript skills | Only if we migrate the web store to TS (not now) | ⚪ Later |
| [yerd.app](https://yerd.app) | Open-source local PHP without Docker | **Not relevant** (we're Python/FastAPI + React) | ⚪ Skip |

---

## Website action list (tie to pre-launch gates)

### Gate: Branding (weeks −4→−2)
- [ ] Install **tasteskill design-taste-frontend** skill → future UI work stays on-brand
- [ ] Once brand colours chosen, run **tasteskill `brandkit`** → logo/colour/typography mockups
- [ ] Apply **no-ai-slop** to all landing/blog copy (authentic township-friendly tone)

### Gate: Site & WA ready (weeks −4→−3)
- [ ] Run **checklist.design** on: Landing, Catalogue, Product Detail, Cart, Checkout
- [ ] Run **checklist.design Flows**: adding-to-cart, making-a-payment, submitting-a-form
- [ ] Add **transitions.dev** polish: cart toast, card hover, modal, skeleton, error shake
- [ ] Add branded **404** (colorion) + **thinking orb** on loading states

### Gate: Post-launch (month 1+)
- [ ] **Flint charts** in admin dashboard (revenue/orders/top SKUs) with a pro theme
- [ ] **Flint → Excel** charts in monthly business reports (upgrade from static images)
- [ ] **codeshots.dev** animated screenshots for social + blog

---

## Why these matter (the problem they solve)

1. **Anti-slop / anti-template** (tasteskill, no-ai-slop): AI-built sites all look the same — generic purple gradients, robotic copy. For a perfume brand selling trust, that's fatal. These keep the store + copy looking original and human.
2. **Audit discipline** (checklist.design): our pre-launch gates already exist; this is the "how to check quality" toolkit so we ship a tested store, not a hopeful one.
3. **Data storytelling** (Flint): our plan is chart-heavy (strategy canvas, courier economics, KPIs). Flint makes those charts professional AND editable (Excel-native) — upgradeable from the current static matplotlib images.

---

## Component libraries — reviewed & recommended (2026-08-08)

| Library | What it is | Verdict for Zen |
|---|---|---|
| [shadcn/ui](https://ui.shadcn.com) | Copy-paste component system on Tailwind + Radix | ✅ **FOUNDATION — adopt this.** Coherent buttons/cards/dialogs/toasts/accordion; unlocks everything below |
| [21st.dev](https://21st.dev) | Huge community shadcn-block marketplace | ✅ Main block source (landing sections, pricing, forms) |
| [shadcnstudio.com](https://shadcnstudio.com) | 800+ shadcn blocks | ✅ Backup block library |
| [pro.ui-layouts.com](https://pro.ui-layouts.com) | Full layouts, not just pieces | ✅ Use for a full dashboard/store template to remix |
| [motion-primitives.com](https://motion-primitives.com) | Framer-motion primitives "motion done right" | ✅ Premium micro-interactions (modals, toasts, accordion) |
| [reactbits.dev](https://reactbits.dev) | Clean animated React bits (text/backgrounds/components) | ✅ Landing flair (animated headings, particles) |
| [number-flow.barvian.me](https://number-flow.barvian.me) | Animated number transitions | ✅ Earnings calculator + KPI dashboard numbers + prices |
| [ui.aceternity.com](https://ui.aceternity.com) | "Components that look expensive" | 🟡 Selective — hero spotlight/cards only |
| [watermelon.sh](https://watermelon.sh) | Modern, minimal, fast components | 🟡 Minimal alternative if shadcn feels heavy |
| [fancycomponents.dev](https://fancycomponents.dev) | Fun/weird creative components | 🟡 Occasional novelty, not core |
| [component.gallery](https://component.gallery) | Patterns from 95 design systems | 🟢 Reference — pick patterns before building |
| [github.com/petergyang/human-review](https://github.com/petergyang/human-review) | Agent skill: human review of designs | ✅ Anti-slop design pass (with tasteskill) |

**Strategy (avoid bloat):**
1. **Adopt shadcn/ui** as the single component foundation (Tailwind v4 compatible)
2. Pull landing/store sections from **21st.dev** / **shadcnstudio** / **pro.ui-layouts**
3. Add **motion-primitives** (or reactbits) for motion + **number-flow** for the calculator/KPIs
4. Use **component.gallery** as the reference for patterns; run **human-review** + **tasteskill redesign** as the anti-slop audit
5. Do NOT install everything — one foundation + two motion/number libs max

---

## Microsoft Flint — implementation plan (feasible NOW)

**Confirmed:** the backend already exposes `/api/analytics/summary` (aggregate) AND `/api/analytics/daily` (time-series: daily orders + revenue). So Flint has real data to chart today.

**Step 1 — Admin dashboard (web): ✅ DONE 2026-08-08**
- Installed `flint-chart` + `chart.js`; built `web/src/components/FlintChart.jsx` (uses `assembleChartjs`)
- Admin dashboard now renders **revenue line chart** + **orders bar chart** from `/api/analytics/daily`
- `npm run build` passes (bundle ~945KB — heavy; consider lazy-loading the dashboard later)

**Step 2 — Excel-native charts (reporting):**
- Flint can emit native Excel charts via Office.js — use for monthly business reports (agent/KPI pack) instead of static matplotlib images
- Note: this targets Excel workbooks, not the .docx — keep matplotlib for the GTM docx, add Flint where interactive/Excel is wanted

**Step 3 — Public-facing (post-launch):**
- "Trend report" pages for agents (top sellers, monthly movers) — the data-monetization lever (O10)

**Effort:** Step 1 ≈ 1 session (install + component + 2 charts). Blocked by nothing but brand-colour choice for the theme.
