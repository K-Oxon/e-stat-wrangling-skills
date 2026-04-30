# estat-api

Claude Code plugin for searching e-Stat downloadable files and API/DB statistical tables.

This plugin contains two skills:

| Skill | Purpose |
| --- | --- |
| [`estat-file-search`](skills/estat-file-search/SKILL.md) | Search `getDataCatalog` for downloadable XLS, CSV, PDF, and browsing Excel resources, then download selected file URLs. |
| [`estat-api-data-search`](skills/estat-api-data-search/SKILL.md) | Search `getStatsList` for API/DB-provided statistical tables and identify `statsDataId` candidates. |

## Environment

Live e-Stat API calls require an application ID.

Get one here:

<https://www.e-stat.go.jp/mypage/user/preregister>

Set it for the session:

```bash
export ESTAT_APP_ID="..."
```

For one-off commands, pass `--app-id "..."` instead. Fixture parsing with `--from-fixture` does not require an app ID.

## Install

```text
/plugin marketplace add K-Oxon/e-stat-wrangling-skills
/plugin install estat-api@e-stat-wrangling
```

## File Search Workflow

Use this path when the target is a downloadable spreadsheet, CSV, PDF, or browsing Excel file.

```bash
uv run --script plugins/estat-api/skills/estat-file-search/scripts/gov_stats_lookup.py \
  --keyword 保育 --has-file

uv run --script plugins/estat-api/skills/estat-file-search/scripts/search.py \
  --stats-code 00450041 \
  --keyword 保育士 \
  --candidates-output out/file-candidates.csv

uv run --script plugins/estat-api/skills/estat-file-search/scripts/download.py \
  --url "https://www.e-stat.go.jp/stat-search/file-download?statInfId=...&fileKind=0" \
  --resource-id 000000000000 \
  --format XLS \
  --dest data/
```

Notes:

- `search.py` uses `getDataCatalog`.
- Search defaults to `dataType=XLS,CSV,PDF,XLS_REP`; use `--data-type ALL` to omit that filter.
- Raw JSON and flattened candidates are both saved.
- Candidate output preserves e-Stat response order. Ranking is intentionally out of v1.

## API/DB Table Search Workflow

Use this path when the target is API/DB data or a `statsDataId`.

```bash
uv run --script plugins/estat-api/skills/estat-api-data-search/scripts/gov_stats_lookup.py \
  --keyword 社会 --has-db

uv run --script plugins/estat-api/skills/estat-api-data-search/scripts/list.py \
  --stats-code 00200502 \
  --keyword 人口 \
  --candidates-output out/table-candidates.csv
```

Notes:

- `list.py` uses `getStatsList`.
- Raw JSON and flattened candidates are both saved.
- Candidate output preserves e-Stat response order. Ranking is intentionally out of v1.
- Metadata inspection with `getMetaInfo` and full data fetching with `getStatsData` are follow-up workflows, not part of the first implementation.

## Scope

Included in v1:

- Government statistics code lookup.
- Keyword hint generation.
- File-oriented `getDataCatalog` discovery.
- API/DB-oriented `getStatsList` discovery.
- Raw response preservation.
- Candidate CSV/JSONL/Markdown output.
- Selected file URL download helper.
- Offline fixture tests.

Deferred:

- Full `getMetaInfo` workflow.
- Full `getStatsData` fetch and normalization workflow.
- Shared `packages/estat-client/` package.
- Ranking or scoring candidates beyond e-Stat response order.
