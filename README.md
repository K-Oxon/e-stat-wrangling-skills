# e-stat-wrangling-skills

Japanese public statistics, especially e-Stat, are optimized for administrative reporting rather
than machine-readable analysis. This repository provides a small monorepo skeleton to turn that
material into reusable skills and Python tooling.

## Layout

```text
.
├── .claude-plugin/          # Marketplace catalog
├── plugins/                 # Skill plugins
├── docs/                    # Architecture and contributor docs
└── .github/workflows/       # CI skeleton
```

## Initial plugins

- `paper-excel-to-table`: workflow notes for turning paper-style Excel sheets into structured
  tables.
- `estat-file-search`: e-Stat file discovery workflow documented as skill + reference + recipes.
- `estat-api-data-search`: e-Stat table discovery workflow documented as skill + reference +
  recipes.

## Development

The current repository is documentation-first. No Python package is included yet.

Packages can be introduced later when a skill has enough stable implementation pressure to justify
shared code, CLI entry points, tests, and dependency management.
