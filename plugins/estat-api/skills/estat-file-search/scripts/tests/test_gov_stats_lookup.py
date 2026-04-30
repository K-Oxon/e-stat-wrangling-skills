from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

import gov_stats_lookup  # noqa: E402


def test_filter_records_by_keyword_and_file_marker() -> None:
    records = [
        {
            "gov_stats_code": "00450041",
            "gov_stats_name": "社会福祉施設等調査",
            "organization": "厚生労働省",
            "department": "",
            "stats_type": "一般統計",
            "has_file": "〇",
            "has_db": "-",
        },
        {
            "gov_stats_code": "99999999",
            "gov_stats_name": "別調査",
            "organization": "テスト省",
            "department": "",
            "stats_type": "一般統計",
            "has_file": "-",
            "has_db": "○",
        },
    ]

    result = gov_stats_lookup.filter_records(
        records,
        keywords=["福祉"],
        organization=None,
        has_file=True,
        has_db=False,
    )

    assert [record["gov_stats_code"] for record in result] == ["00450041"]


def test_truthy_marker_accepts_both_circle_variants() -> None:
    assert gov_stats_lookup.truthy_marker("〇")
    assert gov_stats_lookup.truthy_marker("○")
    assert not gov_stats_lookup.truthy_marker("-")
