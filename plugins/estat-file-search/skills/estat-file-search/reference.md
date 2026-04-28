# Reference

## Purpose

Search file-oriented e-Stat resources and retrieve the final download URL.

## Endpoint mapping

- Search catalog candidates: `getDataCatalog`
- Download a concrete file: direct `GET` against the returned public URL

## Endpoint

`https://api.e-stat.go.jp/rest/3.0/app/json/getDataCatalog`

Required:

- `appId`: read from `ESTAT_APP_ID` unless explicitly overridden.

Primary search parameters:

- `statsCode`: 5-digit organization code or 8-digit government statistics code. The 8-digit government statistics code is the strongest practical filter.
- `searchWord`: keyword. `AND`, `OR`, and `NOT` are supported by the API, but verify behavior from raw responses.
- `dataType`: `XLS`, `CSV`, `PDF`, `XML`, `XLS_REP`, `DB`; comma-separated. Default in this skill is `XLS,CSV,PDF,XLS_REP`.

Pagination:

- `limit`: default 100 for this skill.
- `startPosition`: controlled from `RESULT_INF.NEXT_KEY`.
- `NEXT_KEY`: continue until missing, `--max-pages` is reached, or `--all` is used.

Advanced and suspect filters:

- `surveyYears`, `openYears`, `updatedDate`, `statsField`, `collectArea`, `catalogId`, `resourceId`.
- These can be useful for investigation, but e-Stat metadata is uneven. Prefer displaying these fields over relying on them as hard filters.

## Response paths

Start from:

- `GET_DATA_CATALOG.RESULT`
- `GET_DATA_CATALOG.DATA_CATALOG_LIST_INF`
- `GET_DATA_CATALOG.DATA_CATALOG_LIST_INF.DATA_CATALOG_INF`

Important dataset fields:

- `DATASET.STAT_NAME.@code`: government statistics code
- `DATASET.STAT_NAME.$`: government statistics name
- `DATASET.ORGANIZATION.@code`: organization code
- `DATASET.ORGANIZATION.$`: organization name
- `DATASET.TITLE.NAME`: dataset title
- `DATASET.TITLE.SURVEY_DATE`: survey date
- `DATASET.LANDING_PAGE`: e-Stat landing page

Important resource fields:

- `RESOURCES.RESOURCE.@id`: resource/statistical table ID
- `RESOURCES.RESOURCE.TITLE.NAME`: resource title
- `RESOURCES.RESOURCE.TITLE.TABLE_NO`: table number
- `RESOURCES.RESOURCE.TITLE.TABLE_NAME`: table name
- `RESOURCES.RESOURCE.FORMAT`: file or DB format
- `RESOURCES.RESOURCE.URL`: final download URL or DB link

## Shape drift

The JSON is converted from XML and can shift shape:

- `DATA_CATALOG_INF` may be a single object or an array.
- `RESOURCES.RESOURCE` may be a single object or an array.
- `DESCRIPTION` and similar fields may be strings, empty strings, or nested structures.

Use the scripts' flattened candidate output for normal work, and inspect raw JSON when a field is missing or ambiguous.

## Required environment variables

- `ESTAT_APP_ID`

## Working rules

- Save each response to disk first.
- Inspect the JSON structure before trusting a field.
- Treat `dataType` as a search hint, not a guarantee.
- Use `--data-type ALL` when DB-only data or false negatives matter.
- Download only after validating the candidate row.

## Related skill

`getDataCatalog` can miss API-only or DB-oriented data. If the request is about statistical table IDs, metadata, or API data retrieval rather than downloadable files, use `estat-api-data-search`.
