# Flyer & Price-List — Monthly Edition Model

**Created:** 2026-08-08
**Why:** Catalogue prices change monthly. The only thing that goes stale is the distributed PDF/flyer. This is the operational model that keeps everyone on the current version.

---

## The 3 rules (in order of importance)

### 1. Stamp every flyer with Edition + Validity window
- Header shows: **"Edition 2026-08"** + **"Valid from 01 August 2026 · Valid until 31 August 2026"**
- Footer shows the same edition so it survives printing/cropping
- Implemented in `backend/src/api/agent_tools.py` (wholesale price list) — auto-computed from today's date, no manual config
- Anyone can tell at a glance if they have the latest version

### 2. One canonical "latest" URL that always regenerates
- `GET /api/agent/price-list` → always generates fresh HTML from the DB (never cached stale)
- `GET /flyer` → **consumer retail flyer (IMPLEMENTED 2026-08-08)** — same edition stamp + validity window, retail 2× pricing, gender-grouped, images with initial-letter fallback, WhatsApp CTA. Zero hardcoding: names/prices/images from DB, edition from date, WhatsApp from `FLYER_WHATSAPP`/`ADMIN_PHONE`, featured from `FLYER_FEATURED_IDS` (default first 4).
- Agents/agents always grab the **current** version from these URLs instead of a downloaded old copy
- WhatsApp "price list" command returns the agent link (already wired)

### 3. WhatsApp broadcast on catalogue change
- **Scheduled monthly broadcast** on a fixed day (e.g., the 1st): "📋 *New August price list* — Edition 2026-08 now live. Grab it here: {url}"
- **Change summary** in the broadcast: "3 new fragrances · 2 price drops · 1 discontinued" — agents know if they must re-share
- **Ad-hoc broadcast** only for urgent mid-month changes (supplier cost shock, stock-out)
- If nothing changed, still broadcast "prices unchanged this month" → maintains trust + predictable cadence

---

## Why "monthly edition" beats "v3/date-stamp"

| Approach | Problem |
|---|---|
| Plain date stamp ("Generated 2026-08-08") | No validity window — is it current or a week old? |
| Version "v3" | No cadence — agents don't know when v4 drops |
| **Monthly edition "2026-08"** | **Predictable: new prices every 1st. Agents learn the rhythm.** Validity window makes it self-evident. |

## The monthly operating rhythm (recommended)

| Day | Action |
|---|---|
| **25th** | Decide price changes (from production cost data + sales) |
| **28th** | Update products in DB (backend) |
| **1st** | WhatsApp broadcast: new edition + change summary. Agents re-share. |
| **Mid-month (only if forced)** | Ad-hoc broadcast for urgent changes |

**Rule:** never change prices silently mid-month. Freeze prices for the month unless a supplier change forces it — predictable pricing builds agent trust.

---

*Stored with: launch-plan.md (price ladder), distribution-options.md, click-through-links.md (wa.me/c share exception).*
