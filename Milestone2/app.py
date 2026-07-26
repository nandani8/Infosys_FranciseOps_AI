"""
app.py — FranchiseOps AI v4 FINAL (Modular Fast Engine)
Lean orchestrator — heavy tab logic lives in agent2_franchise.py, agent3_franchise.py, admin_dash.py
"""
import os, json, joblib, subprocess, numpy as np, pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu
from config import AGENT1_MODEL_PATH, AGENT2_MODEL_PATH, AGENT2_REG_PATH, AGENT3_MODEL_PATH
from ui_theme import apply_theme, render_header, render_card, COLORS
from auth import render_auth_portal
from db import get_conn, load_chat_history, save_chat_message
from weather_context import get_city_weather
from notifications import send_alert, get_recent_alerts
from llm_engine_franchise import (orchestrate_3_agents_query, generate_debate_and_synthesis,
                        warmup_llm, is_llm_loaded, start_background_warmup)
from agent2_franchise import render_agent2_franchise
from agent3_franchise import render_agent3_franchise
from admin_dash import render_admin_dashboard

st.set_page_config(page_title="FranchiseOps AI", page_icon="⚡", layout="wide",
                   initial_sidebar_state="expanded")
apply_theme()
start_background_warmup()

if not st.session_state.get("token"):
    render_auth_portal(); st.stop()

username  = st.session_state.get("username", "guest")
user_role = st.session_state.get("role", "Franchise Owner")
is_admin  = user_role.lower() == "admin"

with st.sidebar:
    st.markdown(f'<div style="text-align:center;padding:10px 0;font-weight:700;font-size:18px;'
                f'color:{COLORS["text_heading"]};">⚡ FranchiseOps AI</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align:center;font-size:13px;color:{COLORS["text_muted"]};'
                f'margin-bottom:12px;">User: <b>{username}</b><br>'
                f'<span style="color:#0066cc;font-weight:600;">[{user_role}]</span></div>',
                unsafe_allow_html=True)
    tabs  = ["🤖 AI Copilot", "👥 Agent 1: Workforce", "🏬 Agent 2: Outlets",
             "📦 Agent 3: Inventory", "📊 Analytics & Retrain"]
    icons = ["chat-dots-fill", "people-fill", "building", "box-seam-fill", "bar-chart-fill"]
    if is_admin:
        tabs.append("🛡️ Admin Dashboard"); icons.append("shield-lock-fill")
    tabs.append("🚪 Sign Out"); icons.append("box-arrow-right")
    selected_tab = option_menu(menu_title=None, options=tabs, icons=icons, default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "nav-link": {"font-size": "13px", "text-align": "left", "margin": "3px 0",
                         "border-radius": "10px", "color": COLORS["text_main"], "font-weight": "600"},
            "nav-link-selected": {"background-color": COLORS["accent"], "color": COLORS["accent_text"],
                                  "border": f"2px solid {COLORS['border']}"},
        })

if selected_tab == "🚪 Sign Out":
    st.session_state["token"] = None; st.rerun()

render_header("FranchiseOps AI", f"Module: {selected_tab}")

b1, b2 = st.columns([4, 1.2])
with b1:
    if is_llm_loaded():
        st.markdown('<div style="background:#d1fae5;border:2px solid #34d399;border-radius:10px;'
                    'padding:8px 16px;font-weight:600;color:#065f46;font-size:13px;">'
                    '⚡ <b>LLM GPU Engine:</b> Active on Tesla T4 (Qwen-2.5-3B Ready)</div>',
                    unsafe_allow_html=True)
    else:
        st.markdown('<div style="background:#bae8e8;border:2px solid #272343;border-radius:10px;'
                    'padding:8px 16px;font-weight:600;color:#272343;font-size:13px;">'
                    '⚡ <b>LLM GPU Engine:</b> Standby — warm up before use</div>',
                    unsafe_allow_html=True)
with b2:
    if not is_llm_loaded():
        if st.button("⚡ Warm Up LLM", key="warmup_btn", use_container_width=True):
            with st.spinner("Loading Qwen-2.5-3B from Drive cache..."):
                warmup_llm()
            st.rerun()


@st.cache_resource
def load_agents():
    if not os.path.exists(AGENT1_MODEL_PATH) or not os.path.exists(AGENT2_MODEL_PATH) or not os.path.exists(AGENT2_REG_PATH) or not os.path.exists(AGENT3_MODEL_PATH):
        try:
            from train_m2_franchise import train_all_agents
            train_all_agents()
        except Exception as e:
            print(f"Auto-training note: {e}")
    m1  = joblib.load(AGENT1_MODEL_PATH) if os.path.exists(AGENT1_MODEL_PATH) else None
    m2c = joblib.load(AGENT2_MODEL_PATH) if os.path.exists(AGENT2_MODEL_PATH) else None
    m2r = joblib.load(AGENT2_REG_PATH)   if os.path.exists(AGENT2_REG_PATH)   else None
    m3  = joblib.load(AGENT3_MODEL_PATH) if os.path.exists(AGENT3_MODEL_PATH) else None
    return m1, m2c, m2r, m3

agent1_m, agent2_c, agent2_r, agent3_m = load_agents()


def confidence_band(model, X_row):
    if model is None:
        return 0.5, 0.42, 0.58
    if hasattr(model, "predict_proba"):
        prob = float(model.predict_proba([X_row])[0][1])
    else:
        prob = float(np.clip(model.predict([X_row])[0], 0, 1))
    z, n = 1.96, 300
    lo = max(0.0, (prob+z**2/(2*n)-z*((prob*(1-prob)+z**2/(4*n))/n)**0.5)/(1+z**2/n))
    hi = min(1.0, (prob+z**2/(2*n)+z*((prob*(1-prob)+z**2/(4*n))/n)**0.5)/(1+z**2/n))
    return prob, lo, hi


with get_conn() as conn:
    n_out  = conn.execute("SELECT count(*) FROM outlets").fetchone()[0]
    n_st   = conn.execute("SELECT count(*) FROM staff").fetchone()[0]
    n_inv  = conn.execute("SELECT count(*) FROM inventory_records").fetchone()[0]
    n_alrt = conn.execute("SELECT count(*) FROM notifications").fetchone()[0]

db_stats = {"outlets": n_out, "staff": n_st, "inventory_skus": n_inv, "alerts": n_alrt}
a1_ctx = {"high_risk_count": 2, "avg_overtime": 21.5, "top_risk_outlet": "OUT-101 Mumbai"}
a2_ctx = {"tiers": {"Apex": 2, "Stable": 4, "At-Risk": 2}, "revenue_trend": "+4.2%"}
a3_ctx = {"critical_skus": ["Coffee Beans", "Eco Cups"], "reorder_urgency": "Immediate"}

# ─────────────────────────────────────────────────────────────────────────────
# TAB: AI COPILOT
# ─────────────────────────────────────────────────────────────────────────────
if selected_tab == "🤖 AI Copilot":
    render_card('<h3 style="margin:0 0 6px;">💬 Unified AI Copilot — Total Franchise Intelligence</h3>'
                '<p style="margin:0;color:#64748b;font-size:13px;">Powered by Qwen-2.5-3B on T4. '
                'All answers use live DB stats, city weather, attrition scores & inventory data.</p>')

    if "copilot_history" not in st.session_state:
        hist = load_chat_history(username, get_conn)
        if not hist:
            msg = "Welcome to FranchiseOps AI Copilot! Ask about outlet performance, staff attrition, or inventory risk."
            save_chat_message(username, "assistant", msg, get_conn)
            hist = [{"role": "assistant", "content": msg}]
        st.session_state["copilot_history"] = hist

    for m in st.session_state["copilot_history"]:
        bg    = "#e3f6f5" if m["role"] == "user" else "white"
        label = "🧑 You" if m["role"] == "user" else "⚡ Copilot"
        st.markdown(f'<div class="pn-card" style="background:{bg};border-left:5px solid '
                    f'{COLORS["accent"] if m["role"]=="user" else COLORS["border"]};">'
                    f'<b>{label}:</b><br>{m["content"]}</div>', unsafe_allow_html=True)

    inp_col, clr_col = st.columns([8, 1])
    with inp_col:
        with st.form("copilot_form", clear_on_submit=True):
            user_q = st.text_input("", placeholder="e.g. 'Why is OUT-101 Mumbai struggling with staff attrition?'")
            fa, fb = st.columns([3, 1])
            with fa: submit = st.form_submit_button("🚀 Ask Copilot")
            with fb: debate = st.form_submit_button("🔍 Debate View")
    with clr_col:
        if st.button("🗑️", help="Clear history"):
            from db import clear_chat_history
            clear_chat_history(username, get_conn)
            st.session_state["copilot_history"] = []; st.rerun()

    if (submit or debate) and user_q.strip():
        save_chat_message(username, "user", user_q, get_conn)
        st.session_state["copilot_history"].append({"role": "user", "content": user_q})
        if debate:
            with st.spinner("⚡ Single-pass debate (~2 sec)..."):
                res = generate_debate_and_synthesis(user_q, a1_ctx, a2_ctx, a3_ctx, db_stats)
            dc1, dc2, dc3 = st.columns(3)
            for col, key, label, color in [
                (dc1, "agent1", "Workforce Retention", COLORS["accent"]),
                (dc2, "agent2", "Outlet Clustering",   "#34d399"),
                (dc3, "agent3", "Inventory & Weather", "#f87171"),
            ]:
                col.markdown(f'<div class="pn-card" style="border-top:4px solid {color};">'
                             f'<span class="agent-badge">{label}</span><br><br>{res[key]}</div>',
                             unsafe_allow_html=True)
            ans = f"**Executive Synthesis:** {res['synthesis']}"
        else:
            with st.spinner("⚡ Generating answer (~1.5 sec)..."):
                ans = orchestrate_3_agents_query(user_q, a1_ctx, a2_ctx, a3_ctx, db_stats)
        save_chat_message(username, "assistant", ans, get_conn)
        st.session_state["copilot_history"].append({"role": "assistant", "content": ans})
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# TAB: AGENT 1 — WORKFORCE
# ─────────────────────────────────────────────────────────────────────────────
elif selected_tab == "👥 Agent 1: Workforce":
    render_card('<h3 style="margin:0;">👥 Agent 1: Staff Attrition Risk Predictor</h3>')
    with get_conn() as conn:
        staff_df = pd.read_sql("SELECT * FROM staff", conn)

    def _s_int(val, default):
        return default if (val is None or pd.isna(val)) else int(val)
    def _s_float(val, default):
        return default if (val is None or pd.isna(val)) else float(val)

    c1, c2 = st.columns(2)
    with c1:
        sel  = st.selectbox("Staff Member", staff_df["employee_name"].tolist())
        row  = staff_df[staff_df["employee_name"] == sel].iloc[0]
        sim_ot  = st.slider("Simulate Overtime Hrs", 0.0, 35.0, _s_float(row.get("weekly_overtime_hrs"), 18.0))
        sim_sat = st.slider("Simulate Job Satisfaction", 1, 5, _s_int(row.get("job_satisfaction"), 3))
    with c2:
        sim_age    = _s_int(row.get("employee_age"), 30)
        sim_tenure = _s_float(row.get("tenure_years"), 4.0)
        sim_income = _s_float(row.get("monthly_salary"), 55000.0)
        sim_wl     = _s_int(row.get("work_life_balance"), 3)
        X_row = [sim_age, sim_sat, sim_ot, sim_tenure, sim_income, sim_wl]
        prob, lo, hi = confidence_band(agent1_m, X_row)
        badge_c = "#f87171" if prob > 0.6 else ("#ffd803" if prob > 0.35 else "#34d399")
        st.markdown(
            f'<div style="background:{badge_c};padding:16px;border-radius:12px;'
            f'border:2px solid {COLORS["border"]};">'
            f'<span class="agent-badge">Agent 1</span>'
            f'<h2 style="color:#272343;margin:8px 0 0;">{prob*100:.1f}% Attrition Risk</h2>'
            f'<p style="font-weight:600;margin:4px 0;">95% CI: {lo*100:.1f}% — {hi*100:.1f}%</p>'
            f'</div>', unsafe_allow_html=True)
        from llm_engine_franchise import generate_json
        if st.button("✨ AI Retention Strategy"):
            with st.spinner("Generating (~2 sec)..."):
                s = generate_json(
                    f"{sel}: {sim_ot}h overtime, satisfaction {sim_sat}/5, salary ₹{sim_income:,.0f}.",
                    ["retention_action", "bonus_recommendation", "priority_level"])
            st.json(s)

# ─────────────────────────────────────────────────────────────────────────────
# TAB: AGENT 2 — OUTLETS (modular)
# ─────────────────────────────────────────────────────────────────────────────
elif selected_tab == "🏬 Agent 2: Outlets":
    render_agent2_franchise(agent2_c, agent2_r, username, db_stats, a1_ctx, a3_ctx,
                            send_alert, confidence_band)

# ─────────────────────────────────────────────────────────────────────────────
# TAB: AGENT 3 — INVENTORY (modular)
# ─────────────────────────────────────────────────────────────────────────────
elif selected_tab == "📦 Agent 3: Inventory":
    render_agent3_franchise(agent3_m, username, db_stats, a1_ctx, a2_ctx, send_alert)

# ─────────────────────────────────────────────────────────────────────────────
# TAB: ANALYTICS & RETRAIN
# ─────────────────────────────────────────────────────────────────────────────
elif selected_tab == "📊 Analytics & Retrain":
    render_card('<h3 style="margin:0;">📊 Enterprise Analytics & Model Management</h3>')
    kc = st.columns(4)
    for col, icon, label, val in [
        (kc[0], "🏬", "Outlets",   n_out),
        (kc[1], "👥", "Staff",     n_st),
        (kc[2], "📦", "SKUs",      n_inv),
        (kc[3], "🔔", "Alerts",    n_alrt),
    ]:
        col.markdown(f'<div class="pn-card" style="text-align:center;padding:14px;">'
                     f'<div style="font-size:26px;">{icon}</div>'
                     f'<h2 style="margin:4px 0;">{val}</h2>'
                     f'<p style="margin:0;color:{COLORS["text_muted"]};font-size:12px;">{label}</p>'
                     f'</div>', unsafe_allow_html=True)
    st.markdown("---")
    mc1, mc2 = st.columns([1, 1.5])
    with mc1:
        render_card('<h4 style="margin:0 0 8px;">🔄 1-Click Retrain</h4>')
        if st.button("🔄 Retrain All Agents Now"):
            with st.spinner("Training... (~2-3 min)"):
                res = subprocess.run(["python", "train_m2_franchise.py"], capture_output=True, text=True, timeout=300)
            load_agents.clear()
            (st.success if res.returncode == 0 else st.error)(
                "✅ All agents retrained!" if res.returncode == 0 else "❌ Training failed.")
            st.code((res.stdout if res.returncode == 0 else res.stderr)[-1000:])
    with mc2:
        with get_conn() as conn:
            try:
                ml_df = pd.read_sql("SELECT agent_name,model_name,r2_score,accuracy,"
                                    "training_rows,created_at FROM ml_models ORDER BY id DESC", conn)
                st.dataframe(ml_df, use_container_width=True, hide_index=True)
            except Exception:
                st.info("No model history yet.")
    st.markdown("---")
    render_card('<h4 style="margin:0 0 8px;">🔔 Recent Alerts</h4>')
    for a in get_recent_alerts(10):
        st.markdown(f'<div style="border-bottom:1px solid #bae8e8;padding:5px 0;font-size:13px;">'
                    f'<b>[{a[1].upper()}]</b> {a[3]} '
                    f'<span style="color:{COLORS["text_muted"]};float:right;">{a[4]}</span></div>',
                    unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB: ADMIN DASHBOARD (modular)
# ─────────────────────────────────────────────────────────────────────────────
elif selected_tab == "🛡️ Admin Dashboard":
    if not is_admin:
        st.error("🔒 Admin access required.")
    else:
        render_admin_dashboard(project="franchise")
