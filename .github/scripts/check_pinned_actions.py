#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

USE_PATTERN = re.compile(r"^\s*-\s*uses:\s*([^\s#]+)")
PINNED_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40}$")


def gather_workflow_files(raw_paths: list[str]) -> tuple[list[Path], list[str]]:
    files: list[Path] = []
    missing: list[str] = []
    seen: set[Path] = set()

    for raw_path in raw_paths:
        path = Path(raw_path)
        if not path.exists():
            missing.append(raw_path)
            continue
        if path.is_dir():
            for item in sorted(path.glob("*.yml")) + sorted(path.glob("*.yaml")):
                resolved = item.resolve()
                if resolved in seen:
                    continue
                seen.add(resolved)
                files.append(item)
            continue

        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        files.append(path)

    return files, missing


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: check_pinned_actions.py <workflow-path> [<workflow-path> ...]", file=sys.stderr)
        return 2

    workflow_files, missing_paths = gather_workflow_files(sys.argv[1:])
    violations: list[str] = []
    for missing in missing_paths:
        violations.append(f"missing path: {missing}")

    for path in workflow_files:
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            match = USE_PATTERN.match(line)
            if not match:
                continue

            reference = match.group(1)
            if reference.startswith("./"):
                continue
            if reference.startswith("docker://"):
                continue
            if PINNED_PATTERN.match(reference):
                continue
            violations.append(f"{path}:{line_number}: unpinned action reference '{reference}'")

    if violations:
        print("Found unpinned action references:", file=sys.stderr)
        for violation in violations:
            print(f"  - {violation}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
