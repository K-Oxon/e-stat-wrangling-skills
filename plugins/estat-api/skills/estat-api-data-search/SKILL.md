---
name: estat-api-data-search
description: Use this when the user wants to discover e-Stat API or DB-provided statistical tables, identify a statsDataId, or inspect table metadata before deciding how to fetch and normalize the actual data.
---

# e-Stat API Data Search

Use this skill to discover machine-readable e-Stat statistical tables.

## Workflow

1. Read [reference.md](reference.md) for endpoint behavior and response paths.
2. Decide whether the user needs downloadable files or API/DB-provided statistical tables. If file URLs are the target, use `estat-file-search`.
3. If the government statistics code is unknown, search the bundled government statistics code list with `scripts/gov_stats_lookup.py`.
4. Generate a small set of plausible `searchWord` values before calling the API. Prefer survey names, administrative terms,制度名, and likely table-title nouns over casual wording.
5. Search `getStatsList` with `scripts/list.py`, using `statsCode` and `searchWord` as the main levers.
6. Save the raw JSON response before narrowing or summarizing.
7. Inspect flattened candidates in e-Stat response order. Do not apply opaque scoring in the MVP.
8. Stop at `statsDataId` discovery. Metadata inspection and full data fetching are follow-up workflows.

## Required environment

- `ESTAT_APP_ID`
  - Get one from <https://www.e-stat.go.jp/mypage/user/preregister>
  - Set it with `export ESTAT_APP_ID="<your app id>"`, or pass `--app-id` for a one-off command.
  - If you only need to parse a saved response, use `--from-fixture`; no app ID is needed.

## Scope

- Find candidate tables
- Prepare later data retrieval work

## Operating rules

- Treat e-Stat API/DB search as a two-layer search space: government statistics code, then statistical table ID.
- Use government statistics code discovery and keyword search iteratively.
- `searchKind` is normally omitted; the API default is enough for this skill's table discovery workflow.
- `statsNameList=Y` is not used in MVP because it changes the response from table candidates to survey-name lists.
- `@id` is the `statsDataId`, but candidate output must include surrounding context because IDs can appear duplicated in unhelpful ways.
- Date fields such as `UPDATED_DATE` are display metadata, not authoritative filters.
- Prefer raw JSON plus CSV/JSONL candidate output over one-off `jq` pipelines for heavy responses.
