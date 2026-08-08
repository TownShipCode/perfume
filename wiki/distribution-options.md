# Distribution Options — Deepening Penetration

**Created:** 2026-08-08
**Goal:** Deepen penetration (every township, every town). Two options modeled: (1) Agent-hub WhatsApp model, (2) Distribution centers + agents everywhere. Includes courier-cost ownership and a no-money-handling payment flow.

---

## THE CONTEXT (why these two options)

- Courier economics: sustainable only on **bulk** (≥R500, ideal ≥R2,000/free ship). Single bottles = loss.
- **The agent is the last-mile courier** — we ship once, agents distribute locally for free.
- Both options extend this logic to **deepen penetration**: get product closer to the final customer in more places.

---

## OPTION 1 — Agent-Hub WhatsApp Model (Zero Capital, Start Now)

### The flow

```
HAWKER (or small agent)                      AGENT (local hub)              ZEN
─────────────────────                        ───────────────────            ─────
1. Orders via WhatsApp using AGENT CODE       2. Receives consolidated      │
   (e.g. "10 Sauvage, code AGENT123")            group order in system      │
                                             3. Zen ships ONE bulk drop ──▶ AGENT
                                             4. Agent distributes locally
                                                to hawkers (no courier)
```

### Who carries the courier cost?

| Scenario | Courier owner | Why |
|---|---|---|
| Consolidated group order **≥ R2,000** | **Zen absorbs (free ship)** | 1 drop serving 10 hawkers = ~R6.50/hawker logistics. Cheapest CAC in the market. |
| Consolidated **R500–R2,000** | **Shared** (Zen pays half, agent pays half) | Keeps agent invested, still affordable. |
| **< R500** | **Blocked** (min order) | Courier >13% of value = guaranteed loss. |

**Rule:** the bulk-to-agent leg is the ONLY courier we ever pay. The hawker→customer leg is hand-sell (zero courier). This is what makes penetration cheap.

### Payment flow — NO agent money handling (clean design)

1. **Hawker orders** via WhatsApp with agent code (agent = sponsor)
2. **Zen sends payment link** (Yoco) / EFT+POP / PayShap — **hawker pays ZEN directly** (Zen's bank, not the agent's)
3. **Zen verifies payment** (idempotency + POP image check)
4. **Zen consolidates** the agent's full group of paid hawker orders
5. **Zen ships bulk** to agent (single drop)
6. **Agent distributes** bottles to hawkers locally
7. **Zen pays agent 5% commission** (bank transfer from ZEN) on the wholesale orders placed under their code

**Result:** the agent's hands NEVER touch money. They are a **logistics + recruitment node**, not a cash node. All money flows: Hawker → Zen → (commission) → Agent.

### Option 1 economics (example: hub agent + 10 hawkers)

| Line | Value |
|---|---|
| 10 hawkers × 10 bottles (mid @ R85) | 100 bottles = R8,500 |
| Courier (1 bulk drop, free ≥R2,000) | **R0** |
| Zen collects from hawkers | R8,500 |
| Agent commission (5%) | R425 (paid by Zen) |
| Zen wholesale margin (~35%) | ~R2,975 − R0 courier − R425 commission = **~R2,550 net** |
| Hawker economics | buys R85, sells R170, keeps R85/bottle |
| Logistics cost per hawker | **R0–R6.50** (vs R65 if shipped individually) |

### Option 1 risks & mitigations

| Risk | Mitigation |
|---|---|
| **Agent receives goods but fails to distribute** (holds/takes stock) | Ship to established agents only; commission is withheld until distribution confirmed; small "hub deposit" accumulated from commissions. |
| **Cash-only hawkers** (no bank/EFT) | Accept PayShap / mobile money. For true cash hawkers, agent may collect cash → but this reintroduces money handling → treat as exception, cap per agent. |
| **Agent becomes single point of failure** | 2 agents per town minimum. Rotate when unreliable. |
| **Rural courier surcharge/refusal** | Pargo/Pudo pickup (agent collects). Or consolidate to the nearest town agent. |
| **Agent under-orders (breaks R2,000 band)** | Volume incentive: agents who consolidate ≥R2,000 get faster/priority dispatch + small bonus. |

---

## OPTION 2 — Distribution Centers + Agents in Every Town (Capital Model)

### The flow

```
MANUFACTURER ──bulk──▶ DC (regional) ──regional courier──▶ AGENT in every town ──local──▶ CUSTOMER
                              ▲                                              │
                              └────────────── HAWKERS also served ───────────┘
```

### What it takes (3 levels of DC, from zero-capital to capital-heavy)

| Level | What it is | Capital | When |
|---|---|---|---|
| **L1 — Hub agent (micro-DC)** | Top agent in each town holds 20–50 bottle buffer stock of bestsellers; fulfills local orders same-day | **R0** (agent funds stock, earns fulfillment fee) | Month 3+ (Option 1 → evolve) |
| **L2 — Agent-run depot** | A lead agent runs a mini-warehouse; Zen gives volume discount + priority | R0–R15K (racks/shelving, paid by agent, recovered in margin) | Month 6+ |
| **L3 — Zen regional DC** | Zen rents + staffs + stocks a DC (1 per region: GP, EC, WC...) | **R50K–R150K each** (stock + rent) | Only after 500+ agents; revenue-funded |

### Courier economics of Option 2

| Leg | Cost | Comment |
|---|---|---|
| Manufacturer → DC (bulk) | Very low per unit (container/truckload) | Buy in bulk, big discount |
| DC → Agent (regional) | Short distances, cheaper/faster (24–48hr) | Solves deep-rural surcharge problem |
| Agent → Customer/Hawker | **R0 (local hand-sell)** | Still the last-mile answer |

**Key win over Option 1:** bulk buying power + regional speed. Deep-rural towns get 24–48hr fulfillment instead of 3–5 days, and per-unit courier drops dramatically.

### Payment flow (same clean principle as Option 1)

- Town agents and hawkers pay **Zen directly** (Yoco/EFT/PayShap) on order
- DC fulfills the paid order to the agent
- Agent distributes locally
- Zen pays agent commission + (for L1/L2) fulfillment fee to the hub agent

### Option 2 risks

| Risk | Mitigation |
|---|---|
| **Capital-heavy** (L3 = R50–150K each) | Start at L1 (R0), progress only on revenue. Never seed-capital. |
| **Inventory risk** (stock held at DC) | Start with 20 bestsellers; reorder on sell-through data. |
| **Staffing complexity** (L3) | L1/L2 run by agents (no Zen staff). L3 only when volume justifies. |
| **Towns too small to support an agent** | Threshold: only open a hub where ≥5 active hawkers/agents exist. |

---

## THE DECISION — How they combine to DEEPEN PENETRATION

**They are not either/or — they are a progression.** Option 1 is the zero-capital entry; Option 2 (at L1/L2) is how Option 1 scales into every town.

```
PENETRATION LADDER (deepening over time)
─────────────────────────────────────────
L0  (now)      One bulk drop to a seed agent in Soweto/Tembisa
L1  (mth 1-3)  Option 1: agent hubs — 1 hub per township, hawkers order
               via agent code, Zen absorbs courier on consolidated ≥R2,000
L2  (mth 3-6)  Hub agents hold buffer stock → same-day local fulfillment
               (this is L1 evolving — no new capital)
L3  (mth 6+)   Every town in a region has an agent; hub agents run depots
               (Option 2 L1/L2)
L4  (year 2)   Zen regional DCs ONLY if revenue funds them (Option 2 L3)
```

### Penetration metrics to track

| Metric | Target |
|---|---|
| Towns with an active hub agent | 1 per township by mth 3 → every town by mth 9 |
| Hawkers per hub agent | 10–30 |
| Consolidation rate (orders ≥R2,000) | > 60% |
| Avg last-mile distance | shrink each quarter |
| Courier cost per order | < R6 (bulk consolidation) |

### Bottom line

- **Option 1 = how we enter** (zero capital, deepens penetration via people-network + bulk consolidation).
- **Option 2 = how we scale** (distribution centers in the form of agent-run hubs first; real DCs only when revenue funds them).
- **Both share the same engine:** the agent is the last-mile courier, money never passes through their hands, and Zen absorbs courier only on consolidated bulk (the cheapest way to make penetration economically viable).
