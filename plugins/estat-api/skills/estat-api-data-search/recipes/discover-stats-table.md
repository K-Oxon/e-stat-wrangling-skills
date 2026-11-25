# Discover Stats Table

In the examples below, set `SKILL_DIR` to the absolute path of this installed skill folder.

```bash
uv run --script "$SKILL_DIR/scripts/list.py" \
  --stats-code 00200502 \
  --keyword "人口" \
  --limit 20 \
  --raw-output /tmp/estat-stats-list.json \
  --candidates-output /tmp/estat-stats-list-candidates.csv
```

Raw curl fallback:

```bash
curl -sG "https://api.e-stat.go.jp/rest/3.0/app/json/getStatsList" \
  --data-urlencode "appId=$ESTAT_APP_ID" \
  --data-urlencode "searchWord=人口" \
  --data-urlencode "limit=20" \
  -o /tmp/estat-stats-list.json
```

Then inspect the structure:

```bash
jq 'keys' /tmp/estat-stats-list.json
jq '.GET_STATS_LIST.DATALIST_INF.RESULT_INF' /tmp/estat-stats-list.json
```
