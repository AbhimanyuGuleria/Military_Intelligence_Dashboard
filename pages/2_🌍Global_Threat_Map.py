from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st
from utils.data_loader import read_historical_data
from utils.ui import COLORS, apply_theme, chart_style, hero


st.set_page_config(page_title="Military Intelligence Dashboard - Global Threat Map", layout="wide")
apply_theme()


@st.cache_data
def load_data():
	usecols = [
		"iyear",
		"country_txt",
		"region_txt",
		"attacktype1_txt",
		"nkill",
		"nwound",
		"latitude",
		"longitude",
	]
	df = read_historical_data(usecols)

	for column in ["iyear", "nkill", "nwound", "latitude", "longitude"]:
		if column in df.columns:
			df[column] = pd.to_numeric(df[column], errors="coerce")

	if "nkill" in df.columns:
		df["nkill"] = df["nkill"].fillna(0)
	if "nwound" in df.columns:
		df["nwound"] = df["nwound"].fillna(0)

	return df


def main():
	hero("Geospatial intelligence", "Global threat map", "Explore where recorded incidents are concentrated and how activity varies by year, region, and attack type.")

	loading_message = st.empty()
	loading_message.info("Hang tight — we are plotting the map and pulling the latest incident data.")

	try:
		with st.spinner("Loading map intelligence..."):
			df = load_data()
		loading_message.empty()
	except Exception as error:
		loading_message.empty()
		st.error(f"Unable to load map data: {error}")
		return

	available_years = sorted(df["iyear"].dropna().astype(int).unique().tolist()) if "iyear" in df.columns else []
	min_year = available_years[0] if available_years else 0
	max_year = available_years[-1] if available_years else 0

	st.sidebar.header("Map Filters")

	if available_years:
		year_range = st.sidebar.slider(
			"Year range",
			min_value=min_year,
			max_value=max_year,
			value=(min_year, max_year),
		)
	else:
		year_range = (min_year, max_year)

	region_options = ["All"] + sorted(df["region_txt"].dropna().unique().tolist()) if "region_txt" in df.columns else ["All"]
	selected_region = st.sidebar.selectbox("Region", region_options)

	country_options = ["All"] + sorted(df["country_txt"].dropna().unique().tolist()) if "country_txt" in df.columns else ["All"]
	selected_country = st.sidebar.selectbox("Country", country_options)

	attack_options = ["All"] + sorted(df["attacktype1_txt"].dropna().unique().tolist()) if "attacktype1_txt" in df.columns else ["All"]
	selected_attack = st.sidebar.selectbox("Attack type", attack_options)

	filtered_df = df.copy()
	if available_years:
		filtered_df = filtered_df[(filtered_df["iyear"] >= year_range[0]) & (filtered_df["iyear"] <= year_range[1])]
	if selected_region != "All" and "region_txt" in filtered_df.columns:
		filtered_df = filtered_df[filtered_df["region_txt"] == selected_region]
	if selected_country != "All" and "country_txt" in filtered_df.columns:
		filtered_df = filtered_df[filtered_df["country_txt"] == selected_country]
	if selected_attack != "All" and "attacktype1_txt" in filtered_df.columns:
		filtered_df = filtered_df[filtered_df["attacktype1_txt"] == selected_attack]

	map_df = filtered_df.dropna(subset=["latitude", "longitude"]) if {"latitude", "longitude"}.issubset(filtered_df.columns) else pd.DataFrame()

	metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
	metric_col1.metric("Filtered Incidents", f"{len(filtered_df):,}")
	metric_col2.metric("Fatalities", f"{int(filtered_df['nkill'].sum()):,}" if "nkill" in filtered_df.columns else "0")
	metric_col3.metric("Injuries", f"{int(filtered_df['nwound'].sum()):,}" if "nwound" in filtered_df.columns else "0")
	metric_col4.metric("Mapped Points", f"{len(map_df):,}")

	st.markdown("---")

	map_col, summary_col = st.columns([2, 1])

	with map_col:
		st.subheader("Incident Hotspots")
		if not map_df.empty:
			display_map_df = map_df[["latitude", "longitude"]].dropna()
			if len(display_map_df) > 3000:
				display_map_df = display_map_df.sample(3000, random_state=42)
			display_map_df = display_map_df.astype(float)
			st.map(display_map_df)
		else:
			st.info("No mapped points match the current filters.")

	with summary_col:
		st.subheader("Top Regions")
		if "region_txt" in filtered_df.columns and not filtered_df.empty:
			region_counts = filtered_df["region_txt"].value_counts().head(8).reset_index()
			region_counts.columns = ["Region", "Incidents"]

			region_chart = (
				alt.Chart(region_counts)
				.mark_bar(color=COLORS["teal"])
				.encode(
					x=alt.X("Incidents:Q", title="Incidents"),
					y=alt.Y("Region:N", sort="-x", title="Region"),
					tooltip=["Region:N", "Incidents:Q"],
				)
				.properties(height=280)
			)
			region_chart = chart_style(region_chart)
			st.altair_chart(region_chart, use_container_width=True)
		else:
			st.info("Region data is unavailable for the current selection.")

		st.subheader("Top Countries")
		if "country_txt" in filtered_df.columns and not filtered_df.empty:
			country_counts = filtered_df["country_txt"].value_counts().head(8).reset_index()
			country_counts.columns = ["Country", "Incidents"]

			country_chart = (
				alt.Chart(country_counts)
				.mark_bar(color=COLORS["blue"])
				.encode(
					x=alt.X("Incidents:Q", title="Incidents"),
					y=alt.Y("Country:N", sort="-x", title="Country"),
					tooltip=["Country:N", "Incidents:Q"],
				)
				.properties(height=280)
			)
			country_chart = chart_style(country_chart)
			st.altair_chart(country_chart, use_container_width=True)
		else:
			st.info("Country data is unavailable for the current selection.")

	st.markdown("---")

	st.subheader("Yearly Pattern")
	if "iyear" in filtered_df.columns and not filtered_df.dropna(subset=["iyear"]).empty:
		yearly_counts = (
			filtered_df.dropna(subset=["iyear"])
			.groupby("iyear")
			.size()
			.reset_index(name="Incidents")
			.rename(columns={"iyear": "Year"})
			.sort_values("Year")
		)

		yearly_chart = (
			alt.Chart(yearly_counts)
			.mark_line(point=True, color=COLORS["teal"])
			.encode(
				x=alt.X("Year:Q", title="Year"),
				y=alt.Y("Incidents:Q", title="Incidents"),
				tooltip=[alt.Tooltip("Year:Q", title="Year"), alt.Tooltip("Incidents:Q", title="Incidents")],
			)
			.properties(height=320)
		)
		st.altair_chart(chart_style(yearly_chart), use_container_width=True)
	else:
		st.info("Year data is unavailable for the current selection.")

	st.info("Use the sidebar filters to narrow the map to a specific region, country, attack type, or time window.")


if __name__ == "__main__":
	main()
