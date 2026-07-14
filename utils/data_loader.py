"""Shared data access for the dashboard.

The GTD is a historical, licensed research dataset.  It is deliberately kept
separate from the live open-source news feed because the two have different
collection methods and confidence levels.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
LIVE_FEED_PATH = DATA_DIR / "live_open_source_reports.json"
LEGACY_DATA_DIR = PROJECT_ROOT
HISTORICAL_CANDIDATES = (
    "gtd_latest.xlsx",
    "gtd_latest.csv",
    "globalterrorism_2020.xlsx",
    "globalterrorism_2020.csv",
    "globalterrorismdb_0718dist.csv",
    "gtd_sample.csv",
)


def get_historical_data_path() -> Path:
    """Return the newest supported local GTD file, with the bundled file as fallback.

    Releases uploaded through Settings are stored in ``data/``.  Earlier
    dashboard versions, however, saved ``gtd_latest.*`` in the project root.
    Keep that location supported so an existing 2020 release is not ignored in
    favour of the bundled 2017 fallback.
    """
    uploaded_releases = [
        path
        for directory in (DATA_DIR, LEGACY_DATA_DIR)
        for path in directory.glob("gtd_latest.*")
        if path.suffix.lower() in {".csv", ".xls", ".xlsx"}
    ]
    if uploaded_releases:
        return max(uploaded_releases, key=lambda path: path.stat().st_mtime)
    for filename in HISTORICAL_CANDIDATES:
        if filename.startswith("gtd_latest."):
            continue
        path = DATA_DIR / filename
        if path.exists():
            return path
    raise FileNotFoundError("No GTD data file was found in the data directory.")


def _read_file(path: Path, usecols: list[str] | None = None) -> pd.DataFrame:
    # A callable keeps the app compatible with GTD releases that omit optional fields.
    selector = (lambda column: column in set(usecols)) if usecols else None
    if path.suffix.lower() == ".parquet":
        # Parquet performs projection at the storage layer, avoiding allocation
        # for columns that the active page does not use.
        return pd.read_parquet(path, columns=usecols or None)
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path, usecols=selector)
    return pd.read_csv(path, encoding="latin1", low_memory=False, usecols=selector)


def _preferred_read_path(source_path: Path) -> Path:
    """Use a current Parquet companion when available, otherwise use the upload.

    A Parquet file is considered current only when it is at least as new as the
    uploaded licensed release. This prevents stale conversion output from being
    silently selected after a new file upload.
    """
    parquet_path = source_path.with_suffix(".parquet")
    if parquet_path.exists() and parquet_path.stat().st_mtime_ns >= source_path.stat().st_mtime_ns:
        return parquet_path
    return source_path


def valid_date_part(values: pd.Series) -> pd.Series:
    """Return numeric date parts with GTD's zero placeholders treated as null.

    ``Series.replace(0, pd.NA)`` raises on numpy integer dtypes in recent
    pandas versions. ``mask`` safely promotes the result when nulls are needed.
    """
    numeric = pd.to_numeric(values, errors="coerce")
    return numeric.mask(numeric.eq(0)).astype("float64")


@st.cache_data(show_spinner=False)
def load_historical_data(
    path_string: str,
    modified_time_ns: int,
    usecols_key: tuple[str, ...] = (),
) -> pd.DataFrame:
    """Load a selected GTD release and apply consistent numeric/date cleaning."""
    # ``modified_time_ns`` is intentionally part of the cache key.  It makes
    # a replaced upload visible immediately, even when its filename is reused.
    del modified_time_ns
    
    requested_cols = list(usecols_key) if usecols_key else None
    load_cols = None
    has_event_date = False
    if requested_cols is not None:
        if "event_date" in requested_cols:
            has_event_date = True
            requested_cols = [c for c in requested_cols if c != "event_date"]
            for c in ["iyear", "imonth", "iday"]:
                if c not in requested_cols:
                    requested_cols.append(c)
        load_cols = requested_cols

    df = _read_file(Path(path_string), load_cols)
    
    for column in ["iyear", "imonth", "iday", "nkill", "nwound", "latitude", "longitude", "success", "suicide", "ransom"]:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    # Force date columns to plain numpy float64 so pd.NA from nullable Parquet
    # integer types (Int16/Int8) is converted to np.nan, preventing
    # "cannot convert NA to integer" inside pd.to_datetime.
    for column in ["iyear", "imonth", "iday"]:
        if column in df.columns:
            df[column] = df[column].astype("float64")
    for column in ["nkill", "nwound"]:
        if column in df.columns:
            df[column] = df[column].fillna(0)
            
    if {"iyear", "imonth", "iday"}.issubset(df.columns):
        df["event_date"] = pd.to_datetime(
            {
                "year": df["iyear"],
                "month": valid_date_part(df["imonth"]),
                "day": valid_date_part(df["iday"]),
            },
            errors="coerce",
        )
    elif has_event_date:
        df["event_date"] = pd.NaT
        
    return df


def read_historical_data(usecols: list[str] | None = None) -> pd.DataFrame:
    path = get_historical_data_path()
    read_path = _preferred_read_path(path)
    return load_historical_data(str(read_path), read_path.stat().st_mtime_ns, tuple(usecols or []))


@st.cache_data(show_spinner=False)
def load_summaries_for_events(event_ids: tuple[int, ...]) -> pd.DataFrame:
    """Fetch text only for records currently displayed by the Explorer.

    The full summary field is intentionally never part of Explorer's base
    dataset. On Parquet data, Arrow filters this lookup before it reaches RAM.
    CSV/XLSX releases retain the lightweight Explorer view without summaries.
    """
    if not event_ids:
        return pd.DataFrame(columns=["eventid", "summary"])
    source_path = get_historical_data_path()
    parquet_path = _preferred_read_path(source_path)
    if parquet_path.suffix.lower() != ".parquet":
        return pd.DataFrame(columns=["eventid", "summary"])
    try:
        return pd.read_parquet(parquet_path, columns=["eventid", "summary"], filters=[("eventid", "in", list(event_ids))])
    except (KeyError, ValueError, OSError):
        return pd.DataFrame(columns=["eventid", "summary"])


def attach_display_summaries(frame: pd.DataFrame) -> pd.DataFrame:
    """Attach narrative text to a small display frame without bloating base data."""
    if frame.empty or "eventid" not in frame.columns:
        return frame
    event_ids = tuple(pd.to_numeric(frame["eventid"], errors="coerce").dropna().astype("int64").unique().tolist())
    summaries = load_summaries_for_events(event_ids)
    if summaries.empty:
        return frame
    return frame.merge(summaries, on="eventid", how="left")


@st.cache_data(show_spinner=False)
def _historical_status(path_string: str, modified_time_ns: int) -> dict:
    del modified_time_ns
    path = Path(path_string)
    years = _read_file(_preferred_read_path(path), ["iyear"])
    numeric_years = pd.to_numeric(years.get("iyear"), errors="coerce").dropna()
    return {
        "path": path,
        "records": len(years),
        "first_year": int(numeric_years.min()) if not numeric_years.empty else None,
        "last_year": int(numeric_years.max()) if not numeric_years.empty else None,
        "updated": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc),
    }


def historical_status() -> dict:
    path = get_historical_data_path()
    return _historical_status(str(path), path.stat().st_mtime_ns)


def load_live_reports() -> tuple[pd.DataFrame, dict]:
    if not LIVE_FEED_PATH.exists():
        return pd.DataFrame(), {}
    try:
        payload = json.loads(LIVE_FEED_PATH.read_text(encoding="utf-8"))
        return pd.DataFrame(payload.get("articles", [])), payload.get("metadata", {})
    except (json.JSONDecodeError, OSError):
        return pd.DataFrame(), {}


def refresh_live_reports(days: int = 7, max_records: int = 100) -> tuple[pd.DataFrame, dict]:
    """Fetch recent open-source reports from GDELT's public article API.

    These are news reports, not validated GTD incident records.  The feed is
    therefore presented as a triage queue and never merged into GTD metrics.
    """
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    params = {
        "query": '("terrorist attack" OR bombing OR "suicide attack")',
        "mode": "artlist",
        "format": "json",
        "maxrecords": max(1, min(max_records, 250)),
        "startdatetime": start.strftime("%Y%m%d%H%M%S"),
        "enddatetime": end.strftime("%Y%m%d%H%M%S"),
    }
    request = Request(
        "https://api.gdeltproject.org/api/v2/doc/doc?" + urlencode(params),
        headers={"User-Agent": "Historical-Intelligence-Dashboard/1.0"},
    )
    with urlopen(request, timeout=25) as response:  # nosec B310 - fixed public API endpoint
        payload = json.loads(response.read().decode("utf-8"))

    articles = payload.get("articles", [])
    cleaned, seen_urls = [], set()
    for article in articles:
        url = article.get("url", "")
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        cleaned.append({
            "seen_date": article.get("seendate", ""),
            "title": article.get("title", "Untitled report"),
            "source": article.get("domain", "Unknown source"),
            "source_country": article.get("sourcecountry", ""),
            "url": url,
            "language": article.get("language", ""),
        })
    metadata = {
        "provider": "GDELT 2.1 DOC API",
        "retrieved_at": end.isoformat(),
        "window_days": days,
        "query": params["query"],
        "count": len(cleaned),
    }
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LIVE_FEED_PATH.write_text(json.dumps({"metadata": metadata, "articles": cleaned}, indent=2), encoding="utf-8")
    return pd.DataFrame(cleaned), metadata
