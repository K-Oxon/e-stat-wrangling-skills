# Reference

## Purpose

Find machine-readable e-Stat statistical tables and the identifiers needed to retrieve them later.

## Endpoint mapping

- Search candidate tables: `getStatsList`
- Inspect classification metadata: `getMetaInfo`
- Preview table values later: `getStatsData`

## Working rule

This skill currently documents the discovery workflow only.

- Save each response to disk first.
- Use the saved payload as the primary source for later `jq` or SQL shaping.
- Keep Python wrappers out until the data retrieval workflow is explicitly defined.

## Required environment variables

- `ESTAT_APP_ID`
