#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
"""Look up e-Stat government statistics codes from the bundled CSV."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Iterable


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CSV = SCRIPT_DIR.parent / "reference" / "gov_stats_codes.csv"
DEFAULT_FIELDS = [
    "gov_stats_code",
    "gov_stats_name",
    "organization",
    "department",
    "has_file",
    "has_db",
    "org_info_link",
]


def normalize_text(value: str | None) -> str:
    return (value or "").casefold().strip()


def truthy_marker(value: str | None) -> bool:
    normalized = normalize_text(value)
    return normalized in {"〇", "○", "o", "yes", "true", "1"}


def read_records(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def matches_keywords(record: dict[str, str], keywords: list[str]) -> bool:
    if not keywords:
        return True
    haystack = normalize_text(
        " ".join(
            [
                record.get("gov_stats_code", ""),
                record.get("gov_stats_name", ""),
                record.get("organization", ""),
                record.get("department", ""),
                record.get("stats_type", ""),
            ]
        )
    )
    return all(normalize_text(keyword) in haystack for keyword in keywords)


def filter_records(
    records: Iterable[dict[str, str]],
    *,
    keywords: list[str],
    organization: str | None,
    has_file: bool,
    has_db: bool,
) -> list[dict[str, str]]:
    organization_key = normalize_text(organization)
    result: list[dict[str, str]] = []
    for record in records:
        if not matches_keywords(record, keywords):
            continue
        if organization_key and organization_key not in normalize_text(record.get("organization")):
            continue
        if has_file and not truthy_marker(record.get("has_file")):
            continue
        if has_db and not truthy_marker(record.get("has_db")):
            continue
        result.append(record)
    return result


def project_record(record: dict[str, str], fields: list[str]) -> dict[str, str]:
    return {field: record.get(field, "") for field in fields}


def write_jsonl(records: list[dict[str, str]]) -> None:
    for record in records:
        print(json.dumps(record, ensure_ascii=False))


def write_csv(records: list[dict[str, str]], fields: list[str]) -> None:
    import sys

    # Keep stdout wiring local so filtering stays testable without monkeypatching stdout.
    writer = csv.DictWriter(sys.stdout, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(records)


def write_markdown(records: list[dict[str, str]], fields: list[str]) -> None:
    print("| " + " | ".join(fields) + " |")
    print("| " + " | ".join(["---"] * len(fields)) + " |")
    for record in records:
        print("| " + " | ".join((record.get(field, "") or "").replace("|", "\\|") for field in fields) + " |")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="Path to gov_stats_codes.csv")
    parser.add_argument("--keyword", action="append", default=[], help="Keyword. Repeat for AND search.")
    parser.add_argument("--organization", help="Filter by organization name.")
    parser.add_argument("--has-file", action="store_true", help="Only rows with file-provided data.")
    parser.add_argument("--has-db", action="store_true", help="Only rows with DB-provided data.")
    parser.add_argument("--limit", type=int, default=20, help="Maximum rows to print. Use 0 for all.")
    parser.add_argument("--format", choices=["jsonl", "csv", "md"], default="md", help="Output format.")
    parser.add_argument(
        "--fields",
        default=",".join(DEFAULT_FIELDS),
        help="Comma-separated output fields.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    fields = [field.strip() for field in args.fields.split(",") if field.strip()]
    records = filter_records(
        read_records(args.csv),
        keywords=args.keyword,
        organization=args.organization,
        has_file=args.has_file,
        has_db=args.has_db,
    )
    if args.limit > 0:
        records = records[: args.limit]
    projected = [project_record(record, fields) for record in records]

    if args.format == "jsonl":
        write_jsonl(projected)
    elif args.format == "csv":
        write_csv(projected, fields)
    else:
        write_markdown(projected, fields)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
