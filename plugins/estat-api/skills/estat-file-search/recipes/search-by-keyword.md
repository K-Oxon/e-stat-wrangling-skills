# Search By Keyword

Prefer the script when the skill is installed from this repository:

```bash
uv run --script plugins/estat-api/skills/estat-file-search/scripts/search.py \
  --keyword "人口" \
  --limit 20 \
  --raw-output /tmp/estat-file-search.json \
  --candidates-output /tmp/estat-file-search-candidates.csv
```

The script defaults to `dataType=XLS,CSV,PDF,XLS_REP`. Use `--data-type ALL` when DB-only data or absence checks matter.

Raw curl fallback:

```bash
curl -sG "https://api.e-stat.go.jp/rest/3.0/app/json/getDataCatalog" \
  --data-urlencode "appId=$ESTAT_APP_ID" \
  --data-urlencode "searchWord=人口" \
  --data-urlencode "dataType=XLS,CSV,PDF,XLS_REP" \
  --data-urlencode "limit=20" \
  -o /tmp/estat-file-search.json
```

Then inspect the saved payload:

```bash
jq 'keys' /tmp/estat-file-search.json
jq '.GET_DATA_CATALOG.DATA_CATALOG_LIST_INF.RESULT_INF' /tmp/estat-file-search.json
```
