"""
agent3_franchise.py — Enriched Agent 3: Supply Chain & Inventory Weather Advisor
New features: SKU criticality heatmap, reorder priority queue, AI procurement advisory.
"""
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
from ui_theme import render_card, COLORS
from db import get_conn
from weather_context import get_city_weather
from llm_engine_franchise import orchestrate_3_agents_query, generate_json
from notifications import send_alert

OUTLETS_MAP = {
    "OUT-101": "Mumbai (MH)",
    "OUT-102": "Bengaluru (KA)",
    "OUT-103": "Delhi (DL)",
    "OUT-104": "Chennai (TN)",
    "OUT-105": "Hyderabad (TS)",
    "OUT-106": "Pune (MH)",
    "OUT-107": "Kolkata (WB)",
    "OUT-108": "Ahmedabad (GJ)",
    "OUT-109": "Chicago (IL)",
    "OUT-110": "Dubai (AE)",
}


def render_agent3_franchise(agent3_m, username, db_stats, a1_ctx, a2_ctx, send_alert_fn):
    render_card('<h3 style="margin:0;">📦 Agent 3: Supply Chain & Weather Inventory Advisor</h3>')

    c1, c2 = st.columns(2)
    with c1:
        sel_out = st.selectbox("Outlet", list(OUTLETS_MAP.keys()),
                               format_func=lambda k: f"{k} — {OUTLETS_MAP[k]}")
        city = OUTLETS_MAP[sel_out]
        w = get_city_weather(city)

    with c2:
        render_card(
            f"<b>📍 City:</b> {city}<br>"
            f"<b>Weather:</b> {w['status']} ({w.get('temp_f', 'N/A')}°F)<br>"
            f"<b>Demand Impact:</b> <b>{w['demand_impact_pct']:+.1f}%</b><br>"
            f"<b>Supply Delay:</b> +{w.get('supply_delay_days', 1)} days", alt=True)

    st.markdown("---")
    tab_heat, tab_queue, tab_ai = st.tabs(
        ["🌡️ SKU Heatmap", "📋 Reorder Queue", "🤖 AI Procurement"])

    # ── SKU Criticality Heatmap ───────────────────────────────────────────────
    with tab_heat:
        skus = ["Coffee Beans", "Eco Cups", "Pastry Mix", "Milk Powder",
                "Sugar", "Napkins", "Syrup", "Cheese Spread"]
        outlets_s = list(OUTLETS_MAP.keys())[:6]
        np.random.seed(42)
        base = np.random.uniform(0.1, 0.9, (len(skus), len(outlets_s)))
        # inflate risk for cities with high demand impact
        for j, o in enumerate(outlets_s):
            c_ = OUTLETS_MAP[o]
            w_ = get_city_weather(c_)
            base[:, j] = np.clip(base[:, j] + w_["demand_impact_pct"] / 200, 0, 1)

        heat_df = pd.DataFrame(np.round(base, 2), index=skus, columns=outlets_s)
        fig = px.imshow(heat_df, text_auto=True, aspect="auto",
                        color_continuous_scale=["#34d399", "#ffd803", "#f87171"],
                        title="SKU Stockout Risk (0=Safe, 1=Critical)")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", height=340,
                          margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

    # ── Reorder Priority Queue ────────────────────────────────────────────────
    with tab_queue:
        rows = []
        for o, c_ in list(OUTLETS_MAP.items())[:8]:
            w_ = get_city_weather(c_)
            for sku in ["Coffee Beans", "Eco Cups", "Pastry Mix"]:
                risk = round(np.clip(0.3 + w_["demand_impact_pct"] / 150 + np.random.uniform(0, 0.3), 0, 1), 2)
                rows.append({
                    "Outlet": o, "City": c_.split(" (")[0], "SKU": sku,
                    "Stockout Risk": risk,
                    "Urgency": "🔴 Immediate" if risk > 0.7 else ("🟡 Soon" if risk > 0.45 else "🟢 OK"),
                    "Reorder Qty": int(risk * 500 + 100),
                })
        q_df = pd.DataFrame(rows).sort_values("Stockout Risk", ascending=False).head(10).reset_index(drop=True)
        q_df.index += 1
        st.dataframe(q_df, use_container_width=True)

    # ── AI Procurement Advisory ───────────────────────────────────────────────
    with tab_ai:
        if st.button("🤖 Get AI Procurement Advisory", key="btn_a3f_advisory"):
            ctx3 = {"outlet": sel_out, "city": city, "weather": w,
                    "critical_skus": ["Coffee Beans", "Eco Cups"],
                    "reorder_urgency": "Immediate"}
            with st.spinner("Generating advisory (~2 sec)..."):
                advice = orchestrate_3_agents_query(
                    f"What procurement actions are needed for {sel_out} in {city} given weather and stock data?",
                    a1_ctx, a2_ctx, ctx3, db_stats)
            st.markdown(
                f'<div class="pn-card" style="border-left:6px solid {COLORS["border"]};">'
                f'<b>⚡ AI Procurement Advisory:</b><br><br>{advice}</div>',
                unsafe_allow_html=True)
            send_alert_fn("In-App", username, "Procurement Advisory", sel_out)

        if st.button("📋 Generate JSON Reorder Plan", key="btn_reorder_json"):
            with st.spinner("Generating reorder plan (~2 sec)..."):
                plan = generate_json(
                    f"Outlet {sel_out} in {city}. Weather demand surge: {w['demand_impact_pct']:+.1f}%. "
                    f"Supply delay: {w.get('supply_delay_days', 1)} days. Critical SKUs: Coffee Beans, Eco Cups.",
                    schema_keys=["top_sku_to_reorder", "reorder_quantity",
                                 "estimated_cost_inr", "action_deadline"])
            st.json(plan)
