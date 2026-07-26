"""
Shared ui_theme.py for FreightQuote AI & FranchiseOps AI
Corporate Blue/Navy UI styling, layout cards, and status badges.
"""
import streamlit as st

COLORS = {
    "bg_main":       "#f7f9fc",
    "bg_card":       "#ffffff",
    "bg_alt":        "#eef2f8",
    "text_heading":  "#0b2545",
    "text_body":     "#1c3151",
    "text_main":     "#1c3151",
    "text_muted":    "#5b6b82",
    "border":        "#d7dfe9",
    "accent":        "#1d4ed8",
    "accent_subtle": "#3b6fe0",
    "accent_text":   "#ffffff",
    "cyan":          "#e8f1fb",
    "pink":          "#fdeef2",
    "green":         "#16a34a",
    "yellow":        "#d97706",
    "red":           "#dc2626",
}

NEO_BRUTALIST_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Space+Grotesk:wght@600;700&family=JetBrains+Mono:wght@500;700&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
    color: {COLORS["text_body"]};
    background-color: {COLORS["bg_main"]};
}}

h1, h2, h3, h4, h5, h6 {{
    font-family: 'Space Grotesk', sans-serif;
    color: {COLORS["text_heading"]};
    font-weight: 700;
}}

.pn-card {{
    background: {COLORS["bg_card"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 2px 8px rgba(11, 37, 69, 0.06);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}}
.pn-card:hover {{
    transform: translateY(-1px);
    box-shadow: 0 6px 16px rgba(11, 37, 69, 0.10);
}}
.pn-card-alt {{
    background: {COLORS["cyan"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 2px 8px rgba(11, 37, 69, 0.06);
}}

.pn-badge {{
    display: inline-block;
    padding: 4px 12px;
    border: 1px solid {COLORS["border"]};
    border-radius: 6px;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    font-size: 13px;
    box-shadow: 0 1px 3px rgba(11, 37, 69, 0.08);
    text-transform: uppercase;
}}
.agent-badge {{
    display: inline-block;
    padding: 4px 14px;
    background: {COLORS["accent"]};
    color: {COLORS["accent_text"]};
    border: 1px solid {COLORS["accent"]};
    border-radius: 8px;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 14px;
    box-shadow: 0 2px 6px rgba(29, 78, 216, 0.25);
}}

/* Streamlit Buttons */
div.stButton > button {{
    background: #1d4ed8 !important;
    color: #ffffff !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700 !important;
    border: 1px solid #1d4ed8 !important;
    border-radius: 10px !important;
    padding: 10px 22px !important;
    box-shadow: 0 2px 6px rgba(29, 78, 216, 0.25) !important;
    transition: all 0.15s ease !important;
}}
div.stButton > button:hover {{
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(29, 78, 216, 0.35) !important;
    background: #1e40af !important;
}}

/* Streamlit Inputs & Selectboxes */
div[data-baseweb="input"] > div, div[data-baseweb="select"] > div {{
    background: #ffffff !important;
    border: 1px solid #d7dfe9 !important;
    border-radius: 8px !important;
    box-shadow: 0 1px 3px rgba(11, 37, 69, 0.05) !important;
}}

/* Streamlit Tabs */
button[data-baseweb="tab"] {{
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700 !important;
    color: #5b6b82 !important;
}}
button[data-baseweb="tab"][aria-selected="true"] {{
    color: #0b2545 !important;
    border-bottom: 3px solid #1d4ed8 !important;
}}
</style>
"""

def inject_css():
    st.markdown(NEO_BRUTALIST_CSS, unsafe_allow_html=True)

def apply_theme():
    inject_css()

def render_header(title, subtitle="", icon="⚡"):
    inject_css()
    st.markdown(f"""
    <div style="background:{COLORS['bg_card']};border:1px solid {COLORS['border']};border-radius:14px;padding:22px 28px;margin-bottom:24px;box-shadow:0 2px 8px rgba(11,37,69,0.06);">
        <div style="display:flex;align-items:center;gap:16px;">
            <div style="font-size:42px;line-height:1;">{icon}</div>
            <div>
                <h1 style="margin:0;font-size:26px;letter-spacing:-0.5px;">{title}</h1>
                <p style="margin:4px 0 0;color:{COLORS['text_muted']};font-size:14px;">{subtitle}</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_card(content, alt=False):
    c_class = "pn-card-alt" if alt else "pn-card"
    st.markdown(f'<div class="{c_class}">{content}</div>', unsafe_allow_html=True)

def risk_badge(text, level="Low"):
    color_map = {"Low": COLORS["green"], "Medium": COLORS["yellow"], "High": COLORS["red"], "Critical": COLORS["red"]}
    c = color_map.get(level, COLORS["cyan"])
    return f'<span class="pn-badge" style="background:{c};color:#ffffff;">{text}</span>'