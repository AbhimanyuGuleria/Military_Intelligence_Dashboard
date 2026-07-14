import pandas as pd
import streamlit as st

from utils.data_loader import load_live_reports, refresh_live_reports
from utils.ui import apply_theme, hero


st.set_page_config(page_title="SignalWatch | Live Feed", page_icon="📡", layout="wide")
apply_theme()


def main() -> None:
    hero("Open-source triage", "Live report queue", "Recent news reports matching the query. They are not verified incident records and must not be treated as GTD data.")
    st.warning("Verification required: article language, duplicate reporting, and the use of terrorism-related terms vary by publisher. Review the original source before drawing conclusions.")
    controls = st.columns([1, 1, 3])
    with controls[0]:
        days = st.selectbox("Lookback", [1, 3, 7, 14, 30], index=2)
    with controls[1]:
        max_records = st.selectbox("Max reports", [25, 50, 100, 200], index=2)
    with controls[2]:
        st.write("")
        refresh = st.button("Refresh live reports", type="primary", use_container_width=True)

    if refresh:
        try:
            with st.spinner("Querying open-source reports..."):
                reports, metadata = refresh_live_reports(days=days, max_records=max_records)
            st.success(f"Retrieved {len(reports):,} reports at {metadata['retrieved_at'][:19].replace('T', ' ')} UTC.")
        except Exception as error:
            st.error(f"The live feed could not be refreshed: {error}")
            reports, metadata = load_live_reports()
    else:
        reports, metadata = load_live_reports()

    if reports.empty:
        st.info("No saved reports. Refresh the feed to create a review queue.")
        return

    source_options = sorted(reports["source"].dropna().unique()) if "source" in reports else []
    selected_sources = st.multiselect("Filter by publisher", source_options)
    query = st.text_input("Search titles or publishers")
    filtered = reports.copy()
    if selected_sources:
        filtered = filtered[filtered["source"].isin(selected_sources)]
    if query:
        mask = filtered["title"].fillna("").str.contains(query, case=False, regex=False) | filtered["source"].fillna("").str.contains(query, case=False, regex=False)
        filtered = filtered[mask]

    st.metric("Reports in view", f"{len(filtered):,}")
    display = filtered[[c for c in ["seen_date", "title", "source", "source_country", "language", "url"] if c in filtered]].copy()
    st.dataframe(display, use_container_width=True, hide_index=True, column_config={"url": st.column_config.LinkColumn("Open source", display_text="Open article")})
    st.download_button("Download review queue", filtered.to_csv(index=False), "live_report_queue.csv", "text/csv")
    st.caption(f"Provider: {metadata.get('provider', 'Not refreshed')}. Query: {metadata.get('query', 'n/a')}. Last refresh: {metadata.get('retrieved_at', 'n/a')}.")


main()
