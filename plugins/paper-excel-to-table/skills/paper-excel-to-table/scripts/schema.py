#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["typer>=0.12", "pydantic>=2.6", "pyyaml>=6"]
# ///
"""schema.py — YAML-defined Pydantic model + CSV validator for extractor output.

Purpose: give the paper-excel-extractor subagent a stable, declarative target
when the user supplies a schema. This module converts a minimal YAML schema
into a Pydantic model at runtime and either (a) validates a CSV row-by-row or
(b) dumps the corresponding JSON schema for the subagent to read back.

YAML format (minimal):

    name: suido_gyomu_nenpo_p1
    description: ...
    primary_key: [item_code]             # optional
    columns:
      - name: level
        type: int                        # int | float | str | bool
        required: true
        description: ...
      - name: item_code
        type: str
        required: true
        allow_unknown: true              # optional; permits "?" even when required
      - name: value
        type: str
        required: false

`allow_unknown: true` lets a cell keep the sentinel "?" without failing the
required check. This matches the subagent's rule ("unreadable = ?, never
blank").
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any

import typer
import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, create_model

app = typer.Typer(add_completion=False, no_args_is_help=True)

UNKNOWN_SENTINEL = "?"

_TYPE_MAP: dict[str, type] = {
    "int": int,
    "float": float,
    "str": str,
    "bool": bool,
}


class _ColumnSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    type: str = "str"
    required: bool = False
    description: str | None = None
    allow_unknown: bool = True


class _SchemaDoc(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    description: str | None = None
    primary_key: list[str] = Field(default_factory=list)
    columns: list[_ColumnSpec]


def _load_schema(path: Path) -> _SchemaDoc:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise typer.BadParameter(f"schema root must be a mapping, got {type(raw).__name__}")
    return _SchemaDoc.model_validate(raw)


def _coerce(value: str, target: type, allow_unknown: bool) -> Any:
    if allow_unknown and value == UNKNOWN_SENTINEL:
        return UNKNOWN_SENTINEL  # surfaced as str; validator below accepts it
    if target is str:
        return value
    if target is int:
        return int(value.replace(",", "").strip())
    if target is float:
        return float(value.replace(",", "").strip())
    if target is bool:
        v = value.strip().lower()
        if v in {"true", "1", "yes", "y"}:
            return True
        if v in {"false", "0", "no", "n", ""}:
            return False
        raise ValueError(f"cannot coerce {value!r} to bool")
    raise ValueError(f"unsupported type {target!r}")


def _build_model(schema: _SchemaDoc) -> type[BaseModel]:
    fields: dict[str, Any] = {}
    for col in schema.columns:
        if col.type not in _TYPE_MAP:
            raise typer.BadParameter(
                f"column {col.name!r}: unsupported type {col.type!r} (allowed: {list(_TYPE_MAP)})"
            )
        py_type: Any = _TYPE_MAP[col.type]
        if col.allow_unknown and py_type is not str:
            py_type = py_type | str  # Union with str lets "?" pass through
        if not col.required:
            py_type = py_type | None
        default = ... if col.required else None
        fields[col.name] = (py_type, Field(default=default, description=col.description))
    return create_model(schema.name, __config__=ConfigDict(extra="forbid"), **fields)


def _row_to_obj(
    row: dict[str, str], schema: _SchemaDoc
) -> tuple[dict[str, Any], list[str]]:
    """Convert a CSV row (str values) into a dict of typed values. Collects soft errors."""
    obj: dict[str, Any] = {}
    errs: list[str] = []
    for col in schema.columns:
        raw = row.get(col.name, "")
        if raw == "" and not col.required:
            obj[col.name] = None
            continue
        if raw == "" and col.required:
            errs.append(f"column {col.name!r} is required but empty")
            continue
        try:
            obj[col.name] = _coerce(raw, _TYPE_MAP[col.type], col.allow_unknown)
        except Exception as e:
            errs.append(f"column {col.name!r}: cannot coerce {raw!r}: {e}")
    return obj, errs


@app.command()
def validate(
    csv_path: Path = typer.Argument(..., exists=True, readable=True, resolve_path=True),
    schema_path: Path = typer.Option(
        ..., "--schema", exists=True, readable=True, resolve_path=True
    ),
) -> None:
    """Validate a CSV against a YAML schema. Exit non-zero on any failure."""
    schema = _load_schema(schema_path)
    model = _build_model(schema)

    schema_cols = {c.name for c in schema.columns}
    failures: list[str] = []
    seen_pk: set[tuple[Any, ...]] = set()
    total_rows = 0

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            failures.append("CSV has no header row")
        else:
            missing = schema_cols - set(reader.fieldnames)
            if missing:
                failures.append(f"CSV missing required columns: {sorted(missing)}")
            extra = set(reader.fieldnames) - schema_cols
            if extra:
                failures.append(f"CSV has unknown columns (extra=forbid): {sorted(extra)}")

        for idx, row in enumerate(reader, start=2):  # header is line 1
            total_rows += 1
            obj, soft_errs = _row_to_obj(row, schema)
            for e in soft_errs:
                failures.append(f"row {idx}: {e}")
            try:
                model.model_validate(obj)
            except ValidationError as e:
                for err in e.errors():
                    loc = ".".join(str(p) for p in err["loc"])
                    failures.append(f"row {idx}: {loc}: {err['msg']}")
            if schema.primary_key:
                pk = tuple(row.get(k, "") for k in schema.primary_key)
                if pk in seen_pk:
                    failures.append(f"row {idx}: duplicate primary key {pk}")
                seen_pk.add(pk)

    if failures:
        for f in failures:
            typer.echo(f, err=True)
        typer.echo(
            f"schema.py: validation FAILED ({len(failures)} issue(s), {total_rows} row(s))",
            err=True,
        )
        raise typer.Exit(1)

    typer.echo(f"schema.py: validation OK ({total_rows} row(s))", err=True)
    json.dump(
        {"status": "ok", "rows": total_rows, "schema": schema.name},
        sys.stdout,
        indent=2,
    )
    sys.stdout.write("\n")


@app.command(name="dump-json-schema")
def dump_json_schema(
    schema_path: Path = typer.Option(
        ..., "--schema", exists=True, readable=True, resolve_path=True
    ),
) -> None:
    """Emit the JSON schema of the Pydantic model derived from the YAML schema."""
    schema = _load_schema(schema_path)
    model = _build_model(schema)
    payload = {
        "name": schema.name,
        "description": schema.description,
        "primary_key": schema.primary_key,
        "columns": [c.model_dump() for c in schema.columns],
        "json_schema": model.model_json_schema(),
    }
    json.dump(payload, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    app()
