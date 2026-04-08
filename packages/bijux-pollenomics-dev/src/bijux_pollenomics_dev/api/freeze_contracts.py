"""Repository API freeze checks for schema, pinned JSON, and hash digests."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import yaml


def _load_schema(path: Path) -> dict:
    return yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader) or {}


def _canonical_json_text(payload: dict) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


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

        canonical = _canonical_json_text(_load_schema(schema_path))
        pinned_text = pinned_path.read_text(encoding="utf-8")
        if canonical != pinned_text:
            failures.append(
                f"{package_dir}: pinned_openapi.json does not match schema.yaml"
            )

        digest = hashlib.sha256(pinned_text.encode("utf-8")).hexdigest()
        pinned_digest = _extract_hash_value(hash_path)
        if pinned_digest != digest:
            failures.append(f"{package_dir}: schema.hash does not match pinned_openapi")

    if failures:
        print("API freeze contract violations detected:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    return run(Path.cwd())


if __name__ == "__main__":
    raise SystemExit(main())
