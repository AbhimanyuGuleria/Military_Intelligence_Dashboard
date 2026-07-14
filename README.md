# Intelligence Dashboard

Streamlit dashboard for exploratory, historical terrorism analysis and an explicitly separate live open-source news-triage feed.

## Run

```powershell
pip install -r requirements.txt
streamlit run app.py
```

## Data freshness

The bundled `globalterrorismdb_0718dist.csv` is historical and ends in 2017. GTD's current public release covers 1970–2020 and must be obtained directly from START under its license. Use **Settings → Historical GTD release** to upload that licensed CSV/XLSX; it is saved locally as `data/gtd_latest.*` and becomes the source for every historical page.

The **Live Feed** page can refresh a rolling GDELT news-report feed. It is not GTD data, is not an incident database, and must be assessed by an analyst before use. To refresh it without opening the UI, run:

```powershell
python scripts/refresh_live_feed.py --days 7
```

Schedule that command daily with Task Scheduler, cron, or your CI scheduler. It needs internet access at run time.
