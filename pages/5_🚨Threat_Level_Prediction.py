from pathlib import Path

import altair as alt
import joblib
import numpy as np
import pandas as pd
import streamlit as st
from utils.data_loader import attach_display_summaries, read_historical_data, valid_date_part
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from utils.ui import COLORS, apply_theme, chart_style, hero


st.set_page_config(page_title="Military Intelligence Dashboard - Threat Level Prediction", page_icon="🚨", layout="wide")
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
    "ransom",
    "nkill",
    "nwound",
    "latitude",
    "longitude",
]

CATEGORICAL_COLUMNS = ["country_txt", "region_txt", "attacktype1_txt", "weaptype1_txt", "targtype1_txt", "gname"]
NUMERIC_COLUMNS = ["success", "suicide", "ransom", "nkill", "nwound"]


def compute_threat_level(impact):
    if impact <= 2:
        return "LOW"
    if impact <= 10:
        return "MEDIUM"
    return "HIGH"


def threat_score(success, suicide, ransom, nkill, nwound):
    score = (nkill * 3) + (nwound * 1.5)
    score += 12 if success else 0
    score += 20 if suicide else 0
    score += 5 if ransom else 0
    return score


def threat_band(score):
    if score >= 50:
        return "Critical"
    if score >= 25:
        return "High"
    if score >= 10:
        return "Moderate"
    return "Low"


@st.cache_data
def load_data():
    df = read_historical_data(USECOLS)

    for column in ["iyear", "imonth", "iday", "success", "suicide", "ransom", "nkill", "nwound", "latitude", "longitude"]:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

    df["nkill"] = df["nkill"].fillna(0)
    df["nwound"] = df["nwound"].fillna(0)
    df["success"] = df["success"].fillna(0).astype(int)
    df["suicide"] = df["suicide"].fillna(0).astype(int)
    df["ransom"] = df["ransom"].fillna(0).astype(int)

    df = df.dropna(subset=["country_txt", "region_txt", "attacktype1_txt", "weaptype1_txt", "targtype1_txt", "gname"])
    df["impact"] = df["nkill"] + df["nwound"]
    df["threat_level"] = df["impact"].apply(compute_threat_level)

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


@st.cache_resource
def train_threat_model(df):
    model_df = df[["country_txt", "region_txt", "attacktype1_txt", "weaptype1_txt", "targtype1_txt", "gname", "success", "suicide", "ransom", "nkill", "nwound", "threat_level"]].dropna().copy()

    encoders = {}
    for column in CATEGORICAL_COLUMNS:
        encoder = LabelEncoder()
        model_df[column] = encoder.fit_transform(model_df[column].astype(str))
        encoders[column] = encoder

    target_encoder = LabelEncoder()
    model_df["threat_level"] = target_encoder.fit_transform(model_df["threat_level"])

    features = model_df.drop(columns=["threat_level"])
    target = model_df["threat_level"]

    X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=42, stratify=target)

    model = RandomForestClassifier(n_estimators=30, max_depth=12, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    accuracy = model.score(X_test, y_test)
    return model, encoders, target_encoder, accuracy


def encode_input(encoders, country, region, attack, weapon, target, group):
    return pd.DataFrame(
        {
            "country_txt": [encoders["country_txt"].transform([country])[0]],
            "region_txt": [encoders["region_txt"].transform([region])[0]],
            "attacktype1_txt": [encoders["attacktype1_txt"].transform([attack])[0]],
            "weaptype1_txt": [encoders["weaptype1_txt"].transform([weapon])[0]],
            "targtype1_txt": [encoders["targtype1_txt"].transform([target])[0]],
            "gname": [encoders["gname"].transform([group])[0]],
            "success": [int(st.session_state.get("success_value", 1))],
            "suicide": [int(st.session_state.get("suicide_value", 0))],
            "ransom": [int(st.session_state.get("ransom_value", 0))],
            "nkill": [int(st.session_state.get("nkill_value", 0))],
            "nwound": [int(st.session_state.get("nwound_value", 0))],
        }
    )


def top_value(series, default="Unavailable"):
    clean = series.dropna() if series is not None else pd.Series(dtype="object")
    if clean.empty:
        return default
    return clean.value_counts().idxmax()


def main():
    hero("Scenario assessment", "Threat-level prediction", "Estimate severity from a case profile, then compare it with similar historical incidents and the current data distribution.")

    loading_message = st.empty()
    loading_message.info("Hang tight — we are loading the threat data and preparing the analysis model.")

    try:
        with st.spinner("Building threat intelligence workspace..."):
            df = load_data()
            model, encoders, target_encoder, model_accuracy = train_threat_model(df)
        loading_message.empty()
    except Exception as error:
        loading_message.empty()
        st.error(f"Unable to initialize threat prediction page: {error}")
        return

    st.sidebar.header("Scenario Presets")
    preset = st.sidebar.selectbox(
        "Load a preset",
        ["Custom", "Low risk patrol", "Moderate urban attack", "High risk suicide attack"],
    )

    preset_defaults = {
        "Low risk patrol": {
            "country_txt": df["country_txt"].mode().iloc[0],
            "region_txt": df["region_txt"].mode().iloc[0],
            "attacktype1_txt": df["attacktype1_txt"].mode().iloc[0],
            "weaptype1_txt": df["weaptype1_txt"].mode().iloc[0],
            "targtype1_txt": df["targtype1_txt"].mode().iloc[0],
            "gname": df["gname"].mode().iloc[0],
            "success": 0,
            "suicide": 0,
            "ransom": 0,
            "nkill": 0,
            "nwound": 1,
        },
        "Moderate urban attack": {
            "country_txt": df["country_txt"].mode().iloc[0],
            "region_txt": df["region_txt"].mode().iloc[0],
            "attacktype1_txt": df["attacktype1_txt"].mode().iloc[0],
            "weaptype1_txt": df["weaptype1_txt"].mode().iloc[0],
            "targtype1_txt": df["targtype1_txt"].mode().iloc[0],
            "gname": df["gname"].mode().iloc[0],
            "success": 1,
            "suicide": 0,
            "ransom": 0,
            "nkill": 2,
            "nwound": 8,
        },
        "High risk suicide attack": {
            "country_txt": df["country_txt"].mode().iloc[0],
            "region_txt": df["region_txt"].mode().iloc[0],
            "attacktype1_txt": df["attacktype1_txt"].mode().iloc[0],
            "weaptype1_txt": df["weaptype1_txt"].mode().iloc[0],
            "targtype1_txt": df["targtype1_txt"].mode().iloc[0],
            "gname": df["gname"].mode().iloc[0],
            "success": 1,
            "suicide": 1,
            "ransom": 0,
            "nkill": 6,
            "nwound": 14,
        },
    }

    preset_values = preset_defaults.get(preset, {})

    st.sidebar.caption("Adjust the scenario and see how the predicted threat level changes.")

    country_options = sorted(df["country_txt"].unique().tolist())
    region_options = sorted(df["region_txt"].unique().tolist())
    attack_options = sorted(df["attacktype1_txt"].unique().tolist())
    weapon_options = sorted(df["weaptype1_txt"].unique().tolist())
    target_options = sorted(df["targtype1_txt"].unique().tolist())
    group_options = sorted(df["gname"].unique().tolist())

    def default_index(options, value):
        return options.index(value) if value in options else 0

    with st.form("threat_form"):
        form_col1, form_col2 = st.columns(2)

        with form_col1:
            country = st.selectbox("🌍 Country", country_options, index=default_index(country_options, preset_values.get("country_txt")))
            region = st.selectbox("🌎 Region", region_options, index=default_index(region_options, preset_values.get("region_txt")))
            attack = st.selectbox("💥 Attack Type", attack_options, index=default_index(attack_options, preset_values.get("attacktype1_txt")))
            weapon = st.selectbox("🔫 Weapon Type", weapon_options, index=default_index(weapon_options, preset_values.get("weaptype1_txt")))
            target = st.selectbox("🎯 Target Type", target_options, index=default_index(target_options, preset_values.get("targtype1_txt")))
            group = st.selectbox("👥 Terrorist Group", group_options, index=default_index(group_options, preset_values.get("gname")))

        with form_col2:
            st.session_state["success_value"] = st.selectbox("✅ Attack Successful?", [0, 1], index=int(preset_values.get("success", 1)), format_func=lambda value: "Yes" if value == 1 else "No")
            st.session_state["suicide_value"] = st.selectbox("💣 Suicide Attack?", [0, 1], index=int(preset_values.get("suicide", 0)), format_func=lambda value: "Yes" if value == 1 else "No")
            st.session_state["ransom_value"] = st.selectbox("💰 Ransom Demand?", [0, 1], index=int(preset_values.get("ransom", 0)), format_func=lambda value: "Yes" if value == 1 else "No")
            st.session_state["nkill_value"] = st.number_input("☠ Fatalities", min_value=0, value=int(preset_values.get("nkill", 0)), step=1)
            st.session_state["nwound_value"] = st.number_input("🏥 Injuries", min_value=0, value=int(preset_values.get("nwound", 0)), step=1)

        submitted = st.form_submit_button("🚨 Predict Threat Level")

    st.markdown("---")

    overview_col1, overview_col2, overview_col3, overview_col4 = st.columns(4)
    overview_col1.metric("Records", f"{len(df):,}")
    overview_col2.metric("Threat Model Accuracy", f"{model_accuracy * 100:.2f}%")
    overview_col3.metric("High Severity Cases", f"{int((df['threat_level'] == 'HIGH').sum()):,}")
    overview_col4.metric("Median Impact", f"{df['impact'].median():.1f}")

    if not submitted:
        st.info("Fill in the scenario and click Predict Threat Level to see the result.")
        return

    try:
        input_df = encode_input(encoders, country, region, attack, weapon, target, group)
        prediction = model.predict(input_df)[0]
        probabilities = model.predict_proba(input_df)[0]
        predicted_level = target_encoder.inverse_transform([prediction])[0]
        confidence = float(probabilities.max() * 100)
        top_indices = probabilities.argsort()[::-1][:3]

        score = threat_score(
            st.session_state["success_value"],
            st.session_state["suicide_value"],
            st.session_state["ransom_value"],
            st.session_state["nkill_value"],
            st.session_state["nwound_value"],
        )
        band = threat_band(score)

        result_col1, result_col2 = st.columns([1, 1])

        with result_col1:
            st.subheader("Prediction Result")
            if predicted_level == "LOW":
                st.success(f"Threat Level: {predicted_level}")
            elif predicted_level == "MEDIUM":
                st.warning(f"Threat Level: {predicted_level}")
            else:
                st.error(f"Threat Level: {predicted_level}")

            st.metric("Confidence", f"{confidence:.2f}%")
            st.metric("Threat Score", f"{score:.1f}")
            st.metric("Threat Band", band)

            distribution_df = pd.DataFrame(
                {
                    "Threat Level": [target_encoder.inverse_transform([idx])[0] for idx in top_indices],
                    "Probability": [probabilities[idx] for idx in top_indices],
                }
            ).set_index("Threat Level")
            st.bar_chart(distribution_df)

        with result_col2:
            st.subheader("What Drove This Result")
            st.write(
                f"- Selected country: {country}\n"
                f"- Selected attack type: {attack}\n"
                f"- Selected weapon: {weapon}\n"
                f"- Selected target: {target}\n"
                f"- Selected group: {group}"
            )
            st.write(
                f"- Fatalities: {st.session_state['nkill_value']}\n"
                f"- Injuries: {st.session_state['nwound_value']}\n"
                f"- Success flag: {st.session_state['success_value']}\n"
                f"- Suicide flag: {st.session_state['suicide_value']}\n"
                f"- Ransom flag: {st.session_state['ransom_value']}"
            )

            top_predictions = pd.DataFrame(
                {
                    "Threat Level": [target_encoder.inverse_transform([idx])[0] for idx in top_indices],
                    "Probability": [probabilities[idx] for idx in top_indices],
                }
            )
            st.dataframe(top_predictions, use_container_width=True, hide_index=True)

    except Exception as error:
        st.error(f"Prediction failed: {error}")
        return

    st.markdown("---")

    analysis_col1, analysis_col2 = st.columns(2)

    with analysis_col1:
        st.subheader("Historical Context")
        similar_df = df[
            (df["country_txt"] == country)
            & (df["region_txt"] == region)
            & (df["attacktype1_txt"] == attack)
            & (df["weaptype1_txt"] == weapon)
            & (df["targtype1_txt"] == target)
        ].copy()

        st.metric("Similar Cases", f"{len(similar_df):,}")
        st.metric("Common Threat Level", top_value(similar_df["threat_level"] if not similar_df.empty else None))

        if not similar_df.empty:
            similar_years = similar_df.dropna(subset=["iyear"]).groupby("iyear").size().reset_index(name="Incidents")
            similar_years = similar_years.rename(columns={"iyear": "Year"})
            chart = (
                alt.Chart(similar_years)
                .mark_line(point=True, color=COLORS["primary"])
                .encode(
                    x=alt.X("Year:Q", title="Year"),
                    y=alt.Y("Incidents:Q", title="Incidents"),
                    tooltip=["Year:Q", "Incidents:Q"],
                )
                .properties(height=280)
            )
            st.altair_chart(chart_style(chart), use_container_width=True)
        else:
            st.info("No directly matching historical cases were found for this exact scenario.")

    with analysis_col2:
        st.subheader("Threat Distribution")
        threat_counts = df["threat_level"].value_counts().reset_index()
        threat_counts.columns = ["Threat Level", "Cases"]
        threat_chart = (
            alt.Chart(threat_counts)
            .mark_bar()
            .encode(
                x=alt.X("Threat Level:N", title="Threat Level"),
                y=alt.Y("Cases:Q", title="Cases"),
                color=alt.Color("Threat Level:N", scale=alt.Scale(domain=["LOW", "MEDIUM", "HIGH"], range=[COLORS["safe"], COLORS["warning"], COLORS["critical"]]), legend=None),
                tooltip=["Threat Level:N", "Cases:Q"],
            )
            .properties(height=280)
        )
        st.altair_chart(chart_style(threat_chart), use_container_width=True)

        st.subheader("Risk Notes")
        st.write(
            "This page combines a learned model with a transparent impact score. If the threat score and model disagree, treat the result as a flag to inspect the case more closely."
        )

    st.markdown("---")

    st.subheader("Recent High-Impact Records")
    recent_cols = [
        column
        for column in [
            "event_date",
            "iyear",
            "imonth",
            "iday",
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
            "threat_level",
            "summary",
        ]
        if column in df.columns
    ]
    recent_df = df.sort_values(by=["impact", "event_date"], ascending=[False, False], na_position="last").head(20).copy()
    recent_df = attach_display_summaries(recent_df)
    if "event_date" in recent_df.columns:
        recent_df["event_date"] = recent_df["event_date"].dt.strftime("%Y-%m-%d")
    st.dataframe(recent_df[recent_cols], use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
