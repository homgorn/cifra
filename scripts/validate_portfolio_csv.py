#!/usr/bin/env python3
"""Basic validator for WP portfolio CSV schema."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

REQUIRED_COLUMNS = [
    "post_type",
    "post_status",
    "post_title",
    "post_name",
    "post_content",
    "tax_category",
    "tax_post_tag",
    "featured_image_primary_url",
    "file_path_local",
]


def validate_csv(path: Path) -> int:
    if not path.exists():
        print(f"ERROR: file not found: {path}")
        return 2

    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            print("ERROR: missing required columns:")
            for col in missing:
                print(f"  - {col}")
            return 1

        seen = set()
        duplicate_slugs = 0
        empty_primary = 0
        rows = 0

        for row in reader:
            rows += 1
            slug = (row.get("post_name") or "").strip()
            if slug in seen and slug:
                duplicate_slugs += 1
            seen.add(slug)

            if not (row.get("featured_image_primary_url") or "").strip():
                empty_primary += 1

        print(f"Rows checked: {rows}")
        print(f"Duplicate post_name: {duplicate_slugs}")
        print(f"Empty featured_image_primary_url: {empty_primary}")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate WP portfolio CSV")
    parser.add_argument("csv_path", type=Path, help="Path to CSV file")
    args = parser.parse_args()
    return validate_csv(args.csv_path)


if __name__ == "__main__":
    sys.exit(main())
