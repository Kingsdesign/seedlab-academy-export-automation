## Process to make csv file ready for ALLM

- Export All Courses, lessons and topics from live site
  - Use the existing export template from All Export > Manage Exports
  - If doing a new export make sure to include the following on the export
    - ID
    - Post Type
    - Title
    - Content
    - Course Categories
    - Permalink
    - Attachment URL
    - Attachment Filename
    - Image URL
    - Image Filename
- Add your exported file to the folder
- Follow the steps below

# Learndash CSV Combine Script

This folder includes a Python script (`combine_csvs.py`) to combine the 3 Learndash export CSV files into one file.

## CSV Files expected (file name as exported)

- `Courses-Export-2026-March-27-0057.csv`
- `Lessons-Export-2026-March-27-0100.csv`
- `Topics-Export-2026-March-27-0101.csv`

## Combining Python Script

- `combine_csvs.py`

## What the script does

- Reads the 3 CSV export files
- Merges all rows into one output CSV
- Keeps all unique column headers across all files
- Fills missing values with blank cells when a row doesn't contain a column
- Adds a new column: `Parent Course Category`
- Cross-maps lessons/topics to their parent course category using permalink structure
  - Extracts the slug from `/courses/<course-slug>/...` in lesson/topic permalinks
  - Matches that slug against course permalinks
  - Copies the matched course `Course Categories` value into `Parent Course Category`
- For course rows, `Parent Course Category` is set directly from `Course Categories`
- Adds a new column: `Vimeo Video`
- If `Content` contains a Vimeo iframe/link, extracts the numeric Vimeo video ID and writes:
  - `video_<video_id>.vtt`
  - Example: iframe URL with `/video/123456789` becomes `video_123456789.vtt`

## Requirements

- Python 3 (no extra packages required)

## How to run

- Make sure to update the file names on 'combine_csvs.py' file.
- Open terminal in this folder and run:

```bash
python3 combine_csvs.py
```

This creates:

- `seedlab-lessons-topic-video-map-export-date-time.csv` eg: seedlab-lessons-topic-video-map-export-270326-14-14.csv

## Optional: custom output file name

```bash
python3 combine_csvs.py -o my-combined-file.csv
```

## Optional: custom input files

```bash
python3 combine_csvs.py file1.csv file2.csv file3.csv -o combined.csv
```

## Download materials from Attachment URL + Image URL

Use `download_materials.py` to download all files referenced in:

- `Attachment URL`
- `Image URL`

from `combined-learndash-export.csv` (or another CSV you provide).

### What this script does

- Reads CSV using UTF-8 BOM-safe parsing
- Extracts URLs from both columns above
- Handles **multiple files in a single row/cell** (supports `|`-separated URLs, and line breaks)
- Creates a local `materials` folder automatically
- Downloads files into that folder
- Skips invalid/blank URLs safely
- Avoids filename collisions automatically (e.g. `file.pdf`, `file_1.pdf`, ...)
- Prints a final summary (found, downloaded, skipped, failed, duplicates)

### How to run

Default run:

```bash
python3 download_materials.py
```

Custom CSV / output folder:

```bash
python3 download_materials.py --csv combined-learndash-export.csv --output-dir materials
```

Overwrite existing files:

```bash
python3 download_materials.py --overwrite
```

Set timeout:

```bash
python3 download_materials.py --timeout 60
```

### Note (SSL certificate errors)

`download_materials.py` now attempts to use the `certifi` CA bundle automatically (if installed), which fixes most macOS certificate trust issues.

If needed, install certifi:

```bash
python3 -m pip install --upgrade certifi
```

Then run again:

```bash
python3 download_materials.py

## Notes for future use

- Default CSV inputs are defined at the top of `combine_csvs.py` as:
  - `DEFAULT_COURSES_CSV`
  - `DEFAULT_LESSONS_CSV`
  - `DEFAULT_TOPICS_CSV`
    Update these variables when export filenames change.
- If your export file names change, either:
  - rename them to match the defaults in `combine_csvs.py`, or
  - pass the new file names explicitly as arguments.
- If any input file is missing, the script will show an error listing missing files.
- If a lesson/topic permalink does not include `/courses/<course-slug>/`, then `Parent Course Category` will remain blank.
- If no Vimeo URL is found in `Content`, `Vimeo Video` will remain blank.
```
