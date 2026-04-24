---
name: estat-api-data-search
description: Use this when the user wants to discover e-Stat API or DB-provided statistical tables, identify a statsDataId, or inspect table metadata before deciding how to fetch and normalize the actual data.
---

# e-Stat API Data Search

Use this skill to discover machine-readable e-Stat statistical tables.

## Workflow

1. Read [reference.md](reference.md) for endpoint mapping.
2. Use a saved-response recipe from `recipes/`.
3. Confirm the `statsDataId` candidate before expanding into data retrieval work.

## Required environment

- `ESTAT_APP_ID`

## Scope

- Find candidate tables
- Inspect metadata
- Prepare later data retrieval work

Detailed API shaping is intentionally deferred.
