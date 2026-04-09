"""Repository API freeze checks for schema, pinned JSON, and hash digests."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

import yaml


def _load_artifact(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        return json.loads(text)
    return yaml.safe_load(text)


def _canonicalize(payload: Any) -> Any:
    return json.loads(json.dumps(payload, sort_keys=True))


def _extract_hash_value(path: Path) -> str | None:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("sha256:"):
            return line.split(":", 1)[1].strip()
    return None


def run(repo_root: Path) -> int:
    failures: list[str] = []
    schema_paths = sorted((repo_root / "apis").glob("*/v1/schema.yaml"))
    if not schema_paths:
        print("No OpenAPI schemas found under apis/*/v1/schema.yaml", file=sys.stderr)
        return 1

    for schema_path in schema_paths:
        package_dir = schema_path.parent.parent.name
        pinned_path = schema_path.with_name("pinned_openapi.json")
        hash_path = schema_path.with_name("schema.hash")
        if not pinned_path.exists():
            failures.append(f"{package_dir}: missing pinned_openapi.json")
            continue
        if not hash_path.exists():
            failures.append(f"{package_dir}: missing schema.hash")
            continue

        expected = _canonicalize(_load_artifact(schema_path))
        actual = _canonicalize(_load_artifact(pinned_path))
        if expected != actual:
            failures.append(
                f"{package_dir}: pinned_openapi.json does not match schema.yaml"
            )

        digest = hashlib.sha256(
            schema_path.read_text(encoding="utf-8").encode("utf-8")
        ).hexdigest()
        schema_digest = _extract_hash_value(hash_path)
        if schema_digest != digest:
            failures.append(f"{package_dir}: schema.hash does not match schema.yaml")

    if failures:
        print("API freeze contract violations detected:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate checked-in API freeze contracts for a repository root."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root that contains the apis/ contract tree.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return run(args.repo_root.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
