#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
"""Generate small searchWord hint sets for e-Stat API/DB table search."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass


ADMIN_SYNONYMS = {
    "保育士": ["保育士", "保育所", "保育施設", "児童福祉施設", "社会福祉施設"],
    "保育施設": ["保育施設", "保育所", "認定こども園", "児童福祉施設"],
    "水道": ["水道", "水道事業", "地方公営企業", "上水道"],
    "人口": ["人口", "世帯", "国勢調査", "推計人口"],
}


@dataclass(frozen=True)
class KeywordHint:
    search_word: str
    reason: str


def unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def generate_keyword_hints(
    user_terms: list[str],
    *,
    survey_name: str | None = None,
    max_hints: int = 12,
) -> list[KeywordHint]:
    hints: list[KeywordHint] = []
    base_terms = unique(user_terms + ([survey_name] if survey_name else []))

    for term in base_terms:
        hints.append(KeywordHint(term, "input term"))
        for synonym in ADMIN_SYNONYMS.get(term, []):
            hints.append(KeywordHint(synonym, f"administrative synonym for {term}"))

    if survey_name:
        for term in user_terms:
            hints.append(KeywordHint(f"{survey_name} AND {term}", "survey-anchored AND search"))

    deduped: list[KeywordHint] = []
    seen: set[str] = set()
    for hint in hints:
        if hint.search_word in seen:
            continue
        seen.add(hint.search_word)
        deduped.append(hint)
    return deduped[:max_hints]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("terms", nargs="+", help="User-facing or administrative terms.")
    parser.add_argument("--survey-name", help="Known or suspected survey name.")
    parser.add_argument("--max-hints", type=int, default=12)
    parser.add_argument("--format", choices=["jsonl", "md"], default="md")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    hints = generate_keyword_hints(args.terms, survey_name=args.survey_name, max_hints=args.max_hints)
    if args.format == "jsonl":
        for hint in hints:
            print(json.dumps(hint.__dict__, ensure_ascii=False))
    else:
        print("| searchWord | reason |")
        print("| --- | --- |")
        for hint in hints:
            search_word = hint.search_word.replace("|", "\\|")
            reason = hint.reason.replace("|", "\\|")
            print(f"| {search_word} | {reason} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
