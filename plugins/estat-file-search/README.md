# estat-file-search

Search e-Stat for downloadable XLS, CSV, PDF, and browsing Excel resources.

It provides:

- `SKILL.md` for activation rules
- `reference.md` for endpoint mapping and operating notes
- `scripts/` for government statistics code lookup, catalog search, and downloads
- `recipes/` for reusable curl and script examples

## Environment

Set your e-Stat application ID:

```bash
export ESTAT_APP_ID="..."
```

## Typical workflow

```bash
uv run --script plugins/estat-file-search/skills/estat-file-search/scripts/gov_stats_lookup.py \
  --keyword 保育 --has-file

uv run --script plugins/estat-file-search/skills/estat-file-search/scripts/search.py \
  --stats-code 00450041 \
  --keyword 保育士 \
  --candidates-output out/candidates.csv

uv run --script plugins/estat-file-search/skills/estat-file-search/scripts/download.py \
  --url "https://www.e-stat.go.jp/stat-search/file-download?statInfId=...&fileKind=0" \
  --resource-id 000000000000 \
  --format XLS \
  --dest data/
```

## Notes

- Search defaults to `dataType=XLS,CSV,PDF,XLS_REP`; use `--data-type ALL` to omit that filter.
- Always keep raw JSON when investigating e-Stat behavior.
- Candidate output preserves e-Stat response order; ranking is intentionally out of MVP.
- Government statistics codes are bundled from `scripts/get_gov_stats_codes/gov_stats_codes.csv`. Refresh that source periodically and copy it into the skill reference data.
- Useful local tools for heavy responses: `jq`, `jaq`, `rg`, and `duckdb`.
