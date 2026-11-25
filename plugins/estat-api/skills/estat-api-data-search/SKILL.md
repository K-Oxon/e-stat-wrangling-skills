---
name: estat-api-data-search
description: Discover e-Stat API/DB statistical tables and identify statsDataId (統計表ID・e-Stat APIで使えるデータの検索). Use when locating tables for API retrieval.
compatibility: Requires uv and Python 3.11+. Live search needs network access and ESTAT_APP_ID.
---

# e-Stat API Data Search

1. Identify the survey. If its government statistics code is unknown, run [gov_stats_lookup.py](scripts/gov_stats_lookup.py). Use survey names, administrative terms, and likely table-title keywords.
2. Search `getStatsList` with [list.py](scripts/list.py). Save raw responses before narrowing. Present flattened candidates in e-Stat order, with enough survey and table context to distinguish duplicate IDs. See [the endpoint reference](reference.md) for request parameters, pagination, and response paths.
3. Report the candidate `statsDataId` values. If the task asks for downloadable files, use `estat-file-search`.

Run scripts with `uv run --script` and paths relative to this skill's folder. Set `ESTAT_APP_ID` for live search ([registration](https://www.e-stat.go.jp/mypage/user/preregister)). For a saved response, `--from-fixture` works without an app ID.

- [Discover a statistical table](recipes/discover-stats-table.md)
- [Inspect metadata after confirming an ID](recipes/get-meta-info.md)
- [Preview data for a confirmed ID](recipes/preview-table-data.md)
