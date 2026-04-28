# Reference

## Purpose

Find machine-readable e-Stat statistical tables and the identifiers needed to retrieve them later.

## Endpoint mapping

- Search candidate tables: `getStatsList`
- Inspect classification metadata later: `getMetaInfo`
- Retrieve table values later: `getStatsData`

## Endpoint

`https://api.e-stat.go.jp/rest/3.0/app/json/getStatsList`

Required:

- `appId`: read from `ESTAT_APP_ID` unless explicitly overridden.

Primary search parameters:

- `statsCode`: 5-digit organization code or 8-digit government statistics code. The 8-digit government statistics code is the strongest practical filter.
- `searchWord`: keyword. `AND`, `OR`, and `NOT` are supported by the API, but verify behavior from raw responses.
- `limit`: official default is 100,000. This skill's CLI defaults to 100 for inspectability.

Parameters deliberately not emphasized:

- `searchKind`: normally omit. The API default is enough for regular API/DB table discovery.
- `statsNameList`: do not set in MVP. `Y` returns survey-name lists instead of table candidates.

Advanced and suspect filters:

- `surveyYears`, `openYears`, `updatedDate`, `statsField`, `collectArea`.
- These can be useful for investigation, but e-Stat metadata is uneven. Prefer displaying these fields over relying on them as hard filters.

Pagination:

- `startPosition`: controlled from `RESULT_INF.NEXT_KEY`.
- `NEXT_KEY`: continue until missing, `--max-pages` is reached, or `--all` is used.

## Response paths

Start from:

- `GET_STATS_LIST.RESULT`
- `GET_STATS_LIST.DATALIST_INF`
- `GET_STATS_LIST.DATALIST_INF.TABLE_INF`

Important table fields:

- `TABLE_INF.@id`: statistical table ID (`statsDataId`)
- `STAT_NAME.@code`: government statistics code
- `STAT_NAME.$`: government statistics name
- `GOV_ORG.@code`: organization code
- `GOV_ORG.$`: organization name
- `STATISTICS_NAME`: statistics name
- `TITLE.@no`: title number
- `TITLE.$`: title
- `TITLE_SPEC.TABLE_NAME`: table name
- `CYCLE`: cycle
- `SURVEY_DATE`: survey date
- `OPEN_DATE`: open date
- `UPDATED_DATE`: updated date
- `COLLECT_AREA`: collection area
- `OVERALL_TOTAL_NUMBER`: total row count
- `MAIN_CATEGORY` / `SUB_CATEGORY`: category codes and names

## Shape drift

The JSON is converted from XML and can shift shape:

- `TABLE_INF` may be a single object or an array.
- `TITLE`, `STAT_NAME`, `GOV_ORG`, `MAIN_CATEGORY`, and `SUB_CATEGORY` may contain `@code`, `@no`, and `$` keys.
- `DESCRIPTION` may be a string, empty string, or nested object.
- `@id` can appear duplicated in ways that are not useful for human selection. Always inspect surrounding fields.

Use the scripts' flattened candidate output for normal work, and inspect raw JSON when a field is missing or ambiguous.

## Required environment variables

- `ESTAT_APP_ID`

## Working rules

- Save each response to disk first.
- Inspect the JSON structure before trusting a field.
- Search with `statsCode` and short `searchWord` values as the main levers.
- Present candidates in e-Stat response order.
- Stop at `statsDataId` discovery in MVP.
- Use `estat-file-search` if the user needs downloadable file URLs.
