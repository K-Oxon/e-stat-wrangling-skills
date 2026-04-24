# Search By Keyword

```bash
curl -sG "https://api.e-stat.go.jp/rest/3.0/app/json/getDataCatalog" \
  --data-urlencode "appId=$ESTAT_APP_ID" \
  --data-urlencode "searchWord=人口" \
  --data-urlencode "limit=20" \
  -o /tmp/estat-file-search.json
```

Then inspect the saved payload:

```bash
jq 'keys' /tmp/estat-file-search.json
```
