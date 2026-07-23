# 🛡️ SignalWatch | Military Intelligence Dashboard

A modern, highly optimized military intelligence and situational awareness dashboard built with **Streamlit**, **Pandas**, and **Scikit-Learn**. 

SignalWatch combines structured historical intelligence analysis of Global Terrorism Database (GTD) records with real-time open-source news-report triage via GDELT APIs, complemented by machine learning models for predictive threat assessment and forecasting.

---

## 🎯 Key Features

### 1. Historical Analysis & Situational Awareness
*   **🏠 Overview & Trends:** High-level metrics tracking total historical incidents, fatalities, country volumes, and area chart trends.
*   **🌍 Global Threat Map:** Interactive spatial plotting of incident hotspots with advanced sidebar filters (Year Range, Region, Country, Attack Type).
*   **🌎 Country Analysis:** Granular mix analysis of tactics, target profiles, and weapon choices over time.
*   **🧠 AI Executive Briefings:** Instantly compile executive summaries outlining key regional trends, most active groups, and common attack profiles.
*   **📊 Data Explorer:** Detailed table of historical reports with on-demand summary viewing to protect system memory.

### 2. Machine Learning & Predictive Modeling
*   **🤖 Attack Type Prediction:** Random Forest Classifier predicting the most likely attack strategy (e.g., bombing, armed assault) based on target, group, country, and weapon profiles.
*   **🚨 Threat Level Prediction:** Live, on-demand Random Forest training to classify threat categories (Low, Medium, High) from scenario presets.
*   **📈 Forecasting:** Linear Regression modeling of yearly attack patterns to forecast trends up to 10 years ahead.

### 3. Real-Timeawareness
*   **📡 Live Feed:** Rolling triage queue fed by GDELT API tracking open-source news reporting. Alerts can be fetched, reviewed, and exported.

---

## ⚡ Performance & Memory Optimizations
Designed to run smoothly on systems with severely limited hardware resources (e.g. low-memory WSL/Ubuntu containers):

*   **Column-Level Parquet Loading:** The dataloader reads *only* the specific columns requested by the active view instead of loading the entire 193 MB dataset into cache, reducing baseline memory consumption by **97%** (from 193 MB down to 4.8 MB).
*   **Model Pruning & Quantization:** The pre-trained Random Forest model size was optimized from **1.19 GB down to 52.9 MB** (a 95.6% savings) by setting a structured `max_depth=15` and `n_estimators=50`, preserving **85.11% accuracy** (virtually identical to the unconstrained model) while resolving out-of-memory crashes.
*   **Optimized Live Training:** Live Random Forest training parameters were adjusted (`n_estimators=30`, `max_depth=12`), decreasing runtimes to **<4 seconds** and avoiding thread hanging.

---

## 🚀 Getting Started


### run on StreamLit
https://militaryintelligencedashboard.streamlit.app/

### Prerequisites
Install all dependencies listed in the requirements file:
```bash
pip install -r requirements.txt
```

### Run the App
Launch the Streamlit dashboard on port `8501`:
```bash
streamlit run app.py
```
*Note: On first run, the system automatically builds an optimized Parquet database from your raw CSV to accelerate subsequent loading times by 10-50x.*

### Command-Line Live Feed Update
To update the GDELT open-source news feed as a cron or scheduled task without opening the UI:
```bash
python scripts/refresh_live_feed.py --days 7
```

---

## 📂 Project Structure
```
├── app.py                     # Main dashboard entrypoint
├── requirements.txt           # Package dependencies
├── utils/
│   ├── data_loader.py         # Column-filtered loading and serialization
│   └── ui.py                  # Theme configs and shared UI layout blocks
├── pages/                     # Individual analytical modules
│   ├── 1_🏠Home.py
│   ├── 2_🌍Global_Threat_Map.py
│   ├── 3_🌎Country_Analysis.py
│   ├── 4_🤖 Attack_Prediction.py
│   ├── 5_🚨Threat_Level_Prediction.py
│   ├── 6_📈Forecasting.py
│   ├── 7_🧠Ai_Intelligence_Report.py
│   ├── 8_📊Data_Explorer.py
│   ├── 9_⚙️Settings.py
│   └── 10_📡Live_Feed.py
├── scripts/                   # Background update scripts
└── models/                    # Pickled Scikit-Learn classifiers
```

---

## 📄 License & Data Attributions
*   **Historical Data:** Global Terrorism Database (GTD) obtained via licensing directly from the National Consortium for the Study of Terrorism and Responses to Terrorism (START).
*   **Real-time Data:** Global Database of Events, Language, and Tone (GDELT) project APIs.
