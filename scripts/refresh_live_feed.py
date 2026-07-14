"""Command-line refresh for the live open-source report queue."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.data_loader import refresh_live_reports  # noqa: E402


parser = argparse.ArgumentParser(description="Refresh live GDELT open-source reports.")
parser.add_argument("--days", type=int, default=7, help="Rolling lookback window (1-30).")
parser.add_argument("--max-records", type=int, default=100, help="Maximum reports to save (1-250).")
args = parser.parse_args()

reports, metadata = refresh_live_reports(days=max(1, min(args.days, 30)), max_records=args.max_records)
print(f"Saved {len(reports)} live reports at {metadata['retrieved_at']}")
