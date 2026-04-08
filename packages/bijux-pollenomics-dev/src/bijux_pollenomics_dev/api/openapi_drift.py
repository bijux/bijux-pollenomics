"""OpenAPI drift checks for repository API contracts."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml


def _load_schema(text: str) -> dict:
    return yaml.safe_load(text) or {}


def _git_show(path: str) -> str | None:
    try:
        return subprocess.check_output(["git", "show", f"HEAD~1:{path}"], text=True)
    except Exception:
        return None


def _extract_fields(schema: dict) -> set[str]:
    fields: set[str] = set()
    components = schema.get("components", {})
    schemas = components.get("schemas", {})
    for name, payload in schemas.items():
        props = (payload or {}).get("properties", {}) or {}
        for prop in props:
            fields.add(f"{name}.{prop}")
    return fields


def run(repo_root: Path) -> int:
    schema_paths = sorted((repo_root / "apis").glob("*/v1/schema.yaml"))
    if not schema_paths:
        print("No OpenAPI schemas found; skipping.")
        return 0

    failures: list[str] = []
    for schema_path in schema_paths:
        rel = schema_path.relative_to(repo_root).as_posix()
        current_schema = _load_schema(schema_path.read_text(encoding="utf-8"))
        previous_text = _git_show(rel)
        if not previous_text:
            continue
        previous_schema = _load_schema(previous_text)
        removed_fields = _extract_fields(previous_schema) - _extract_fields(current_schema)
        if not removed_fields:
            continue
        current_version = (current_schema.get("info") or {}).get("version")
        previous_version = (previous_schema.get("info") or {}).get("version")
        if current_version == previous_version:
            failures.append(f"{rel}: breaking change without version bump")
            for field in sorted(removed_fields):
                failures.append(f"{rel}: removed {field}")

    if failures:
        print("Breaking OpenAPI changes detected:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    return run(Path.cwd())


if __name__ == "__main__":
    sys.exit(main())
