---
name: paper-excel-to-table
description: Use this when the user wants to turn a paper-style Excel workbook with merged cells and presentation-heavy layout into a structured CSV or validation-ready intermediate output.
---

# Paper Excel To Table

This skill is for spreadsheet forms that are visually readable by humans but not directly usable as
machine-readable tables.

## Trigger

Use this skill when the request looks like:

- "帳票 Excel を CSV にしたい"
- "複雑なセル結合の Excel を構造化したい"
- "紙様式の Excel から表形式を取り出したい"

## Current workflow

1. Confirm the input workbook or PDF path.
2. Inspect the workbook layout and identify the target tables.
3. Create an extraction plan before introducing any package code.
4. Keep raw workbook/PDF evidence and intermediate notes attached to the task.

## Notes

- There is no Python package for this skill yet.
- Promote to a package only after the target workflow, schema shape, and extraction boundary are
  stable enough to test.
