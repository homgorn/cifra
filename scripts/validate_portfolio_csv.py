#!/usr/bin/env python3
"""Basic validator for WP portfolio CSV schema."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict, dataclass, field
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

EXIT_OK = 0
EXIT_VALIDATION_ERROR = 1
EXIT_NOT_FOUND = 2


@dataclass
class ValidationStats:
    rows_checked: int = 0
    duplicate_slugs: int = 0
    empty_primary_url: int = 0
    malformed_extra_columns: int = 0
    malformed_missing_columns: int = 0
    empty_required_cells: int = 0
    malformed_extra_rows: list[int] = field(default_factory=list)
    malformed_missing_rows: list[int] = field(default_factory=list)
    duplicate_slug_rows: list[int] = field(default_factory=list)
    empty_primary_rows: list[int] = field(default_factory=list)
    empty_required_details: list[tuple[int, str]] = field(default_factory=list)


@dataclass
class ValidationResult:
    exit_code: int
    stats: ValidationStats = field(default_factory=ValidationStats)
    errors: list[str] = field(default_factory=list)


def _format_lines(lines: list[int]) -> str:
    return ", ".join(map(str, lines))


def _build_error_messages(
    stats: ValidationStats,
    *,
    fail_on_duplicate_slug: bool,
    fail_on_empty_primary_url: bool,
    fail_on_empty_required: bool,
) -> list[str]:
    errors: list[str] = []

    if stats.malformed_extra_rows:
        errors.append(
            "ERROR: malformed rows detected with extra CSV columns "
            f"at lines: {_format_lines(stats.malformed_extra_rows)}"
        )

    if stats.malformed_missing_rows:
        errors.append(
            "ERROR: malformed rows detected with missing CSV columns "
            f"at lines: {_format_lines(stats.malformed_missing_rows)}"
        )

    if fail_on_duplicate_slug and stats.duplicate_slug_rows:
        errors.append(
            "ERROR: duplicate post_name values detected "
            f"at lines: {_format_lines(stats.duplicate_slug_rows)}"
        )

    if fail_on_empty_primary_url and stats.empty_primary_rows:
        errors.append(
            "ERROR: empty featured_image_primary_url values detected "
            f"at lines: {_format_lines(stats.empty_primary_rows)}"
        )

    if fail_on_empty_required and stats.empty_required_details:
        details = ", ".join(f"{line}:{column}" for line, column in stats.empty_required_details)
        errors.append(f"ERROR: empty values in required columns at {details}")

    return errors


def _result_payload(result: ValidationResult) -> dict[str, object]:
    return {
        "exit_code": result.exit_code,
        "stats": asdict(result.stats),
        "errors": result.errors,
    }


def _print_summary(stats: ValidationStats) -> None:
    print(f"Rows checked: {stats.rows_checked}")
    print(f"Duplicate post_name: {stats.duplicate_slugs}")
    print(f"Empty featured_image_primary_url: {stats.empty_primary_url}")
    print(f"Malformed rows (extra columns): {stats.malformed_extra_columns}")
    print(f"Malformed rows (missing columns): {stats.malformed_missing_columns}")
    print(f"Empty required cells: {stats.empty_required_cells}")


def _print_json(result: ValidationResult) -> None:
    print(json.dumps(_result_payload(result), ensure_ascii=False, indent=2))


def _write_json_report(path: Path, result: ValidationResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_result_payload(result), ensure_ascii=False, indent=2), encoding="utf-8")


def validate_csv(
    path: Path,
    *,
    fail_on_duplicate_slug: bool = False,
    fail_on_empty_primary_url: bool = False,
    fail_on_empty_required: bool = False,
) -> ValidationResult:
    if not path.exists():
        return ValidationResult(
            exit_code=EXIT_NOT_FOUND,
            errors=[f"ERROR: file not found: {path}"],
        )

    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            errors = ["ERROR: missing required columns:"] + [f"  - {col}" for col in missing]
            return ValidationResult(exit_code=EXIT_VALIDATION_ERROR, errors=errors)

        stats = ValidationStats()
        seen_slugs: set[str] = set()

        for row_idx, row in enumerate(reader, start=2):
            stats.rows_checked += 1

            overflow = row.get(None) or []
            if overflow:
                stats.malformed_extra_columns += 1
                stats.malformed_extra_rows.append(row_idx)

            if any(value is None for key, value in row.items() if key is not None):
                stats.malformed_missing_columns += 1
                stats.malformed_missing_rows.append(row_idx)

            for col in REQUIRED_COLUMNS:
                if not (row.get(col) or "").strip():
                    stats.empty_required_cells += 1
                    stats.empty_required_details.append((row_idx, col))

            slug = (row.get("post_name") or "").strip()
            if slug in seen_slugs and slug:
                stats.duplicate_slugs += 1
                stats.duplicate_slug_rows.append(row_idx)
            seen_slugs.add(slug)

            if not (row.get("featured_image_primary_url") or "").strip():
                stats.empty_primary_url += 1
                stats.empty_primary_rows.append(row_idx)

        errors = _build_error_messages(
            stats,
            fail_on_duplicate_slug=fail_on_duplicate_slug,
            fail_on_empty_primary_url=fail_on_empty_primary_url,
            fail_on_empty_required=fail_on_empty_required,
        )

        exit_code = EXIT_VALIDATION_ERROR if errors else EXIT_OK
        return ValidationResult(exit_code=exit_code, stats=stats, errors=errors)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate WP portfolio CSV")
    parser.add_argument("csv_path", type=Path, help="Path to CSV file")
    parser.add_argument(
        "--fail-on-duplicate-slug",
        action="store_true",
        help="Return non-zero if duplicate post_name values are found",
    )
    parser.add_argument(
        "--fail-on-empty-primary-url",
        action="store_true",
        help="Return non-zero if featured_image_primary_url is empty in any row",
    )
    parser.add_argument(
        "--fail-on-empty-required",
        action="store_true",
        help="Return non-zero if any required cell is empty",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output",
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        help="Optional path to write JSON validation report",
    )
    args = parser.parse_args()

    result = validate_csv(
        args.csv_path,
        fail_on_duplicate_slug=args.fail_on_duplicate_slug,
        fail_on_empty_primary_url=args.fail_on_empty_primary_url,
        fail_on_empty_required=args.fail_on_empty_required,
    )

    if args.report_path:
        _write_json_report(args.report_path, result)

    if args.json:
        _print_json(result)
    else:
        if result.errors and result.stats.rows_checked == 0 and result.stats.empty_required_cells == 0:
            for error in result.errors:
                print(error)
        else:
            _print_summary(result.stats)
            for error in result.errors:
                print(error)

    return result.exit_code


if __name__ == "__main__":
    sys.exit(main())
