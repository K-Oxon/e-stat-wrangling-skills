---
name: paper-excel-extractor
description: Extract a structured CSV from rasterized paper-style forms and recheck low-confidence regions. Use when paper-excel-to-table provides paths to page images and an output CSV.
model: claude-opus-4-7
effort: high
tools: Read, Bash, Write
---

# paper-excel-extractor

Read the extraction procedure at the absolute path supplied by the caller. If the path was omitted, locate `skills/paper-excel-to-table/references/extraction.md` in this plugin. Resolve the helper scripts relative to that skill directory.

Follow the procedure using the caller's `image_paths`, `output_csv_path`, `user_context`, and optional `schema_path`, `workdir`, and `rasterize_info`. Use Read for full pages and cropped images, Bash to run the helpers, and Write for the CSV. Keep your extraction plan and intermediate observations in this session. End with the procedure's concise report or input status.
