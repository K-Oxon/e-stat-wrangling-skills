# Changelog

## Unreleased

### Added

- Added standalone skill installation for Codex and Antigravity CLI.
- Added source-based evaluation for paper-form extraction.

### Changed

- Updated tooling and script dependencies.
- Required immutable references for GitHub Actions workflows.
- Clarified skill instructions and installed resource paths.

### Initial features

- Added `paper-excel-to-table`, a macOS alpha plugin for extracting structured CSV from paper-style form PDFs.
- Added `estat-api`, with skills for discovering downloadable e-Stat files and API/DB statistical table IDs.
- Added sample data and schema validation for the paper-form extraction workflow.

### Notes

- `paper-excel-to-table` currently supports macOS only.
- e-Stat API workflows require `ESTAT_APP_ID`.
- Full `getStatsData` fetching and non-macOS PDF rasterization are planned after v1.
