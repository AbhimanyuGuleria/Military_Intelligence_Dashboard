from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
from sklearn.linear_model import LinearRegression
from utils.data_loader import read_historical_data
from utils.ui import COLORS, apply_theme, chart_style, hero


st.set_page_config(page_title="Military Intelligence Dashboard - Forecasting", page_icon="📈", layout="wide")
apply_theme()



USECOLS = [
    "iyear",
    "country_txt",
    "region_txt",
    "attacktype1_txt",
    "weaptype1_txt",
    "targtype1_txt",
    "nkill",
    "nwound",
]


@st.cache_data
def load_data():
    df = read_historical_data(USECOLS)
    df["iyear"] = pd.to_numeric(df["iyear"], errors="coerce")
    df["nkill"] = pd.to_numeric(df["nkill"], errors="coerce").fillna(0)
    df["nwound"] = pd.to_numeric(df["nwound"], errors="coerce").fillna(0)
    df = df.dropna(subset=["iyear", "country_txt", "region_txt", "attacktype1_txt", "weaptype1_txt", "targtype1_txt"])
    return df


def build_yearly_series(df):
    yearly = (
        df.groupby("iyear")
        .size()
        .reset_index(name="Attacks")
        .rename(columns={"iyear": "Year"})
        .sort_values("Year")
    )
    return yearly


def forecast_series(yearly, years_ahead, method="linear"):
    model = LinearRegression()
    x = yearly[["Year"]]
    y = yearly["Attacks"]
    model.fit(x, y)

    last_year = int(yearly["Year"].max())
    future_years = np.arange(last_year + 1, last_year + years_ahead + 1)
    future_df = pd.DataFrame({"Year": future_years})

    if method == "moving average":
        window = min(5, len(yearly))
        baseline = yearly["Attacks"].tail(window).mean()
        trend = yearly["Attacks"].diff().tail(window - 1).mean() if window > 1 else 0
        preds = []
        current = baseline
        for _ in future_years:
            current = max(current + trend, 0)
            preds.append(current)
        predictions = np.array(preds)
    else:
        predictions = model.predict(future_df)

    predictions = np.maximum(predictions, 0)
    forecast = pd.DataFrame({"Year": future_years, "Forecasted Attacks": predictions.round().astype(int)})

    return forecast, model


def top_value(series, default="Unavailable"):
    clean = series.dropna() if series is not None else pd.Series(dtype="object")
    if clean.empty:
        return default
    return clean.value_counts().idxmax()


def main():
    hero("Trend projection", "Historical activity forecasting", "Project recorded incident volume from the selected historical series, with transparent context for every estimate.")
    st.markdown(
        "Forecast future incident volume from historical GTD data, then compare the projection against the current trend and the filtered data slice."
    )

    loading_message = st.empty()
    loading_message.info("Hang tight — we are loading historical data and preparing the forecast view.")

    try:
        with st.spinner("Building forecasting workspace..."):
            df = load_data()
        loading_message.empty()
    except Exception as error:
        loading_message.empty()
        st.error(f"Unable to load forecasting data: {error}")
        return

    years = sorted(df["iyear"].dropna().astype(int).unique().tolist())
    min_year = years[0] if years else 0
    max_year = years[-1] if years else 0

    st.sidebar.header("Forecast Settings")
    scope = st.sidebar.selectbox("Forecast scope", ["All Countries", "Single Country"])
    selected_country = None
    if scope == "Single Country":
        country_options = sorted(df["country_txt"].dropna().unique().tolist())
        selected_country = st.sidebar.selectbox("Country", country_options)

    selected_region = st.sidebar.selectbox("Region", ["All"] + sorted(df["region_txt"].dropna().unique().tolist()))
    selected_attack = st.sidebar.selectbox("Attack Type", ["All"] + sorted(df["attacktype1_txt"].dropna().unique().tolist()))
    selected_weapon = st.sidebar.selectbox("Weapon Type", ["All"] + sorted(df["weaptype1_txt"].dropna().unique().tolist()))
    selected_target = st.sidebar.selectbox("Target Type", ["All"] + sorted(df["targtype1_txt"].dropna().unique().tolist()))
    years_ahead = st.sidebar.slider("Forecast years ahead", min_value=1, max_value=10, value=5)
    method = st.sidebar.selectbox("Forecast method", ["linear", "moving average"])

    filtered_df = df.copy()
    if selected_country:
        filtered_df = filtered_df[filtered_df["country_txt"] == selected_country]
    if selected_region != "All":
        filtered_df = filtered_df[filtered_df["region_txt"] == selected_region]
    if selected_attack != "All":
        filtered_df = filtered_df[filtered_df["attacktype1_txt"] == selected_attack]
    if selected_weapon != "All":
        filtered_df = filtered_df[filtered_df["weaptype1_txt"] == selected_weapon]
    if selected_target != "All":
        filtered_df = filtered_df[filtered_df["targtype1_txt"] == selected_target]

    yearly = build_yearly_series(filtered_df)

    if len(yearly) < 5:
        st.warning("Not enough historical data for forecasting with the current filters.")
        st.stop()

    forecast, model = forecast_series(yearly, years_ahead, method=method)

    historical_last = int(yearly.iloc[-1]["Attacks"])
    forecast_last = int(forecast.iloc[-1]["Forecasted Attacks"])
    growth = ((forecast_last - historical_last) / max(historical_last, 1)) * 100
    direction = "Increasing" if growth >= 15 else "Stable" if growth >= 0 else "Decreasing"

    st.subheader("Forecast Overview")
    if scope == "Single Country" and selected_country:
        st.caption(f"Forecast scope: {selected_country}")
    else:
        st.caption("Forecast scope: all countries combined")

    overview_col1, overview_col2, overview_col3, overview_col4 = st.columns(4)
    overview_col1.metric("Historical Last Year", f"{historical_last:,}")
    overview_col2.metric(f"Forecast ({years_ahead} yrs)", f"{forecast_last:,}")
    overview_col3.metric("Growth", f"{growth:.2f}%")
    overview_col4.metric("Trend", direction)

    hist_df = yearly.rename(columns={"Attacks": "Value"}).assign(Type="Historical")
    fore_df = forecast.rename(columns={"Forecasted Attacks": "Value"}).assign(Type="Forecast")
    chart_df = pd.concat([hist_df, fore_df], ignore_index=True)

    chart = (
        alt.Chart(chart_df)
        .mark_line(point=True)
        .encode(
            x=alt.X("Year:Q", title="Year"),
            y=alt.Y("Value:Q", title="Number of Attacks"),
            color=alt.Color("Type:N", scale=alt.Scale(range=[COLORS["blue"], COLORS["crimson"]]), title=""),
            tooltip=["Year:Q", "Value:Q", "Type:N"],
        )
        .properties(height=420)
    )

    st.altair_chart(chart_style(chart), use_container_width=True)

    left_col, right_col = st.columns([1, 1])

    with left_col:
        st.subheader("Forecast Table")
        st.dataframe(forecast, use_container_width=True, hide_index=True)
        st.download_button(
            label="📥 Download Forecast CSV",
            data=forecast.to_csv(index=False),
            file_name=f"forecast_{selected_country or 'all'}_{method}.csv",
            mime="text/csv",
        )

    with right_col:
        st.subheader("Forecast Context")
        st.write(
            f"- Selected region: {selected_region}\n"
            f"- Selected attack type: {selected_attack}\n"
            f"- Selected weapon type: {selected_weapon}\n"
            f"- Selected target type: {selected_target}\n"
            f"- Historical years covered: {int(yearly['Year'].min())} to {int(yearly['Year'].max())}"
        )
        st.metric("Most Frequent Attack Type", top_value(filtered_df["attacktype1_txt"] if "attacktype1_txt" in filtered_df.columns else None))
        st.metric("Most Frequent Weapon", top_value(filtered_df["weaptype1_txt"] if "weaptype1_txt" in filtered_df.columns else None))
        st.metric("Most Frequent Target", top_value(filtered_df["targtype1_txt"] if "targtype1_txt" in filtered_df.columns else None))

    st.markdown("---")

    detail_col1, detail_col2 = st.columns(2)

    with detail_col1:
        st.subheader("Trend Intelligence")
        st.write(
            "The forecast uses a simple regression or moving-average projection on yearly incident counts. It is best treated as a directional estimate rather than a precise prediction."
        )
        if len(yearly) >= 3:
            recent_trend = yearly.tail(5).copy()
            recent_trend["YoY Change"] = recent_trend["Attacks"].pct_change().fillna(0) * 100
            st.dataframe(recent_trend, use_container_width=True, hide_index=True)

    with detail_col2:
        st.subheader("Top Breakdowns")
        if not filtered_df.empty:
            attack_counts = filtered_df["attacktype1_txt"].value_counts().head(8).reset_index()
            attack_counts.columns = ["Attack Type", "Incidents"]
            attack_chart = (
                alt.Chart(attack_counts)
                .mark_bar(color=COLORS["indigo"])
                .encode(
                    x=alt.X("Incidents:Q", title="Incidents"),
                    y=alt.Y("Attack Type:N", sort="-x", title="Attack Type"),
                    tooltip=["Attack Type:N", "Incidents:Q"],
                )
                .properties(height=260)
            )
            st.altair_chart(chart_style(attack_chart), use_container_width=True)

    st.markdown("---")

    st.subheader("Forecast Guidance")
    if growth < 0:
        st.success("The current projection suggests a decline relative to the last historical year.")
    elif growth < 15:
        st.warning("The projection is relatively stable with only a small increase.")
    else:
        st.error("The projection suggests a noticeable increase in incident volume.")


if __name__ == "__main__":
    main()
