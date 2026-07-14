from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st
from utils.data_loader import attach_display_summaries, read_historical_data, valid_date_part
from utils.ui import apply_theme, hero


st.set_page_config(page_title="Military Intelligence Dashboard - Country Analysis", layout="wide")
apply_theme()


@st.cache_data
def load_data():
	usecols = [
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


def top_label(series, default="Unavailable"):
	if series is None:
		return default
	clean_series = series.dropna()
	if clean_series.empty:
		return default
	return clean_series.value_counts().idxmax()


def main():
	hero("Comparative analysis", "Country intelligence", "Explore how recorded activity changes by country, region, attack type, and year in one focused analytical workspace.")

	loading_message = st.empty()
	loading_message.info("Hang tight — we are loading country intelligence and building the analysis view.")

	try:
		with st.spinner("Loading country intelligence..."):
			df = load_data()
		loading_message.empty()
	except Exception as error:
		loading_message.empty()
		st.error(f"Unable to load country analysis data: {error}")
		return

	available_years = sorted(df["iyear"].dropna().astype(int).unique().tolist()) if "iyear" in df.columns else []
	min_year = available_years[0] if available_years else 0
	max_year = available_years[-1] if available_years else 0

	st.sidebar.header("Country Filters")

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

	country_options = ["All Countries"] + sorted(df["country_txt"].dropna().unique().tolist()) if "country_txt" in df.columns else ["All Countries"]
	selected_country = st.sidebar.selectbox("Country", country_options)

	attack_options = ["All"] + sorted(df["attacktype1_txt"].dropna().unique().tolist()) if "attacktype1_txt" in df.columns else ["All"]
	selected_attack = st.sidebar.selectbox("Attack type", attack_options)

	weapon_options = ["All"] + sorted(df["weaptype1_txt"].dropna().unique().tolist()) if "weaptype1_txt" in df.columns else ["All"]
	selected_weapon = st.sidebar.selectbox("Weapon type", weapon_options)

	filtered_df = df.copy()
	if available_years:
		filtered_df = filtered_df[(filtered_df["iyear"] >= year_range[0]) & (filtered_df["iyear"] <= year_range[1])]
	if selected_region != "All" and "region_txt" in filtered_df.columns:
		filtered_df = filtered_df[filtered_df["region_txt"] == selected_region]
	if selected_country != "All Countries" and "country_txt" in filtered_df.columns:
		filtered_df = filtered_df[filtered_df["country_txt"] == selected_country]
	if selected_attack != "All" and "attacktype1_txt" in filtered_df.columns:
		filtered_df = filtered_df[filtered_df["attacktype1_txt"] == selected_attack]
	if selected_weapon != "All" and "weaptype1_txt" in filtered_df.columns:
		filtered_df = filtered_df[filtered_df["weaptype1_txt"] == selected_weapon]

	map_df = filtered_df.dropna(subset=["latitude", "longitude"]) if {"latitude", "longitude"}.issubset(filtered_df.columns) else pd.DataFrame()

	st.subheader(f"Viewing: {selected_country}" if selected_country != "All Countries" else "Viewing: All Countries")
	st.caption("This page combines country totals, top actors, weapon trends, and recent incident records for the selected view.")

	incidents = len(filtered_df)
	fatalities = int(filtered_df["nkill"].sum()) if "nkill" in filtered_df.columns else 0
	injuries = int(filtered_df["nwound"].sum()) if "nwound" in filtered_df.columns else 0
	countries = int(filtered_df["country_txt"].nunique()) if "country_txt" in filtered_df.columns else 0
	attack_types = int(filtered_df["attacktype1_txt"].nunique()) if "attacktype1_txt" in filtered_df.columns else 0
	top_group = top_label(filtered_df["gname"] if "gname" in filtered_df.columns else None)
	top_weapon = top_label(filtered_df["weaptype1_txt"] if "weaptype1_txt" in filtered_df.columns else None)
	top_target = top_label(filtered_df["targtype1_txt"] if "targtype1_txt" in filtered_df.columns else None)
	top_attack = top_label(filtered_df["attacktype1_txt"] if "attacktype1_txt" in filtered_df.columns else None)

	metric_col1, metric_col2, metric_col3, metric_col4, metric_col5 = st.columns(5)
	metric_col1.metric("Incidents", f"{incidents:,}")
	metric_col2.metric("Fatalities", f"{fatalities:,}")
	metric_col3.metric("Injuries", f"{injuries:,}")
	metric_col4.metric("Countries", f"{countries:,}")
	metric_col5.metric("Attack Types", f"{attack_types:,}")

	st.markdown("---")

	if selected_country != "All Countries":
		country_count = int(filtered_df["country_txt"].eq(selected_country).sum()) if "country_txt" in filtered_df.columns else len(filtered_df)
		summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
		summary_col1.metric("Top Terrorist Group", top_group)
		summary_col2.metric("Top Weapon", top_weapon)
		summary_col3.metric("Top Target", top_target)
		summary_col4.metric("Top Attack Type", top_attack)

		st.markdown("---")

		detail_tabs = st.tabs(["Top Groups", "Top Weapons", "Top Targets", "Top Attacks"])

		with detail_tabs[0]:
			if "gname" in filtered_df.columns and not filtered_df.empty:
				group_counts = filtered_df["gname"].value_counts().head(10).reset_index()
				group_counts.columns = ["Terrorist Group", "Incidents"]
				group_chart = (
					alt.Chart(group_counts)
					.mark_bar(color="#7A5195")
					.encode(
						x=alt.X("Incidents:Q", title="Incidents"),
						y=alt.Y("Terrorist Group:N", sort="-x", title="Terrorist Group"),
						tooltip=["Terrorist Group:N", "Incidents:Q"],
					)
					.properties(height=320)
				)
				st.altair_chart(group_chart, use_container_width=True)
			else:
				st.info("No terrorist-group data available for this selection.")

		with detail_tabs[1]:
			if "weaptype1_txt" in filtered_df.columns and not filtered_df.empty:
				weapon_counts = filtered_df["weaptype1_txt"].value_counts().head(10).reset_index()
				weapon_counts.columns = ["Weapon", "Incidents"]
				weapon_chart = (
					alt.Chart(weapon_counts)
					.mark_bar(color="#F28E2B")
					.encode(
						x=alt.X("Incidents:Q", title="Incidents"),
						y=alt.Y("Weapon:N", sort="-x", title="Weapon"),
						tooltip=["Weapon:N", "Incidents:Q"],
					)
					.properties(height=320)
				)
				st.altair_chart(weapon_chart, use_container_width=True)
			else:
				st.info("No weapon data available for this selection.")

		with detail_tabs[2]:
			if "targtype1_txt" in filtered_df.columns and not filtered_df.empty:
				target_counts = filtered_df["targtype1_txt"].value_counts().head(10).reset_index()
				target_counts.columns = ["Target", "Incidents"]
				target_chart = (
					alt.Chart(target_counts)
					.mark_bar(color="#2E86AB")
					.encode(
						x=alt.X("Incidents:Q", title="Incidents"),
						y=alt.Y("Target:N", sort="-x", title="Target"),
						tooltip=["Target:N", "Incidents:Q"],
					)
					.properties(height=320)
				)
				st.altair_chart(target_chart, use_container_width=True)
			else:
				st.info("No target data available for this selection.")

		with detail_tabs[3]:
			if "attacktype1_txt" in filtered_df.columns and not filtered_df.empty:
				attack_counts = filtered_df["attacktype1_txt"].value_counts().head(10).reset_index()
				attack_counts.columns = ["Attack Type", "Incidents"]
				attack_chart = (
					alt.Chart(attack_counts)
					.mark_bar(color="#D1495B")
					.encode(
						x=alt.X("Incidents:Q", title="Incidents"),
						y=alt.Y("Attack Type:N", sort="-x", title="Attack Type"),
						tooltip=["Attack Type:N", "Incidents:Q"],
					)
					.properties(height=320)
				)
				st.altair_chart(attack_chart, use_container_width=True)
			else:
				st.info("No attack-type data available for this selection.")

		st.markdown("---")

	top_col, insight_col = st.columns([2, 1])

	with top_col:
		st.subheader("Country Activity Over Time")
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
				.mark_line(point=True)
				.encode(
					x=alt.X("Year:Q", title="Year"),
					y=alt.Y("Incidents:Q", title="Incidents"),
					tooltip=[alt.Tooltip("Year:Q", title="Year"), alt.Tooltip("Incidents:Q", title="Incidents")],
				)
				.properties(height=340)
			)
			st.altair_chart(yearly_chart, use_container_width=True)
		else:
			st.info("Year data is unavailable for the current filters.")

	with insight_col:
		st.subheader("Quick Readout")
		st.write(
			f"- Selected country: {selected_country}\n"
			f"- Selected region: {selected_region}\n"
			f"- Date window: {year_range[0]} to {year_range[1]}\n"
			f"- Records in view: {len(filtered_df):,}\n"
			f"- Top group: {top_group}\n"
			f"- Top weapon: {top_weapon}"
		)

		if not filtered_df.empty and "country_txt" in filtered_df.columns:
			country_rollup = filtered_df["country_txt"].value_counts().head(8).reset_index()
			country_rollup.columns = ["Country", "Incidents"]

			country_chart = (
				alt.Chart(country_rollup)
				.mark_bar(color="#2E86AB")
				.encode(
					x=alt.X("Incidents:Q", title="Incidents"),
					y=alt.Y("Country:N", sort="-x", title="Country"),
					tooltip=["Country:N", "Incidents:Q"],
				)
				.properties(height=260)
			)
			st.altair_chart(country_chart, use_container_width=True)
		else:
			st.info("No country rollup available for the current selection.")

	st.markdown("---")

	st.subheader("Country Spotlight")
	if selected_country != "All Countries":
		focus_df = filtered_df.copy()

		focus_metric_col1, focus_metric_col2, focus_metric_col3, focus_metric_col4 = st.columns(4)
		focus_metric_col1.metric("Country Incidents", f"{len(focus_df):,}")
		focus_metric_col2.metric("Fatalities", f"{int(focus_df['nkill'].sum()):,}" if "nkill" in focus_df.columns else "0")
		focus_metric_col3.metric("Injuries", f"{int(focus_df['nwound'].sum()):,}" if "nwound" in focus_df.columns else "0")
		focus_metric_col4.metric("Attack Types", f"{int(focus_df['attacktype1_txt'].nunique()):,}" if "attacktype1_txt" in focus_df.columns else "0")

		spotlight_col1, spotlight_col2 = st.columns(2)

		with spotlight_col1:
			st.subheader("Attack Type Breakdown")
			if "attacktype1_txt" in focus_df.columns and not focus_df.empty:
				focus_attack_counts = focus_df["attacktype1_txt"].value_counts().head(8).reset_index()
				focus_attack_counts.columns = ["Attack Type", "Incidents"]

				focus_attack_chart = (
					alt.Chart(focus_attack_counts)
					.mark_bar(color="#D1495B")
					.encode(
						x=alt.X("Incidents:Q", title="Incidents"),
						y=alt.Y("Attack Type:N", sort="-x", title="Attack Type"),
						tooltip=["Attack Type:N", "Incidents:Q"],
					)
					.properties(height=280)
				)
				st.altair_chart(focus_attack_chart, use_container_width=True)
			else:
				st.info("No attack-type data available for the selected country.")

		with spotlight_col2:
			st.subheader("Yearly Pattern")
			if "iyear" in focus_df.columns and not focus_df.dropna(subset=["iyear"]).empty:
				focus_yearly_counts = (
					focus_df.dropna(subset=["iyear"])
					.groupby("iyear")
					.size()
					.reset_index(name="Incidents")
					.rename(columns={"iyear": "Year"})
					.sort_values("Year")
				)

				focus_yearly_chart = (
					alt.Chart(focus_yearly_counts)
					.mark_line(point=True)
					.encode(
						x=alt.X("Year:Q", title="Year"),
						y=alt.Y("Incidents:Q", title="Incidents"),
						tooltip=[alt.Tooltip("Year:Q", title="Year"), alt.Tooltip("Incidents:Q", title="Incidents")],
					)
					.properties(height=280)
				)
				st.altair_chart(focus_yearly_chart, use_container_width=True)
			else:
				st.info("No year data available for the selected country.")

		st.subheader("Recent Records")
		if not focus_df.empty:
			sort_columns = ["event_date", "iyear", "imonth", "iday"] if "event_date" in focus_df.columns else ["iyear"]
			recent_df = focus_df.sort_values(by=sort_columns, ascending=False, na_position="last").head(25).copy()
			recent_df = attach_display_summaries(recent_df)
			display_columns = [
				column
				for column in ["event_date", "iyear", "imonth", "iday", "country_txt", "region_txt", "city", "provstate", "gname", "attacktype1_txt", "weaptype1_txt", "targtype1_txt", "nkill", "nwound", "latitude", "longitude", "summary"]
				if column in recent_df.columns
			]
			recent_df["event_date_display"] = recent_df["event_date"].dt.strftime("%Y-%m-%d") if "event_date" in recent_df.columns else "Unknown"
			st.dataframe(
				recent_df[display_columns + (["event_date_display"] if "event_date_display" in recent_df.columns else [])]
				,
				use_container_width=True,
			)
		else:
			st.info("No detailed records available for the selected country.")
	else:
		st.info("Select a specific country from the sidebar to open its detailed spotlight view.")

	chart_col1, chart_col2 = st.columns(2)

	with chart_col1:
		st.subheader("Attack Type Mix")
		if "attacktype1_txt" in filtered_df.columns and not filtered_df.empty:
			attack_counts = filtered_df["attacktype1_txt"].value_counts().head(8).reset_index()
			attack_counts.columns = ["Attack Type", "Incidents"]

			attack_chart = (
				alt.Chart(attack_counts)
				.mark_bar(color="#D1495B")
				.encode(
					x=alt.X("Incidents:Q", title="Incidents"),
					y=alt.Y("Attack Type:N", sort="-x", title="Attack Type"),
					tooltip=["Attack Type:N", "Incidents:Q"],
				)
				.properties(height=300)
			)
			st.altair_chart(attack_chart, use_container_width=True)
		else:
			st.info("Attack-type data is unavailable for the current filters.")

	with chart_col2:
		st.subheader("Impact Snapshot")
		if not filtered_df.empty:
			impact_df = pd.DataFrame(
				{
					"Measure": ["Fatalities", "Injuries"],
					"Count": [fatalities, injuries],
				}
			)

			impact_chart = (
				alt.Chart(impact_df)
				.mark_bar()
				.encode(
					x=alt.X("Measure:N", title="Measure"),
					y=alt.Y("Count:Q", title="Count"),
					color=alt.Color("Measure:N", scale=alt.Scale(range=["#0B4F6C", "#01BAEF"]), legend=None),
					tooltip=["Measure:N", "Count:Q"],
				)
				.properties(height=300)
			)
			st.altair_chart(impact_chart, use_container_width=True)
		else:
			st.info("No impact data available for the current filters.")

	st.markdown("---")

	st.subheader("Geographic View")
	if not map_df.empty:
		display_map_df = map_df[["latitude", "longitude"]].dropna()
		if len(display_map_df) > 3000:
			display_map_df = display_map_df.sample(3000, random_state=42)
		display_map_df = display_map_df.astype(float)
		st.map(display_map_df)
	else:
		st.info("No coordinates are available for the current country selection.")

	st.info("Use the sidebar to narrow the analysis down by country, region, attack type, weapon type, and year.")


if __name__ == "__main__":
	main()
