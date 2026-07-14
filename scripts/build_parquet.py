"""
build_parquet.py
----------------
One-time conversion: gtd_latest.csv  ->  gtd_latest.parquet

Run manually:
    python scripts/build_parquet.py

Or called automatically by data_loader when the parquet cache is missing.

The parquet file is:
  - ~12x smaller than the CSV (snappy compression)
  - Columnar: pages read ONLY the columns they need (~1-3 MB each)
  - 10-50x faster to load than CSV
  - Stored in: data/gtd_latest.parquet
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd

# Only the columns used anywhere in the dashboard
KEEP_COLUMNS = [
    "eventid",
    "iyear", "imonth", "iday",
    "country_txt", "region_txt",
    "city", "provstate",
    "attacktype1_txt",
    "weaptype1_txt",
    "targtype1_txt",
    "gname",
    "success", "suicide", "ransom",
    "nkill", "nwound",
    "latitude", "longitude",
    "summary",
]

DTYPE_MAP = {
    "eventid": "Int64",
    "iyear":   "Int16",
    "imonth":  "Int8",
    "iday":    "Int8",
    "success": "Int8",
    "suicide": "Int8",
    "ransom":  "Int8",
    "nkill":   "float32",
    "nwound":  "float32",
    "latitude":  "float32",
    "longitude": "float32",
}


def build_parquet(csv_path: Path, parquet_path: Path) -> Path:
    print(f"Reading CSV: {csv_path.name}  ({csv_path.stat().st_size / 1024**2:.1f} MB)")
    t0 = time.time()

    chunks = []
    chunk_size = 50_000
    total_rows = 0

    reader = pd.read_csv(
        csv_path,
        encoding="latin1",
        low_memory=False,
        chunksize=chunk_size,
        usecols=lambda c: c in KEEP_COLUMNS,
    )

    for i, chunk in enumerate(reader):
        # Apply dtypes for memory savings
        for col, dtype in DTYPE_MAP.items():
            if col in chunk.columns:
                chunk[col] = pd.to_numeric(chunk[col], errors="coerce").astype(dtype)
        # String columns: use efficient category for high-cardinality ones
        for col in ["country_txt", "region_txt", "attacktype1_txt",
                    "weaptype1_txt", "targtype1_txt"]:
            if col in chunk.columns:
                chunk[col] = chunk[col].astype("category")
        chunks.append(chunk)
        total_rows += len(chunk)
        print(f"  Processed {total_rows:,} rows…", end="\r")

    df = pd.concat(chunks, ignore_index=True)
    print(f"\nTotal rows: {len(df):,}  |  Columns: {len(df.columns)}")

    # Write parquet
    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(parquet_path, index=False, compression="snappy", engine="pyarrow")

    size_mb = parquet_path.stat().st_size / 1024**2
    elapsed = time.time() - t0
    print(f"Parquet saved: {parquet_path.name}  ({size_mb:.1f} MB)  [{elapsed:.1f}s]")
    print(f"Compression ratio: {csv_path.stat().st_size / parquet_path.stat().st_size:.1f}x")
    return parquet_path


if __name__ == "__main__":
    data_dir = PROJECT_ROOT / "data"

    # Find the source CSV
    candidates = list(data_dir.glob("gtd_latest.csv"))
    if not candidates:
        candidates = list(data_dir.glob("gtd*.csv"))
    if not candidates:
        print("ERROR: No GTD CSV found in data/. Upload one via the Settings page first.")
        sys.exit(1)

    csv_path = candidates[0]
    parquet_path = data_dir / "gtd_latest.parquet"

    if parquet_path.exists() and parquet_path.stat().st_mtime >= csv_path.stat().st_mtime:
        print(f"Parquet is already up to date: {parquet_path.name}")
        sys.exit(0)

    build_parquet(csv_path, parquet_path)
    print("Done. All dashboard pages will now load from the parquet file.")
