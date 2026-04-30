from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

import gov_stats_lookup  # noqa: E402


def test_filter_records_by_keyword_and_db_marker() -> None:
    records = [
        {
            "gov_stats_code": "00200502",
            "gov_stats_name": "社会・人口統計体系",
            "organization": "総務省",
            "department": "",
            "stats_type": "加工統計",
            "has_file": "〇",
            "has_db": "○",
        },
        {
            "gov_stats_code": "99999999",
            "gov_stats_name": "別調査",
            "organization": "テスト省",
            "department": "",
            "stats_type": "一般統計",
            "has_file": "〇",
            "has_db": "-",
        },
    ]

    result = gov_stats_lookup.filter_records(
        records,
        keywords=["人口"],
        organization=None,
        has_file=False,
        has_db=True,
    )

    assert [record["gov_stats_code"] for record in result] == ["00200502"]


def test_truthy_marker_accepts_both_circle_variants() -> None:
    assert gov_stats_lookup.truthy_marker("〇")
    assert gov_stats_lookup.truthy_marker("○")
    assert not gov_stats_lookup.truthy_marker("-")
