# BioMed — Agent Instructions

## ⚠️ PRE-FLIGHT (EVERY SESSION)

### MUST read the project wiki first
This project has a wiki at `wiki/` with architecture, status, and learnings.
The cross-project wiki at [`TownShipCode/wiki`](https://github.com/TownShipCode/wiki) contains patterns learned from production incidents across all TownShipCode projects.

**Read these before touching any code:**

```
1. wiki/_index.md                              ← navigation hub (~30 sec)
2. wiki/learnings.md                           ← latest session outcomes, errors (~1 min)
3. wiki/status.md                              ← feature status, pending items (~1 min)
4. wiki/architecture.md                        ← stack, key files, state machine (~2 min)
```

### Answer these 3 pre-mortem questions before writing code:
1. "Do all external dependencies exist?" — check API keys in .env, Kapso liveness, env vars
2. "What changed since last session?" — run `git log --oneline -5`, check `wiki/learnings.md`
3. "Will this break the webhook?" — test signature verification, idempotency, state machine

### Verify secrets hygiene (every session):
- `.env` is in `.gitignore`: `git check-ignore .env`
- No tokens in tracked files: `git grep -l "TOKEN\|API_KEY" -- "*.json" "*.yaml"`

---

## 🚀 Token Optimization Rules

From `TownShipCode/wiki/learnings/token-waste-patterns.md`:

- **Read wiki first** — `wiki/_index.md` saves 12K+ tokens of blind recon
- **One final verification only** — batch all edits, verify once at the end
- **No temp verify files** — use inline `python -c` or permanent tests
- **No re-reading files in context** — use `grep_search` for targeted lookups
- **Batch edits** — use `multi_replace_string_in_file` for parallel changes
- **Todo list**: max 1 per 5 turns (each costs ~500 tokens)
- **Check CWD before `cd`** — terminal CWD may already be `backend/`

---

## 🔧 Project-Specific Config

### Tech Stack
- Language: Python 3.12
- Framework: FastAPI
- Database: PostgreSQL (Railway) / SQLite (local dev)
- Deployment: Railway (backend) + Vercel (dashboard)
- Frontend: React + Vite
- WhatsApp: Kapso gateway → Meta Cloud API v24.0

### Key Files
- Entry point: `backend/src/main.py`
- Config: `backend/src/config.py`
- Webhook: `backend/src/api/webhook.py`
- Order flow: `backend/src/services/order_flow.py`
- Message templates: `backend/src/services/message_templates.py`
- WhatsApp sender: `backend/src/services/whatsapp_sender.py`
- Migrations: `backend/src/db/migrations/`
- Tests: `backend/tests/`
- Dashboard: `dashboard/src/`

### Deploy Pipeline
- Platform: Railway (GitHub auto-deploy from `main`)
- Dashboard: Vercel (auto-deploy from `main`)
- Health check: `GET /health` (DB-independent)
- Health check URL: `https://biomed-production.up.railway.app/health`

### Local Dev
```powershell
# Install
.\.venv\Scripts\python -m pip install -e .\backend pytest

# Test
.\.venv\Scripts\python -m pytest backend\tests

# Run
$env:PYTHONPATH = "C:\Users\Sanel\Desktop\miana\perfume\backend"
.\.venv\Scripts\python -m uvicorn src.main:app --host 127.0.0.1 --port 8000
```

---

## 🔒 Security Reminders

From `TownShipCode/wiki/patterns/production-hardening.md`:

- [ ] Webhook signature verification is active (`WHATSAPP_APP_SECRET` set)
- [ ] `DASHBOARD_API_KEY` set in production (or middleware is NO-OP)
- [ ] `APP_ENV=production` only after WhatsApp keys configured
- [ ] Rate limiting active: 60 req/min per IP on webhook
- [ ] Idempotency active: `processed_messages` table
- [ ] `.env` in `.gitignore`, no secrets in code

### Before deploying:
Read `TownShipCode/wiki/patterns/pre-deploy-checklist.md`:
- [ ] `DATABASE_URL` is set in Railway Dashboard
- [ ] `/health` returns `"db":"postgres"` (not sqlite)
- [ ] `healthcheckTimeout: 120` in `railway.json`
- [ ] Batch all fixes into ONE commit → ONE deploy
- [ ] Wait 5 min after push before testing

---

## 📋 Session End

**MUST run at the end of EVERY session:**
```powershell
npx tokencrusher log --root (git rev-parse --show-toplevel) --ide antigravity --task <type> --used <N> --baseline <N> --consulted <N> --avoided <N> --hits <N>
```

Update `wiki/learnings.md` with:
- What changed this session
- New errors found & fixed
- Token waste patterns observed
- Updated status of pending items
