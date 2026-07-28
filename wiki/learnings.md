# BioMed — Learnings & Session Log

**Last updated:** 2026-07-28
**Global wiki reference:** [`TownShipCode/wiki`](https://github.com/TownShipCode/wiki)

---

## Key Takeaways from Build (2026-07-24 to 2026-07-26)

### What Worked Well
- **Database abstraction** — Dual Postgres/SQLite via `connection.py` made local testing fast
- **State machine design** — `State` enum made extending flow trivial
- **Template-driven messages** — All replies are DB-backed, editable via dashboard
- **Env-driven config** — Every business rule is an env var, no hardcoded values
- **Fire-and-forget replies** — `BackgroundTasks` cut webhook latency by ~50%

### Biggest Wastes
- **Kapso webhook debugging: ~3 hours** — Kapso v2 format is different from Meta's. See [kapso-debugging.md](kapso-debugging.md)
- **Inline Python in PowerShell: ~30 min** — Escaping issues. Write `.py` files instead.
- **Railway CLI timeouts: ~20 min** — Use GitHub auto-deploy, not `railway up`

### Errors Found & Fixed (16 total)
See [retrospective.md](retrospective.md) for the full table. Key ones:
1. `boolean = integer` Postgres error — split queries by `database.mode`
2. Webhook verification 400 — needed `Query(alias="hub.mode")`
3. Decimal JSON serialization crash — wrapped in `jsonable_encoder()`
4. Escape hatches missing in address collection — CANCEL/HELP/CATALOGUE swallowed

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
