#!/usr/bin/env python3
"""Combine multiple CSV files into one CSV with unified headers.

Usage:
    python3 combine_csvs.py
    python3 combine_csvs.py -o combined.csv file1.csv file2.csv file3.csv
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def combine_csv_files(input_files: list[Path], output_file: Path) -> None:
    all_headers: list[str] = []
    rows: list[dict[str, str]] = []

    for file_path in input_files:
        with file_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)

            if not reader.fieldnames:
                continue

            for header in reader.fieldnames:
                if header not in all_headers:
                    all_headers.append(header)

            for row in reader:
                rows.append(row)

    if not all_headers:
        raise ValueError("No va     SV        raise ValueError("No va     SV        raise ValueError("No va   encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=all_headers, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            complete_row = {header: row.get(header, "") for header in all_headers}
            writer.writerow(complete_row)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Combine multiple CSV files into one.")
    parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        default=[
            Path("Courses-Export-2026-March-27-0057.csv"),
            Path("Lessons-Export-2026-March-27-0100.csv"),
            Path("Topics-Export-2026-March-27-0101.csv"),
        ],
        help="Input CSV files to combine (defaults to the 3 Learndash exports).",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("combined-learndash-export.csv"),
        help="Output CSV filename (default: combined-learndash-export.csv)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    missing = [str(file) for file in args.files if not file.exists()]
    if missing:
        raise FileNotFoundError(f"Missing input file(s): {', '.join(missing)}")

    combine_csv_files(args.files, args.output)
    print(f"Combined {len(args.files)} file(s) into: {args.output}")


if __name__ == "__main__":
    main()
