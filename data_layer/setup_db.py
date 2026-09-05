import sqlite3
import os
from datetime import datetime
import random

from data_layer.db import DB_PATH, get_connection

def init_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    with get_connection() as conn:
        # Create Tables
        conn.executescript("""
            CREATE TABLE customers (
                customer_id TEXT PRIMARY KEY,
                name TEXT,
                loyalty_tier TEXT,
                avg_spend REAL,
                tags TEXT,
                discount_fatigue_flag BOOLEAN,
                offers_received_this_month INTEGER
            );
            
            CREATE TABLE restaurant_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                timestamp TEXT,
                total_tables INTEGER,
                occupied_tables INTEGER,
                occupancy_pct REAL,
                is_peak_hour BOOLEAN,
                cancellations_last_30min INTEGER,
                cancellations_today INTEGER
            );
            
            CREATE TABLE reservations (
                reservation_id TEXT PRIMARY KEY,
                customer_id TEXT,
                table_id TEXT,
                time_slot TEXT,
                status TEXT,
                cancelled_at TEXT
            );
            
            CREATE TABLE decisions_log (
                decision_id TEXT PRIMARY KEY,
                timestamp TEXT,
                occupancy_snapshot REAL,
                decision_type TEXT,
                target_customer_id TEXT,
                offer TEXT,
                reasoning TEXT
            );
        """)
        
        # Seed Customers
        customers = [
            {"id": "C001", "name": "Anita Menon", "tier": "Gold", "spend": 1450, "tags": '["vegetarian"]', "fatigue": 0, "offers": 1},
            {"id": "C002", "name": "Rohan Iyer", "tier": "Platinum", "spend": 2600, "tags": '[]', "fatigue": 0, "offers": 0},
            {"id": "C003", "name": "Sara Thomas", "tier": "Silver", "spend": 900, "tags": '[]', "fatigue": 1, "offers": 3},
            {"id": "C004", "name": "Vikram Nair", "tier": "Bronze", "spend": 620, "tags": '[]', "fatigue": 0, "offers": 1},
        ]
        
        for c in customers:
            conn.execute(
                "INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?, ?)",
                (c["id"], c["name"], c["tier"], c["spend"], c["tags"], c["fatigue"], c["offers"])
            )
            
        # Seed State
        now = datetime.now()
        is_peak = now.hour in (12, 13, 19, 20)
        conn.execute(
            "INSERT INTO restaurant_state VALUES (1, ?, 20, 15, 75.0, ?, 0, 1)",
            (now.isoformat(), is_peak)
        )
        
        # Seed Reservations
        for i in range(1, 16):
            conn.execute(
                "INSERT INTO reservations VALUES (?, ?, ?, ?, ?, ?)",
                (f"R{i:03d}", random.choice(customers)["id"], f"T{i:02d}", now.isoformat(), "confirmed", None)
            )
            
        conn.commit()

if __name__ == "__main__":
    init_db()
    print("Database initialized and seeded.")
