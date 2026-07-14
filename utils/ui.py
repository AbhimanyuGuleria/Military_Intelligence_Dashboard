"""Shared presentation utilities for the SignalWatch workspace.

These helpers intentionally contain no data or application state so page logic
remains independent of the visual system.
"""

import altair as alt
import streamlit as st


COLORS = {
    "primary": "#7BD9FF",
    "secondary": "#E9C349",
    "critical": "#FF2B2B",
    "warning": "#FFA500",
    "safe": "#09AB3B",
    "text": "#DDE3E7",
    "muted": "#BCC8D0",
    "grid": "#3D494E",
    # Legacy mappings to prevent KeyErrors
    "teal": "#7BD9FF",
    "blue": "#7BD9FF",
    "indigo": "#E9C349",
    "crimson": "#FF2B2B",
    "amber": "#FFA500",
}


def apply_theme() -> None:
    """Inject the Aegis Command visual system into a Streamlit page."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@600;700;800&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500;600&display=swap');

        :root {
            --bg: #0E1417;
            --panel: rgba(28, 31, 38, 0.7);
            --line: rgba(134, 147, 153, 0.1);
            --outline-variant: #3D494E;
            --text: #DDE3E7;
            --muted: #BCC8D0;
            --primary: #7BD9FF;
            --on-primary: #003545;
            --secondary: #E9C349;
            --red: #FF2B2B;
            --green: #09AB3B;
            --amber: #FFA500;
        }

        /* Tactical Grid Background */
        .stApp {
            background-color: var(--bg);
            background-image: radial-gradient(rgba(123, 217, 255, 0.035) 1px, transparent 1px);
            background-size: 32px 32px;
            color: var(--text);
            font-family: Inter, sans-serif;
        }

        .block-container {
            max-width: 1450px;
            padding-top: 2.35rem;
            padding-bottom: 3rem;
        }

        /* Glassmorphism Header */
        [data-testid="stHeader"] {
            background: rgba(14, 20, 23, 0.75);
            border-bottom: 1px solid var(--line);
            backdrop-filter: blur(20px);
        }

        [data-testid="stToolbar"] {
            right: 1rem;
        }

        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background: #111619;
            border-right: 1px solid var(--line);
        }

        [data-testid="stSidebar"] > div:first-child {
            padding-top: 1.4rem;
        }

        [data-testid="stSidebar"] .stMarkdown h1,
        [data-testid="stSidebar"] .stMarkdown h2,
        [data-testid="stSidebar"] .stMarkdown h3 {
            margin-top: .75rem;
        }

        /* Typography */
        h1, h2, h3 {
            color: var(--text) !important;
            font-family: 'Hanken Grotesk', Inter, sans-serif;
            letter-spacing: -0.02em;
        }

        h1 {
            font-size: 2.2rem !important;
            font-weight: 700 !important;
        }

        h2 {
            font-size: 1.4rem !important;
            font-weight: 600 !important;
            margin-top: 1.7rem !important;
        }

        p, li, [data-testid="stCaptionContainer"] {
            color: var(--muted);
            line-height: 1.6;
        }

        /* Tactical HUD Metrics */
        div[data-testid="stMetric"] {
            min-height: 112px;
            padding: 1rem 1.05rem;
            background: var(--panel);
            backdrop-filter: blur(20px);
            border: 1px solid var(--line);
            border-radius: 4px !important;
            transition: border-color .18s ease;
        }

        div[data-testid="stMetric"]:hover {
            border-color: rgba(123, 217, 255, 0.4);
        }

        div[data-testid="stMetricLabel"] {
            color: var(--muted);
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.7rem;
            font-weight: 500;
            letter-spacing: 0.1em;
            text-transform: uppercase;
        }

        div[data-testid="stMetricValue"] {
            color: var(--text);
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.45rem;
            font-weight: 600;
        }

        div[data-testid="stMetricDelta"] svg {
            fill: var(--primary);
        }

        /* Soft-Geometric Buttons */
        .stButton > button, .stDownloadButton > button, [data-testid="stBaseButton-primary"] {
            border-radius: 4px !important;
            font-weight: 600;
            transition: all 0.18s ease;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.8rem;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }

        /* Primary Button */
        [data-testid="stBaseButton-primary"],
        .stButton > button[kind="primary"] {
            background-color: var(--primary) !important;
            color: var(--on-primary) !important;
            border: 1px solid var(--primary) !important;
        }

        [data-testid="stBaseButton-primary"]:hover,
        .stButton > button[kind="primary"]:hover {
            opacity: 0.9;
        }

        /* Secondary/Ghost Button */
        .stButton > button[kind="secondary"],
        .stDownloadButton > button {
            background-color: transparent !important;
            color: var(--text) !important;
            border: 1px solid var(--line) !important;
        }

        .stButton > button[kind="secondary"]:hover,
        .stDownloadButton > button:hover {
            border-color: var(--primary) !important;
            color: var(--primary) !important;
        }

        /* Inputs & Dropdowns */
        [data-baseweb="select"] > div,
        [data-baseweb="input"] > div,
        [data-baseweb="base-input"] {
            background-color: #12181b !important;
            border: 1px solid var(--outline-variant) !important;
            border-radius: 4px !important;
            color: var(--text) !important;
        }

        [data-baseweb="select"] > div:hover,
        [data-baseweb="input"] > div:focus-within {
            border-color: var(--primary) !important;
        }

        /* Form Container */
        [data-testid="stForm"] {
            background-color: rgba(22, 28, 31, 0.6);
            padding: 1.35rem;
            border: 1px solid var(--line);
            border-radius: 4px !important;
        }

        /* File Uploader */
        [data-testid="stFileUploader"] {
            background: rgba(22, 28, 31, 0.4);
            border: 1px dashed rgba(123, 217, 255, 0.25);
            padding: 0.7rem;
            border-radius: 4px !important;
        }

        /* Tabs */
        [data-baseweb="tab-list"] {
            gap: 0.45rem;
            border-bottom: 1px solid var(--line);
        }

        button[data-baseweb="tab"] {
            color: var(--muted);
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.8rem;
            font-weight: 500;
            padding: 0.65rem 0.85rem;
            text-transform: uppercase;
        }

        button[data-baseweb="tab"][aria-selected="true"] {
            color: var(--primary);
            border-bottom-color: var(--primary) !important;
        }

        /* Tables & DataFrames */
        [data-testid="stDataFrame"] {
            border: 1px solid var(--line);
            border-radius: 4px !important;
            overflow: hidden;
        }

        [data-testid="stVerticalBlockBorderWrapper"] {
            border-color: var(--line);
            border-radius: 4px !important;
        }

        /* Alerts & Status Boxes */
        [data-testid="stAlert"] {
            border-radius: 4px !important;
            border: 1px solid var(--line);
            background-color: rgba(22, 28, 31, 0.8);
        }

        hr {
            border-color: var(--line);
            margin: 1.8rem 0;
        }

        /* Scrollbars */
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }

        ::-webkit-scrollbar-track {
            background: var(--bg);
        }

        ::-webkit-scrollbar-thumb {
            background: var(--outline-variant);
            border-radius: 2px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: var(--primary);
        }

        /* Aegis Kicker Status Pip */
        .intel-kicker {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            color: var(--primary);
            background: rgba(123, 217, 255, 0.08);
            border: 1px solid rgba(123, 217, 255, 0.2);
            border-radius: 4px;
            padding: 0.28rem 0.6rem;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.7rem;
            font-weight: 600;
            letter-spacing: 0.1em;
            text-transform: uppercase;
        }

        .intel-kicker:before {
            content: '';
            width: 0.38rem;
            height: 0.38rem;
            background: var(--primary);
            border-radius: 50%;
            box-shadow: 0 0 8px var(--primary);
        }

        /* Command Center Banner */
        .intel-hero {
            position: relative;
            overflow: hidden;
            padding: 1.75rem 1.9rem;
            border-radius: 4px;
            background: linear-gradient(135deg, rgba(22, 28, 31, 0.85) 0%, rgba(14, 20, 23, 0.75) 100%);
            border: 1px solid var(--line);
            margin-bottom: 1.4rem;
            animation: intel-rise 0.45s ease-out both;
        }

        .intel-hero:after {
            content: '';
            position: absolute;
            width: 22rem;
            height: 22rem;
            right: -9rem;
            top: -15rem;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(123, 217, 255, 0.18), transparent 65%);
            pointer-events: none;
        }

        .intel-hero h1 {
            margin: 0.75rem 0 0.45rem !important;
            max-width: 800px;
        }

        .intel-hero-copy {
            max-width: 780px;
            color: var(--muted);
            line-height: 1.6;
        }

        .intel-section {
            padding: 1.1rem 1.2rem;
            margin: 0.7rem 0 1.1rem;
            background: rgba(22, 28, 31, 0.5);
            border: 1px solid var(--line);
            border-radius: 4px;
        }

        @keyframes intel-rise {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Render tactical sidebar header
    st.sidebar.markdown(
        '<div class="sidebar-header" style="padding: 0.8rem 0; border-bottom: 1px solid rgba(134, 147, 153, 0.1); margin-bottom: 1.5rem; text-align: center;">'
        '<div class="intel-kicker" style="font-size: 0.6rem; padding: 0.15rem 0.45rem;">SYSTEM SECURE</div>'
        '<h3 style="margin: 0.6rem 0 0; font-size: 1.3rem; font-weight: 700; color: #7BD9FF !important; font-family: \'Hanken Grotesk\', sans-serif; letter-spacing: -0.03em;">SIGNALWATCH</h3>'
        '<p style="margin: 0.1rem 0 0; font-size: 0.6rem; font-family: \'JetBrains Mono\', monospace; color: #BCC8D0; letter-spacing: 0.08em; text-transform: uppercase; opacity: 0.8;">Unit: SW-1</p>'
        '</div>',
        unsafe_allow_html=True
    )


def hero(kicker: str, title: str, description: str) -> None:
    st.markdown(
        f'<section class="intel-hero"><div class="intel-kicker">{kicker}</div><h1>{title}</h1><div class="intel-hero-copy">{description}</div></section>',
        unsafe_allow_html=True,
    )


def chart_style(chart: alt.Chart) -> alt.Chart:
    """Apply readable dark-mode defaults to an Altair chart matching Aegis Command System."""
    return chart.configure_view(
        strokeOpacity=0
    ).configure_axis(
        domain=False,
        gridColor=COLORS["grid"],
        gridOpacity=0.4,
        labelColor=COLORS["muted"],
        titleColor=COLORS["muted"],
        labelFont="Inter, sans-serif",
        titleFont="Inter, sans-serif",
    ).configure_legend(
        labelColor=COLORS["muted"],
        titleColor=COLORS["text"],
        labelFont="Inter, sans-serif",
        titleFont="Inter, sans-serif",
    )
