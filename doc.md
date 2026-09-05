# Restaurant Reservation Concierge — Build Documentation
### Cymonic "Intern to Wings" Round 2 Hackathon | Team of 4 | 5-Hour Build

---

## 1. Problem Restatement

Restaurants lose margin during off-peak hours and cancellations — but blanket discounts on every empty table train customers to expect freebies and erode premium positioning.

**Mission:** Build an agent that tracks occupancy and decides whether to notify loyalty customers with a *contextual* incentive — a discount, a complimentary item, or a soft nudge to shift booking time — based on occupancy levels, cancellation trends, and time of day.

**Required output per decision:** `notify / low_incentive / high_incentive` + reasoning + the corresponding offer + updated reservation records.

**Non-negotiables from the brief:**
- No external APIs (no WhatsApp/Twilio/real email). "Sending a notification" = rendering the fully formatted payload on-screen.
- No provided dataset — design your own, with extra fields (tiers, tags, flags) to support advanced reasoning.
- **Dynamic reasoning, not hardcoded logic.** The agent must parse context → evaluate the situation → choose a strategy → execute it → update the dataset, and it must *show* the reasoning. A big if/else tree reads as hardcoded no matter how it's dressed up — route the actual decision through an LLM call using the API keys you were told to bring.

---

## 2. Architecture (the shape everyone is building toward)

```
[Reservation/Occupancy State] --> [Context Builder] --> [LLM Reasoning Agent] --> [Decision JSON]
                                                                |
                                                                v
                                                [Fallback Rule Engine] (only if API fails)
                                                                |
                                                                v
                                        [Dataset Writer: updates reservations + decisions_log]
                                                                |
                                                                v
                                          [UI: live state, decision card, notification mock, table]
```

One LLM call per decision. Structured JSON in, structured JSON out. Everything else (UI, dataset, fallback) is scaffolding around that one call.

---

## 3. Shared Data Contract (lock this before anyone codes — do not deviate)

Everyone builds against these exact field names. If someone needs a new field, it gets added here first and announced to the group.

### `customers.json`
```json
{
  "customer_id": "C001",
  "name": "Anita Menon",
  "loyalty_tier": "Gold",
  "visit_frequency": "weekly",
  "last_visit_date": "2026-08-28",
  "avg_spend": 1450,
  "tags": ["vegetarian", "prefers_window_seat"],
  "discount_fatigue_flag": false,
  "offers_received_this_month": 1
}
```

### `restaurant_state.json`
```json
{
  "timestamp": "2026-09-05T15:30:00",
  "total_tables": 20,
  "occupied_tables": 6,
  "occupancy_pct": 30,
  "is_peak_hour": false,
  "cancellations_last_30min": 2,
  "cancellations_today": 5
}
```

### `reservations_log.json`
```json
{
  "reservation_id": "R101",
  "customer_id": "C001",
  "table_id": "T04",
  "time_slot": "2026-09-05T19:00:00",
  "status": "cancelled",
  "cancelled_at": "2026-09-05T15:12:00"
}
```

### `decisions_log.json` (the agent writes here — this is your proof of dynamic reasoning during the demo)
```json
{
  "decision_id": "D001",
  "timestamp": "2026-09-05T15:30:05",
  "occupancy_snapshot": 30,
  "decision_type": "high_incentive",
  "target_customer_id": "C001",
  "offer": "20% off + free dessert, tonight only",
  "reasoning": "Off-peak evening slot, occupancy dropped to 30% after two recent cancellations, and the target customer has not received a discount this month.",
  "rendered_payload": "..."
}
```

### The exact JSON the LLM must return (this is the interface between the agent and everything else)
```json
{
  "decision": "notify_only | low_incentive | high_incentive | no_action",
  "target_customer_id": "C00X",
  "offer": "plain-language description of the offer",
  "reasoning": "2-3 sentences explaining the decision"
}
```

---

## 4. Master Build Prompt (for Antigravity — paste as-is to scaffold the whole app)

Use this if one person is scaffolding the skeleton first, or as the reference every individual prompt below is scoped from.

```
Build a Python + Streamlit app called "Restaurant Reservation Concierge" — an agentic
system for restaurant revenue management. No external notification APIs; "sending a
notification" means rendering a formatted card on-screen.

DATA: Three local JSON files as the datastore — customers.json, restaurant_state.json,
reservations_log.json — plus decisions_log.json which the agent writes to. Use these
exact schemas: [paste the four JSON schemas from Section 3].

Seed customers.json with 15-20 realistic fictional customers spanning loyalty tiers
Bronze/Silver/Gold/Platinum, varied visit frequency, avg_spend, tags (dietary
preferences, seating preferences), and a discount_fatigue_flag (true for customers who
have already received 2+ offers this month).

AGENT LOGIC: Write a function that (1) builds a context object from current
restaurant_state.json + candidate customers (exclude discount_fatigue_flag=true where
possible), (2) sends that context to an LLM (use the Anthropic/OpenAI/Gemini API,
whichever key is available) with a system prompt instructing it to weigh occupancy
level, peak vs off-peak, and cancellation trend, and to return strict JSON matching:
{"decision": "notify_only|low_incentive|high_incentive|no_action",
"target_customer_id": "...", "offer": "...", "reasoning": "..."}.
Parse the JSON response. If the API call fails or returns malformed JSON, fall back to
a simple weighted-scoring rule engine (occupancy weight + cancellation-trend weight +
time-of-day weight against threshold bands) so the app never crashes.

Write every decision to decisions_log.json with a timestamp and the occupancy snapshot
at decision time.

UI (Streamlit): One page, three sections. (1) Live state panel showing occupancy
gauge, peak/off-peak badge, cancellation counters, and buttons "Simulate cancellation"
and "Advance time slot" that mutate restaurant_state.json and trigger a new agent
decision. (2) Decision panel showing the latest decision's reasoning as readable text
and a mocked notification card (styled like a push notification or email) rendering
the offer to the target customer. (3) A live table of reservations_log.json and
decisions_log.json that updates after each decision.

Keep styling minimal — st.columns() layout, no auth, no multi-page nav, no external
CSS frameworks. Prioritize a working end-to-end loop (state change -> LLM decision ->
UI update -> log write) over visual polish.
```

---

## 5. Work Split — 4 Roles

| Person | Role | Owns |
|---|---|---|
| **A** | Data & Domain Engineer | Dataset design, realistic seed data, schema discipline |
| **B** | Agent/Reasoning Engineer | The LLM call, prompt design, JSON parsing, fallback rule engine |
| **C** | UI/Frontend Engineer | Streamlit dashboard, live state panel, notification card rendering |
| **D** | Integration & Demo Lead | Wires A+B+C together, edge cases, scenario testing, demo script |

Everyone codes against the Section 3 contract independently from **10:15–11:30**, then Person D integrates from **11:30 onward**. This means B can build and test the agent against *mock* restaurant_state.json before A's real data exists, and C can build the UI against *mock* decision JSON before B's agent is done. Nobody blocks anybody.

---

## 6. Individual Prompts (each person pastes their own into Antigravity)

### Person A — Data & Domain Engineer

```
I'm building the data layer for a restaurant revenue-management agent hackathon
project. Generate three Python scripts that create realistic seed JSON files:

1. customers.json — 18 fictional loyalty customers with fields: customer_id, name,
   loyalty_tier (Bronze/Silver/Gold/Platinum, distributed realistically with fewer
   Platinum), visit_frequency (weekly/biweekly/monthly/rare), last_visit_date, avg_spend
   (in rupees, varying by tier), tags (a list drawn from: vegetarian, non_vegetarian,
   vegan, prefers_window_seat, prefers_quiet_area, celebrates_birthday_this_month,
   large_group_regular), discount_fatigue_flag (true for ~4 of them),
   offers_received_this_month (0-3).

2. restaurant_state.json — a single object: timestamp, total_tables (20),
   occupied_tables, occupancy_pct (computed), is_peak_hour (true if timestamp falls in
   12-2pm or 7-9pm), cancellations_last_30min, cancellations_today. Also write a small
   helper function recompute_state(occupied_tables, total_tables, timestamp) that
   updates occupancy_pct and is_peak_hour whenever occupied_tables or timestamp changes.

3. reservations_log.json — 25 reservation records with reservation_id, customer_id
   (referencing the customers above), table_id, time_slot, status
   (confirmed/cancelled/completed), cancelled_at (null unless cancelled). Make sure a
   handful are cancelled today at varying times so cancellation-trend logic has real
   data to react to.

Also write a tiny CLI script simulate_event.py with two functions:
simulate_cancellation() (picks a confirmed reservation, marks it cancelled, updates
restaurant_state.json accordingly) and advance_time_slot() (moves the timestamp forward
30 minutes and recomputes is_peak_hour). These will be called from the UI later, so
keep their signatures clean and importable.

Do not build any UI or agent logic — just the data files and these two helper
functions. Keep it in plain Python + JSON, no database.
```

---

### Person B — Agent/Reasoning Engineer

```
I'm building the decision-making core of a restaurant revenue-management agent for a
hackathon. It must NOT be a hardcoded if/else tree — the actual decision has to go
through an LLM call, with a simple rule-based fallback only for when the API fails.

Write a Python module agent.py with:

1. build_context(state: dict, customers: list) -> dict — assembles a context object
   from a restaurant_state dict (fields: occupancy_pct, is_peak_hour,
   cancellations_last_30min, cancellations_today) and a list of customer dicts,
   filtering out customers with discount_fatigue_flag=true where at least one
   non-flagged candidate exists.

2. decide(context: dict) -> dict — sends the context to an LLM (use whichever of
   Anthropic/OpenAI/Gemini has an API key set as an environment variable — write it so
   swapping providers is a one-line change) with this system prompt:

   "You are a restaurant revenue-management agent. Given the context, decide ONE of:
   notify_only, low_incentive, high_incentive, no_action. Guidelines: peak hours rarely
   need incentives since tables fill naturally; off-peak + low occupancy + rising
   cancellations justifies a stronger incentive; never offer a discount to a customer
   flagged discount_fatigue_flag=true, use notify_only or a non-discount nudge instead;
   prefer the cheapest lever that plausibly fills the gap (soft nudge < complimentary
   item < discount); don't discount when occupancy is merely normal, not empty. Pick
   ONE target customer from the candidates. Return ONLY strict JSON, no prose:
   {"decision": "...", "target_customer_id": "...", "offer": "...",
   "reasoning": "2-3 sentences"}"

   Parse the response as JSON. If parsing fails or the API call throws, fall back to
   fallback_decide(context) — a scoring function: score = (100 - occupancy_pct) * 0.5 +
   cancellations_last_30min * 15 + (0 if is_peak_hour else 20). Map score < 30 ->
   no_action, 30-55 -> notify_only, 55-75 -> low_incentive, >75 -> high_incentive. Pick
   the first non-fatigued candidate as target. Fill offer/reasoning with a template
   string noting this was a fallback decision.

3. log_decision(decision: dict, context: dict) -> None — appends the decision plus a
   timestamp and the occupancy snapshot to decisions_log.json.

Write it so I can call agent.decide(some_context_dict) standalone and get back valid
JSON, without needing the UI or the real dataset — I'll test it against a few
hand-written mock context dicts first (e.g. {"occupancy_pct": 25, "is_peak_hour": false,
"cancellations_last_30min": 2, "cancellations_today": 4} with 3 mock candidate
customers, one of them discount_fatigue_flag=true).
```

---

### Person C — UI/Frontend Engineer

```
I'm building the Streamlit dashboard for a restaurant revenue-management agent
hackathon project. Build app.py with three sections, using mock data for now (a
teammate is building the real data/agent modules in parallel — I'll swap in real
imports later, so keep the data-loading calls isolated in clearly-named functions I can
redirect).

SECTION 1 — Live State: a header showing occupancy as a progress bar/gauge (e.g.
"6/20 tables occupied — 30%"), a badge showing "PEAK HOUR" or "OFF-PEAK", and counters
for cancellations in the last 30 minutes and today. Two buttons: "Simulate
Cancellation" and "Advance Time Slot" — for now, wire them to a placeholder function
mock_simulate_event() that just randomly tweaks the numbers in session_state, since the
real versions come from a teammate's module.

SECTION 2 — Agent Decision: after either button is pressed, show a "decision card"
with: the decision type as a colored badge (no_action=grey, notify_only=blue,
low_incentive=orange, high_incentive=green), the reasoning text in a quote block, and
below it a mocked "notification" styled like a push notification or email — customer
name, the offer text, a fake timestamp — to make clear this stands in for the real
send. Use a placeholder function mock_get_decision() returning a dict shaped like:
{"decision": "high_incentive", "target_customer_id": "C001", "offer": "20% off +
free dessert", "reasoning": "..."} — I'll swap this for the real agent output later.

SECTION 3 — Records: two expandable tables (st.dataframe) — one for reservations, one
for the decisions log — driven by placeholder functions mock_get_reservations() and
mock_get_decisions_log() returning small lists of dicts in the same shape as
reservations_log.json / decisions_log.json (ask me for the exact schema if needed).

Use st.columns() for layout, keep styling minimal (no custom CSS/theming), no
multi-page nav, no auth. Structure the file so every "mock_" function is one line I can
later replace with a real import — that's the main thing that matters here.
```

---

### Person D — Integration & Demo Lead

```
I'm the integration lead for a 4-person hackathon team building a restaurant
revenue-management agent (Streamlit UI + an LLM-based decision agent + a JSON
dataset). Teammates are building: (A) the dataset + simulate_cancellation() /
advance_time_slot() helpers, (B) agent.py with decide(context) that calls an LLM and
returns {"decision", "target_customer_id", "offer", "reasoning"} plus a rule-based
fallback, (C) a Streamlit app.py currently wired to mock_ placeholder functions for
state, decisions, and records.

Help me:

1. Write the glue code that replaces every mock_ function in app.py with real calls
   into A's data module and B's agent module, keeping the same function signatures so
   the UI code barely changes.

2. Write 4 test scenarios I can run end-to-end before the demo, each described as a
   restaurant_state.json + customers.json snapshot, to prove the agent behaves
   differently under different conditions:
   - Scenario 1: Peak hour, 85% occupancy, no cancellations -> expect no_action.
   - Scenario 2: Off-peak, 30% occupancy, 2 cancellations in last 30 min, best
     candidate customer is NOT discount_fatigue_flag -> expect high_incentive.
   - Scenario 3: Off-peak, 55% occupancy, 1 cancellation, best candidate IS
     discount_fatigue_flag -> expect notify_only or a non-discount nudge, not a
     discount.
   - Scenario 4: Off-peak, 45% occupancy, no recent cancellations -> expect
     low_incentive or notify_only (borderline case — good for showing nuanced
     reasoning, not just threshold cliffs).

3. Write a small script or button set that lets me switch the live app between these
   4 scenarios instantly during the demo, so I don't have to manually edit JSON on
   stage.

4. Draft a 90-second demo script structured as: problem (10s) -> approach / why an LLM
   decides instead of hardcoded rules (20s) -> live run through 2 of the 4 scenarios
   showing different decisions with reasoning (40s) -> result / what the dataset looks
   like after (20s).

Also flag anything in A's or B's modules that looks like it will break integration
(mismatched field names, wrong types) so we can fix it before code freeze.
```

---

## 7. Timeline Recap

| Time | Activity |
|---|---|
| 9:45–10:15 | Split immediately: A designs dataset, B tests one raw LLM call, C scaffolds UI on mocks, D writes the JSON contract (Section 3) and shares it |
| 10:15–11:30 | Everyone builds their module independently against the contract |
| 11:30–12:30 | D integrates; get one full end-to-end flow working — this is your MVP checkpoint |
| 12:30–1:00 | Lunch |
| 1:00–2:00 | Add edge cases (discount fatigue, peak-hour override, multi-cancellation), improve reasoning text quality |
| 2:00–2:30 | Run the 4 demo scenarios end-to-end 2-3 times, fix only what's broken |
| 2:30–2:45 | Code freeze, assign demo speaking parts |
| 2:45–3:15 | Demo (~10 min) |

## 8. What to say in individual 1:1s

Scoring is per-person. Each teammate should be ready to explain **their own piece and the trade-off behind it** — not just what the code does:
- A: why these customers/tags/flags, and what "advanced reasoning" hook the tags enable
- B: why an LLM call instead of hardcoded rules, and what the fallback protects against
- C: why this layout communicates the decision clearly to a non-technical judge
- D: how the scenarios were chosen to prove the agent isn't just threshold-based