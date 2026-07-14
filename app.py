import streamlit as st

from utils.data_loader import historical_status, load_live_reports
from utils.ui import apply_theme, hero


st.set_page_config(page_title="SignalWatch | Intelligence Dashboard", page_icon="🛡️", layout="wide")
apply_theme()


def main() -> None:
    hero(
        "Historical analysis + live awareness",
        "SignalWatch Intelligence Dashboard",
        "Explore licensed historical GTD data, monitor a separate open-source report queue, and keep every conclusion traceable to its source.",
    )
    try:
        status = historical_status()
        reports, metadata = load_live_reports()
    except Exception as error:
        st.error(f"Data status could not be read: {error}")
        return

    cols = st.columns(4)
    cols[0].metric("Historical coverage", f"{status['first_year']}–{status['last_year']}")
    cols[1].metric("Historical records", f"{status['records']:,}")
    cols[2].metric("Live reports cached", f"{len(reports):,}")
    cols[3].metric("Last live refresh", metadata.get("retrieved_at", "Not yet refreshed")[:19].replace("T", " "))

    st.subheader("Start here")
    st.info(
        "Use **Home** for a concise operating picture, **Live Feed** for current open-source reporting, and **Settings** to load a newer licensed GTD release. "
        "Prediction pages are retrospective analytical aids—not early-warning systems or operational recommendations."
    )
    st.caption("Data boundaries: GTD historical metrics and live news reports are never merged. Validate any live report against primary sources before acting on it.")


if __name__ == "__main__":
    main()
