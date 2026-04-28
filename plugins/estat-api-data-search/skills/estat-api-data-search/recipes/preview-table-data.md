# Preview Table Data

`getStatsData` preview is deferred. Use this only after a `statsDataId` candidate is confirmed and
the data retrieval/normalization workflow has been scoped.

```bash
curl -sG "https://api.e-stat.go.jp/rest/3.0/app/json/getStatsData" \
  --data-urlencode "appId=$ESTAT_APP_ID" \
  --data-urlencode "statsDataId=REPLACE_ME" \
  --data-urlencode "limit=10" \
  -o /tmp/estat-stats-data-preview.json
```

This stays a preview-oriented recipe until the downstream normalization workflow is specified.
