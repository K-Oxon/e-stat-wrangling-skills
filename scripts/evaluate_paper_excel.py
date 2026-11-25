# /// script
# requires-python = ">=3.11"
# ///
"""Prepare and score model-independent paper form extraction cases."""

import argparse
import csv
import json
import re
import shutil
import statistics
import sys
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES_DIR = ROOT / "samples/paper-excel-to-table/tk46-010-001/evaluation"
KEY_COLUMNS = ("row_code", "col_code")
METRICS = ("key_f1", "structure_accuracy", "important_notes_recall")
ATTEMPTS = 3
VALID_KEY = re.compile(r"[0-9]{2}/[0-9]{3}")
NUMBER_PREFIX = re.compile(r"^(?:(?:\([0-9]+\)|[0-9]+\.(?![0-9]))|(?:[0-9]+[、．]))+")


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream, strict=True)
        header = next(reader, [])
        if not header or len(set(header)) != len(header) or not all(header):
            raise ValueError(f"{path}: missing or duplicate header columns")
        rows = []
        for row in reader:
            if not row:
                continue
            if len(row) != len(header):
                raise ValueError(f"{path}:{reader.line_num}: row width differs from header")
            rows.append(dict(zip(header, row)))
    return header, rows


def row_key(row: dict[str, str]) -> str:
    return "/".join(row[field].strip() for field in KEY_COLUMNS)


def normalize(value: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", value)).casefold()


def normalize_field(field: str, value: str) -> str:
    text = normalize(value)
    if field in {"section", "row_label"}:
        text = "/".join(
            NUMBER_PREFIX.sub("", part) for part in re.split(r"[/|>→]", text)
        )
    return text


def matches(field: str, expected: str, actual: str, aliases: dict) -> bool:
    alternatives = [expected, *aliases.get(field, {}).get(expected, [])]
    return normalize_field(field, actual) in {
        normalize_field(field, value) for value in alternatives
    }


def score(case: dict, expected_path: Path, output: Path) -> dict:
    expected_header, expected_rows = read_csv(expected_path)
    output_header, predicted_rows = read_csv(output)
    if set(output_header) != set(expected_header):
        missing = sorted(set(expected_header) - set(output_header))
        extra = sorted(set(output_header) - set(expected_header))
        raise ValueError(f"{output}: columns differ; missing={missing}, extra={extra}")

    expected = {row_key(row): row for row in expected_rows}
    if not expected or len(expected) != len(expected_rows) or not all(
        VALID_KEY.fullmatch(key) for key in expected
    ):
        raise ValueError(f"{expected_path}: fixture keys must be present, unique and zero-padded")
    predicted = {row_key(row): row for row in predicted_rows}
    occurrences = Counter(row_key(row) for row in predicted_rows)
    matched = {key for key in predicted.keys() & expected.keys() if occurrences[key] == 1}
    missing = sorted(expected.keys() - predicted.keys())
    extra = sorted(predicted.keys() - expected.keys())
    duplicates = {key: n for key, n in sorted(occurrences.items()) if n > 1}

    fields = case["fields"]
    aliases = case.get("aliases", {})
    misses = []
    correct_by_field = dict.fromkeys(fields, 0)
    for key, wanted in expected.items():
        for field in fields:
            actual = predicted[key][field] if key in matched else None
            if actual is not None and matches(field, wanted[field], actual, aliases):
                correct_by_field[field] += 1
            else:
                kind = "missing_or_duplicate" if actual is None else "unknown" if actual.strip() == "?" else "mismatch"
                misses.append({"key": key, "field": field, "kind": kind, "expected": wanted[field], "actual": actual})

    note_misses = []
    note_total = 0
    for key, required in case["important_notes"].items():
        note_total += len(required)
        observed = normalize(predicted[key]["notes"]) if key in matched else ""
        for alternatives in required:
            if not any(normalize(phrase) in observed for phrase in alternatives):
                note_misses.append({"key": key, "expected_any": alternatives})

    return {
        "status": "scored",
        "key_f1": 2 * len(matched) / (len(expected) + len(predicted_rows)),
        "structure_accuracy": sum(correct_by_field.values()) / (len(expected) * len(fields)),
        "important_notes_recall": (note_total - len(note_misses)) / note_total,
        "keys": {
            "expected": len(expected),
            "predicted": len(predicted_rows),
            "matched": len(matched),
            "missing": missing,
            "extra": extra,
            "duplicates": duplicates,
        },
        "field_accuracy": {
            field: count / len(expected) for field, count in correct_by_field.items()
        },
        "unknown_cells": [
            {"key": row_key(row), "field": field}
            for row in predicted_rows
            for field, value in row.items()
            if value.strip() == "?"
        ],
        "field_misses": misses,
        "missing_important_notes": note_misses,
    }


def compare(case_id: str, baseline: list[dict], candidate: list[dict]) -> dict:
    def medians(attempts: list[dict]) -> dict | None:
        if len(attempts) != ATTEMPTS or any(
            result.get("status") != "scored" or result.get("case") != case_id
            for result in attempts
        ):
            return None
        return {metric: statistics.median(result[metric] for result in attempts) for metric in METRICS}

    reference = medians(baseline)
    alternative = medians(candidate)
    status = "unverified"
    if reference is not None and alternative is not None:
        status = "at_least_baseline" if all(
            alternative[m] >= value for m, value in reference.items()
        ) else "below_baseline"
    return {"case": case_id, "status": status, "baseline": reference, "candidate": alternative}


def prepare(case: dict, work_dir: Path) -> None:
    work_dir.mkdir(parents=True, exist_ok=True)
    if any(work_dir.iterdir()):
        raise ValueError(f"{work_dir}: use an empty directory for each attempt")
    shutil.copyfile(CASES_DIR.parent / case["pdf"], work_dir / "input.pdf")
    shutil.copyfile(CASES_DIR / "layout.yaml", work_dir / "layout.yaml")
    shutil.copyfile(CASES_DIR / case["prompt"], work_dir / "prompt.txt")


def main() -> int:
    config = json.loads((CASES_DIR / "cases.json").read_text(encoding="utf-8"))
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare_args = commands.add_parser("prepare", help="Copy only the public inputs into an empty directory.")
    prepare_args.add_argument("--work-dir", required=True, type=Path)
    score_args = commands.add_parser("score", help="Score a produced CSV against the source-checked fixture.")
    score_args.add_argument("--csv", required=True, type=Path)
    compare_args = commands.add_parser("compare", help="Compare the median scores of three attempts per model.")
    compare_args.add_argument("--baseline", required=True, type=Path, nargs="+")
    compare_args.add_argument("--candidate", required=True, type=Path, nargs="+")
    for command in (prepare_args, score_args, compare_args):
        command.add_argument("--case", required=True, choices=config)
    args = parser.parse_args()
    case = config[args.case]

    try:
        if args.command == "prepare":
            prepare(case, args.work_dir)
            return 0
        if args.command == "score":
            result = score(case, CASES_DIR / case["expected"], args.csv)
            result["case"] = args.case
        else:
            reference, alternative = (
                [json.loads(path.read_text(encoding="utf-8")) for path in paths]
                for paths in (args.baseline, args.candidate)
            )
            result = compare(args.case, reference, alternative)
    except (OSError, csv.Error, UnicodeError, ValueError) as error:
        if args.command == "score":
            print(json.dumps({"case": args.case, "status": "unscorable", "reason": str(error)}, ensure_ascii=False))
        else:
            print(str(error), file=sys.stderr)
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return {"below_baseline": 1, "unverified": 2}.get(result["status"], 0)


if __name__ == "__main__":
    raise SystemExit(main())
