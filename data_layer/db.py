"""
db.py
-----
NEW FILE — this is the piece that didn't exist in the JSON version.
Every bit of raw SQL lives here. seed_data.py and state_manager.py never
write SQL themselves; they call functions from this module. That keeps the
"how do we talk to the database" concern in exactly one place, the same
way contract.py keeps "what are the field names" in exactly one place.
 
Design choices, so you can explain them on stage:
  - sqlite3.Row row_factory -> every SELECT gives you dict-like rows
    (row["name"]), not fragile positional tuples.
  - tags is stored as a JSON string inside one TEXT column rather than a
    separate join table — for 18 customers with a short tag list, a real
    many-to-many table would be over-engineering for a 5-hour build.
  - restaurant_state is a single row (id=1) that gets UPDATEd, not
    INSERTed repeatedly, so "the current state" is always one clean row.
"""
 
import json
import sqlite3
from contextlib import contextmanager
 
from contract import (
    DB_FILE,
    TABLE_CUSTOMERS,
    TABLE_RESTAURANT_STATE,
    TABLE_RESERVATIONS,
    TABLE_DECISIONS,
    CUSTOMER_FIELDS,
    RESTAURANT_STATE_FIELDS,
    RESERVATION_FIELDS,
    DECISION_LOG_FIELDS,
)
 
 
@contextmanager
def get_conn():
    """Opens a connection with dict-style rows, commits on success, always closes."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
 
 
def _create_table_sql(table_name, fields):
    cols = ", ".join(f"{name} {sql_type}" for name, sql_type in fields)
    return f"CREATE TABLE IF NOT EXISTS {table_name} ({cols});"
 
 
def init_db():
    """Creates all four tables if they don't exist yet. Safe to call every run."""
    with get_conn() as conn:
        conn.execute(_create_table_sql(TABLE_CUSTOMERS, CUSTOMER_FIELDS))
        conn.execute(_create_table_sql(TABLE_RESTAURANT_STATE, RESTAURANT_STATE_FIELDS))
        conn.execute(_create_table_sql(TABLE_RESERVATIONS, RESERVATION_FIELDS))
        conn.execute(_create_table_sql(TABLE_DECISIONS, DECISION_LOG_FIELDS))
 
 
def reset_db():
    """Drops and recreates all tables — used by seed_data.py for a clean reset."""
    with get_conn() as conn:
        for table in (TABLE_CUSTOMERS, TABLE_RESTAURANT_STATE, TABLE_RESERVATIONS, TABLE_DECISIONS):
            conn.execute(f"DROP TABLE IF EXISTS {table};")
    init_db()
 
 
# ---------------------------------------------------------------------------
# row <-> dict conversion helpers (handles the tags-as-JSON and 0/1-as-bool
# translation so every other module can just work with normal Python dicts)
# ---------------------------------------------------------------------------
 
def _customer_to_row(c):
    return (
        c["customer_id"], c["name"], c["loyalty_tier"], c["avg_spend"],
        c["visit_frequency"], json.dumps(c["tags"]), int(c["discount_fatigue_flag"]),
    )
 
 
def _row_to_customer(row):
    d = dict(row)
    d["tags"] = json.loads(d["tags"])
    d["discount_fatigue_flag"] = bool(d["discount_fatigue_flag"])
    return d
 
 
def _row_to_state(row):
    d = dict(row)
    d["is_peak_hour"] = bool(d["is_peak_hour"])
    d.pop("id", None)
    return d
 
 
# ---------------------------------------------------------------------------
# customers
# ---------------------------------------------------------------------------
 
def insert_customers(customers):
    with get_conn() as conn:
        conn.executemany(
            f"INSERT INTO {TABLE_CUSTOMERS} "
            f"(customer_id, name, loyalty_tier, avg_spend, visit_frequency, tags, discount_fatigue_flag) "
            f"VALUES (?, ?, ?, ?, ?, ?, ?)",
            [_customer_to_row(c) for c in customers],
        )
 
 
def get_all_customers():
    with get_conn() as conn:
        rows = conn.execute(f"SELECT * FROM {TABLE_CUSTOMERS}").fetchall()
    return [_row_to_customer(r) for r in rows]
 
 
def get_customer(customer_id):
    with get_conn() as conn:
        row = conn.execute(
            f"SELECT * FROM {TABLE_CUSTOMERS} WHERE customer_id = ?", (customer_id,)
        ).fetchone()
    return _row_to_customer(row) if row else None
 
 
# ---------------------------------------------------------------------------
# restaurant_state (single row, id = 1)
# ---------------------------------------------------------------------------
 
def set_state(state):
    with get_conn() as conn:
        conn.execute(f"DELETE FROM {TABLE_RESTAURANT_STATE} WHERE id = 1")
        conn.execute(
            f"INSERT INTO {TABLE_RESTAURANT_STATE} "
            f"(id, timestamp, occupied_tables, total_tables, occupancy_pct, "
            f"is_peak_hour, cancellations_last_30min, cancellations_today) "
            f"VALUES (1, ?, ?, ?, ?, ?, ?, ?)",
            (
                state["timestamp"], state["occupied_tables"], state["total_tables"],
                state["occupancy_pct"], int(state["is_peak_hour"]),
                state["cancellations_last_30min"], state["cancellations_today"],
            ),
        )
 
 
def get_state():
    with get_conn() as conn:
        row = conn.execute(f"SELECT * FROM {TABLE_RESTAURANT_STATE} WHERE id = 1").fetchone()
    return _row_to_state(row) if row else None
 
 
# ---------------------------------------------------------------------------
# reservations_log
# ---------------------------------------------------------------------------
 
def insert_reservations(reservations):
    with get_conn() as conn:
        conn.executemany(
            f"INSERT INTO {TABLE_RESERVATIONS} "
            f"(reservation_id, customer_id, status, table_size, time_slot, created_at, cancelled_at) "
            f"VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                (r["reservation_id"], r["customer_id"], r["status"], r["table_size"],
                 r["time_slot"], r["created_at"], r.get("cancelled_at"))
                for r in reservations
            ],
        )
 
 
def get_all_reservations():
    with get_conn() as conn:
        rows = conn.execute(f"SELECT * FROM {TABLE_RESERVATIONS}").fetchall()
    return [dict(r) for r in rows]
 
 
def get_confirmed_reservations():
    with get_conn() as conn:
        rows = conn.execute(
            f"SELECT * FROM {TABLE_RESERVATIONS} WHERE status = 'confirmed'"
        ).fetchall()
    return [dict(r) for r in rows]
 
 
def update_reservation_status(reservation_id, status, cancelled_at=None):
    with get_conn() as conn:
        conn.execute(
            f"UPDATE {TABLE_RESERVATIONS} SET status = ?, cancelled_at = ? WHERE reservation_id = ?",
            (status, cancelled_at, reservation_id),
        )
 
 
# ---------------------------------------------------------------------------
# decisions_log (Person B's agent.py writes here — table starts empty)
# ---------------------------------------------------------------------------
 
def insert_decision(decision):
    with get_conn() as conn:
        conn.execute(
            f"INSERT INTO {TABLE_DECISIONS} "
            f"(decision_id, timestamp, customer_id, decision_type, reasoning, scenario) "
            f"VALUES (?, ?, ?, ?, ?, ?)",
            (
                decision["decision_id"], decision["timestamp"], decision.get("customer_id"),
                decision["decision_type"], decision["reasoning"], decision.get("scenario"),
            ),
        )
 
 
def get_all_decisions():
    with get_conn() as conn:
        rows = conn.execute(f"SELECT * FROM {TABLE_DECISIONS} ORDER BY timestamp").fetchall()
    return [dict(r) for r in rows]
 