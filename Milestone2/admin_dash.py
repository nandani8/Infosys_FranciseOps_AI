"""admin_dash.py — Shared Admin Dashboard renderer for FreightQuote & FranchiseOps AI"""
import subprocess, datetime
import streamlit as st
import pandas as pd
import plotly.express as px
from db import get_conn
from notifications import get_recent_alerts
from ui_theme import render_card, COLORS

_APP_START = datetime.datetime.now()


def _smi(query):
    try:
        r = subprocess.run(
            ["nvidia-smi", f"--query-gpu={query}", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=3)
        return r.stdout.strip()
    except Exception:
        return "N/A"


def render_admin_dashboard(project="freight"):
    render_card('<h3 style="margin:0;">🛡️ Admin Dashboard — System Intelligence</h3>')

    # ── 1. System Health ─────────────────────────────────────────────────────
    st.markdown(f'<h4 style="color:{COLORS["text_heading"]};margin:16px 0 8px;">⚙️ System Health</h4>',
                unsafe_allow_html=True)
    gpu_mem  = _smi("memory.used")
    gpu_tot  = _smi("memory.total")
    gpu_util = _smi("utilization.gpu")
    uptime   = str(datetime.datetime.now() - _APP_START).split(".")[0]
    h1, h2, h3, h4 = st.columns(4)
    for col, icon, label, val in [
        (h1, "🖥️", "GPU VRAM Used",  f"{gpu_mem} / {gpu_tot} MB"),
        (h2, "⚡", "GPU Utilization", f"{gpu_util}%"),
        (h3, "🕒", "App Uptime",      uptime),
        (h4, "✅", "LLM Status",      "Active" if gpu_mem != "N/A" else "Standby"),
    ]:
        col.markdown(
            f'<div class="pn-card" style="text-align:center;padding:14px;">'
            f'<div style="font-size:26px;">{icon}</div>'
            f'<h3 style="margin:6px 0 2px;font-size:1.1rem;">{val}</h3>'
            f'<p style="margin:0;color:{COLORS["text_muted"]};font-size:12px;">{label}</p>'
            f'</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ── 2. User Management ───────────────────────────────────────────────────
    st.markdown(f'<h4 style="color:{COLORS["text_heading"]};margin:0 0 8px;">👥 User Management</h4>',
                unsafe_allow_html=True)
    with get_conn() as conn:
        try:
            users_df = pd.read_sql(
                "SELECT id, username, role, email, created_at FROM users ORDER BY id DESC", conn)
        except Exception:
            users_df = pd.DataFrame(columns=["id","username","role","email","created_at"])

    if users_df.empty:
        st.info("No users registered yet.")
    else:
        for _, row in users_df.iterrows():
            uc1, uc2, uc3, uc4 = st.columns([2, 2, 2, 1])
            uc1.markdown(f"**{row['username']}**")
            uc2.markdown(f'<span style="color:#0066cc;font-weight:600;">[{row["role"]}]</span>',
                         unsafe_allow_html=True)
            uc3.markdown(f'<span style="color:{COLORS["text_muted"]};font-size:12px;">'
                         f'{row.get("created_at","—")}</span>', unsafe_allow_html=True)
            with uc4:
                if st.button("🗑️", key=f"del_user_{row['id']}", help=f"Delete {row['username']}"):
                    with get_conn() as c:
                        c.execute("DELETE FROM users WHERE id=?", (row["id"],))
                    st.success(f"Deleted {row['username']}")
                    st.rerun()

    st.markdown("---")

    # ── 3. LLM Activity Monitor ──────────────────────────────────────────────
    st.markdown(f'<h4 style="color:{COLORS["text_heading"]};margin:0 0 8px;">🤖 LLM Activity Monitor</h4>',
                unsafe_allow_html=True)
    with get_conn() as conn:
        try:
            chat_df = pd.read_sql(
                "SELECT username, count(*) as queries FROM chat_history "
                "WHERE role='user' GROUP BY username ORDER BY queries DESC", conn)
            total_q = int(chat_df["queries"].sum()) if not chat_df.empty else 0
        except Exception:
            chat_df = pd.DataFrame(columns=["username","queries"])
            total_q = 0

    mc1, mc2 = st.columns([1, 1.6])
    with mc1:
        st.metric("Total Copilot Queries", total_q)
        st.dataframe(chat_df, use_container_width=True, hide_index=True)
    with mc2:
        if not chat_df.empty:
            fig = px.pie(chat_df, names="username", values="queries",
                         title="Queries per User", hole=0.4,
                         color_discrete_sequence=px.colors.sequential.Teal)
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              height=250, margin=dict(l=10,r=10,t=40,b=10))
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # ── 4. ML Model Audit ────────────────────────────────────────────────────
    st.markdown(f'<h4 style="color:{COLORS["text_heading"]};margin:0 0 8px;">📈 ML Model Audit</h4>',
                unsafe_allow_html=True)
    with get_conn() as conn:
        try:
            ml_df = pd.read_sql(
                "SELECT agent_name, model_name, r2_score, accuracy, "
                "training_rows, created_at FROM ml_models ORDER BY id DESC", conn)
        except Exception:
            ml_df = pd.DataFrame()
    if ml_df.empty:
        st.info("No model training records found. Run retraining from Analytics tab.")
    else:
        st.dataframe(ml_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # ── 5. Live Alert Log ────────────────────────────────────────────────────
    st.markdown(f'<h4 style="color:{COLORS["text_heading"]};margin:0 0 8px;">🔔 Live Alert Log</h4>',
                unsafe_allow_html=True)
    filt = st.selectbox("Filter by type", ["All","In-App","Email","SMS"], key="admin_alert_filt")
    alerts = get_recent_alerts(50)
    for a in alerts:
        if filt != "All" and a[1].lower() != filt.lower():
            continue
        badge = {"email":"#ffd803","sms":"#f87171","in-app":"#34d399"}.get(a[1].lower(),"#bae8e8")
        st.markdown(
            f'<div style="border-left:4px solid {badge};padding:4px 10px;margin:3px 0;'
            f'font-size:13px;"><b>[{a[1].upper()}]</b> {a[3]} '
            f'<span style="color:{COLORS["text_muted"]};float:right;">{a[4]}</span></div>',
            unsafe_allow_html=True)
