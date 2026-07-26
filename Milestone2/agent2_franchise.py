"""
agent2_franchise.py — Enriched Agent 2: Outlet Territory Clustering & City Weather
New features: City demand surge chart, revenue vs weather scatter, AI territory advisory.
Extended Indian cities + global franchise locations.
"""
import pandas as pd
import streamlit as st
import plotly.express as px
from ui_theme import render_card, COLORS
from db import get_conn
from weather_context import get_city_weather
from llm_engine_franchise import orchestrate_3_agents_query

# ── Full outlet / city list (heavy India coverage) ───────────────────────────
INDIA_CITIES = [
    "Mumbai (MH)", "Delhi (DL)", "Bengaluru (KA)", "Hyderabad (TS)",
    "Chennai (TN)", "Pune (MH)", "Kolkata (WB)", "Ahmedabad (GJ)",
    "Jaipur (RJ)", "Surat (GJ)", "Lucknow (UP)", "Chandigarh (PB)",
    "Bhopal (MP)", "Indore (MP)", "Nagpur (MH)", "Coimbatore (TN)",
    "Kochi (KL)", "Visakhapatnam (AP)", "Patna (BR)", "Ranchi (JH)",
]
GLOBAL_CITIES = [
    "Chicago (IL)", "Los Angeles (CA)", "New York (NY)", "Houston (TX)",
    "London (UK)", "Dubai (AE)", "Singapore (SG)",
]
ALL_CITIES = INDIA_CITIES + GLOBAL_CITIES


def render_agent2_franchise(agent2_c, agent2_r, username, db_stats, a1_ctx, a3_ctx,
                             send_alert, confidence_band):
    render_card('<h3 style="margin:0;">🏬 Agent 2: Outlet Territory Clustering</h3>')

    with get_conn() as conn:
        try:
            out_df = pd.read_sql("SELECT * FROM outlets", conn)
        except Exception:
            out_df = pd.DataFrame()

    c1, c2 = st.columns([1.3, 1])
    with c1:
        if not out_df.empty:
            st.dataframe(
                out_df[["outlet_id", "outlet_name", "city",
                        "monthly_revenue", "monthly_costs", "tier_cluster"]],
                use_container_width=True, hide_index=True)
            fig = px.scatter(
                out_df, x="monthly_costs", y="monthly_revenue",
                color="tier_cluster", size="staff_headcount",
                hover_name="outlet_name",
                title="Revenue vs Cost Clustering",
                color_discrete_sequence=["#34d399", "#ffd803", "#f87171"])
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              height=280, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        render_card('<h4 style="margin:0 0 10px;">Simulate New Outlet</h4>')
        city_sel = st.selectbox("City", ALL_CITIES)
        new_rev  = st.number_input("Monthly Revenue (₹)", 80000.0, 2000000.0, 380000.0, step=10000.0)
        new_cost = st.number_input("Monthly Costs (₹)", 50000.0, 1500000.0, 260000.0, step=10000.0)
        new_hc   = st.slider("Staff Headcount", 5, 80, 22)
        if st.button("⚡ Predict Tier Cluster", key="btn_predict_tier"):
            idx = (agent2_c.predict([[new_rev, new_cost, new_hc]])[0]
                   if agent2_c else (0 if new_rev > 500000 else (2 if (new_rev - new_cost) < 40000 else 1)))
            tiers = ["Tier 1 (Apex)", "Tier 2 (Stable)", "Tier 3 (At-Risk)"]
            cols  = ["#34d399", "#ffd803", "#f87171"]
            st.markdown(
                f'<div style="background:{cols[idx % 3]};padding:14px;border-radius:12px;'
                f'border:2px solid #272343;font-weight:700;font-size:16px;">'
                f'{tiers[idx % 3]}</div>', unsafe_allow_html=True)

    st.markdown("---")
    tab_demand, tab_corr, tab_ai = st.tabs(
        ["📊 City Demand Surge", "📈 Revenue vs Weather", "🤖 AI Advisory"])

    # ── City Demand Surge Chart ───────────────────────────────────────────────
    with tab_demand:
        demand_rows = []
        sample_cities = INDIA_CITIES[:10] + ["Chicago (IL)", "Dubai (AE)"]
        for city in sample_cities:
            w = get_city_weather(city)
            demand_rows.append({
                "City": city.split(" (")[0],
                "Demand Impact %": w.get("demand_impact_pct", 0),
                "Weather": w.get("status", "Normal"),
            })
        d_df = pd.DataFrame(demand_rows).sort_values("Demand Impact %", ascending=False)
        fig2 = px.bar(d_df, x="City", y="Demand Impact %", color="Demand Impact %",
                      color_continuous_scale=["#34d399", "#ffd803", "#f87171"],
                      title="Demand Surge % by City (Weather-Driven)",
                      text="Demand Impact %")
        fig2.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           height=320, margin=dict(l=10, r=10, t=40, b=80),
                           xaxis_tickangle=-35)
        st.plotly_chart(fig2, use_container_width=True)

    # ── Revenue vs Weather Correlation ────────────────────────────────────────
    with tab_corr:
        if not out_df.empty and "city" in out_df.columns:
            out_df["demand_impact"] = out_df["city"].apply(
                lambda c: get_city_weather(c).get("demand_impact_pct", 0))
            fig3 = px.scatter(out_df, x="demand_impact", y="monthly_revenue",
                              color="tier_cluster", size="staff_headcount",
                              hover_name="outlet_name",
                              trendline="ols",
                              title="Revenue vs Weather Demand Impact",
                              color_discrete_sequence=["#34d399", "#ffd803", "#f87171"])
            fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                               height=300, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("Outlet data with city weather not available.")

    # ── AI Territory Advisory ─────────────────────────────────────────────────
    with tab_ai:
        if st.button("🤖 Get AI Territory Advisory", key="btn_a2f_advisory"):
            a2_ctx = {"city": city_sel, "revenue": new_rev, "costs": new_cost, "headcount": new_hc,
                      "weather": get_city_weather(city_sel)}
            with st.spinner("Generating advisory (~2 sec)..."):
                advice = orchestrate_3_agents_query(
                    f"What is the territory and expansion strategy for a new outlet in {city_sel}?",
                    a1_ctx, a2_ctx, a3_ctx, db_stats)
            st.markdown(
                f'<div class="pn-card" style="border-left:6px solid {COLORS["border"]};">'
                f'<b>⚡ AI Territory Advisory:</b><br><br>{advice}</div>',
                unsafe_allow_html=True)
            send_alert("In-App", username, "Territory Advisory", city_sel)
