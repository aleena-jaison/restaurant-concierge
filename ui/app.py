"""
Aurelio's — Reservation Concierge
UI layer only. Every call that should eventually hit real data/agent modules
is isolated below `INTEGRATION POINTS` — swap these for real imports from
Person A's data module and Person B's agent.py without touching anything else
in this file.
"""

import random
from datetime import datetime, timedelta

import streamlit as st
from dotenv import load_dotenv
import agent
from integration.scenarios import get_scenario

load_dotenv()

# ----------------------------------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------------------------------

st.set_page_config(
    page_title="Aurelio's — Reservation Concierge",
    page_icon="🥂",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ----------------------------------------------------------------------------
# STYLE — a dining room, not a dashboard
# ----------------------------------------------------------------------------

def inject_style():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,wght@0,300;0,500;0,600;1,400&family=Inter:wght@400;500;600&display=swap');

        :root {
            --bg: #FBF4EC;
            --surface: #F5E9DC;
            --surface-raised: #FAF0E4;
            --ivory: #4A3F35;
            --sage: #8C7A68;
            --brass: #B98A2E;
            --brass-soft: #E3C68B;
            --wine: #B5615F;
            --copper: #C97C42;
            --stone: #8F8676;
            --hairline: rgba(74, 63, 53, 0.14);
        }

        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        .stApp { background: radial-gradient(ellipse at top, #FFFDF8 0%, var(--bg) 60%); color: var(--ivory); }

        #MainMenu, footer, header { visibility: hidden; }
        .block-container { padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1100px; }

        /* ---------- Hero ---------- */
        .concierge-hero { display: flex; justify-content: space-between; align-items: flex-end;
            border-bottom: 1px solid var(--hairline); padding-bottom: 1.1rem; margin-bottom: 1.6rem; }
        .concierge-mark { font-family: 'Fraunces', serif; font-weight: 500; font-size: 2.15rem;
            color: var(--ivory); letter-spacing: 0.01em; }
        .concierge-mark span { color: var(--brass); font-style: italic; }
        .concierge-tag { color: var(--sage); font-size: 0.92rem; margin-top: 0.15rem; }
        .concierge-clock { text-align: right; color: var(--sage); font-size: 0.85rem; line-height: 1.5; }
        .concierge-clock b { color: var(--ivory); font-weight: 500; }

        .divider-flourish { display: flex; align-items: center; gap: 0.6rem; margin: 2.1rem 0 1.1rem 0; }
        .divider-flourish::before, .divider-flourish::after { content: ""; flex: 1; height: 1px;
            background: var(--hairline); }
        .divider-flourish span { color: var(--brass); font-size: 0.6rem; }
        .room-title { font-family: 'Fraunces', serif; font-weight: 500; font-size: 1.25rem;
            color: var(--ivory); white-space: nowrap; }

        /* ---------- Floor: table dots ---------- */
        .floor-grid { display: flex; flex-wrap: wrap; gap: 9px; margin: 0.9rem 0 1.3rem 0; }
        .table-dot { width: 17px; height: 17px; border-radius: 50%; border: 1.5px solid var(--stone); }
        .table-dot.occupied { background: radial-gradient(circle at 35% 30%, var(--brass-soft), var(--brass) 70%);
            border-color: var(--brass); box-shadow: 0 0 6px rgba(185, 138, 46, 0.3); }

        .status-row { display: flex; gap: 0.85rem; flex-wrap: wrap; margin-bottom: 0.4rem; }
        .status-pill { padding: 0.32rem 0.85rem; border-radius: 100px; font-size: 0.82rem;
            border: 1px solid var(--hairline); background: var(--surface); color: var(--sage); }
        .status-pill.peak { border-color: var(--wine); color: var(--wine); }
        .status-pill.offpeak { border-color: var(--brass); color: var(--brass); }
        .status-pill b { color: var(--ivory); }

        .metric-row { display: flex; gap: 1.4rem; margin-top: 0.9rem; flex-wrap: wrap; }
        .metric-box { background: var(--surface); border: 1px solid var(--hairline); border-radius: 10px;
            padding: 0.85rem 1.15rem; min-width: 150px; }
        .metric-box .num { font-family: 'Fraunces', serif; font-size: 1.7rem; color: var(--brass); }
        .metric-box .lbl { font-size: 0.78rem; color: var(--sage); margin-top: 0.1rem; }

        /* ---------- Decision ticket ---------- */
        .ticket { background: var(--surface-raised); border-radius: 4px; border: 1px solid var(--hairline);
            border-left: 4px solid var(--ticket-color, var(--stone)); padding: 1.2rem 1.4rem;
            animation: rise 0.5s ease-out; }
        @keyframes rise { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
        .ticket-badge { display: inline-block; font-size: 0.72rem; letter-spacing: 0.04em;
            color: var(--ticket-color, var(--stone)); border: 1px solid var(--ticket-color, var(--stone));
            border-radius: 100px; padding: 0.15rem 0.65rem; margin-bottom: 0.7rem; }
        .ticket-reason { font-family: 'Fraunces', serif; font-style: italic; font-weight: 300;
            font-size: 1.12rem; line-height: 1.55; color: var(--ivory); }
        .ticket-meta { margin-top: 0.8rem; font-size: 0.8rem; color: var(--sage); }

        /* ---------- Notification stub ---------- */
        .stub-wrap { display: flex; margin-top: 1.1rem; animation: rise 0.6s ease-out; }
        .stub { flex: 1; max-width: 430px; background: linear-gradient(160deg, var(--surface-raised), var(--surface));
            border: 1px solid var(--hairline); border-radius: 8px; padding: 1.25rem 1.4rem;
            position: relative; }
        .stub::before { content: ""; position: absolute; left: -1px; top: 0; bottom: 0; width: 1px;
            background-image: radial-gradient(circle, var(--bg) 2px, transparent 2.2px);
            background-size: 10px 14px; background-position: -5px 0; }
        .stub-eyebrow { font-size: 0.75rem; color: var(--brass); }
        .stub-name { font-family: 'Fraunces', serif; font-size: 1.3rem; margin: 0.15rem 0 0.5rem 0; }
        .stub-offer { font-size: 0.98rem; color: var(--ivory); line-height: 1.5; }
        .stub-foot { margin-top: 0.9rem; padding-top: 0.6rem; border-top: 1px dashed var(--hairline);
            font-size: 0.76rem; color: var(--sage); display: flex; justify-content: space-between; }

        /* ---------- Buttons ---------- */
        div[data-testid="stButton"] button { background: var(--surface); color: var(--ivory);
            border: 1px solid var(--brass); border-radius: 6px; padding: 0.5rem 1.1rem;
            font-size: 0.88rem; transition: background 0.2s ease; }
        div[data-testid="stButton"] button:hover { background: var(--brass); color: #FFFBF3; border-color: var(--brass); }

        /* ---------- Ledger tables ---------- */
        .ledger-table { width: 100%; border-collapse: collapse; font-size: 0.86rem; }
        .ledger-table th { text-align: left; color: var(--sage); font-weight: 500; font-size: 0.76rem;
            padding: 0.5rem 0.7rem; border-bottom: 1px solid var(--hairline); }
        .ledger-table td { padding: 0.55rem 0.7rem; border-bottom: 1px solid var(--hairline); color: var(--ivory); }
        .ledger-table tr:last-child td { border-bottom: none; }
        .tag-chip { display: inline-block; font-size: 0.72rem; color: var(--sage);
            border: 1px solid var(--hairline); border-radius: 100px; padding: 0.05rem 0.5rem; margin: 1px; }
        .status-confirmed { color: var(--brass); }
        .status-cancelled { color: var(--wine); }
        .status-completed { color: var(--sage); }
        </style>
        """,
        unsafe_allow_html=True,
    )


def fmt_time(dt) -> str:
    """12-hour clock, no leading zero — portable across Windows/Mac/Linux
    (the '%-I' strftime flag only works on Linux's libc)."""
    return dt.strftime("%I:%M %p").lstrip("0")


def fmt_date_short(dt) -> str:
    """e.g. 'Sep 5' — same portability reasoning as fmt_time()."""
    return f"{dt.strftime('%b')} {dt.day}"


DECISION_STYLE = {
    "no_action":      {"label": "No action needed", "color": "var(--stone)"},
    "notify_only":     {"label": "Notify only",       "color": "var(--brass)"},
    "low_incentive":   {"label": "Low incentive",     "color": "var(--copper)"},
    "high_incentive":  {"label": "High incentive",    "color": "var(--wine)"},
}

# ----------------------------------------------------------------------------
# INTEGRATION POINTS
# Every function in this block is a placeholder. Swap the body for a real
# call into A's data module / B's agent module — signatures stay the same,
# so nothing below this block has to change.
# ----------------------------------------------------------------------------

def _seed_state():
    if "state" not in st.session_state:
        st.session_state.state = {
            "timestamp": datetime(2026, 9, 5, 15, 30, 0),
            "total_tables": 20,
            "occupied_tables": 6,
            "occupancy_pct": 30,
            "is_peak_hour": False,
            "cancellations_last_30min": 2,
            "cancellations_today": 5,
        }
    if "customers" not in st.session_state:
        st.session_state.customers = [
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
            {"customer_id": "C005", "name": "Divya Pillai", "loyalty_tier": "Gold",
             "avg_spend": 1700, "tags": ["vegan", "prefers_window_seat"],
             "discount_fatigue_flag": False, "offers_received_this_month": 0},
        ]
    if "reservations" not in st.session_state:
        base = datetime(2026, 9, 5, 15, 0, 0)
        st.session_state.reservations = [
            {"reservation_id": "R101", "customer_id": "C001", "table_id": "T04",
             "time_slot": base + timedelta(hours=4), "status": "cancelled",
             "cancelled_at": base + timedelta(minutes=12)},
            {"reservation_id": "R102", "customer_id": "C002", "table_id": "T09",
             "time_slot": base + timedelta(hours=4, minutes=30), "status": "confirmed", "cancelled_at": None},
            {"reservation_id": "R103", "customer_id": "C003", "table_id": "T02",
             "time_slot": base + timedelta(hours=3), "status": "completed", "cancelled_at": None},
            {"reservation_id": "R104", "customer_id": "C004", "table_id": "T11",
             "time_slot": base + timedelta(hours=5), "status": "confirmed", "cancelled_at": None},
            {"reservation_id": "R105", "customer_id": "C005", "table_id": "T06",
             "time_slot": base + timedelta(hours=4, minutes=15), "status": "cancelled",
             "cancelled_at": base + timedelta(minutes=28)},
        ]
    if "decisions_log" not in st.session_state:
        st.session_state.decisions_log = []
    if "decision_counter" not in st.session_state:
        st.session_state.decision_counter = 0


def get_restaurant_state() -> dict:
    """INTEGRATION POINT: replace with A's real restaurant_state.json loader."""
    return st.session_state.state


def get_customers() -> list:
    """INTEGRATION POINT: replace with A's real customers.json loader."""
    return st.session_state.customers


def get_reservations() -> list:
    """INTEGRATION POINT: replace with A's real reservations_log.json loader."""
    return st.session_state.reservations


def get_decisions_log() -> list:
    """INTEGRATION POINT: replace with the real decisions_log.json reader."""
    return st.session_state.decisions_log


def simulate_cancellation():
    """INTEGRATION POINT: replace with A's simulate_cancellation()."""
    state = st.session_state.state
    confirmed = [r for r in st.session_state.reservations if r["status"] == "confirmed"]
    if confirmed:
        pick = random.choice(confirmed)
        pick["status"] = "cancelled"
        pick["cancelled_at"] = state["timestamp"]
    state["occupied_tables"] = max(0, state["occupied_tables"] - 1)
    state["occupancy_pct"] = round(100 * state["occupied_tables"] / state["total_tables"])
    state["cancellations_last_30min"] += 1
    state["cancellations_today"] += 1
    _run_decision()


def advance_time_slot():
    """INTEGRATION POINT: replace with A's advance_time_slot()."""
    state = st.session_state.state
    state["timestamp"] += timedelta(minutes=30)
    hour = state["timestamp"].hour
    state["is_peak_hour"] = (12 <= hour < 14) or (19 <= hour < 21)
    state["cancellations_last_30min"] = 0
    _run_decision()


def get_decision(state: dict, customers: list) -> dict:
    """
    INTEGRATION POINT: replace this whole body with B's agent.decide(context) —
    the real LLM call. Keep the same return shape:
    {"decision", "target_customer_id", "offer", "reasoning"}.
    This placeholder is a weighted stand-in so the UI has something live to
    render before the agent module exists.
    """
    context = agent.build_context(state, customers)
    decision = agent.decide(context)
    
    # The UI needs _target_name to render the stub, so we find it from the dataset
    target = next((c for c in customers if c["customer_id"] == decision.get("target_customer_id")), None)
    if target:
        decision["_target_name"] = target["name"]
    else:
        decision["_target_name"] = "Guest"
        
    # Also log it
    agent.log_decision(decision, context)
        
    return decision


def _run_decision():
    state = st.session_state.state
    decision = get_decision(state, st.session_state.customers)
    st.session_state.decision_counter += 1
    entry = {
        "decision_id": f"D{st.session_state.decision_counter:03d}",
        "timestamp": state["timestamp"],
        "occupancy_snapshot": state["occupancy_pct"],
        "decision_type": decision["decision"],
        "target_customer_id": decision["target_customer_id"],
        "target_name": decision["_target_name"],
        "offer": decision["offer"],
        "reasoning": decision["reasoning"],
    }
    st.session_state.decisions_log.insert(0, entry)
    st.session_state.latest_decision = entry


# ----------------------------------------------------------------------------
# RENDER HELPERS
# ----------------------------------------------------------------------------

def render_hero(state):
    st.markdown(
        f"""
        <div class="concierge-hero">
            <div>
                <div class="concierge-mark">Aurelio's <span>Concierge</span></div>
                <div class="concierge-tag">Occupancy, cancellations, and the quiet art of filling a table.</div>
            </div>
            <div class="concierge-clock">Reading the floor as of<br><b>{fmt_time(state['timestamp'])}, {fmt_date_short(state['timestamp'])}</b></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def room_title(text):
    st.markdown(
        f'<div class="divider-flourish"><span>❖</span><div class="room-title">{text}</div><span>❖</span></div>',
        unsafe_allow_html=True,
    )


def render_floor(state):
    room_title("The Floor")

    dots = "".join(
        f'<div class="table-dot{" occupied" if i < state["occupied_tables"] else ""}"></div>'
        for i in range(state["total_tables"])
    )
    st.markdown(f'<div class="floor-grid">{dots}</div>', unsafe_allow_html=True)

    peak_class = "peak" if state["is_peak_hour"] else "offpeak"
    peak_label = "Peak hour" if state["is_peak_hour"] else "Off-peak"
    st.markdown(
        f"""
        <div class="status-row">
            <div class="status-pill {peak_class}"><b>{peak_label}</b></div>
            <div class="status-pill">{state['occupied_tables']}/{state['total_tables']} tables — <b>{state['occupancy_pct']}%</b> full</div>
        </div>
        <div class="metric-row">
            <div class="metric-box"><div class="num">{state['cancellations_last_30min']}</div><div class="lbl">Cancellations, last 30 min</div></div>
            <div class="metric-box"><div class="num">{state['cancellations_today']}</div><div class="lbl">Cancellations today</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, _ = st.columns([1, 1, 2])
    with col1:
        if st.button("Simulate cancellation", use_container_width=True):
            simulate_cancellation()
            st.rerun()
    with col2:
        if st.button("Advance time slot", use_container_width=True):
            advance_time_slot()
            st.rerun()


def render_concierge():
    room_title("The Concierge")

    entry = st.session_state.get("latest_decision")
    if not entry:
        st.markdown(
            '<div class="ticket"><span class="ticket-reason">'
            "No decision yet — simulate a cancellation or advance the clock to see the concierge think."
            "</span></div>",
            unsafe_allow_html=True,
        )
        return

    style = DECISION_STYLE[entry["decision_type"]]
    st.markdown(
        f"""
        <div class="ticket" style="--ticket-color: {style['color']};">
            <div class="ticket-badge">{style['label']}</div>
            <div class="ticket-reason">“{entry['reasoning']}”</div>
            <div class="ticket-meta">{entry['decision_id']} · occupancy at decision time: {entry['occupancy_snapshot']}%</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if entry["decision_type"] != "no_action":
        st.markdown(
            f"""
            <div class="stub-wrap">
                <div class="stub">
                    <div class="stub-eyebrow">Sent to</div>
                    <div class="stub-name">{entry['target_name']}</div>
                    <div class="stub-offer">{entry['offer']}</div>
                    <div class="stub-foot"><span>{entry['target_customer_id']}</span><span>{fmt_time(entry['timestamp'])}</span></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_ledger():
    room_title("The Ledger")

    tab1, tab2 = st.tabs(["Reservations", "Decisions"])

    with tab1:
        rows = ""
        for r in st.session_state.reservations:
            rows += (
                f"<tr><td>{r['reservation_id']}</td><td>{r['customer_id']}</td>"
                f"<td>{r['table_id']}</td><td>{fmt_time(r['time_slot'])}</td>"
                f"<td class='status-{r['status']}'>{r['status']}</td></tr>"
            )
        st.markdown(
            f"""<table class="ledger-table">
                <tr><th>Reservation</th><th>Customer</th><th>Table</th><th>Time</th><th>Status</th></tr>
                {rows}</table>""",
            unsafe_allow_html=True,
        )

    with tab2:
        if not st.session_state.decisions_log:
            st.markdown('<span style="color: var(--sage);">No decisions logged yet.</span>', unsafe_allow_html=True)
        else:
            rows = ""
            for d in st.session_state.decisions_log:
                style = DECISION_STYLE[d["decision_type"]]
                rows += (
                    f"<tr><td>{d['decision_id']}</td><td>{fmt_time(d['timestamp'])}</td>"
                    f"<td>{d['occupancy_snapshot']}%</td>"
                    f"<td style='color:{style['color']};'>{style['label']}</td>"
                    f"<td>{d['target_name']}</td></tr>"
                )
            st.markdown(
                f"""<table class="ledger-table">
                    <tr><th>ID</th><th>Time</th><th>Occupancy</th><th>Decision</th><th>Customer</th></tr>
                    {rows}</table>""",
                unsafe_allow_html=True,
            )


# ----------------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------------

def main():
    inject_style()
    _seed_state()
    
    st.sidebar.title("Demo Controls")
    scenario_options = {
        "Custom / Live": 0,
        "1. Peak & Full": 1,
        "2. Off-Peak Softness": 2,
        "3. Discount Fatigue": 3,
        "4. Borderline": 4
    }
    selected_scenario = st.sidebar.radio("Load Scenario Snapshot:", list(scenario_options.keys()))
    
    idx = scenario_options[selected_scenario]
    if idx > 0:
        if st.sidebar.button(f"Load Scenario {idx}"):
            state, customers = get_scenario(idx)
            st.session_state.state = state
            st.session_state.customers = customers
            st.session_state.decisions_log = []
            st.session_state.decision_counter = 0
            if "latest_decision" in st.session_state:
                del st.session_state["latest_decision"]
            st.rerun()

    state = get_restaurant_state()
    render_hero(state)
    render_floor(state)
    render_concierge()
    render_ledger()


if __name__ == "__main__":
    main()
