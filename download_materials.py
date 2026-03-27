#!/usr/bin/env python3
"""Download files from Attachment URL and Image URL columns into a materials folder.

Usage:
    python3 download_materials.py
    python3 download_materials.py --csv seedlab-lessons-topic-video-map-export-270326-14-14.csv --output-dir materials
    python3 download_materials.py --overwrite
"""

from __future__ import annotations

import argparse
import csv
import re
import ssl
import urllib.error
import urllib.request
from pathlib import Path
from typing import Iterable
from urllib.parse import unquote, urlparse

try:
    import certifi
except ImportError:
    certifi = None


DEFAULT_CSV = Path("seedlab-lessons-topic-video-map-export-270326-14-14.csv")
DEFAULT_OUTPUT_DIR = Path("materials")
URL_COLUMNS = ("Attachment URL", "Image URL")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download files listed in Attachment URL and Image URL columns."
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=DEFAULT_CSV,
        help="CSV file to read (default: seedlab-lessons-topic-video-map-export-270326-14-14.csv)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Folder where files will be downloaded (default: materials)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing files instead of skipping them.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="HTTP timeout in seconds (default: 30)",
    )
    return parser.parse_args()


def iter_cell_urls(cell_value: str) -> Iterable[str]:
    if not cell_value:
        return
    # Learndash exports commonly store multiple file URLs in one cell using '|'.
    # Some exports may also include line breaks, so we split on both.
    for part in re.split(r"[|\r\n]+", cell_value):
        url = part.strip()
        if url:
            yield url


def is_http_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def sanitize_filename(filename: str) -> str:
    filename = filename.strip().strip(".")
    filename = re.sub(r"[<>:\"/\\|?*\x00-\x1F]", "_", filename)
    return filename or "downloaded_file"


def filename_from_url(url: str) -> str:
    parsed = urlparse(url)
    name = unquote(Path(parsed.path).name)
    return sanitize_filename(name or "downloaded_file")


def make_unique_path(base_path: Path) -> Path:
    if not base_path.exists():
        return base_path

    stem = base_path.stem
    suffix = base_path.suffix
    counter = 1
    while True:
        candidate = base_path.with_name(f"{stem}_{counter}{suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def build_ssl_context() -> ssl.SSLContext:
    """Build SSL context, preferring certifi CA bundle when available."""
    context = ssl.create_default_context()
    if certifi is not None:
        context.load_verify_locations(certifi.where())
    return context


def download_file(url: str, destination: Path, timeout: int, ssl_context: ssl.SSLContext) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=timeout, context=ssl_context) as response, destination.open("wb") as f:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)


def collect_urls(csv_path: Path) -> tuple[list[str], int]:
    urls: list[str] = []
    invalid_count = 0

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return urls, invalid_count

        for row in reader:
            for column in URL_COLUMNS:
                for url in iter_cell_urls(row.get(column, "")):
                    if is_http_url(url):
                        urls.append(url)
                    else:
                        invalid_count += 1

    return urls, invalid_count


def unique_preserve_order(items: list[str]) -> tuple[list[str], int]:
    seen: set[str] = set()
    unique_items: list[str] = []
    duplicates = 0
    for item in items:
        if item in seen:
            duplicates += 1
            continue
        seen.add(item)
        unique_items.append(item)
    return unique_items, duplicates


def main() -> None:
    args = parse_args()

    if not args.csv.exists():
        raise FileNotFoundError(f"CSV file not found: {args.csv}")

    args.output_dir.mkdir(parents=True, exist_ok=True)

    all_urls, invalid_urls = collect_urls(args.csv)
    unique_urls, duplicate_urls = unique_preserve_order(all_urls)
    ssl_context = build_ssl_context()

    downloaded = 0
    skipped_existing = 0
    failed = 0

    for index, url in enumerate(unique_urls, start=1):
        filename = filename_from_url(url)
        target = args.output_dir / filename

        if target.exists() and not args.overwrite:
            skipped_existing += 1
            print(f"[{index}/{len(unique_urls)}] Skipped (exists): {target.name}")
            continue

        if target.exists() and args.overwrite:
            destination = target
        else:
            destination = make_unique_path(target)

        try:
            download_file(url, destination, timeout=args.timeout, ssl_context=ssl_context)
            downloaded += 1
            print(f"[{index}/{len(unique_urls)}] Downloaded: {destination.name}")
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
            failed += 1
            if destination.exists():
                destination.unlink(missing_ok=True)
            print(f"[{index}/{len(unique_urls)}] Failed: {url} ({exc})")

    print("\nDownload summary")
    print("----------------")
    print(f"Rows URLs found      : {len(all_urls)}")
    print(f"Unique URLs attempted: {len(unique_urls)}")
    print(f"Downloaded           : {downloaded}")
    print(f"Skipped (existing)   : {skipped_existing}")
    print(f"Failed               : {failed}")
    print(f"Duplicate URLs       : {duplicate_urls}")
    print(f"Invalid URLs         : {invalid_urls}")
    print(f"Output directory     : {args.output_dir}")


if __name__ == "__main__":
    main()
