"""Build a compact, column-projectable Parquet companion for a GTD CSV release.

The converter reads a bounded number of rows at a time, so creating the cache
does not require the full licensed dataset to be held in memory.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


def build_parquet(source: Path, destination: Path, chunk_size: int = 10_000) -> None:
    if source.suffix.lower() != ".csv":
        raise ValueError("The bounded-memory converter currently accepts CSV releases.")

    temporary = destination.with_suffix(destination.suffix + ".tmp")
    if temporary.exists():
        temporary.unlink()

    writer = None
    try:
        for chunk in pd.read_csv(source, encoding="latin1", dtype=str, chunksize=chunk_size, low_memory=False):
            # Keep a stable integer key for deferred text lookups. All other
            # fields stay as strings and are converted by the page that needs
            # them, matching the existing loader's cleaning behavior.
            if "eventid" in chunk.columns:
                chunk["eventid"] = pd.to_numeric(chunk["eventid"], errors="coerce").astype("Int64")
            table = pa.Table.from_pandas(chunk, preserve_index=False)
            if writer is None:
                writer = pq.ParquetWriter(temporary, table.schema, compression="zstd")
            writer.write_table(table)
    finally:
        if writer is not None:
            writer.close()

    if not temporary.exists():
        raise RuntimeError("No Parquet output was produced.")
    temporary.replace(destination)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a bounded-memory Parquet cache for a GTD CSV.")
    parser.add_argument("source", type=Path, help="Path to the active GTD CSV")
    parser.add_argument("--output", type=Path, help="Destination .parquet path (defaults beside the source)")
    parser.add_argument("--chunk-size", type=int, default=10_000)
    args = parser.parse_args()
    output = args.output or args.source.with_suffix(".parquet")
    build_parquet(args.source, output, args.chunk_size)
    print(f"Created {output}")


if __name__ == "__main__":
    main()
