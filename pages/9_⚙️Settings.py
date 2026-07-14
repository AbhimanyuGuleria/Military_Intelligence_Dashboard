from pathlib import Path

import streamlit as st

from utils.data_loader import DATA_DIR, LIVE_FEED_PATH, historical_status, load_historical_data
from utils.ui import apply_theme, hero


st.set_page_config(page_title="SignalWatch | Settings", page_icon="⚙️", layout="wide")
apply_theme()


def main() -> None:
    hero("Data administration", "Settings & data health", "Update the licensed historical release, inspect data coverage, and configure the live-refresh workflow.")
    has_status = False
    try:
        status = historical_status()
        has_status = True
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Historical records", f"{status['records']:,}")
        col2.metric("Coverage", f"{status['first_year']}–{status['last_year']}")
        col3.metric("Active file", status['path'].name)
        col4.metric("File modified (UTC)", status['updated'].strftime("%Y-%m-%d"))
    except Exception as error:
        st.warning("No historical GTD dataset found. Use the uploader below to initialize the dashboard with your licensed GTD data release (.csv or .xlsx).")


    st.subheader("Historical GTD release")
    st.info("The official GTD provider's current public release covers 1970–2020. Download it directly from START after accepting its license, then upload it here. The dashboard will never download or redistribute licensed GTD data on your behalf.")
    uploaded = st.file_uploader("Upload licensed GTD CSV or XLSX", type=["csv", "xlsx", "xls"])
    if uploaded is not None:
        target = DATA_DIR / f"gtd_latest{Path(uploaded.name).suffix.lower()}"
        try:
            target.write_bytes(uploaded.getbuffer())
            st.cache_data.clear()
            updated = historical_status()
            if updated["last_year"] < 2018:
                st.warning(f"Saved {target.name}, but its latest year appears to be {updated['last_year']}. Confirm this is the intended GTD release.")
            else:
                st.success(f"Saved {target.name}. Historical pages now use coverage through {updated['last_year']}.")
        except Exception as error:
            st.error(f"The file could not be saved or read: {error}")

    st.subheader("Live open-source refresh")
    st.write("Live Feed uses GDELT’s public news API and stores the last response locally. It does not alter historical GTD metrics.")
    st.code("python scripts/refresh_live_feed.py --days 7", language="powershell")
    if LIVE_FEED_PATH.exists():
        st.success(f"A cached review queue exists: {LIVE_FEED_PATH.name}")
    else:
        st.warning("No live feed cache yet. Open Live Feed and choose Refresh live reports.")

    st.subheader("Analytical safeguards")
    st.markdown(
        "- Historical trends are descriptive and reflect the loaded GTD release.\n"
        "- Live articles require analyst verification and may be duplicated or incomplete.\n"
        "- Prediction outputs are retrospective statistical classifications, not forecasts of specific incidents.\n"
        "- Do not use this dashboard as the sole basis for operational or safety decisions."
    )


main()
