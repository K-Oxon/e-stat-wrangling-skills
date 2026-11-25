---
name: estat-file-search
description: Find and download e-Stat files such as Excel, CSV, or PDF. Use for e-Stat dataset or survey-file discovery (政府統計ファイルの検索・ダウンロード).
compatibility: Requires uv and Python 3.11+. Live search needs network access and ESTAT_APP_ID.
---

# e-Stat File Search

1. Identify the survey. If its government statistics code is unknown, run [gov_stats_lookup.py](scripts/gov_stats_lookup.py) and use survey names, administrative terms, and likely table-title keywords.
2. Search `getDataCatalog` with [search.py](scripts/search.py). Save the raw response before narrowing and inspect flattened candidates in e-Stat order. Use [the endpoint reference](reference.md) for response paths, pagination, and quirks.
3. Verify `RESOURCES.RESOURCE.FORMAT` and the candidate's landing page or URL. The default filter `XLS,CSV,PDF,XLS_REP` is a hint. Use `--data-type ALL` to check for missing or DB-only results. If the task requires an API table ID, use `estat-api-data-search`.
4. Once a candidate is validated or the user asks for the likely file, pass its URL to [download.py](scripts/download.py).

Run scripts with `uv run --script` and paths relative to this skill's folder. Set `ESTAT_APP_ID` for live search ([registration](https://www.e-stat.go.jp/mypage/user/preregister)). For a saved response, `--from-fixture` works without an app ID.

- [Keyword search](recipes/search-by-keyword.md)
- [Prefecture search](recipes/filter-by-prefecture.md)
- [Download a confirmed file](recipes/download-file.md)
