# Discover Stats Table

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
```
