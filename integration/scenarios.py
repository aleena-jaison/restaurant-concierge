from datetime import datetime

CUSTOMERS = [
    {"customer_id": "C001", "name": "Anita Menon", "loyalty_tier": "Gold",
     "avg_spend": 1450, "tags": ["vegetarian", "prefers_window_seat"],
     "discount_fatigue_flag": False, "offers_received_this_month": 1},
    {"customer_id": "C002", "name": "Rohan Iyer", "loyalty_tier": "Platinum",
     "avg_spend": 2600, "tags": ["celebrates_birthday_this_month"],
     "discount_fatigue_flag": False, "offers_received_this_month": 0},
    {"customer_id": "C003", "name": "Sara Thomas", "loyalty_tier": "Silver",
     "avg_spend": 900, "tags": ["large_group_regular"],
     "discount_fatigue_flag": True, "offers_received_this_month": 3},
    {"customer_id": "C004", "name": "Vikram Nair", "loyalty_tier": "Bronze",
     "avg_spend": 620, "tags": ["prefers_quiet_area"],
     "discount_fatigue_flag": False, "offers_received_this_month": 1},
]

def get_scenario(idx: int):
    """
    Returns (state, customers) for the given scenario index.
    """
    if idx == 1:
        # Scenario 1: Peak hour, 85% occupancy, no cancellations -> expect no_action.
        state = {
            "timestamp": datetime(2026, 9, 5, 20, 0, 0),
            "total_tables": 20,
            "occupied_tables": 17,
            "occupancy_pct": 85,
            "is_peak_hour": True,
            "cancellations_last_30min": 0,
            "cancellations_today": 1,
        }
        return state, CUSTOMERS

    elif idx == 2:
        # Scenario 2: Off-peak, 30% occupancy, 2 cancellations in last 30 min
        state = {
            "timestamp": datetime(2026, 9, 5, 15, 30, 0),
            "total_tables": 20,
            "occupied_tables": 6,
            "occupancy_pct": 30,
            "is_peak_hour": False,
            "cancellations_last_30min": 2,
            "cancellations_today": 5,
        }
        return state, CUSTOMERS

    elif idx == 3:
        # Scenario 3: Off-peak, 55% occupancy, 1 cancellation, best candidate IS fatigued
        state = {
            "timestamp": datetime(2026, 9, 5, 16, 0, 0),
            "total_tables": 20,
            "occupied_tables": 11,
            "occupancy_pct": 55,
            "is_peak_hour": False,
            "cancellations_last_30min": 1,
            "cancellations_today": 3,
        }
        # Provide only fatigued customers so the agent is forced to use one
        fatigued_customers = [
            {"customer_id": "C001", "name": "Anita Menon", "discount_fatigue_flag": True},
            {"customer_id": "C002", "name": "Rohan Iyer", "discount_fatigue_flag": True},
        ]
        return state, fatigued_customers

    elif idx == 4:
        # Scenario 4: Off-peak, 45% occupancy, no recent cancellations
        state = {
            "timestamp": datetime(2026, 9, 5, 16, 30, 0),
            "total_tables": 20,
            "occupied_tables": 9,
            "occupancy_pct": 45,
            "is_peak_hour": False,
            "cancellations_last_30min": 0,
            "cancellations_today": 1,
        }
        return state, CUSTOMERS

    return None, None
