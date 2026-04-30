#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "httpx>=0.27,<1",
#   "pydantic>=2,<3",
# ]
# ///
"""Search e-Stat API/DB statistical table candidates with getStatsList."""

from __future__ import annotations

import argparse
import csv
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import httpx
from pydantic import BaseModel


ENDPOINT = "https://api.e-stat.go.jp/rest/3.0/app/json/getStatsList"
DEFAULT_OUTPUT_DIR = Path("estat-api-data-search-output")
ESTAT_APP_ID_REGISTRATION_URL = "https://www.e-stat.go.jp/mypage/user/preregister"


class EstatApiError(RuntimeError):
    """Raised when e-Stat returns an API-level error status."""


class ResultStatus(BaseModel):
    status: int
    error_msg: str = ""
    date: str | None = None


class TableCandidate(BaseModel):
    stats_data_id: str | None = None
    stat_code: str | None = None
    stat_name: str | None = None
    gov_org_code: str | None = None
    gov_org_name: str | None = None
    statistics_name: str | None = None
    title_no: str | None = None
    title: str | None = None
    table_name: str | None = None
    cycle: str | None = None
    survey_date: str | None = None
    open_date: str | None = None
    updated_date: str | None = None
    small_area: str | None = None
    collect_area: str | None = None
    main_category_code: str | None = None
    main_category_name: str | None = None
    sub_category_code: str | None = None
    sub_category_name: str | None = None
    overall_total_number: str | None = None
    tabulation_category: str | None = None
    tabulation_sub_category1: str | None = None
    description: str | None = None


CANDIDATE_FIELDS = list(TableCandidate.model_fields.keys())


def ensure_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def text_value(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, dict):
        if "$" in value:
            return text_value(value.get("$"))
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    if isinstance(value, (list, tuple)):
        return " / ".join(part for part in (text_value(item) for item in value) if part)
    return str(value)


def get_path(obj: dict[str, Any], path: Iterable[str], default: Any = None) -> Any:
    current: Any = obj
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def root(payload: dict[str, Any]) -> dict[str, Any]:
    value = payload.get("GET_STATS_LIST")
    return value if isinstance(value, dict) else {}


def parse_result_status(payload: dict[str, Any]) -> ResultStatus:
    result = get_path(root(payload), ["RESULT"], {})
    if not isinstance(result, dict):
        result = {}
    return ResultStatus(
        status=int(result.get("STATUS", 299)),
        error_msg=text_value(result.get("ERROR_MSG")) or "",
        date=text_value(result.get("DATE")),
    )


def assert_api_success(payload: dict[str, Any]) -> ResultStatus:
    status = parse_result_status(payload)
    if status.status >= 100:
        raise EstatApiError(f"e-Stat API error {status.status}: {status.error_msg}")
    return status


def data_list_info(payload: dict[str, Any]) -> dict[str, Any]:
    value = get_path(root(payload), ["DATALIST_INF"], {})
    return value if isinstance(value, dict) else {}


def get_next_key(payload: dict[str, Any]) -> str | None:
    return text_value(get_path(data_list_info(payload), ["RESULT_INF", "NEXT_KEY"]))


def iter_tables(payload: dict[str, Any]) -> Iterable[dict[str, Any]]:
    tables = data_list_info(payload).get("TABLE_INF")
    for table in ensure_list(tables):
        if isinstance(table, dict):
            yield table


def code_name_code(value: Any) -> str | None:
    return text_value(value.get("@code")) if isinstance(value, dict) else None


def code_name_text(value: Any) -> str | None:
    return text_value(value.get("$")) if isinstance(value, dict) else text_value(value)


def description_text(value: Any) -> str | None:
    if value is None or value == "":
        return None
    if isinstance(value, dict):
        parts = [text_value(item) for item in value.values()]
        return " / ".join(part for part in parts if part) or None
    return text_value(value)


def flatten_table(table: dict[str, Any]) -> TableCandidate:
    stat_name = table.get("STAT_NAME")
    gov_org = table.get("GOV_ORG")
    title = table.get("TITLE")
    main_category = table.get("MAIN_CATEGORY")
    sub_category = table.get("SUB_CATEGORY")
    statistics_name_spec = table.get("STATISTICS_NAME_SPEC")
    title_spec = table.get("TITLE_SPEC")

    return TableCandidate(
        stats_data_id=text_value(table.get("@id")),
        stat_code=code_name_code(stat_name),
        stat_name=code_name_text(stat_name),
        gov_org_code=code_name_code(gov_org),
        gov_org_name=code_name_text(gov_org),
        statistics_name=text_value(table.get("STATISTICS_NAME")),
        title_no=text_value(title.get("@no")) if isinstance(title, dict) else None,
        title=code_name_text(title),
        table_name=text_value(get_path(title_spec, ["TABLE_NAME"])) if isinstance(title_spec, dict) else None,
        cycle=text_value(table.get("CYCLE")),
        survey_date=text_value(table.get("SURVEY_DATE")),
        open_date=text_value(table.get("OPEN_DATE")),
        updated_date=text_value(table.get("UPDATED_DATE")),
        small_area=text_value(table.get("SMALL_AREA")),
        collect_area=text_value(table.get("COLLECT_AREA")),
        main_category_code=code_name_code(main_category),
        main_category_name=code_name_text(main_category),
        sub_category_code=code_name_code(sub_category),
        sub_category_name=code_name_text(sub_category),
        overall_total_number=text_value(table.get("OVERALL_TOTAL_NUMBER")),
        tabulation_category=text_value(get_path(statistics_name_spec, ["TABULATION_CATEGORY"])) if isinstance(statistics_name_spec, dict) else None,
        tabulation_sub_category1=text_value(get_path(statistics_name_spec, ["TABULATION_SUB_CATEGORY1"])) if isinstance(statistics_name_spec, dict) else None,
        description=description_text(table.get("DESCRIPTION")),
    )


def parse_table_candidates(payloads: Iterable[dict[str, Any]]) -> list[TableCandidate]:
    candidates: list[TableCandidate] = []
    for payload in payloads:
        status = assert_api_success(payload)
        if status.status == 1:
            continue
        for table in iter_tables(payload):
            candidates.append(flatten_table(table))
    return candidates


def build_params(args: argparse.Namespace, app_id: str, start_position: str | None) -> dict[str, str]:
    params = {
        "appId": app_id,
        "lang": args.lang,
        "limit": str(args.limit),
    }
    if args.keyword:
        params["searchWord"] = args.keyword
    if args.stats_code:
        params["statsCode"] = args.stats_code
    if args.survey_years:
        params["surveyYears"] = args.survey_years
    if args.open_years:
        params["openYears"] = args.open_years
    if args.updated_date:
        params["updatedDate"] = args.updated_date
    if start_position:
        params["startPosition"] = start_position
    return params


def resolve_app_id(args: argparse.Namespace) -> str:
    app_id = args.app_id or os.environ.get("ESTAT_APP_ID")
    if app_id:
        return app_id
    raise SystemExit(
        "ESTAT_APP_ID is required for live e-Stat API calls.\n"
        f"Get an application ID: {ESTAT_APP_ID_REGISTRATION_URL}\n"
        "Then run one of:\n"
        "  export ESTAT_APP_ID='<your app id>'\n"
        "  list.py --app-id '<your app id>' ...\n"
        "Use --from-fixture to parse a saved response without an app ID."
    )


def fetch_payloads(args: argparse.Namespace) -> list[dict[str, Any]]:
    app_id = resolve_app_id(args)

    payloads: list[dict[str, Any]] = []
    start_position: str | None = None
    page = 0
    with httpx.Client(timeout=args.timeout, headers={"Accept": "application/json"}) as client:
        while True:
            page += 1
            response = client.get(ENDPOINT, params=build_params(args, app_id, start_position))
            response.raise_for_status()
            payload = response.json()
            assert_api_success(payload)
            payloads.append(payload)
            next_key = get_next_key(payload)
            if not next_key:
                break
            if not args.all and page >= args.max_pages:
                break
            start_position = next_key
            time.sleep(args.sleep_seconds)
    return payloads


def default_output_path(suffix: str, extension: str, output_dir: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return output_dir / f"estat-api-data-search-{timestamp}-{suffix}.{extension}"


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def write_candidates(path: Path, candidates: list[TableCandidate], output_format: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [candidate.model_dump() for candidate in candidates]
    if output_format == "jsonl":
        with path.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    elif output_format == "csv":
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=CANDIDATE_FIELDS, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
    elif output_format == "md":
        with path.open("w", encoding="utf-8") as handle:
            handle.write("| " + " | ".join(CANDIDATE_FIELDS) + " |\n")
            handle.write("| " + " | ".join(["---"] * len(CANDIDATE_FIELDS)) + " |\n")
            for row in rows:
                values = [(str(row.get(field) or "")).replace("|", "\\|") for field in CANDIDATE_FIELDS]
                handle.write("| " + " | ".join(values) + " |\n")
    else:
        raise ValueError(f"Unsupported output format: {output_format}")


def load_fixture(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keyword", help="searchWord for getStatsList.")
    parser.add_argument("--stats-code", help="5-digit organization code or 8-digit government statistics code.")
    parser.add_argument("--limit", type=int, default=100, help="Table candidates per page.")
    parser.add_argument("--max-pages", type=int, default=10, help="Maximum pages unless --all is set.")
    parser.add_argument("--all", action="store_true", help="Follow NEXT_KEY until exhausted.")
    parser.add_argument("--app-id", help="Override ESTAT_APP_ID.")
    parser.add_argument("--lang", default="J", choices=["J", "E"])
    parser.add_argument("--survey-years", help="Advanced filter. Prefer not using this for broad discovery.")
    parser.add_argument("--open-years", help="Advanced filter. Prefer not using this for broad discovery.")
    parser.add_argument("--updated-date", help="Advanced filter. Prefer not using this for broad discovery.")
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--sleep-seconds", type=float, default=0.2)
    parser.add_argument("--from-fixture", type=Path, help="Parse a saved getStatsList JSON instead of calling e-Stat.")
    parser.add_argument("--raw-output", type=Path, help="Where to write raw payload JSON.")
    parser.add_argument("--candidates-output", type=Path, help="Where to write flattened candidates.")
    parser.add_argument("--format", choices=["jsonl", "csv", "md"], default="csv", help="Candidate output format.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args(argv)


def main() -> int:
    args = parse_args()
    if args.limit < 1:
        raise SystemExit("--limit must be >= 1")
    if args.max_pages < 1:
        raise SystemExit("--max-pages must be >= 1")

    if args.from_fixture:
        payloads = [load_fixture(args.from_fixture)]
    else:
        payloads = fetch_payloads(args)

    candidates = parse_table_candidates(payloads)
    raw_output = args.raw_output or default_output_path("raw", "json", args.output_dir)
    candidates_output = args.candidates_output or default_output_path("candidates", args.format, args.output_dir)

    raw_value: Any = payloads[0] if len(payloads) == 1 else {"pages": payloads}
    write_json(raw_output, raw_value)
    write_candidates(candidates_output, candidates, args.format)

    print(f"raw_output={raw_output}")
    print(f"candidates_output={candidates_output}")
    print(f"candidate_count={len(candidates)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
