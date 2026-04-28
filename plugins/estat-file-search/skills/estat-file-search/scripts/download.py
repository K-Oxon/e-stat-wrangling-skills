#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "httpx>=0.27,<1",
#   "pydantic>=2,<3",
# ]
# ///
"""Download a selected e-Stat file URL and write a manifest."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from email.message import Message
from pathlib import Path
from urllib.parse import unquote, urlparse

import httpx
from pydantic import BaseModel


FORMAT_EXTENSIONS = {
    "XLS": ".xls",
    "XLSX": ".xlsx",
    "XLS_REP": ".xls",
    "CSV": ".csv",
    "PDF": ".pdf",
    "XML": ".xml",
    "DB": ".json",
}

CONTENT_TYPE_EXTENSIONS = {
    "application/pdf": ".pdf",
    "text/csv": ".csv",
    "application/csv": ".csv",
    "application/vnd.ms-excel": ".xls",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/xml": ".xml",
    "text/xml": ".xml",
    "application/zip": ".zip",
}


class DownloadManifest(BaseModel):
    url: str
    final_url: str | None = None
    path: str | None = None
    filename: str | None = None
    status_code: int | None = None
    content_type: str | None = None
    content_length: int | None = None
    bytes_written: int = 0
    dry_run: bool = False
    resource_id: str | None = None
    format: str | None = None


def safe_filename(value: str) -> str:
    value = unquote(value).strip().replace("/", "_").replace("\\", "_")
    value = re.sub(r"[\x00-\x1f]+", "", value)
    return value or "downloaded-file"


def content_disposition_filename(header_value: str | None) -> str | None:
    if not header_value:
        return None
    message = Message()
    message["content-disposition"] = header_value
    params = message.get_params(header="content-disposition", unquote=True)
    for key, value in params:
        if key.lower() in {"filename*", "filename"} and value:
            if isinstance(value, tuple):
                _, _, value = value
            return safe_filename(str(value))
    return None


def extension_from_url(url: str) -> str | None:
    suffix = Path(urlparse(url).path).suffix
    return suffix if suffix else None


def infer_extension(format_value: str | None, url: str | None, content_type: str | None) -> str:
    if format_value:
        ext = FORMAT_EXTENSIONS.get(format_value.upper())
        if ext:
            return ext
    if url:
        ext = extension_from_url(url)
        if ext:
            return ext
    if content_type:
        media_type = content_type.split(";", 1)[0].strip().lower()
        ext = CONTENT_TYPE_EXTENSIONS.get(media_type)
        if ext:
            return ext
    return ".bin"


def choose_filename(
    *,
    explicit_filename: str | None,
    content_disposition: str | None,
    resource_id: str | None,
    format_value: str | None,
    url: str,
    content_type: str | None,
) -> str:
    if explicit_filename:
        return safe_filename(explicit_filename)
    disposition_filename = content_disposition_filename(content_disposition)
    if disposition_filename:
        return disposition_filename
    ext = infer_extension(format_value, url, content_type)
    if resource_id:
        return safe_filename(resource_id + ext)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"estat-file-{timestamp}{ext}"


def write_manifest(path: Path, manifest: DownloadManifest) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(manifest.model_dump(), handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True, help="Selected RESOURCES.RESOURCE.URL value.")
    parser.add_argument("--dest", type=Path, default=Path("."), help="Destination directory.")
    parser.add_argument("--filename", help="Override output filename.")
    parser.add_argument("--resource-id", help="Resource/statistical table ID for fallback filename.")
    parser.add_argument("--format", dest="format_value", help="FORMAT value for extension inference.")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Resolve headers and filename without writing the file.")
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--manifest", type=Path, help="Manifest path. Defaults to <file>.manifest.json.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.dest.mkdir(parents=True, exist_ok=True)

    with httpx.Client(timeout=args.timeout, follow_redirects=True) as client:
        if args.dry_run:
            response = client.head(args.url)
            if response.status_code in {405, 403}:
                response = client.get(args.url, headers={"Range": "bytes=0-0"})
        else:
            response = client.get(args.url)
        response.raise_for_status()

    content_type = response.headers.get("content-type")
    filename = choose_filename(
        explicit_filename=args.filename,
        content_disposition=response.headers.get("content-disposition"),
        resource_id=args.resource_id,
        format_value=args.format_value,
        url=str(response.url),
        content_type=content_type,
    )
    output_path = args.dest / filename
    if output_path.exists() and not args.overwrite and not args.dry_run:
        raise SystemExit(f"Refusing to overwrite existing file: {output_path}")

    bytes_written = 0
    if not args.dry_run:
        output_path.write_bytes(response.content)
        bytes_written = len(response.content)

    manifest = DownloadManifest(
        url=args.url,
        final_url=str(response.url),
        path=str(output_path),
        filename=filename,
        status_code=response.status_code,
        content_type=content_type,
        content_length=int(response.headers["content-length"]) if response.headers.get("content-length", "").isdigit() else None,
        bytes_written=bytes_written,
        dry_run=args.dry_run,
        resource_id=args.resource_id,
        format=args.format_value,
    )
    manifest_path = args.manifest or output_path.with_suffix(output_path.suffix + ".manifest.json")
    write_manifest(manifest_path, manifest)

    print(f"path={output_path}")
    print(f"manifest={manifest_path}")
    print(f"bytes_written={bytes_written}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
