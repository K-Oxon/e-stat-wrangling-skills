# estat-api-data-search

Search e-Stat for API/DB-provided statistical tables and identify `statsDataId` candidates.

## Environment

Set your e-Stat application ID:

```bash
export ESTAT_APP_ID="..."
```

## Typical workflow

```bash
uv run --script plugins/estat-api-data-search/skills/estat-api-data-search/scripts/gov_stats_lookup.py \
  --keyword 社会 --has-db

uv run --script plugins/estat-api-data-search/skills/estat-api-data-search/scripts/list.py \
  --stats-code 00200502 \
  --keyword 人口 \
  --candidates-output out/tables.csv
```

## Notes

- Use this plugin when the target is API/DB data or a `statsDataId`.
- Use `estat-file-search` when the target is a downloadable XLS, CSV, or PDF URL.
- `searchKind` is normally omitted.
- Candidate output preserves e-Stat response order; ranking is intentionally out of MVP.
- Metadata inspection with `getMetaInfo` is a follow-up workflow, not part of the first implementation.
