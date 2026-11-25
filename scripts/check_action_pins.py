# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0.4,<7"]
# ///
"""Check immutable references in tracked GitHub workflows and actions."""

import re
import subprocess
import sys
from pathlib import Path
from typing import Iterator

import yaml


ACTION_SHA = re.compile(r"[^/@\s]+/[^@\s]+@[0-9a-f]{40}", re.IGNORECASE)
IMAGE_DIGEST = re.compile(r"[^@\s]+@sha256:[0-9a-f]{64}")
WORKFLOWS = Path(".github/workflows")


def uses_reference(value: str) -> bool:
    if value.startswith("./"):
        return True
    if value.startswith("docker://"):
        return bool(IMAGE_DIGEST.fullmatch(value.removeprefix("docker://")))
    return bool(ACTION_SHA.fullmatch(value))


def check_steps(steps: list, prefix: str) -> Iterator[str]:
    for index, step in enumerate(steps, 1):
        if "uses" in step and not uses_reference(step["uses"]):
            yield f"{prefix}[{index}].uses needs an immutable ref: {step['uses']}"


def image_uses_digest(image: str) -> bool:
    return bool(IMAGE_DIGEST.fullmatch(image.removeprefix("docker://")))


def check_workflow(document: dict) -> Iterator[str]:
    for name, job in document.get("jobs", {}).items():
        location = f"jobs.{name}"
        if "uses" in job and not uses_reference(job["uses"]):
            yield f"{location}.uses needs an immutable ref: {job['uses']}"
        yield from check_steps(job.get("steps", []), f"{location}.steps")

        containers = dict(job.get("services", {}))
        if "container" in job:
            containers["container"] = job["container"]
        for container, definition in containers.items():
            image = definition["image"] if isinstance(definition, dict) else definition
            if not image_uses_digest(image):
                yield f"{location} container {container} needs a digest: {image}"


def check_action(document: dict) -> Iterator[str]:
    run = document.get("runs", {})
    if run.get("using") == "composite":
        yield from check_steps(run.get("steps", []), "runs.steps")
    if run.get("using") == "docker":
        image = run["image"]
        if image.startswith("docker://") and not image_uses_digest(image):
            yield f"runs.image needs a digest: {image}"


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    tracked = subprocess.check_output(
        ["git", "-C", str(root), "ls-files", "-z", "--", "*.yml", "*.yaml"]
    )
    failed = False
    for filename in tracked.decode().split("\0"):
        path = Path(filename)
        if path.parent == WORKFLOWS:
            check = check_workflow
        elif path.name in {"action.yml", "action.yaml"}:
            check = check_action
        else:
            continue
        try:
            document = yaml.load((root / path).read_text(), Loader=yaml.BaseLoader)
            for issue in check(document):
                print(f"{path}: {issue}", file=sys.stderr)
                failed = True
        except (OSError, yaml.YAMLError, TypeError, AttributeError, KeyError) as error:
            print(f"{path}: could not inspect references: {error}", file=sys.stderr)
            failed = True
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
