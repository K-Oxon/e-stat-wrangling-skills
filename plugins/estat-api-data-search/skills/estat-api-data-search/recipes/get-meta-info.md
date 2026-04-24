# Get Meta Info

```bash
curl -sG "https://api.e-stat.go.jp/rest/3.0/app/json/getMetaInfo" \
  --data-urlencode "appId=$ESTAT_APP_ID" \
  --data-urlencode "statsDataId=REPLACE_ME" \
  -o /tmp/estat-meta-info.json
```

Replace `REPLACE_ME` after a candidate `statsDataId` has been confirmed.
