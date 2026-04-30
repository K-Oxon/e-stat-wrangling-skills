from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

import search  # noqa: E402


FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_parse_singleton_catalog_and_resource() -> None:
    payload = load_fixture("get_data_catalog_single_resource.json")

    candidates = search.parse_candidates([payload])

    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.stat_code == "00450041"
    assert candidate.stat_name == "社会福祉施設等調査"
    assert candidate.dataset_id == "000001255613"
    assert candidate.resource_id == "000008508466"
    assert candidate.format == "XLS"
    assert candidate.table_name == "保育所"
    assert candidate.url.endswith("fileKind=0")


def test_parse_list_catalog_and_resource() -> None:
    payload = load_fixture("get_data_catalog_list_resource.json")

    candidates = search.parse_candidates([payload])

    assert len(candidates) == 2
    assert [candidate.resource_id for candidate in candidates] == ["resource-1", "resource-2"]
    assert [candidate.format for candidate in candidates] == ["CSV", "PDF"]
    assert search.get_next_key(payload) == "3"


def test_status_one_is_empty_not_error() -> None:
    payload = {
        "GET_DATA_CATALOG": {
            "RESULT": {
                "STATUS": 1,
                "ERROR_MSG": "正常に終了しましたが、該当データはありませんでした。"
            }
        }
    }

    assert search.parse_candidates([payload]) == []


def test_api_error_raises() -> None:
    payload = {
        "GET_DATA_CATALOG": {
            "RESULT": {
                "STATUS": 100,
                "ERROR_MSG": "認証に失敗しました。"
            }
        }
    }

    with pytest.raises(search.EstatApiError):
        search.parse_candidates([payload])


def test_default_data_type_is_file_oriented() -> None:
    assert search.DEFAULT_DATA_TYPE == "XLS,CSV,PDF,XLS_REP"


def test_missing_app_id_message_points_to_registration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ESTAT_APP_ID", raising=False)

    with pytest.raises(SystemExit) as exc_info:
        search.resolve_app_id(search.parse_args(["--keyword", "人口"]))

    message = str(exc_info.value)
    assert "ESTAT_APP_ID is required" in message
    assert search.ESTAT_APP_ID_REGISTRATION_URL in message
    assert "--app-id" in message
