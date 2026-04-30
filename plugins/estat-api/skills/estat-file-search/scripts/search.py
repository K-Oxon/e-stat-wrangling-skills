#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "httpx>=0.27,<1",
#   "pydantic>=2,<3",
# ]
# ///
"""Search downloadable e-Stat catalog resources with getDataCatalog."""

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
from pydantic import BaseModel, ConfigDict


ENDPOINT = "https://api.e-stat.go.jp/rest/3.0/app/json/getDataCatalog"
DEFAULT_DATA_TYPE = "XLS,CSV,PDF,XLS_REP"
DEFAULT_OUTPUT_DIR = Path("estat-file-search-output")
ESTAT_APP_ID_REGISTRATION_URL = "https://www.e-stat.go.jp/mypage/user/preregister"


class EstatApiError(RuntimeError):
    """Raised when e-Stat returns an API-level error status."""


class ResultStatus(BaseModel):
    model_config = ConfigDict(coerce_numbers_to_str=True)

    status: int
    error_msg: str = ""
    date: str | None = None


class Candidate(BaseModel):
    stat_code: str | None = None
    stat_name: str | None = None
    organization_code: str | None = None
    organization_name: str | None = None
    dataset_id: str | None = None
    dataset_title: str | None = None
    tabulation_category: str | None = None
    survey_date: str | None = None
    release_date: str | None = None
    last_modified_date: str | None = None
    landing_page: str | None = None
    resource_id: str | None = None
    resource_title: str | None = None
    table_no: str | None = None
    table_name: str | None = None
    format: str | None = None
    url: str | None = None
    resource_release_date: str | None = None
    resource_last_modified_date: str | None = None
    language: str | None = None


CANDIDATE_FIELDS = list(Candidate.model_fields.keys())


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
    value = payload.get("GET_DATA_CATALOG")
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


def list_info(payload: dict[str, Any]) -> dict[str, Any]:
    value = get_path(root(payload), ["DATA_CATALOG_LIST_INF"], {})
    return value if isinstance(value, dict) else {}


def get_next_key(payload: dict[str, Any]) -> str | None:
    value = get_path(list_info(payload), ["RESULT_INF", "NEXT_KEY"])
    return text_value(value)


def iter_catalogs(payload: dict[str, Any]) -> Iterable[dict[str, Any]]:
    catalogs = list_info(payload).get("DATA_CATALOG_INF")
    for catalog in ensure_list(catalogs):
        if isinstance(catalog, dict):
            yield catalog


def iter_resources(catalog: dict[str, Any]) -> Iterable[dict[str, Any]]:
    resources = get_path(catalog, ["RESOURCES", "RESOURCE"])
    for resource in ensure_list(resources):
        if isinstance(resource, dict):
            yield resource


def flatten_candidate(catalog: dict[str, Any], resource: dict[str, Any]) -> Candidate:
    dataset = catalog.get("DATASET") if isinstance(catalog.get("DATASET"), dict) else {}
    title = dataset.get("TITLE") if isinstance(dataset.get("TITLE"), dict) else {}
    stat_name = dataset.get("STAT_NAME") if isinstance(dataset.get("STAT_NAME"), dict) else {}
    organization = dataset.get("ORGANIZATION") if isinstance(dataset.get("ORGANIZATION"), dict) else {}
    resource_title = resource.get("TITLE") if isinstance(resource.get("TITLE"), dict) else {}

    return Candidate(
        stat_code=text_value(stat_name.get("@code")),
        stat_name=text_value(stat_name.get("$")),
        organization_code=text_value(organization.get("@code")),
        organization_name=text_value(organization.get("$")),
        dataset_id=text_value(catalog.get("@id")),
        dataset_title=text_value(title.get("NAME")),
        tabulation_category=text_value(title.get("TABULATION_CATEGORY")),
        survey_date=text_value(title.get("SURVEY_DATE")),
        release_date=text_value(dataset.get("RELEASE_DATE")),
        last_modified_date=text_value(dataset.get("LAST_MODIFIED_DATE")),
        landing_page=text_value(dataset.get("LANDING_PAGE")),
        resource_id=text_value(resource.get("@id")),
        resource_title=text_value(resource_title.get("NAME")),
        table_no=text_value(resource_title.get("TABLE_NO")),
        table_name=text_value(resource_title.get("TABLE_NAME")),
        format=text_value(resource.get("FORMAT")),
        url=text_value(resource.get("URL")),
        resource_release_date=text_value(resource.get("RELEASE_DATE")),
        resource_last_modified_date=text_value(resource.get("LAST_MODIFIED_DATE")),
        language=text_value(resource.get("LANGUAGE")),
    )


def parse_candidates(payloads: Iterable[dict[str, Any]]) -> list[Candidate]:
    candidates: list[Candidate] = []
    for payload in payloads:
        status = assert_api_success(payload)
        if status.status == 1:
            continue
        for catalog in iter_catalogs(payload):
            for resource in iter_resources(catalog):
                candidates.append(flatten_candidate(catalog, resource))
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
    if args.data_type.upper() != "ALL":
        params["dataType"] = args.data_type
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
        "  search.py --app-id '<your app id>' ...\n"
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
            params = build_params(args, app_id, start_position)
            response = client.get(ENDPOINT, params=params)
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
    return output_dir / f"estat-file-search-{timestamp}-{suffix}.{extension}"


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def write_candidates(path: Path, candidates: list[Candidate], output_format: str) -> None:
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
    parser.add_argument("--keyword", help="searchWord for getDataCatalog.")
    parser.add_argument("--stats-code", help="5-digit organization code or 8-digit government statistics code.")
    parser.add_argument("--data-type", default=DEFAULT_DATA_TYPE, help="Comma-separated dataType values, or ALL to omit.")
    parser.add_argument("--limit", type=int, default=100, help="Catalog datasets per page.")
    parser.add_argument("--max-pages", type=int, default=10, help="Maximum pages unless --all is set.")
    parser.add_argument("--all", action="store_true", help="Follow NEXT_KEY until exhausted.")
    parser.add_argument("--app-id", help="Override ESTAT_APP_ID.")
    parser.add_argument("--lang", default="J", choices=["J", "E"])
    parser.add_argument("--survey-years", help="Advanced filter. Prefer not using this for broad discovery.")
    parser.add_argument("--open-years", help="Advanced filter. Prefer not using this for broad discovery.")
    parser.add_argument("--updated-date", help="Advanced filter. Prefer not using this for broad discovery.")
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--sleep-seconds", type=float, default=0.2)
    parser.add_argument("--from-fixture", type=Path, help="Parse a saved getDataCatalog JSON instead of calling e-Stat.")
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

    candidates = parse_candidates(payloads)
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
