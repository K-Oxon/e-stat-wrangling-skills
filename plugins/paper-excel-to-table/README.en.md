# paper-excel-to-table

**Claude Code plugin that extracts a structured CSV from a paper-style Excel form (exported as PDF) using Opus 4.7 vision.**

[日本語版 →](README.md) / [Project README →](../../README.en.md)

---

## What this plugin does for you

In a Claude Code session, you can say:

```
Turn this PDF into a CSV: /path/to/water_utility_report.pdf

This is city X's water utility annual report (FY2025). item_code is on
the RIGHT edge of each row, and indentation encodes parent/child
relationships. Footnotes use '※'.
```

What happens under the hood:

1. The PDF is rasterized to high-resolution PNGs (300 DPI)
2. A dedicated **subagent** (`paper-excel-extractor`, Opus 4.7, `effort: high`) reads the images and plans the extraction layout
3. First-pass extract → detects low-confidence cells → **automatically crops** those regions → re-reads them at native resolution → overwrites the CSV
4. (Optional) Validates the CSV against a YAML schema with Pydantic
5. Returns a short report: row count, which side the ID column was on, crop count, list of low-confidence cells

Because extraction runs in a subagent, **no image bytes or intermediate tables end up in the main session context** — your long-running conversation stays clean.

---

## Prerequisites

| Item | Requirement |
| --- | --- |
| OS | macOS (PDFKit is required for rasterization) |
| Xcode Command Line Tools | Installed (`xcode-select --install`); `swift` must be on PATH |
| Claude Code | 0.124.0 or later |
| Input | **PDF only.** Convert xlsx beforehand via "File → Save As → PDF" in Excel or Numbers |
| API key | None (the vision work runs inside your Claude Code Opus 4.7 session) |

xlsx → PDF conversion is intentionally left to the user: Excel/Numbers' built-in PDF export is the most reliable path across templates, and alternatives (LibreOffice headless, etc.) break on enough forms that we chose not to ship an unreliable automation ([detailed design §4.1](../../docs/dev/plugins/paper-excel-to-table.md)).

---

## Install

Inside a Claude Code session:

```
/plugin marketplace add K-Oxon/e-stat-wrangling-skills
/plugin install paper-excel-to-table@e-stat-wrangling
```

### First-install caveat

Subagents may not be picked up on initial install. Right after `/plugin install`, run:

```
/reload-plugins
```

once. Subsequent sessions pick the plugin up normally.

### Recommended permissions (optional)

To pre-approve commands the plugin invokes routinely, add the following to `~/.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "Bash(uv run --script *)",
      "Bash(swift --version)",
      "Bash(xcode-select -p)",
      "Bash(mdls -name kMDItemNumberOfPages *)"
    ]
  }
}
```

Claude Code does not yet allow plugins to ship their own allowlists, so this is per-user.

---

## Usage

Just ask in natural language:

```
I want to convert /path/to/form.pdf to CSV. It's the layout of the monthly
long-term-care insurance status report. Page 1 only.
```

SKILL.md's trigger fires and runs the 5-step flow above.

### Giving the subagent enough context up front

The subagent asks for `user_context` first. Providing the following in your original request avoids an `INSUFFICIENT_CONTEXT` round-trip:

- **Official form name** (e.g., "Local public enterprise financial status survey — water utility layout")
- **Year / issuing agency**
- **Known column structure and vocabulary** ("item_code is on the right", "※ means footnote", "'-' means missing")
- **Target pages**
- **YAML schema path, if you have one**

---

## Schema-driven mode

If you repeatedly process a form with a fixed column definition, supply a YAML schema and the subagent will validate the CSV with Pydantic before returning. Just mention the schema path in natural language; SKILL.md incorporates it into the subagent prompt.

### Sample: water utility annual report

The bundled `scripts/schemas/suido_gyomu_nenpo.yaml` is the minimal example:

```yaml
name: suido_gyomu_nenpo
description: Sample schema for the water utility layout of the Local Public Enterprise Financial Status Survey.
primary_key: [item_code]
columns:
  - name: level
    type: int
    required: true
    description: Hierarchy depth encoded by indentation (0-based).
  - name: item_code
    type: str
    required: true
  - name: item_label
    type: str
    required: true
  - name: unit
    type: str
    required: false
  - name: value
    type: str           # values include "-" and annotations, so keep as str
    required: false
  - name: notes
    type: str
    required: false
```

Schema format details are in the `scripts/schema.py` module docstring.

---

## Calling the bundled scripts directly (for debugging / non-Claude-Code use)

The normal path is through Claude Code, but each script is runnable on its own.

### 1. Rasterize a PDF

```bash
uv run --script plugins/paper-excel-to-table/skills/paper-excel-to-table/scripts/rasterize.py \
  input.pdf out_dir/ [--dpi 300] [--pages 1-]
```

stdout returns a JSON with `page_count` and per-page `width_px`/`height_px`.

### 2. Crop an image

```bash
uv run --script plugins/paper-excel-to-table/skills/paper-excel-to-table/scripts/crop.py \
  out_dir/page-001.png --rel-box 0.0,0.15,1.0,0.25 -o crop.png
```

Use `--box` for absolute pixels or `--rel-box` for fractions of the image. They cannot be mixed in one invocation (Typer does not preserve relative order across different options); call twice if you need both.

### 3. Validate a CSV against a schema

```bash
uv run --script plugins/paper-excel-to-table/skills/paper-excel-to-table/scripts/schema.py \
  validate out.csv --schema scripts/schemas/suido_gyomu_nenpo.yaml
```

Failures are listed on stderr line-by-line (row index, column, reason).

---

## Pitfalls worth knowing up front

| Concern | Mitigation |
| --- | --- |
| Indentation-encoded hierarchy disappears in CSV | The subagent always emits a `level` integer column (0-based). Schemas should require it. |
| ID column may be on the **right** edge | Do not assume left-to-right. The subagent reports `id_column` with the side it chose. |
| Visually merged cells ≠ logically merged cells | Borders alone aren't enough. Pass the form's semantics via `user_context`. |
| Footnote markers (※, `*`, `注1)`) | Split into a `notes` column rather than mixing them into the value column. |
| Uncertain cells | Never left blank — marked with `?` and listed under `low_confidence` in the report. |
| Opus 4.7 vision auto-downscales inputs (~2576 px long edge) | Raw PNGs are kept at 300 DPI; crops keep native resolution for subsequent re-reads. |

---

## Related documents

- [Detailed design](../../docs/dev/plugins/paper-excel-to-table.md) — why the subagent architecture, backend contract, future package-promotion criteria
- [Project README](../../README.en.md)
- [SKILL.md](skills/paper-excel-to-table/SKILL.md) — Claude Code trigger + workflow (the surface an LLM sees)
- [agents/paper-excel-extractor.md](agents/paper-excel-extractor.md) — subagent input contract and hard rules

---

## License

[MIT](../../LICENSE) — same as the rest of the project.
