from pathlib import Path

import joblib
import pandas as pd
import streamlit as st
from utils.data_loader import get_historical_data_path, read_historical_data
from utils.ui import apply_theme, hero


st.set_page_config(page_title="Military Intelligence Dashboard - Attack Prediction", page_icon="🤖", layout="wide")
apply_theme()


MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "attack_prediction_model.pkl"
ENCODER_PATH = Path(__file__).resolve().parents[1] / "models" / "feature_encoders.pkl"
TARGET_ENCODER_PATH = Path(__file__).resolve().parents[1] / "models" / "target_encoder.pkl"

FEATURE_COLUMNS = [
    "country_txt",
    "region_txt",
    "weaptype1_txt",
    "targtype1_txt",
    "gname",
    "success",
    "suicide",
    "nkill",
    "nwound",
]

CATEGORICAL_COLUMNS = ["country_txt", "region_txt", "weaptype1_txt", "targtype1_txt", "gname"]


@st.cache_resource
def load_artifacts():
    model = joblib.load(MODEL_PATH)
    encoders = joblib.load(ENCODER_PATH)
    target_encoder = joblib.load(TARGET_ENCODER_PATH)
    return model, encoders, target_encoder


@st.cache_data
def load_data():
    df = read_historical_data(FEATURE_COLUMNS + ["attacktype1_txt"])

    for column in ["nkill", "nwound", "success", "suicide"]:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna(subset=["country_txt", "region_txt", "weaptype1_txt", "targtype1_txt", "gname", "attacktype1_txt"])
    df["nkill"] = df["nkill"].fillna(0)
    df["nwound"] = df["nwound"].fillna(0)
    df["success"] = df["success"].fillna(0).astype(int)
    df["suicide"] = df["suicide"].fillna(0).astype(int)
    return df


def encode_value(encoders, column, value):
    return encoders[column].transform([value])[0]


def risk_label(nkill, nwound, success, suicide):
    score = (nkill * 2) + nwound + (20 if success else 0) + (15 if suicide else 0)
    if score >= 80:
        return "Critical"
    if score >= 35:
        return "High"
    if score >= 15:
        return "Moderate"
    return "Low"


def main():
    hero("Scenario modeling", "Attack type prediction", "Compare a structured scenario against historical patterns. Outputs are analytical aids, not operational recommendations.")
    st.markdown(
        "Predict the most likely attack type from an incident profile. Use the form, then review the top predictions, confidence, and similar historical cases."
    )

    loading_banner = st.empty()
    loading_banner.info("Hang tight — we are loading the model and preparing the prediction workspace.")

    try:
        with st.spinner("Loading prediction engine..."):
            model, encoders, target_encoder = load_artifacts()
            df = load_data()
        loading_banner.empty()
    except Exception as error:
        loading_banner.empty()
        st.error(f"Unable to initialize prediction page: {error}")
        return

    if MODEL_PATH.stat().st_mtime < get_historical_data_path().stat().st_mtime:
        st.warning("The classifier predates the active historical file. Run `python train_attack_model.py` after validating the new release to retrain it.")

    st.sidebar.header("Quick Scenario Presets")
    preset = st.sidebar.selectbox(
        "Load a starter scenario",
        [
            "Custom",
            "Urban explosive attack",
            "Rural armed assault",
            "Hostage-style incident",
        ],
    )

    preset_defaults = {
        "Urban explosive attack": {
            "country_txt": df["country_txt"].mode().iloc[0],
            "region_txt": df["region_txt"].mode().iloc[0],
            "weaptype1_txt": "Explosives",
            "targtype1_txt": "Private Citizens & Property",
            "gname": df["gname"].mode().iloc[0],
            "success": 1,
            "suicide": 0,
            "nkill": 5,
            "nwound": 12,
        },
        "Rural armed assault": {
            "country_txt": df["country_txt"].mode().iloc[0],
            "region_txt": df["region_txt"].mode().iloc[0],
            "weaptype1_txt": "Firearms",
            "targtype1_txt": "Police",
            "gname": df["gname"].mode().iloc[0],
            "success": 1,
            "suicide": 0,
            "nkill": 2,
            "nwound": 4,
        },
        "Hostage-style incident": {
            "country_txt": df["country_txt"].mode().iloc[0],
            "region_txt": df["region_txt"].mode().iloc[0],
            "weaptype1_txt": "Firearms",
            "targtype1_txt": "Business",
            "gname": df["gname"].mode().iloc[0],
            "success": 1,
            "suicide": 0,
            "nkill": 0,
            "nwound": 1,
        },
    }

    if preset != "Custom":
        st.sidebar.success(f"Preset selected: {preset}")

    with st.form("prediction_form"):
        form_col1, form_col2 = st.columns(2)

        with form_col1:
            country = st.selectbox(
                "🌍 Country",
                sorted(df["country_txt"].unique()),
                index=sorted(df["country_txt"].unique()).index(preset_defaults.get(preset, {}).get("country_txt", sorted(df["country_txt"].unique())[0])) if preset in preset_defaults and preset_defaults[preset]["country_txt"] in sorted(df["country_txt"].unique()) else 0,
            )
            region = st.selectbox(
                "🌎 Region",
                sorted(df["region_txt"].unique()),
                index=sorted(df["region_txt"].unique()).index(preset_defaults.get(preset, {}).get("region_txt", sorted(df["region_txt"].unique())[0])) if preset in preset_defaults and preset_defaults[preset]["region_txt"] in sorted(df["region_txt"].unique()) else 0,
            )
            weapon = st.selectbox(
                "🔫 Weapon Type",
                sorted(df["weaptype1_txt"].unique()),
                index=sorted(df["weaptype1_txt"].unique()).index(preset_defaults.get(preset, {}).get("weaptype1_txt", sorted(df["weaptype1_txt"].unique())[0])) if preset in preset_defaults and preset_defaults[preset]["weaptype1_txt"] in sorted(df["weaptype1_txt"].unique()) else 0,
            )
            target = st.selectbox(
                "🎯 Target Type",
                sorted(df["targtype1_txt"].unique()),
                index=sorted(df["targtype1_txt"].unique()).index(preset_defaults.get(preset, {}).get("targtype1_txt", sorted(df["targtype1_txt"].unique())[0])) if preset in preset_defaults and preset_defaults[preset]["targtype1_txt"] in sorted(df["targtype1_txt"].unique()) else 0,
            )

        with form_col2:
            group = st.selectbox(
                "👥 Terrorist Group",
                sorted(df["gname"].unique()),
                index=sorted(df["gname"].unique()).index(preset_defaults.get(preset, {}).get("gname", sorted(df["gname"].unique())[0])) if preset in preset_defaults and preset_defaults[preset]["gname"] in sorted(df["gname"].unique()) else 0,
            )
            success = st.selectbox(
                "✅ Attack Successful?",
                [0, 1],
                index=1 if preset in preset_defaults and preset_defaults[preset]["success"] == 1 else 0,
                format_func=lambda value: "Yes" if value == 1 else "No",
            )
            suicide = st.selectbox(
                "💣 Suicide Attack?",
                [0, 1],
                index=1 if preset in preset_defaults and preset_defaults[preset]["suicide"] == 1 else 0,
                format_func=lambda value: "Yes" if value == 1 else "No",
            )
            nkill = st.number_input(
                "☠ Number of Fatalities",
                min_value=0,
                value=int(preset_defaults.get(preset, {}).get("nkill", 0)),
                step=1,
            )
            nwound = st.number_input(
                "🏥 Number of Injured",
                min_value=0,
                value=int(preset_defaults.get(preset, {}).get("nwound", 0)),
                step=1,
            )

        submitted = st.form_submit_button("🚀 Predict Attack Type")

    st.markdown("---")

    overview_col1, overview_col2, overview_col3, overview_col4 = st.columns(4)
    overview_col1.metric("Records Available", f"{len(df):,}")
    overview_col2.metric("Attack Types", f"{df['attacktype1_txt'].nunique():,}")
    overview_col3.metric("Countries", f"{df['country_txt'].nunique():,}")
    overview_col4.metric("Risk Level", risk_label(nkill, nwound, success, suicide))

    if not submitted:
        st.info("Fill in the form and press Predict Attack Type to see the result.")
        return

    try:
        encoded_input = pd.DataFrame(
            {
                "country_txt": [encode_value(encoders, "country_txt", country)],
                "region_txt": [encode_value(encoders, "region_txt", region)],
                "weaptype1_txt": [encode_value(encoders, "weaptype1_txt", weapon)],
                "targtype1_txt": [encode_value(encoders, "targtype1_txt", target)],
                "gname": [encode_value(encoders, "gname", group)],
                "success": [int(success)],
                "suicide": [int(suicide)],
                "nkill": [int(nkill)],
                "nwound": [int(nwound)],
            }
        )

        prediction = model.predict(encoded_input)
        predicted_attack = target_encoder.inverse_transform(prediction)[0]
        prediction_probabilities = model.predict_proba(encoded_input)[0]
        top_indices = prediction_probabilities.argsort()[::-1][:3]
        top_predictions = [
            {
                "attack": target_encoder.inverse_transform([index])[0],
                "probability": float(prediction_probabilities[index]),
            }
            for index in top_indices
        ]

        scenario_mask = (
            (df["country_txt"] == country)
            & (df["region_txt"] == region)
            & (df["weaptype1_txt"] == weapon)
            & (df["targtype1_txt"] == target)
        )
        scenario_df = df[scenario_mask].copy()
        similar_cases = len(scenario_df)
        common_attack = scenario_df["attacktype1_txt"].mode().iloc[0] if not scenario_df.empty else "Unavailable"
        common_fatalities = int(scenario_df["nkill"].median()) if not scenario_df.empty else 0
        common_injuries = int(scenario_df["nwound"].median()) if not scenario_df.empty else 0

        result_col1, result_col2 = st.columns([1, 1])

        with result_col1:
            st.success(f"Predicted Attack Type: {predicted_attack}")
            st.metric("Prediction Confidence", f"{prediction_probabilities.max() * 100:.2f}%")

            st.subheader("Top Prediction Alternatives")
            st.bar_chart(
                pd.DataFrame(
                    {
                        "Attack Type": [item["attack"] for item in top_predictions],
                        "Probability": [item["probability"] for item in top_predictions],
                    }
                ).set_index("Attack Type")
            )

        with result_col2:
            st.subheader("Scenario Intelligence")
            st.write(
                f"- Similar historical cases: {similar_cases:,}\n"
                f"- Most common attack type in similar cases: {common_attack}\n"
                f"- Median fatalities in similar cases: {common_fatalities}\n"
                f"- Median injuries in similar cases: {common_injuries}"
            )

            if similar_cases > 0:
                similar_sample = scenario_df[
                    ["country_txt", "region_txt", "attacktype1_txt", "weaptype1_txt", "targtype1_txt", "nkill", "nwound"]
                ].head(10)
                st.dataframe(similar_sample, use_container_width=True)
            else:
                st.info("No directly matching historical cases were found for this scenario.")

        st.markdown("---")

        insights_col1, insights_col2 = st.columns(2)

        with insights_col1:
            st.subheader("What the Model Is Using")
            st.write(
                "The model was trained on country, region, weapon type, target type, group name, success flag, suicide flag, fatalities, and injuries. "
                "That means the prediction is best treated as a statistical suggestion, not a deterministic answer."
            )

        with insights_col2:
            st.subheader("Quick Guidance")
            st.write(
                "Use the scenario presets to test common incident patterns, then compare the confidence score and the historical case similarity. "
                "If confidence is low or the case count is tiny, the model is giving a weaker signal."
            )

    except Exception as error:
        st.error(f"Prediction failed: {error}")


if __name__ == "__main__":
    main()
