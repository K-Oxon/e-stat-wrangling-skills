# Architecture

Each skill directory is the source for standalone Agent Skills and for the Claude Code plugins.

- `plugins/` contains skill-facing workflow descriptions, references, recipes, scripts, and subagents.
- `samples/` contains public sample inputs, context, and representative outputs.
- `docs/` contains architecture, skill maintenance notes, and evaluation results.
- `scripts/` contains repository-level maintenance or source data refresh helpers.
- `packages/` is intentionally absent until a workflow needs reusable implementation code.

## Current Plugins

- `paper-excel-to-table` has a shared extraction procedure and local helper scripts. The Claude Code plugin supplies a dedicated subagent.
- `estat-api` contains e-Stat API discovery skills:
  - `estat-file-search` is a PEP 723 script workflow for `getDataCatalog` discovery and file download.
  - `estat-api-data-search` is a PEP 723 script workflow for `getStatsList` table discovery.

## Principles

- Workflow activation, task framing, recipes, thin scripts, and subagent contracts belong in `plugins/`.
- Reusable implementation code can be promoted into `packages/` later.
- Add PEP 723 scripts when repeatable output, raw evidence capture, or fixture tests matter.
- Save raw e-Stat responses before shaping them.
- Keep fixture-first tests so CI can stay mostly offline.
- Standalone installs for Codex and Antigravity CLI share the project skill directory. The Claude Code marketplace loads the same skills.

## Data Boundaries

- `samples/` is for public examples that users can follow.
- `scripts/tests/fixtures/` is for small deterministic test data.
- `samples/paper-excel-to-table/` contains the source-checked evaluation fixtures outside the distributed skills.

When package code becomes necessary, introduce it as a separate decision with a clear owner workflow, tests, and CLI surface.
