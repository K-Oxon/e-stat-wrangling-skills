# Filter By Prefecture

`collectArea` is not reliable enough to be the first lever. Prefer anchoring the search with
`statsCode`, then use keyword variants and inspect candidate titles/landing pages.

```bash
uv run --script plugins/estat-file-search/skills/estat-file-search/scripts/search.py \
  --stats-code 00200521 \
  --keyword "東京 AND 人口" \
  --limit 100 \
  --raw-output /tmp/estat-prefecture-raw.json \
  --candidates-output /tmp/estat-prefecture-candidates.csv
```

If the response is too broad, try a short keyword set instead of one overloaded query:

```bash
uv run --script plugins/estat-file-search/skills/estat-file-search/scripts/keyword_hints.py \
  人口 東京 \
  --survey-name 国勢調査
```
