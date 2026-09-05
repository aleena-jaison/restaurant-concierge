"""
Aurelio's — Reservation Concierge
UI layer, SQLite-backed MVP version.
"""

import random
from datetime import datetime, timedelta

import streamlit as st  # type: ignore
from dotenv import load_dotenv

import sys
import os
# Add the project root to sys.path so Streamlit can find our local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import agent
from data_layer import db, setup_db

load_dotenv()

st.set_page_config(
    page_title="Aurelio's — Reservation Concierge",
    page_icon="🥂",
    layout="wide",
    initial_sidebar_state="collapsed",
)

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

def fmt_time(dt_str) -> str:
    if not dt_str: return ""
    dt = datetime.fromisoformat(dt_str)
    return dt.strftime("%I:%M %p").lstrip("0")

def fmt_date_short(dt_str) -> str:
    if not dt_str: return ""
    dt = datetime.fromisoformat(dt_str)
    return f"{dt.strftime('%b')} {dt.day}"

DECISION_STYLE = {
    "no_action":      {"label": "No action needed", "color": "var(--stone)"},
    "notify_only":     {"label": "Notify only",       "color": "var(--brass)"},
    "low_incentive":   {"label": "Low incentive",     "color": "var(--copper)"},
    "high_incentive":  {"label": "High incentive",    "color": "var(--wine)"},
}

def simulate_cancellation():
    reservations = db.get_reservations()
    confirmed = [r for r in reservations if r["status"] == "confirmed"]
    if confirmed:
        pick = random.choice(confirmed)
        now_str = datetime.now().isoformat()
        db.cancel_reservation(pick["reservation_id"], now_str)
        _run_decision()

def advance_time_slot():
    db.advance_time_slot()
    _run_decision()

def _run_decision():
    state = db.get_restaurant_state()
    customers = db.get_customers()
    
    context = agent.build_context(state, customers)
    decision = agent.decide(context)
    
    target = next((c for c in customers if c["customer_id"] == decision.get("target_customer_id")), None)
    if target:
        decision["_target_name"] = target["name"]
    else:
        decision["_target_name"] = "Guest"
        
    # Agent logs decision directly to DB
    agent.log_decision(decision, context)

def render_hero(state):
    st.markdown(
        f'''
        <div class="concierge-hero">
            <div>
                <div class="concierge-mark">Aurelio's <span>Concierge</span></div>
                <div class="concierge-tag">Occupancy, cancellations, and the quiet art of filling a table.</div>
            </div>
            <div class="concierge-clock">Reading the floor as of<br><b>{fmt_time(state['timestamp'])}, {fmt_date_short(state['timestamp'])}</b></div>
        </div>
        ''',
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
        f'''
        <div class="status-row">
            <div class="status-pill {peak_class}"><b>{peak_label}</b></div>
            <div class="status-pill">{state['occupied_tables']}/{state['total_tables']} tables — <b>{state['occupancy_pct']}%</b> full</div>
        </div>
        <div class="metric-row">
            <div class="metric-box"><div class="num">{state['cancellations_last_30min']}</div><div class="lbl">Cancellations, last 30 min</div></div>
            <div class="metric-box"><div class="num">{state['cancellations_today']}</div><div class="lbl">Cancellations today</div></div>
        </div>
        ''',
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
    logs = db.get_decisions_log()
    
    if not logs:
        st.markdown(
            '<div class="ticket"><span class="ticket-reason">'
            "No decision yet — simulate a cancellation or advance the clock to see the concierge think."
            "</span></div>",
            unsafe_allow_html=True,
        )
        return

    entry = logs[0] # Top row is the latest
    
    # find name for stub
    customers = db.get_customers()
    target = next((c for c in customers if c["customer_id"] == entry.get("target_customer_id")), None)
    target_name = target["name"] if target else "Guest"

    style = DECISION_STYLE[entry["decision_type"]]
    st.markdown(
        f'''
        <div class="ticket" style="--ticket-color: {style['color']};">
            <div class="ticket-badge">{style['label']}</div>
            <div class="ticket-reason">“{entry['reasoning']}”</div>
            <div class="ticket-meta">{entry['decision_id']} · occupancy at decision time: {entry['occupancy_snapshot']}%</div>
        </div>
        ''',
        unsafe_allow_html=True,
    )

    if entry["decision_type"] != "no_action":
        st.markdown(
            f'''
            <div class="stub-wrap">
                <div class="stub">
                    <div class="stub-eyebrow">Sent to</div>
                    <div class="stub-name">{target_name}</div>
                    <div class="stub-offer">{entry['offer']}</div>
                    <div class="stub-foot"><span>{entry['target_customer_id']}</span><span>{fmt_time(entry['timestamp'])}</span></div>
                </div>
            </div>
            ''',
            unsafe_allow_html=True,
        )

def render_ledger():
    room_title("The Ledger")
    tab1, tab2 = st.tabs(["Reservations", "Decisions"])
    
    with tab1:
        rows = ""
        for r in db.get_reservations():
            rows += (
                f"<tr><td>{r['reservation_id']}</td><td>{r['customer_id']}</td>"
                f"<td>{r['table_id']}</td><td>{fmt_time(r['time_slot'])}</td>"
                f"<td class='status-{r['status']}'>{r['status']}</td></tr>"
            )
        st.markdown(
            f'''<table class="ledger-table">
                <tr><th>Reservation</th><th>Customer</th><th>Table</th><th>Time</th><th>Status</th></tr>
                {rows}</table>''',
            unsafe_allow_html=True,
        )
        
    with tab2:
        logs = db.get_decisions_log()
        if not logs:
            st.markdown('<span style="color: var(--sage);">No decisions logged yet.</span>', unsafe_allow_html=True)
        else:
            customers = {c["customer_id"]: c["name"] for c in db.get_customers()}
            rows = ""
            for d in logs:
                style = DECISION_STYLE[d["decision_type"]]
                target_name = customers.get(d['target_customer_id'], "Guest")
                rows += (
                    f"<tr><td>{d['decision_id']}</td><td>{fmt_time(d['timestamp'])}</td>"
                    f"<td>{d['occupancy_snapshot']}%</td>"
                    f"<td style='color:{style['color']};'>{style['label']}</td>"
                    f"<td>{target_name}</td></tr>"
                )
            st.markdown(
                f'''<table class="ledger-table">
                    <tr><th>ID</th><th>Time</th><th>Occupancy</th><th>Decision</th><th>Customer</th></tr>
                    {rows}</table>''',
                unsafe_allow_html=True,
            )

def main():
    inject_style()
    
    state = db.get_restaurant_state()
    if state is None:
        setup_db.init_db()
        state = db.get_restaurant_state()
        
    render_hero(state)
    render_floor(state)
    render_concierge()
    render_ledger()

if __name__ == "__main__":
    main()
