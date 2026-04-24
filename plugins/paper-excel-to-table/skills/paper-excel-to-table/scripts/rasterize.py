#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["typer>=0.12"]
# ///
"""rasterize.py — thin Python wrapper around rasterize.swift.

Renders a PDF to per-page PNGs by shelling out to the colocated Swift script.
The Swift script owns the actual rasterization (PDFKit + Core Graphics); this
wrapper just fail-fasts on non-Darwin hosts, checks that `swift` is available,
redirects Swift's module cache to a writable location, and passes the Backend
Contract stdout JSON (see docs/dev/plugins/paper-excel-to-table.md §4.3) back
through to the caller verbatim.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

import typer

app = typer.Typer(add_completion=False, no_args_is_help=True)

SWIFT_SCRIPT = Path(__file__).resolve().parent / "rasterize.swift"
CACHE_ROOT = Path.home() / ".cache" / "paper-excel-to-table" / "swift-module-cache"


def _fail(msg: str, code: int = 1) -> None:
    typer.echo(f"rasterize.py: {msg}", err=True)
    raise typer.Exit(code)


def _ensure_env() -> None:
    if platform.system() != "Darwin":
        _fail("macOS only in MVP (rasterize.swift requires PDFKit).", code=2)
    if shutil.which("swift") is None:
        _fail(
            "`swift` not found. Install Xcode Command Line Tools: `xcode-select --install`",
            code=2,
        )
    if not SWIFT_SCRIPT.exists():
        _fail(f"rasterize.swift missing at {SWIFT_SCRIPT}", code=2)


@app.command()
def run(
    pdf_path: Path = typer.Argument(..., exists=True, readable=True, resolve_path=True),
    out_dir: Path = typer.Argument(..., resolve_path=True),
    dpi: int = typer.Option(300, "--dpi", min=1, help="Rendering DPI (default 300)."),
    box: str = typer.Option("media", "--box", help="Page box: media|crop"),
    colorspace: str = typer.Option("sRGB", "--colorspace", help="sRGB|Gray"),
    alpha: bool = typer.Option(False, "--alpha", help="Keep alpha channel"),
    no_annots: bool = typer.Option(False, "--no-annots", help="Suppress PDF annotations"),
    pages: str | None = typer.Option(
        None, "--pages", help='Page spec e.g. "1-", "1,3,5", "2-4,7"'
    ),
) -> None:
    """Render PDF pages to PNGs via rasterize.swift."""
    _ensure_env()

    if box not in {"media", "crop"}:
        _fail("--box must be 'media' or 'crop'", code=2)
    if colorspace not in {"sRGB", "Gray"}:
        _fail("--colorspace must be 'sRGB' or 'Gray'", code=2)

    out_dir.mkdir(parents=True, exist_ok=True)
    CACHE_ROOT.mkdir(parents=True, exist_ok=True)

    cmd: list[str] = [
        "swift",
        str(SWIFT_SCRIPT),
        str(pdf_path),
        str(out_dir),
        "--dpi",
        str(dpi),
        "--box",
        box,
        "--colorspace",
        colorspace,
    ]
    if alpha:
        cmd.append("--alpha")
    if no_annots:
        cmd.append("--no-annots")
    if pages:
        cmd.extend(["--pages", pages])

    env = os.environ.copy()
    env.setdefault("CLANG_MODULE_CACHE_PATH", str(CACHE_ROOT))
    env.setdefault("SWIFT_MODULECACHE_PATH", str(CACHE_ROOT))

    result = subprocess.run(cmd, env=env, check=False)
    raise typer.Exit(result.returncode)


if __name__ == "__main__":
    app()
