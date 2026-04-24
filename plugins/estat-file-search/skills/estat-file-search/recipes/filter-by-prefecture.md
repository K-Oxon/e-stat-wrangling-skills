# Filter By Prefecture

Start from the keyword recipe, then add the region-related query parameter once the concrete search
shape is fixed.

```bash
curl -sG "https://api.e-stat.go.jp/rest/3.0/app/json/getDataCatalog" \
  --data-urlencode "appId=$ESTAT_APP_ID" \
  --data-urlencode "searchWord=人口" \
  --data-urlencode "limit=20" \
  -o /tmp/estat-file-search-prefecture.json
```

This file is intentionally a placeholder for the later, more detailed parameter design.
