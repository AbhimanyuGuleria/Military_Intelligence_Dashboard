"""Shared presentation utilities for the SignalWatch workspace.

These helpers intentionally contain no data or application state so page logic
remains independent of the visual system.
"""

import altair as alt
import streamlit as st


COLORS = {
    "teal": "#62D6C7",
    "blue": "#4C8BF5",
    "indigo": "#8B5CF6",
    "crimson": "#EF4444",
    "amber": "#F5B942",
    "text": "#F1F5F9",
    "muted": "#94A3B8",
    "grid": "#263247",
}


def apply_theme() -> None:
    """Inject the shared dark SaaS visual system into a Streamlit page."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Outfit:wght@500;600;700&display=swap');

        :root { --bg:#0B0F19; --panel:rgba(21,30,46,.82); --line:rgba(255,255,255,.08); --text:#F1F5F9; --muted:#94A3B8; --teal:#62D6C7; --blue:#4C8BF5; --indigo:#8B5CF6; --red:#EF4444; }
        .stApp { background: radial-gradient(circle at 8% -10%, rgba(76,139,245,.18), transparent 28rem), radial-gradient(circle at 92% 0%, rgba(98,214,199,.11), transparent 26rem), var(--bg); color:var(--text); font-family:Inter, sans-serif; }
        .block-container { max-width: 1450px; padding-top: 2.35rem; padding-bottom: 3rem; }
        [data-testid="stHeader"] { background:rgba(11,15,25,.72); border-bottom:1px solid rgba(255,255,255,.04); backdrop-filter:blur(16px); }
        [data-testid="stToolbar"] { right:1rem; }
        [data-testid="stSidebar"] { background:linear-gradient(180deg,#111927 0%,#0d1421 100%); border-right:1px solid var(--line); }
        [data-testid="stSidebar"] > div:first-child { padding-top:1.4rem; }
        [data-testid="stSidebar"] .stMarkdown h1, [data-testid="stSidebar"] .stMarkdown h2, [data-testid="stSidebar"] .stMarkdown h3 { margin-top: .75rem; }
        h1,h2,h3 { color:var(--text) !important; font-family:Outfit,Inter,sans-serif; letter-spacing:-.025em; }
        h1 { font-size:2.2rem !important; } h2 { font-size:1.4rem !important; margin-top:1.7rem !important; }
        p,li,[data-testid="stCaptionContainer"] { color:var(--muted); line-height:1.6; }
        div[data-testid="stMetric"] { min-height:112px; padding:1rem 1.05rem; background:linear-gradient(145deg,rgba(29,42,64,.88),rgba(16,24,39,.86)); border:1px solid var(--line); border-radius:15px; box-shadow:0 10px 28px rgba(0,0,0,.18); transition:transform .18s ease,border-color .18s ease,box-shadow .18s ease; }
        div[data-testid="stMetric"]:hover { transform:translateY(-3px); border-color:rgba(98,214,199,.4); box-shadow:0 16px 34px rgba(0,0,0,.25); }
        div[data-testid="stMetricLabel"] { color:var(--muted); font-size:.75rem; letter-spacing:.07em; text-transform:uppercase; }
        div[data-testid="stMetricValue"] { color:var(--text); font-family:Outfit,Inter,sans-serif; font-size:1.45rem; }
        div[data-testid="stMetricDelta"] svg { fill:var(--teal); }
        .stButton > button, .stDownloadButton > button, [data-testid="stBaseButton-primary"] { border:1px solid rgba(98,214,199,.38); border-radius:10px; background:linear-gradient(135deg,#176d6b,#267eaa); color:#f8ffff; font-weight:600; transition:all .18s ease; }
        .stButton > button:hover, .stDownloadButton > button:hover { transform:translateY(-2px); border-color:var(--teal); box-shadow:0 10px 22px rgba(38,126,170,.25); color:white; }
        .stButton > button[kind="secondary"] { background:#182438; border-color:var(--line); }
        [data-baseweb="select"] > div, [data-baseweb="input"] > div, [data-baseweb="base-input"] { background:#121c2d !important; border-color:rgba(148,163,184,.25) !important; border-radius:9px !important; color:var(--text) !important; }
        [data-baseweb="select"] > div:hover, [data-baseweb="input"] > div:focus-within { border-color:var(--teal) !important; box-shadow:0 0 0 1px rgba(98,214,199,.28) !important; }
        [data-testid="stFileUploader"] { background:rgba(21,30,46,.7); border:1px dashed rgba(98,214,199,.35); padding:.7rem; border-radius:13px; }
        [data-testid="stForm"] { background:rgba(21,30,46,.72); padding:1.35rem; border:1px solid var(--line); border-radius:16px; }
        [data-baseweb="tab-list"] { gap:.45rem; border-bottom:1px solid var(--line); }
        button[data-baseweb="tab"] { color:var(--muted); font-weight:600; padding:.65rem .85rem; }
        button[data-baseweb="tab"][aria-selected="true"] { color:var(--teal); border-bottom-color:var(--teal) !important; }
        [data-testid="stAlert"] { border-radius:12px; border:1px solid var(--line); background:rgba(21,30,46,.84); }
        [data-testid="stDataFrame"] { border:1px solid var(--line); border-radius:14px; overflow:hidden; }
        [data-testid="stVerticalBlockBorderWrapper"] { border-color:var(--line); border-radius:14px; }
        hr { border-color:var(--line); margin:1.8rem 0; }
        ::-webkit-scrollbar { width:10px; height:10px; } ::-webkit-scrollbar-track { background:#0b0f19; } ::-webkit-scrollbar-thumb { background:#2b3b55; border-radius:10px; } ::-webkit-scrollbar-thumb:hover { background:#62d6c7; }
        .intel-kicker { display:inline-flex; align-items:center; gap:.4rem; color:var(--teal); background:rgba(98,214,199,.09); border:1px solid rgba(98,214,199,.2); border-radius:999px; padding:.28rem .6rem; font-size:.7rem; font-weight:700; letter-spacing:.12em; text-transform:uppercase; }
        .intel-kicker:before { content:''; width:.38rem; height:.38rem; background:var(--teal); border-radius:50%; box-shadow:0 0 12px var(--teal); }
        .intel-hero { position:relative; overflow:hidden; padding:1.75rem 1.9rem; border-radius:20px; background:linear-gradient(120deg,rgba(25,43,68,.9),rgba(23,30,55,.78)); border:1px solid rgba(255,255,255,.1); box-shadow:0 18px 45px rgba(0,0,0,.2); margin-bottom:1.4rem; animation:intel-rise .45s ease-out both; }
        .intel-hero:after { content:''; position:absolute; width:22rem; height:22rem; right:-9rem; top:-15rem; border-radius:50%; background:radial-gradient(circle,rgba(98,214,199,.23),transparent 65%); pointer-events:none; }
        .intel-hero h1 { margin:.75rem 0 .45rem !important; max-width:800px; } .intel-hero-copy { max-width:780px; color:#bcc9d9; line-height:1.6; }
        .intel-section { padding:1.1rem 1.2rem; margin:.7rem 0 1.1rem; background:rgba(21,30,46,.56); border:1px solid var(--line); border-radius:15px; }
        @keyframes intel-rise { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:translateY(0); } }
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero(kicker: str, title: str, description: str) -> None:
    st.markdown(
        f'<section class="intel-hero"><div class="intel-kicker">{kicker}</div><h1>{title}</h1><div class="intel-hero-copy">{description}</div></section>',
        unsafe_allow_html=True,
    )


def chart_style(chart: alt.Chart) -> alt.Chart:
    """Apply readable dark-mode defaults to an Altair chart without altering data."""
    return chart.configure_view(strokeOpacity=0).configure_axis(
        domain=False, gridColor=COLORS["grid"], gridOpacity=0.65,
        labelColor=COLORS["muted"], titleColor=COLORS["muted"],
    ).configure_legend(labelColor=COLORS["muted"], titleColor=COLORS["text"])
