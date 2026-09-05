"""
seed_data.py
------------
Generates the three starting datasets from scratch — "day zero" data
creation. Run once at the start of the demo (and again anytime you want
a clean reset).
 
CHANGED FOR SQLITE MIGRATION:
  - No more json.dump to three separate files.
  - main() now calls db.reset_db() (drop + recreate tables) then inserts
    the generated rows via db.insert_customers / db.set_state / db.insert_reservations.
  - is_peak_hour() and recompute_state() are pure functions — unchanged —
    because they never touched storage in the first place.
"""
 
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
 
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
 
from contract import TOTAL_TABLES, PEAK_WINDOWS, LOYALTY_TIERS, CUSTOMER_TAGS, VISIT_FREQUENCIES
from data_layer import db
 
FIRST_NAMES = [
    "Aarav", "Vihaan", "Ananya", "Diya", "Ishaan", "Kavya", "Rohan", "Meera",
    "Arjun", "Sneha", "Kabir", "Priya", "Aditya", "Naina", "Devansh", "Riya",
    "Sanjay", "Lakshmi",
]
LAST_NAMES = [
    "Nair", "Menon", "Iyer", "Pillai", "Rao", "Reddy", "Kumar", "Varma",
    "Sharma", "Gupta", "Krishnan", "Warrier",
]
 
 
def is_peak_hour(dt):
    """Checks a datetime against contract.PEAK_WINDOWS. The one definition
    of 'peak hour' in the whole app."""
    t = dt.strftime("%H:%M")
    return any(start <= t <= end for start, end in PEAK_WINDOWS)
 
 
def recompute_state(occupied_tables, total_tables, timestamp):
    """Takes raw numbers, returns a dict with occupancy_pct and is_peak_hour
    filled in. Does NOT touch cancellation counters — those come from the
    actual reservations log, not from arithmetic."""
    return {
        "timestamp": timestamp.isoformat(),
        "occupied_tables": occupied_tables,
        "total_tables": total_tables,
        "occupancy_pct": round(100 * occupied_tables / total_tables, 1),
        "is_peak_hour": is_peak_hour(timestamp),
    }
 
 
def generate_customers(n=18):
    customers = []
    fatigued_indices = set(random.sample(range(n), 4))  # exactly 4 forced fatigued
    tier_weights = [0.35, 0.35, 0.20, 0.10]  # weighted toward Bronze/Silver
 
    for i in range(n):
        tier = random.choices(LOYALTY_TIERS, weights=tier_weights)[0]
        spend_base = {"Bronze": 400, "Silver": 700, "Gold": 1200, "Platinum": 2000}[tier]
        customers.append({
            "customer_id": f"CUST{i+1:03d}",
            "name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
            "loyalty_tier": tier,
            "avg_spend": round(spend_base * random.uniform(0.8, 1.3), 2),
            "visit_frequency": random.choice(VISIT_FREQUENCIES),
            "tags": random.sample(CUSTOMER_TAGS, k=random.randint(0, 2)),
            "discount_fatigue_flag": i in fatigued_indices,
        })
    return customers
 
 
def generate_initial_state():
    now = datetime(2025, 1, 1, 15, 30)  # seed timestamp: 3:30pm
    state = recompute_state(occupied_tables=6, total_tables=TOTAL_TABLES, timestamp=now)
    state["cancellations_last_30min"] = 2
    state["cancellations_today"] = 5
    return state
 
 
def generate_reservations(n=25):
    reservations = []
    now = datetime(2025, 1, 1, 15, 30)
    statuses = ["confirmed"] * 12 + ["completed"] * 8 + ["cancelled"] * 5
 
    for i, status in enumerate(statuses):
        created_at = now - timedelta(hours=random.randint(1, 6))
        cancelled_at = None
        if status == "cancelled":
            # spread cancellations so some fall inside "last 30 min", some don't
            minutes_ago = random.choice([5, 15, 25, 45, 90])
            cancelled_at = (now - timedelta(minutes=minutes_ago)).isoformat()
        reservations.append({
            "reservation_id": f"RES{i+1:03d}",
            "customer_id": f"CUST{random.randint(1, 18):03d}",
            "status": status,
            "table_size": random.randint(2, 8),
            "time_slot": (created_at + timedelta(hours=1)).strftime("%H:%M"),
            "created_at": created_at.isoformat(),
            "cancelled_at": cancelled_at,
        })
    return reservations
 
 
def main():
    random.seed(42)  # reproducible seed data across runs/demos
 
    db.reset_db()  # drop + recreate all four tables, clean slate
 
    customers = generate_customers()
    state = generate_initial_state()
    reservations = generate_reservations()
 
    db.insert_customers(customers)
    print(f"Wrote {len(customers)} customers to customers table")
 
    db.set_state(state)
    print("Wrote restaurant_state to restaurant_state table")
 
    db.insert_reservations(reservations)
    print(f"Wrote {len(reservations)} reservations to reservations_log table")
 
    print("decisions_log table created empty — Person B's agent.py will INSERT into it")
 
 
if __name__ == "__main__":
    main()
 




