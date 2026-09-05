"""
state_manager.py
-----------------
Everything that changes the data after it's been seeded — what the UI's
buttons and the demo's scenario switcher call while the app is running.
 
CHANGED FOR SQLITE MIGRATION:
  - _load()/_save() JSON helpers are gone entirely — db.py owns all reads
    and writes now.
  - _recount_cancellations() is now a SQL-driven scan: it pulls reservations
    from the DB and recomputes the two counters fresh every time, same
    "never let counters silently drift" guarantee as before, just backed
    by SELECTs instead of a JSON list held in memory.
  - simulate_cancellation() and advance_time_slot() now call db.get_state()/
    db.set_state() and db.update_reservation_status() instead of loading/
    saving whole JSON files.
  - load_scenario() now writes scenario customers + state via db functions,
    and clears/reinserts the customers table so old scenario data doesn't
    linger.
"""
 
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path
 
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
 
from contract import TOTAL_TABLES
from data_layer import db
from data_layer.seed_data import is_peak_hour, recompute_state
 
 
def _recount_cancellations(now):
    """Scans reservations_log in the DB and counts cancellations today vs.
    in the last 30 minutes, relative to `now`. Recalculated from scratch
    every call so the counters can never drift out of sync with the log."""
    reservations = db.get_all_reservations()
    today_count = 0
    last_30_count = 0
    for r in reservations:
        if r["status"] != "cancelled" or not r["cancelled_at"]:
            continue
        cancelled_at = datetime.fromisoformat(r["cancelled_at"])
        if cancelled_at.date() == now.date():
            today_count += 1
        if now - cancelled_at <= timedelta(minutes=30):
            last_30_count += 1
    return last_30_count, today_count
 
 
def simulate_cancellation():
    """Picks a random confirmed reservation, flips it to cancelled, frees
    its table, and recomputes state. Returns the cancelled reservation dict,
    or None if nothing was left to cancel."""
    import random
 
    confirmed = db.get_confirmed_reservations()
    if not confirmed:
        return None
 
    reservation = random.choice(confirmed)
    now = datetime.fromisoformat(db.get_state()["timestamp"])
 
    db.update_reservation_status(
        reservation["reservation_id"], status="cancelled", cancelled_at=now.isoformat()
    )
 
    state = db.get_state()
    new_state = recompute_state(
        occupied_tables=max(0, state["occupied_tables"] - 1),
        total_tables=state["total_tables"],
        timestamp=now,
    )
    last_30, today = _recount_cancellations(now)
    new_state["cancellations_last_30min"] = last_30
    new_state["cancellations_today"] = today
    db.set_state(new_state)
 
    reservation["status"] = "cancelled"
    reservation["cancelled_at"] = now.isoformat()
    return reservation
 
 
def advance_time_slot(minutes=30):
    """Moves the clock forward and recalculates is_peak_hour and both
    cancellation counters against the new time. occupied_tables is left
    untouched — this only moves time, not occupancy (deliberate scope cut)."""
    state = db.get_state()
    now = datetime.fromisoformat(state["timestamp"]) + timedelta(minutes=minutes)
 
    new_state = recompute_state(
        occupied_tables=state["occupied_tables"],
        total_tables=state["total_tables"],
        timestamp=now,
    )
    last_30, today = _recount_cancellations(now)
    new_state["cancellations_last_30min"] = last_30
    new_state["cancellations_today"] = today
    db.set_state(new_state)
    return new_state
 
 
def load_scenario(scenario):
    """Overwrites customers + restaurant_state with a pre-built scenario
    dict. Used for demo-day scenario switching, not normal operation."""
    with db.get_conn() as conn:
        conn.execute(f"DELETE FROM {db.TABLE_CUSTOMERS}")
    db.insert_customers(scenario["customers"])
    db.set_state(scenario["state"])
    return db.get_state()
 
 
# ---------------------------------------------------------------------------
# SCENARIOS — 4 named, ready-to-fire demo setups. Each has its own small
# hand-picked customer list so the "why this decision" story is obvious
# on stage.
# ---------------------------------------------------------------------------
 
def _now():
    return datetime(2025, 1, 1, 13, 0)  # inside a peak window for peak scenarios
 
 
def _customer(cid, name, tier, spend, freq, tags, fatigued):
    return {
        "customer_id": cid, "name": name, "loyalty_tier": tier, "avg_spend": spend,
        "visit_frequency": freq, "tags": tags, "discount_fatigue_flag": fatigued,
    }
 
 
SCENARIOS = {
    "peak_no_action": {
        "customers": [
            _customer("CUST900", "Ravi Sharma", "Gold", 1400, "frequent", [], False),
        ],
        "state": recompute_state(18, TOTAL_TABLES, datetime(2025, 1, 1, 13, 0))
                 | {"cancellations_last_30min": 0, "cancellations_today": 1},
    },
    "offpeak_high_incentive": {
        "customers": [
            _customer("CUST901", "Meera Iyer", "Silver", 650, "occasional",
                       ["price_sensitive"], False),
        ],
        "state": recompute_state(4, TOTAL_TABLES, datetime(2025, 1, 1, 16, 0))
                 | {"cancellations_last_30min": 3, "cancellations_today": 6},
    },
    "offpeak_fatigued_notify_only": {
        "customers": [
            _customer("CUST902", "Arjun Nair", "Bronze", 420, "very_frequent",
                       ["price_sensitive"], True),
        ],
        "state": recompute_state(4, TOTAL_TABLES, datetime(2025, 1, 1, 16, 0))
                 | {"cancellations_last_30min": 3, "cancellations_today": 6},
    },
    "offpeak_borderline": {
        "customers": [
            _customer("CUST903", "Diya Menon", "Silver", 700, "occasional",
                       ["celebrates_birthday_this_month"], False),
        ],
        "state": recompute_state(9, TOTAL_TABLES, datetime(2025, 1, 1, 17, 0))
                 | {"cancellations_last_30min": 1, "cancellations_today": 3},
    },
}
 
 
if __name__ == "__main__":
    db.init_db()
    if len(sys.argv) < 2:
        print("Usage: python data_layer/state_manager.py [cancel|advance|scenario <name>]")
        sys.exit(1)
 
    cmd = sys.argv[1]
    if cmd == "cancel":
        result = simulate_cancellation()
        print(result if result else "No confirmed reservations left to cancel.")
    elif cmd == "advance":
        print(advance_time_slot())
    elif cmd == "scenario":
        if len(sys.argv) < 3 or sys.argv[2] not in SCENARIOS:
            print(f"Usage: python data_layer/state_manager.py scenario <{'|'.join(SCENARIOS)}>")
            sys.exit(1)
        print(load_scenario(SCENARIOS[sys.argv[2]]))
    else:
        print(f"Unknown command: {cmd}")
 