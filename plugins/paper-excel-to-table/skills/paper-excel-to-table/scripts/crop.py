#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["typer>=0.12", "pillow>=10"]
# ///
"""crop.py — crop rectangular regions from a page PNG.

The paper-excel-extractor subagent calls this when a full-page extraction has
low confidence on some rows. Each invocation can produce one or more crops.
Boxes may be given in absolute pixels (`--box x,y,w,h`) or as fractions of the
image (`--rel-box x,y,w,h` where each value is in [0,1]); origin is top-left.
Output PNGs inherit DPI metadata from the source so downstream readers still
see "native resolution" crops.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import typer
from PIL import Image

app = typer.Typer(add_completion=False, no_args_is_help=True)


def _parse_four(spec: str, name: str) -> tuple[float, float, float, float]:
    parts = [p.strip() for p in spec.split(",")]
    if len(parts) != 4:
        raise typer.BadParameter(f"{name} expects 4 comma-separated numbers, got '{spec}'")
    try:
        a, b, c, d = (float(p) for p in parts)
    except ValueError as e:
        raise typer.BadParameter(f"{name} parse failed: {e}") from e
    return a, b, c, d


def _to_abs_box(
    abs_box: str | None,
    rel_box: str | None,
    img_w: int,
    img_h: int,
) -> tuple[int, int, int, int]:
    """Return (left, top, right, bottom) in pixel coords, validated."""
    if (abs_box is None) == (rel_box is None):
        raise typer.BadParameter("exactly one of --box or --rel-box is required per crop")

    if abs_box is not None:
        x, y, w, h = _parse_four(abs_box, "--box")
        left, top = int(round(x)), int(round(y))
        right, bottom = int(round(x + w)), int(round(y + h))
    else:
        assert rel_box is not None
        x, y, w, h = _parse_four(rel_box, "--rel-box")
        for v, label in ((x, "x"), (y, "y"), (w, "w"), (h, "h")):
            if v < 0.0 or v > 1.0:
                raise typer.BadParameter(f"--rel-box {label}={v} out of [0,1]")
        left = int(round(x * img_w))
        top = int(round(y * img_h))
        right = int(round((x + w) * img_w))
        bottom = int(round((y + h) * img_h))

    left = max(0, min(img_w, left))
    right = max(0, min(img_w, right))
    top = max(0, min(img_h, top))
    bottom = max(0, min(img_h, bottom))
    if right - left <= 0 or bottom - top <= 0:
        raise typer.BadParameter(
            f"crop is empty after clamping: box=({left},{top})-({right},{bottom})"
        )
    return left, top, right, bottom


@app.command()
def run(
    image: Path = typer.Argument(..., exists=True, readable=True, resolve_path=True),
    box: list[str] = typer.Option(
        [],
        "--box",
        help="Absolute pixel box: 'x,y,w,h' (top-left origin). Repeatable.",
    ),
    rel_box: list[str] = typer.Option(
        [],
        "--rel-box",
        help="Relative box: 'x,y,w,h' each in [0,1]. Repeatable.",
    ),
    out: list[Path] = typer.Option(
        [],
        "-o",
        "--out",
        help="Output PNG path. Repeat once per --box/--rel-box in order.",
    ),
) -> None:
    """Crop the image. Each --box/--rel-box pairs with one -o in the order given."""
    all_boxes: list[tuple[str, str]] = [("abs", b) for b in box] + [("rel", b) for b in rel_box]
    if not all_boxes:
        raise typer.BadParameter("provide at least one --box or --rel-box")
    if len(out) != len(all_boxes):
        raise typer.BadParameter(
            f"need one -o per crop; got {len(all_boxes)} boxes and {len(out)} outputs"
        )

    with Image.open(image) as src:
        src.load()
        img_w, img_h = src.size
        dpi = src.info.get("dpi")

        results = []
        for (kind, spec), out_path in zip(all_boxes, out, strict=True):
            if kind == "abs":
                lbox = _to_abs_box(spec, None, img_w, img_h)
            else:
                lbox = _to_abs_box(None, spec, img_w, img_h)
            cropped = src.crop(lbox)
            out_path = out_path.resolve()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            save_kwargs: dict = {}
            if dpi is not None:
                save_kwargs["dpi"] = dpi
            cropped.save(out_path, format="PNG", **save_kwargs)
            results.append(
                {
                    "source": str(image),
                    "out": str(out_path),
                    "box_px": {
                        "left": lbox[0],
                        "top": lbox[1],
                        "right": lbox[2],
                        "bottom": lbox[3],
                        "width": lbox[2] - lbox[0],
                        "height": lbox[3] - lbox[1],
                    },
                    "spec_kind": kind,
                    "spec": spec,
                }
            )

    json.dump({"source_size_px": [img_w, img_h], "crops": results}, sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    app()
