from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st
from utils.data_loader import attach_display_summaries, read_historical_data, valid_date_part
from utils.ui import apply_theme, hero


st.set_page_config(page_title="Military Intelligence Dashboard - Data Explorer", page_icon="📊", layout="wide")
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


def top_value(series, default="Unavailable"):
    clean = series.dropna() if series is not None else pd.Series(dtype="object")
    if clean.empty:
        return default
    return clean.value_counts().idxmax()


def add_display_summaries(frame: pd.DataFrame) -> pd.DataFrame:
    """Attach text only to the small table currently being rendered."""
    return attach_display_summaries(frame)


@st.cache_data(ttl=60, show_spinner=False, max_entries=2)
def make_download_csv(frame: pd.DataFrame) -> bytes:
    """Cache export bytes briefly instead of retaining them for the session."""
    return frame.to_csv(index=False).encode("utf-8")


def apply_filters(df, selected_years, selected_countries, selected_regions, selected_attacks, selected_weapons, selected_groups, search_text, impact_only):
    filtered = df.copy()

    if selected_years:
        filtered = filtered[filtered["iyear"].isin(selected_years)]
    if selected_countries:
        filtered = filtered[filtered["country_txt"].isin(selected_countries)]
    if selected_regions:
        filtered = filtered[filtered["region_txt"].isin(selected_regions)]
    if selected_attacks:
        filtered = filtered[filtered["attacktype1_txt"].isin(selected_attacks)]
    if selected_weapons:
        filtered = filtered[filtered["weaptype1_txt"].isin(selected_weapons)]
    if selected_groups:
        filtered = filtered[filtered["gname"].isin(selected_groups)]
    if impact_only:
        filtered = filtered[filtered["impact"] >= 10]

    if search_text:
        search_text = search_text.strip()
        if search_text:
            search_mask = (
                filtered["city"].fillna("").str.contains(search_text, case=False)
                | filtered["country_txt"].fillna("").str.contains(search_text, case=False)
                | filtered["provstate"].fillna("").str.contains(search_text, case=False)
                | filtered["gname"].fillna("").str.contains(search_text, case=False)
            )
            filtered = filtered[search_mask]

    return filtered


def main():
    hero("Data workspace", "Global terrorism data explorer", "Filter, inspect, and export the historical dataset while keeping every record in analytical context.")
    st.markdown(
        "Explore, filter, compare, and download the GTD dataset. This page is designed for quick slicing of the data and for inspecting the records behind the visuals."
    )

    loading_message = st.empty()
    loading_message.info("Hang tight — we are loading the dataset and preparing the explorer.")

    try:
        with st.spinner("Loading explorer workspace..."):
            df = load_data()
        loading_message.empty()
    except Exception as error:
        loading_message.empty()
        st.error(f"Unable to load explorer data: {error}")
        return

    years = sorted(df["iyear"].dropna().astype(int).unique().tolist()) if "iyear" in df.columns else []
    year_min = years[0] if years else 0
    year_max = years[-1] if years else 0

    st.sidebar.header("Filter Dataset")

    selected_years = st.sidebar.multiselect("Year", years, default=[])
    selected_countries = st.sidebar.multiselect("Country", sorted(df["country_txt"].dropna().unique().tolist()))
    selected_regions = st.sidebar.multiselect("Region", sorted(df["region_txt"].dropna().unique().tolist()))
    selected_attacks = st.sidebar.multiselect("Attack Type", sorted(df["attacktype1_txt"].dropna().unique().tolist()))
    selected_weapons = st.sidebar.multiselect("Weapon Type", sorted(df["weaptype1_txt"].dropna().unique().tolist()))
    selected_groups = st.sidebar.multiselect("Terrorist Group", sorted(df["gname"].dropna().unique().tolist()))
    impact_only = st.sidebar.checkbox("Show only high-impact cases", value=False)

    search_text = st.text_input("🔍 Search by city, province/state, country, or group")

    filtered_df = apply_filters(
        df,
        selected_years,
        selected_countries,
        selected_regions,
        selected_attacks,
        selected_weapons,
        selected_groups,
        search_text,
        impact_only,
    )

    st.subheader("Dataset Summary")
    metric_col1, metric_col2, metric_col3, metric_col4, metric_col5 = st.columns(5)
    metric_col1.metric("Incidents", f"{len(filtered_df):,}")
    metric_col2.metric("Countries", f"{filtered_df['country_txt'].nunique():,}")
    metric_col3.metric("Fatalities", f"{int(filtered_df['nkill'].sum()):,}")
    metric_col4.metric("Injuries", f"{int(filtered_df['nwound'].sum()):,}")
    metric_col5.metric("High Impact", f"{int((filtered_df['impact'] >= 10).sum()):,}")

    summary_col1, summary_col2 = st.columns([2, 1])

    with summary_col1:
        st.info(
            f"Most affected country: {top_value(filtered_df['country_txt'])}\n\n"
            f"Most active group: {top_value(filtered_df['gname'])}\n\n"
            f"Most common attack type: {top_value(filtered_df['attacktype1_txt'])}\n\n"
            f"Most common weapon type: {top_value(filtered_df['weaptype1_txt'])}"
        )

    with summary_col2:
        st.metric("Records in view", f"{len(filtered_df):,}")
        st.metric("Countries in view", f"{filtered_df['country_txt'].nunique():,}")
        st.metric("Median impact", f"{filtered_df['impact'].median():.1f}")

    if filtered_df.empty:
        st.warning("No records match the current filters.")
        return

    st.markdown("---")

    tabs = st.tabs(["Preview", "Countries", "Attack Types", "Weapons", "Record Details"])

    with tabs[0]:
        st.subheader("Filtered Dataset Preview")
        preview_cols = [
            column
            for column in ["event_date", "iyear", "country_txt", "region_txt", "city", "provstate", "gname", "attacktype1_txt", "weaptype1_txt", "targtype1_txt", "nkill", "nwound", "impact", "summary"]
            if column in filtered_df.columns
        ]
        preview_df = filtered_df.sort_values(by=["impact", "event_date"], ascending=[False, False], na_position="last").head(100).copy()
        preview_df = add_display_summaries(preview_df)
        if "event_date" in preview_df.columns:
            preview_df["event_date"] = preview_df["event_date"].dt.strftime("%Y-%m-%d")
        st.dataframe(preview_df[preview_cols], use_container_width=True, hide_index=True)

    with tabs[1]:
        st.subheader("Top Countries")
        country_counts = filtered_df["country_txt"].value_counts().head(10).reset_index()
        country_counts.columns = ["Country", "Incidents"]
        country_chart = (
            alt.Chart(country_counts)
            .mark_bar(color="#2E86AB")
            .encode(
                x=alt.X("Incidents:Q", title="Incidents"),
                y=alt.Y("Country:N", sort="-x", title="Country"),
                tooltip=["Country:N", "Incidents:Q"],
            )
            .properties(height=340)
        )
        st.altair_chart(country_chart, use_container_width=True)

    with tabs[2]:
        st.subheader("Attack Type Distribution")
        attack_counts = filtered_df["attacktype1_txt"].value_counts().reset_index()
        attack_counts.columns = ["Attack Type", "Incidents"]
        attack_chart = (
            alt.Chart(attack_counts)
            .mark_bar(color="#D1495B")
            .encode(
                x=alt.X("Incidents:Q", title="Incidents"),
                y=alt.Y("Attack Type:N", sort="-x", title="Attack Type"),
                tooltip=["Attack Type:N", "Incidents:Q"],
            )
            .properties(height=340)
        )
        st.altair_chart(attack_chart, use_container_width=True)

    with tabs[3]:
        st.subheader("Weapon Type Distribution")
        weapon_counts = filtered_df["weaptype1_txt"].value_counts().reset_index()
        weapon_counts.columns = ["Weapon", "Incidents"]
        weapon_chart = (
            alt.Chart(weapon_counts)
            .mark_bar(color="#7A5195")
            .encode(
                x=alt.X("Incidents:Q", title="Incidents"),
                y=alt.Y("Weapon:N", sort="-x", title="Weapon"),
                tooltip=["Weapon:N", "Incidents:Q"],
            )
            .properties(height=340)
        )
        st.altair_chart(weapon_chart, use_container_width=True)

    with tabs[4]:
        st.subheader("Dataset Diagnostics")
        missing = filtered_df.isnull().sum().reset_index()
        missing.columns = ["Column", "Missing Values"]
        st.dataframe(missing.sort_values("Missing Values", ascending=False), use_container_width=True, hide_index=True)

        info_col1, info_col2 = st.columns(2)
        with info_col1:
            st.write(f"Rows: {filtered_df.shape[0]}")
            st.write(f"Columns: {filtered_df.shape[1]}")
            st.write(f"Memory Usage (MB): {round(filtered_df.memory_usage(deep=True).sum() / 1024**2, 2)}")
        with info_col2:
            st.write("Columns available in the current view:")
            st.write(filtered_df.columns.tolist())

    st.markdown("---")

    st.subheader("Recent Records")
    recent_df = filtered_df.sort_values(by=["event_date", "impact"], ascending=[False, False], na_position="last").head(50).copy()
    recent_df = add_display_summaries(recent_df)
    if "event_date" in recent_df.columns:
        recent_df["event_date"] = recent_df["event_date"].dt.strftime("%Y-%m-%d")

    recent_columns = [
        column
        for column in ["event_date", "iyear", "country_txt", "region_txt", "city", "provstate", "gname", "attacktype1_txt", "weaptype1_txt", "targtype1_txt", "nkill", "nwound", "impact", "summary"]
        if column in recent_df.columns
    ]

    st.dataframe(recent_df[recent_columns], use_container_width=True, hide_index=True)

    st.download_button(
        label="📥 Download Filtered Data",
        data=make_download_csv(filtered_df),
        file_name="Filtered_GTD_Data.csv",
        mime="text/csv",
    )


if __name__ == "__main__":
    main()
