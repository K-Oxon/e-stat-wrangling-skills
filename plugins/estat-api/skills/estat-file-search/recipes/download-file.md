# Download File

In the examples below, set `SKILL_DIR` to the absolute path of this installed skill folder.

After identifying the final URL from the saved catalog response, first do a dry run:

```bash
uv run --script "$SKILL_DIR/scripts/download.py" \
  --url "https://www.e-stat.go.jp/stat-search/file-download?statInfId=...&fileKind=0" \
  --resource-id 000000000000 \
  --format XLS \
  --dest ./data \
  --dry-run
```

Then download:

```bash
uv run --script "$SKILL_DIR/scripts/download.py" \
  --url "https://www.e-stat.go.jp/stat-search/file-download?statInfId=...&fileKind=0" \
  --resource-id 000000000000 \
  --format XLS \
  --dest ./data
```

Filename policy:

- Prefer server `Content-Disposition`.
- Fallback to `resource_id` plus inferred extension.
- Write a manifest next to the file.
