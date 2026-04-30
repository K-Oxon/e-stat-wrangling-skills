---
name: estat-file-search
description: Use this when the user wants to search e-Stat for downloadable files such as xlsx, csv, or pdf and is still working at the search-and-download stage rather than the downstream parsing stage.
---

# e-Stat File Search

Use this skill to locate downloadable e-Stat files.

## Workflow

1. Read [reference.md](reference.md) to confirm endpoint behavior and response paths.
2. Decide whether the user needs file-provided data or API/DB-provided data. If the request is API/DB-oriented, hand off to `estat-api-data-search`.
3. If the government statistics code is unknown, search the bundled government statistics code list with `scripts/gov_stats_lookup.py`.
4. Generate a small set of plausible `searchWord` values before calling the API. Prefer survey names, administrative terms,制度名, and likely table-title nouns over casual wording.
5. Search `getDataCatalog` with `scripts/search.py`, using `statsCode` and `searchWord` as the main levers.
6. Save the raw JSON response before narrowing or summarizing.
7. Inspect the flattened candidates in e-Stat response order. Do not apply opaque scoring in the MVP.
8. Download the selected file URL with `scripts/download.py` only after the candidate row has been validated or the user explicitly asks for the likely file.

## Required environment

- `ESTAT_APP_ID`
  - Get one from <https://www.e-stat.go.jp/mypage/user/preregister>
  - Set it with `export ESTAT_APP_ID="<your app id>"`, or pass `--app-id` for a one-off command.
  - If you only need to parse a saved response, use `--from-fixture`; no app ID is needed.

## Scope

- Search
- Filter
- Download

## Operating rules

- Treat e-Stat as a three-layer search space: government statistics code, dataset, then resource/statistical table/file format.
- Use government statistics code discovery and keyword search iteratively.
- Default file search uses `dataType=XLS,CSV,PDF,XLS_REP`, but `dataType` is only a hint. Always verify `RESOURCES.RESOURCE.FORMAT`.
- Use `--data-type ALL` when absence matters or DB-only data may be relevant.
- If `FORMAT=DB` dominates or the target appears API-only, switch to `estat-api-data-search`.
- Date fields such as `LAST_MODIFIED_DATE` are display metadata, not authoritative filters.
- Prefer raw JSON plus CSV/JSONL candidate output over one-off `jq` pipelines for heavy responses.
