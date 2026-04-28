# Download File

After identifying the final URL from the saved catalog response, first do a dry run:

```bash
uv run --script plugins/estat-file-search/skills/estat-file-search/scripts/download.py \
  --url "https://www.e-stat.go.jp/stat-search/file-download?statInfId=...&fileKind=0" \
  --resource-id 000000000000 \
  --format XLS \
  --dest ./data \
  --dry-run
```

Then download:

```bash
uv run --script plugins/estat-file-search/skills/estat-file-search/scripts/download.py \
  --url "https://www.e-stat.go.jp/stat-search/file-download?statInfId=...&fileKind=0" \
  --resource-id 000000000000 \
  --format XLS \
  --dest ./data
```

Filename policy:

- Prefer server `Content-Disposition`.
- Fallback to `resource_id` plus inferred extension.
- Write a manifest next to the file.
