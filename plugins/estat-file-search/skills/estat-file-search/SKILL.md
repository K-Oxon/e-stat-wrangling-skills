---
name: estat-file-search
description: Use this when the user wants to search e-Stat for downloadable files such as xlsx, csv, or pdf and is still working at the search-and-download stage rather than the downstream parsing stage.
---

# e-Stat File Search

Use this skill to locate downloadable e-Stat files.

## Workflow

1. Read [reference.md](reference.md) to confirm the endpoint and required parameters.
2. Start from one of the prepared recipes under `recipes/`.
3. Save the raw JSON response before narrowing it with `jq`.
4. Download the selected file URL only after the candidate row has been validated.

## Required environment

- `ESTAT_APP_ID`

## Scope

- Search
- Filter
- Download

Detailed parameter tuning and API behavior will be filled in later.
