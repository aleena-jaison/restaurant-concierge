"""
contract.py
-----------
Single shared rulebook for the whole team. Only constants live here —
paths, table names, and field lists everyone imports so nothing drifts.
 
This version matches the ACTUAL data schema in data/*.json:
  - customers now includes last_visit_date and offers_received_this_month
  - reservations uses table_id (e.g. "T11"), not a table_size number
"""
 
from pathlib import Path
 
ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
 
# Source JSON files (kept as the human-editable source of truth)
CUSTOMERS_JSON = DATA_DIR / "customers.json"
RESTAURANT_STATE_JSON = DATA_DIR / "restaurant_state.json"
RESERVATIONS_JSON = DATA_DIR / "reservations_log.json"
DECISIONS_JSON = DATA_DIR / "decisions_log.json"
 
# SQLite database — built FROM the JSON files above
DB_FILE = DATA_DIR / "restaurant.db"
 
# --- table names -------------------------------------------------------
TABLE_CUSTOMERS = "customers"
TABLE_RESTAURANT_STATE = "restaurant_state"
TABLE_RESERVATIONS = "reservations_log"
TABLE_DECISIONS = "decisions_log"
 
# --- fixed config --------------------------------------------------------
TOTAL_TABLES = 20
PEAK_WINDOWS = [("12:00", "14:00"), ("19:00", "21:30")]
 
# --- fixed vocabularies --------------------------------------------------
LOYALTY_TIERS = ["Bronze", "Silver", "Gold", "Platinum"]
CUSTOMER_TAGS = [
    "large_group_regular", "vegetarian", "non_vegetarian", "vegan",
    "celebrates_birthday_this_month", "prefers_quiet_area", "prefers_window_seat",
]
RESERVATION_STATUSES = ["confirmed", "completed", "cancelled"]
VISIT_FREQUENCIES = ["rare", "monthly", "biweekly", "weekly"]
DECISION_TYPES = ["discount_offer", "soft_nudge", "notify_only", "no_action"]
 
# --- schema: column name + SQL type, in exact order used by db.py --------
CUSTOMER_FIELDS = [
    ("customer_id", "TEXT PRIMARY KEY"),
    ("name", "TEXT NOT NULL"),
    ("loyalty_tier", "TEXT NOT NULL"),
    ("visit_frequency", "TEXT NOT NULL"),
    ("last_visit_date", "TEXT NOT NULL"),
    ("avg_spend", "REAL NOT NULL"),
    ("tags", "TEXT NOT NULL"),                       # JSON-encoded list
    ("discount_fatigue_flag", "INTEGER NOT NULL"),   # 0/1
    ("offers_received_this_month", "INTEGER NOT NULL"),
]
 
RESTAURANT_STATE_FIELDS = [
    ("id", "INTEGER PRIMARY KEY CHECK (id = 1)"),    # single-row table
    ("timestamp", "TEXT NOT NULL"),
    ("total_tables", "INTEGER NOT NULL"),
    ("occupied_tables", "INTEGER NOT NULL"),
    ("occupancy_pct", "REAL NOT NULL"),
    ("is_peak_hour", "INTEGER NOT NULL"),            # 0/1
    ("cancellations_last_30min", "INTEGER NOT NULL"),
    ("cancellations_today", "INTEGER NOT NULL"),
]
 
RESERVATION_FIELDS = [
    ("reservation_id", "TEXT PRIMARY KEY"),
    ("customer_id", "TEXT NOT NULL"),
    ("table_id", "TEXT NOT NULL"),
    ("time_slot", "TEXT NOT NULL"),
    ("status", "TEXT NOT NULL"),
    ("cancelled_at", "TEXT"),                        # nullable
]
 
DECISION_LOG_FIELDS = [
    ("decision_id", "TEXT PRIMARY KEY"),
    ("timestamp", "TEXT NOT NULL"),
    ("customer_id", "TEXT"),
    ("decision_type", "TEXT NOT NULL"),
    ("reasoning", "TEXT NOT NULL"),
    ("scenario", "TEXT"),
]
 
# Shape Person B's agent.py must return — independent of storage
AGENT_RESPONSE_FIELDS = ["decision_type", "reasoning", "target_customer_id"]