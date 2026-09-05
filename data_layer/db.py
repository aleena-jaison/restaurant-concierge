import sqlite3
import os
import json
from datetime import datetime
import uuid

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'concierge.db')

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_restaurant_state():
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM restaurant_state LIMIT 1").fetchone()
        if not row:
            return None
        return dict(row)

def get_customers():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM customers").fetchall()
        customers = []
        for r in rows:
            c = dict(r)
            if c.get("tags"):
                c["tags"] = json.loads(c["tags"])
            else:
                c["tags"] = []
            customers.append(c)
        return customers

def get_reservations():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM reservations ORDER BY time_slot DESC").fetchall()
        return [dict(r) for r in rows]

def get_decisions_log():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM decisions_log ORDER BY timestamp DESC").fetchall()
        return [dict(r) for r in rows]

def cancel_reservation(reservation_id: str, timestamp: str):
    """Marks a reservation as cancelled and updates the restaurant state metrics."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE reservations SET status = 'cancelled', cancelled_at = ? WHERE reservation_id = ?",
            (timestamp, reservation_id)
        )
        
        conn.execute(
            """UPDATE restaurant_state 
               SET occupied_tables = MAX(0, occupied_tables - 1),
                   cancellations_last_30min = cancellations_last_30min + 1,
                   cancellations_today = cancellations_today + 1"""
        )
        
        conn.execute(
            """UPDATE restaurant_state 
               SET occupancy_pct = ROUND(100.0 * occupied_tables / total_tables)"""
        )
        conn.commit()

def advance_time_slot():
    from datetime import timedelta
    with get_connection() as conn:
        row = conn.execute("SELECT timestamp FROM restaurant_state LIMIT 1").fetchone()
        if not row: return
        new_time = datetime.fromisoformat(row["timestamp"]) + timedelta(minutes=30)
        is_peak = new_time.hour in (12, 13, 19, 20)
        conn.execute(
            "UPDATE restaurant_state SET timestamp = ?, is_peak_hour = ?, cancellations_last_30min = 0",
            (new_time.isoformat(), is_peak)
        )
        conn.commit()

def log_decision(decision: dict, state: dict):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO decisions_log 
               (decision_id, timestamp, occupancy_snapshot, decision_type, target_customer_id, offer, reasoning)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                f"D{uuid.uuid4().hex[:4].upper()}",
                datetime.now().isoformat(),
                state.get("occupancy_pct", 0),
                decision.get("decision"),
                decision.get("target_customer_id"),
                decision.get("offer"),
                decision.get("reasoning")
            )
        )
        conn.commit()
