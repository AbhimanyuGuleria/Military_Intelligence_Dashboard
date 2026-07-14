from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st
from utils.data_loader import attach_display_summaries, read_historical_data, valid_date_part
from utils.ui import COLORS, apply_theme, chart_style, hero


st.set_page_config(page_title="Military Intelligence Dashboard - AI Intelligence Report", page_icon="🧠", layout="wide")
apply_theme()



USECOLS = [
    "eventid",
    "iyear",
    "imonth",
    "iday",
    "country_txt",
    "region_txt",
    "city",
    "provstate",
    "attacktype1_txt",
    "weaptype1_txt",
    "targtype1_txt",
    "gname",
    "success",
    "suicide",
    "nkill",
    "nwound",
    "latitude",
    "longitude",
]


def threat_band_from_impact(impact):
    if impact <= 2:
        return "Low"
    if impact <= 10:
        return "Medium"
    return "High"


def top_value(series, default="Unavailable"):
    clean = series.dropna() if series is not None else pd.Series(dtype="object")
    if clean.empty:
        return default
    return clean.value_counts().idxmax()


@st.cache_data
def load_data():
    df = read_historical_data(USECOLS)

    for column in ["iyear", "imonth", "iday", "success", "suicide", "nkill", "nwound", "latitude", "longitude"]:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

    df["nkill"] = df["nkill"].fillna(0)
    df["nwound"] = df["nwound"].fillna(0)
    df["success"] = df["success"].fillna(0).astype(int)
    df["suicide"] = df["suicide"].fillna(0).astype(int)

    df = df.dropna(subset=["country_txt", "region_txt", "attacktype1_txt", "weaptype1_txt", "targtype1_txt", "gname"])
    df["impact"] = df["nkill"] + df["nwound"]
    df["threat_band"] = df["impact"].apply(threat_band_from_impact)

    if {"iyear", "imonth", "iday"}.issubset(df.columns):
        df["event_date"] = pd.to_datetime(
            {
                "year": df["iyear"].astype("float64"),
                "month": valid_date_part(df["imonth"]),
                "day": valid_date_part(df["iday"]),
            },
            errors="coerce",
        )
    else:
        df["event_date"] = pd.NaT

    return df


def build_summary_text(df, selected_year, selected_region):
    incidents = len(df)
    fatalities = int(df["nkill"].sum()) if "nkill" in df.columns else 0
    injuries = int(df["nwound"].sum()) if "nwound" in df.columns else 0
    countries = int(df["country_txt"].nunique()) if "country_txt" in df.columns else 0

    top_country = top_value(df["country_txt"] if "country_txt" in df.columns else None)
    top_group = top_value(df["gname"] if "gname" in df.columns else None)
    top_attack = top_value(df["attacktype1_txt"] if "attacktype1_txt" in df.columns else None)
    top_weapon = top_value(df["weaptype1_txt"] if "weaptype1_txt" in df.columns else None)
    top_target = top_value(df["targtype1_txt"] if "targtype1_txt" in df.columns else None)

    threat_level = threat_band_from_impact((df["impact"].median() if "impact" in df.columns else 0))

    return f"""
Executive AI Intelligence Brief

Scope:
- Year filter: {selected_year}
- Region filter: {selected_region}

Key Findings:
- Total incidents: {incidents:,}
- Fatalities: {fatalities:,}
- Injuries: {injuries:,}
- Countries covered: {countries:,}
- Assessed threat band: {threat_level}

Pattern Summary:
- Most affected country: {top_country}
- Most active group: {top_group}
- Most common attack type: {top_attack}
- Most common weapon type: {top_weapon}
- Most common target type: {top_target}

Analyst Note:
The filtered dataset shows where activity is concentrated and which actors or tactics dominate the selected scope. Use the charts below to validate the trend before drawing operational conclusions.
"""


def main():
    hero("Executive synthesis", "AI intelligence report", "Generate a concise, source-aware analytical brief from the selected historical records.")
    st.markdown(
        "Generate a compact intelligence brief from GTD data. The report combines key metrics, trend visuals, dominant actors, and a downloadable narrative summary."
    )

    loading_message = st.empty()
    loading_message.info("Hang tight — we are loading the data and assembling the intelligence report.")

    try:
        with st.spinner("Building AI intelligence report..."):
            df = load_data()
        loading_message.empty()
    except Exception as error:
        loading_message.empty()
        st.error(f"Unable to load report data: {error}")
        return

    years = sorted(df["iyear"].dropna().astype(int).unique().tolist()) if "iyear" in df.columns else []
    st.sidebar.header("Report Filters")

    selected_year = st.sidebar.selectbox("Year", ["All"] + years)
    region_options = ["All"] + sorted(df["region_txt"].dropna().unique().tolist()) if "region_txt" in df.columns else ["All"]
    selected_region = st.sidebar.selectbox("Region", region_options)
    show_only_high_impact = st.sidebar.checkbox("Show only high-impact cases", value=False)

    filtered_df = df.copy()
    if selected_year != "All":
        filtered_df = filtered_df[filtered_df["iyear"] == selected_year]
    if selected_region != "All":
        filtered_df = filtered_df[filtered_df["region_txt"] == selected_region]
    if show_only_high_impact:
        filtered_df = filtered_df[filtered_df["impact"] >= 10]

    if filtered_df.empty:
        st.warning("No records match the current filters.")
        return

    incidents = len(filtered_df)
    fatalities = int(filtered_df["nkill"].sum())
    injuries = int(filtered_df["nwound"].sum())
    countries = int(filtered_df["country_txt"].nunique())
    groups = int(filtered_df["gname"].nunique())
    threat_band = threat_band_from_impact(filtered_df["impact"].median())

    top_country = top_value(filtered_df["country_txt"])
    top_group = top_value(filtered_df["gname"])
    top_attack = top_value(filtered_df["attacktype1_txt"])
    top_weapon = top_value(filtered_df["weaptype1_txt"])
    top_target = top_value(filtered_df["targtype1_txt"])

    st.subheader("Key Intelligence Indicators")
    metric_col1, metric_col2, metric_col3, metric_col4, metric_col5 = st.columns(5)
    metric_col1.metric("Incidents", f"{incidents:,}")
    metric_col2.metric("Fatalities", f"{fatalities:,}")
    metric_col3.metric("Injuries", f"{injuries:,}")
    metric_col4.metric("Countries", f"{countries:,}")
    metric_col5.metric("Threat Band", threat_band)

    st.markdown("---")

    summary_text = build_summary_text(filtered_df, selected_year, selected_region)
    st.subheader("Executive Summary")
    st.info(summary_text)

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("Top Countries")
        country_counts = filtered_df["country_txt"].value_counts().head(10).reset_index()
        country_counts.columns = ["Country", "Incidents"]
        country_chart = (
            alt.Chart(country_counts)
            .mark_bar(color=COLORS["primary"])
            .encode(
                x=alt.X("Incidents:Q", title="Incidents"),
                y=alt.Y("Country:N", sort="-x", title="Country"),
                tooltip=["Country:N", "Incidents:Q"],
            )
            .properties(height=320)
        )
        st.altair_chart(chart_style(country_chart), use_container_width=True)

    with chart_col2:
        st.subheader("Top Terrorist Groups")
        group_counts = filtered_df["gname"].value_counts().head(10).reset_index()
        group_counts.columns = ["Group", "Incidents"]
        group_chart = (
            alt.Chart(group_counts)
            .mark_bar(color=COLORS["secondary"])
            .encode(
                x=alt.X("Incidents:Q", title="Incidents"),
                y=alt.Y("Group:N", sort="-x", title="Group"),
                tooltip=["Group:N", "Incidents:Q"],
            )
            .properties(height=320)
        )
        st.altair_chart(chart_style(group_chart), use_container_width=True)

    detail_tabs = st.tabs(["Attack Types", "Weapons", "Targets", "Risk Bands"])

    with detail_tabs[0]:
        attack_counts = filtered_df["attacktype1_txt"].value_counts().head(10).reset_index()
        attack_counts.columns = ["Attack Type", "Incidents"]
        attack_chart = (
            alt.Chart(attack_counts)
            .mark_bar(color=COLORS["critical"])
            .encode(
                x=alt.X("Incidents:Q", title="Incidents"),
                y=alt.Y("Attack Type:N", sort="-x", title="Attack Type"),
                tooltip=["Attack Type:N", "Incidents:Q"],
            )
            .properties(height=300)
        )
        st.altair_chart(chart_style(attack_chart), use_container_width=True)

    with detail_tabs[1]:
        weapon_counts = filtered_df["weaptype1_txt"].value_counts().head(10).reset_index()
        weapon_counts.columns = ["Weapon", "Incidents"]
        weapon_chart = (
            alt.Chart(weapon_counts)
            .mark_bar(color=COLORS["secondary"])
            .encode(
                x=alt.X("Incidents:Q", title="Incidents"),
                y=alt.Y("Weapon:N", sort="-x", title="Weapon"),
                tooltip=["Weapon:N", "Incidents:Q"],
            )
            .properties(height=300)
        )
        st.altair_chart(chart_style(weapon_chart), use_container_width=True)

    with detail_tabs[2]:
        target_counts = filtered_df["targtype1_txt"].value_counts().head(10).reset_index()
        target_counts.columns = ["Target", "Incidents"]
        target_chart = (
            alt.Chart(target_counts)
            .mark_bar(color=COLORS["primary"])
            .encode(
                x=alt.X("Incidents:Q", title="Incidents"),
                y=alt.Y("Target:N", sort="-x", title="Target"),
                tooltip=["Target:N", "Incidents:Q"],
            )
            .properties(height=300)
        )
        st.altair_chart(chart_style(target_chart), use_container_width=True)

    with detail_tabs[3]:
        band_counts = filtered_df["threat_band"].value_counts().reset_index()
        band_counts.columns = ["Threat Band", "Cases"]
        band_chart = (
            alt.Chart(band_counts)
            .mark_bar()
            .encode(
                x=alt.X("Threat Band:N", title="Threat Band"),
                y=alt.Y("Cases:Q", title="Cases"),
                color=alt.Color("Threat Band:N", scale=alt.Scale(domain=["Low", "Medium", "High"], range=[COLORS["safe"], COLORS["warning"], COLORS["critical"]]), legend=None),
                tooltip=["Threat Band:N", "Cases:Q"],
            )
            .properties(height=300)
        )
        st.altair_chart(chart_style(band_chart), use_container_width=True)

    st.markdown("---")

    insight_col1, insight_col2 = st.columns(2)

    with insight_col1:
        st.subheader("Analyst Notes")
        st.write(
            f"- Most affected country: {top_country}\n"
            f"- Most active group: {top_group}\n"
            f"- Most common attack type: {top_attack}\n"
            f"- Most common weapon: {top_weapon}\n"
            f"- Most common target: {top_target}"
        )

    with insight_col2:
        st.subheader("Recommended Focus")
        if threat_band == "High":
            st.error("Increase monitoring on the dominant countries, groups, and attack methods in this filtered scope.")
        elif threat_band == "Medium":
            st.warning("Maintain active monitoring and review the strongest trends for early warning signs.")
        else:
            st.success("Threat band is relatively low in this filtered view, but keep trend monitoring active.")

    st.markdown("---")

    st.subheader("Recent High-Impact Records")
    recent_df = filtered_df.sort_values(by=["impact", "event_date"], ascending=[False, False], na_position="last").head(25).copy()
    recent_df = attach_display_summaries(recent_df)
    if "event_date" in recent_df.columns:
        recent_df["event_date"] = recent_df["event_date"].dt.strftime("%Y-%m-%d")

    display_columns = [
        column
        for column in [
            "event_date",
            "iyear",
            "country_txt",
            "region_txt",
            "city",
            "provstate",
            "gname",
            "attacktype1_txt",
            "weaptype1_txt",
            "targtype1_txt",
            "nkill",
            "nwound",
            "impact",
            "summary",
        ]
        if column in recent_df.columns
    ]
    st.dataframe(recent_df[display_columns], use_container_width=True, hide_index=True)

    report_text = f"""
AI INTELLIGENCE REPORT

Scope
- Year: {selected_year}
- Region: {selected_region}
- High-impact filter: {'Enabled' if show_only_high_impact else 'Disabled'}

Summary
- Incidents: {incidents:,}
- Fatalities: {fatalities:,}
- Injuries: {injuries:,}
- Countries: {countries:,}
- Threat band: {threat_band}

Dominant Patterns
- Country: {top_country}
- Group: {top_group}
- Attack type: {top_attack}
- Weapon: {top_weapon}
- Target: {top_target}

Assessment
The filtered GTD slice shows the strongest concentration around the dominant countries, actors, and methods above. Use the trend and breakdown charts to validate the operational picture before making planning decisions.
"""

    st.download_button(
        label="📄 Download Intelligence Brief",
        data=report_text,
        file_name="AI_Intelligence_Report.txt",
        mime="text/plain",
    )


if __name__ == "__main__":
    main()
