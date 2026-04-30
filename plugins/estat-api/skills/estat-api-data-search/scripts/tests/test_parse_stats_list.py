from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

import list as stats_list  # noqa: E402


FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_parse_singleton_table_inf() -> None:
    payload = load_fixture("get_stats_list_single_table.json")

    candidates = stats_list.parse_table_candidates([payload])

    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.stats_data_id == "0000010101"
    assert candidate.stat_code == "00200502"
    assert candidate.stat_name == "社会・人口統計体系"
    assert candidate.gov_org_name == "総務省"
    assert candidate.statistics_name == "都道府県データ 基礎データ"
    assert candidate.title == "Ａ　人口・世帯"
    assert candidate.table_name == "Ａ　人口・世帯"
    assert candidate.collect_area == "都道府県"
    assert candidate.overall_total_number == "550080"
    assert candidate.tabulation_category == "都道府県データ"
    assert "都道府県ごと" in (candidate.description or "")


def test_parse_list_table_inf_and_next_key() -> None:
    payload = load_fixture("get_stats_list_list_table.json")

    candidates = stats_list.parse_table_candidates([payload])

    assert len(candidates) == 2
    assert [candidate.stats_data_id for candidate in candidates] == ["0000010101", "0000010102"]
    assert [candidate.title for candidate in candidates] == ["Ａ　人口・世帯", "Ｂ　自然環境"]
    assert stats_list.get_next_key(payload) == "3"


def test_status_one_is_empty_not_error() -> None:
    payload = {
        "GET_STATS_LIST": {
            "RESULT": {
                "STATUS": 1,
                "ERROR_MSG": "正常に終了しましたが、該当データはありませんでした。"
            }
        }
    }

    assert stats_list.parse_table_candidates([payload]) == []


def test_api_error_raises() -> None:
    payload = {
        "GET_STATS_LIST": {
            "RESULT": {
                "STATUS": 100,
                "ERROR_MSG": "認証に失敗しました。"
            }
        }
    }

    with pytest.raises(stats_list.EstatApiError):
        stats_list.parse_table_candidates([payload])


def test_missing_app_id_message_points_to_registration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ESTAT_APP_ID", raising=False)

    with pytest.raises(SystemExit) as exc_info:
        stats_list.resolve_app_id(stats_list.parse_args(["--keyword", "人口"]))

    message = str(exc_info.value)
    assert "ESTAT_APP_ID is required" in message
    assert stats_list.ESTAT_APP_ID_REGISTRATION_URL in message
    assert "--app-id" in message
