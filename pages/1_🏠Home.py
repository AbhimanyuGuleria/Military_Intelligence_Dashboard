import altair as alt
import pandas as pd
import streamlit as st

from utils.data_loader import historical_status, load_live_reports, read_historical_data
from utils.ui import COLORS, apply_theme, chart_style, hero


st.set_page_config(page_title="SignalWatch | Overview", page_icon="🛡️", layout="wide")
apply_theme()


def main() -> None:
    hero("Operational overview", "Intelligence at a glance", "A source-aware summary of the historical database and the current open-source review queue.")
    columns = ["iyear", "country_txt", "region_txt", "attacktype1_txt", "nkill", "nwound"]
    try:
        df = read_historical_data(columns)
        status = historical_status()
        live_reports, live_metadata = load_live_reports()
    except Exception as error:
        st.error(f"Unable to load the dashboard data: {error}")
        return

    df = df.dropna(subset=["iyear"])
    yearly = df.groupby("iyear").size().reset_index(name="Incidents").rename(columns={"iyear": "Year"}).sort_values("Year")
    latest_year = int(yearly["Year"].max())
    latest_count = int(yearly.iloc[-1]["Incidents"])
    prior_count = int(yearly.iloc[-2]["Incidents"]) if len(yearly) > 1 else 0
    delta = latest_count - prior_count

    metrics = st.columns(5)
    metrics[0].metric("Historical incidents", f"{len(df):,}")
    metrics[1].metric("Fatalities", f"{int(df['nkill'].sum()):,}")
    metrics[2].metric("Countries", f"{df['country_txt'].nunique():,}")
    metrics[3].metric(f"Incidents in {latest_year}", f"{latest_count:,}", delta=f"{delta:+,} vs prior year")
    metrics[4].metric("Live reports to review", f"{len(live_reports):,}")

    notice = "Current historical file: " + status["path"].name + f" (through {status['last_year']})."
    if status["last_year"] < 2020:
        st.warning(notice + " Load the licensed 1970–2020 GTD release from Settings to improve historical coverage.")
    else:
        st.success(notice)

    left, right = st.columns([2, 1])
    with left:
        st.subheader("Historical incident trend")
        chart = alt.Chart(yearly).mark_area(line={"color": COLORS["teal"]}, color="#7BD9FF25").encode(
            x=alt.X("Year:Q", title=None), y=alt.Y("Incidents:Q", title="Recorded incidents"),
            tooltip=[alt.Tooltip("Year:Q", format=".0f"), alt.Tooltip("Incidents:Q", format=",")],
        ).properties(height=340)
        st.altair_chart(chart_style(chart), use_container_width=True)
    with right:
        st.subheader("Highest-volume countries")
        top_countries = df["country_txt"].value_counts().head(8).rename_axis("Country").reset_index(name="Incidents")
        chart = alt.Chart(top_countries).mark_bar(color=COLORS["blue"]).encode(
            x=alt.X("Incidents:Q", title=None), y=alt.Y("Country:N", sort="-x", title=None), tooltip=["Country", "Incidents"]
        ).properties(height=340)
        st.altair_chart(chart_style(chart), use_container_width=True)

    st.subheader("Latest open-source reports")
    if live_reports.empty:
        st.info("No live feed is cached yet. Open Live Feed and refresh it, or schedule `python scripts/refresh_live_feed.py` daily.")
    else:
        preview = live_reports[[c for c in ["seen_date", "title", "source", "source_country", "url"] if c in live_reports]].head(8)
        st.dataframe(preview, use_container_width=True, hide_index=True, column_config={"url": st.column_config.LinkColumn("Source link")})
        st.caption(f"Live feed provider: {live_metadata.get('provider', 'Unknown')}. These are unverified articles, not GTD incidents.")


main()
