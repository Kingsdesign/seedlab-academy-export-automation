#!/usr/bin/env python3
"""Combine multiple CSV files into one CSV with unified headers.

Usage:
    python3 combine_csvs.py
    python3 combine_csvs.py -o combined.csv file1.csv file2.csv file3.csv
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from urllib.parse import urlparse


# Default CSV filenames (edit these in one place for future exports)
DEFAULT_COURSES_CSV = "Courses-Export-2026-March-27-0057.csv"
DEFAULT_LESSONS_CSV = "Lessons-Export-2026-March-27-0100.csv"
DEFAULT_TOPICS_CSV = "Topics-Export-2026-March-27-0101.csv"

DEFAULT_INPUT_FILES = [
    Path(DEFAULT_COURSES_CSV),
    Path(DEFAULT_LESSONS_CSV),
    Path(DEFAULT_TOPICS_CSV),
]


def extract_course_slug(permalink: str) -> str | None:
    """Extract course slug from permalink path if present.

    Example:
    https://example.com/courses/week-2-your-business/lessons/goal-setting/
    -> week-2-your-business
    """
    if not permalink:
        return None

    path_parts = [part for part in urlparse(permalink).path.split("/") if part]
    for index, part in enumerate(path_parts):
        if part == "courses" and index + 1 < len(path_parts):
            return path_parts[index + 1]
    return None


def build_course_category_map(input_files: list[Path]) -> dict[str, str]:
    """Map course slug -> course category using rows from the courses export."""
    course_map: dict[str, str] = {}

    for file_path in input_files:
        with file_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                continue

            for row in reader:
                post_type = (row.get("Post Type") or "").strip().lower()
                if post_type != "sfwd-courses":
                    continue

                slug = extract_course_slug(row.get("Permalink", ""))
                category = (row.get("Course Categories") or "").strip()
                if slug:
                    course_map[slug] = category

    return course_map


def extract_vimeo_video_filename(content: str) -> str:
    """Return video_<vimeo_id>.vtt when a Vimeo ID is found in content, else blank.

    Supports common iframe/source patterns such as:
    - https://player.vimeo.com/video/123456789
    - https://vimeo.com/123456789
    """
    if not content:
        return ""

    patterns = [
        r"player\.vimeo\.com/video/(\d+)",
        r"vimeo\.com/(\d+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, content)
        if match:
            video_id = match.group(1)
            return f"video_{video_id}.vtt"

    return ""


def combine_csv_files(input_files: list[Path], output_file: Path) -> None:
    course_category_map = build_course_category_map(input_files)

    all_headers: list[str] = []
    rows: list[dict[str, str]] = []

    mapped_category_column = "Parent Course Category"
    vimeo_video_column = "Vimeo Video"

    for file_path in input_files:
        with file_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)

            if not reader.fieldnames:
                continue

            for header in reader.fieldnames:
                if header not in all_headers:
                    all_headers.append(header)

            if mapped_category_column not in all_headers:
                all_headers.append(mapped_category_column)

            if vimeo_video_column not in all_headers:
                all_headers.append(vimeo_video_column)

            for row in reader:
                post_type = (row.get("Post Type") or "").strip().lower()

                if post_type == "sfwd-courses":
                    mapped_category = (row.get("Course Categories") or "").strip()
                else:
                    slug = extract_course_slug(row.get("Permalink", ""))
                    mapped_category = course_category_map.get(slug, "") if slug else ""

                row[mapped_category_column] = mapped_category
                row[vimeo_video_column] = extract_vimeo_video_filename(row.get("Content", ""))
                rows.append(row)

    if not all_headers:
        raise ValueError("No valid CSV headers found in the provided files.")

    with output_file.open("w", encoding="utf-8", newline="") as f:
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
        default=DEFAULT_INPUT_FILES,
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