# Architecture

This repository uses a plugin-first structure.

- `plugins/` contains skill-facing workflow descriptions, references, recipes, scripts, and subagents.
- `samples/` contains public sample inputs, context, and representative outputs.
- `docs/dev/` contains design notes, planning records, and temporary investigation artifacts.
- `scripts/` contains repository-level maintenance or source data refresh helpers.
- `packages/` is intentionally absent until a workflow needs reusable implementation code.

## Current Plugins

- `paper-excel-to-table` is a Claude Code subagent workflow with local helper scripts.
- `estat-api` contains e-Stat API discovery skills:
  - `estat-file-search` is a PEP 723 script workflow for `getDataCatalog` discovery and file download.
  - `estat-api-data-search` is a PEP 723 script workflow for `getStatsList` table discovery.

## Principles

- Workflow activation, task framing, recipes, thin scripts, and subagent contracts belong in `plugins/`.
- Reusable implementation code can be promoted into `packages/` later.
- Add PEP 723 scripts when repeatable output, raw evidence capture, or fixture tests matter.
- Save raw e-Stat responses before shaping them.
- Keep fixture-first tests so CI can stay mostly offline.
- v1 targets Claude Code plugin marketplace usage.
- Other install surfaces are future work until they are tested and cheap to maintain.

## Data Boundaries

- `samples/` is for public examples that users can follow.
- `scripts/tests/fixtures/` is for small deterministic test data.
- `docs/dev/` is for design and investigation artifacts, not the public happy path.

When package code becomes necessary, introduce it as a separate decision with a clear owner workflow, tests, and CLI surface.
