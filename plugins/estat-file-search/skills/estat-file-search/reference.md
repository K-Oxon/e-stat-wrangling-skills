# Reference

## Purpose

Search file-oriented e-Stat resources and retrieve the final download URL.

## Endpoint mapping

- Search catalog candidates: `getDataCatalog`
- Download a concrete file: direct `GET` against the returned public URL

## Working rule

Keep this skill documentation-first for now.

- Save each response to disk first.
- Inspect the JSON structure before deciding the final `jq` expression.
- Avoid wrapping the flow in Python until the workflow is stable.

## Required environment variables

- `ESTAT_APP_ID`

## Placeholder response handling

The final JSON extraction rules will be refined later. At this stage the recipes focus on:

- reproducible request shapes
- file-first response storage
- a stable place to grow endpoint notes
