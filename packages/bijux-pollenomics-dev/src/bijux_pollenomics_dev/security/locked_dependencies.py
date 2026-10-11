"""Audit every registry distribution in the frozen workspace graph."""

from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path
import re
import sys
import tomllib
from typing import Any

from bijux_pollenomics_dev.trusted_process import run_text


def registry_batches(lockfile: Path) -> list[list[tuple[str, str]]]:
    """Keep platform and optional forks while excluding local workspace packages."""
    packages = tomllib.loads(lockfile.read_text(encoding="utf-8")).get("package")
    if not isinstance(packages, list) or not packages:
        raise ValueError("lockfile has no package records")
    versions: dict[str, set[str]] = defaultdict(set)
    for package in packages:
        source = package.get("source", {})
        if "registry" not in source:
            if "editable" in source or "virtual" in source:
                continue
            raise ValueError(f"unsupported locked source: {source}")
        if source["registry"].rstrip("/") != "https://pypi.org/simple":
            raise ValueError(f"unsupported registry source: {source}")
        name = package.get("name")
        version = package.get("version")
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+", name):
            raise ValueError("invalid registry distribution name")
        if not isinstance(version, str) or not re.fullmatch(
            r"[A-Za-z0-9.!+_-]+", version
        ):
            raise ValueError(f"invalid locked version for {name}")
        versions[re.sub(r"[-_.]+", "-", name).lower()].add(version)
    if not versions:
        raise ValueError("lockfile has no registry distributions")
    batches: list[list[tuple[str, str]]] = []
    for name, values in sorted(versions.items()):
        for index, version in enumerate(sorted(values)):
            if index == len(batches):
                batches.append([])
            batches[index].append((name, version))
    return batches


def validate_report(report: Any, expected: list[tuple[str, str]]) -> bool:
    """Reject omitted, skipped or vulnerable entries, including platform forks."""
    dependencies = report.get("dependencies") if isinstance(report, dict) else None
    if not isinstance(dependencies, list):
        return False
    observed: set[tuple[str, str]] = set()
    for dependency in dependencies:
        if not isinstance(dependency, dict):
            return False
        name = dependency.get("name", "")
        version = dependency.get("version", "")
        if not isinstance(name, str) or not isinstance(version, str):
            return False
        pair = (re.sub(r"[-_.]+", "-", name).lower(), version)
        if pair in observed or pair not in expected:
            return False
        observed.add(pair)
        if dependency.get("skip_reason") or dependency.get("vulns") != []:
            return False
    return observed == set(expected)


def run(repo_root: Path) -> int:
    """Query pinned versions directly without installing scientific extras."""
    output = repo_root / "artifacts/security/locked-dependencies"
    output.mkdir(parents=True, exist_ok=True)
    batches = registry_batches(repo_root / "uv.lock")
    accepted = True
    for index, batch in enumerate(batches):
        requirements = output / f"requirements-{index}.txt"
        report = output / f"audit-{index}.json"
        requirements.write_text(
            "".join(f"{name}=={version}\n" for name, version in batch), encoding="utf-8"
        )
        report.unlink(missing_ok=True)
        result = run_text(
            [
                Path(sys.executable).absolute(),
                "-m",
                "pip_audit",
                "--disable-pip",
                "--no-deps",
                "--progress-spinner",
                "off",
                "--cache-dir",
                str(output / "cache"),
                "-r",
                str(requirements),
                "-f",
                "json",
                "-o",
                str(report),
            ],
            cwd=repo_root,
            check=False,
            capture_output=True,
        )
        (output / f"audit-{index}.log").write_text(
            result.stdout + result.stderr, encoding="utf-8"
        )
        try:
            data = json.loads(report.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = None
        accepted = result.returncode == 0 and validate_report(data, batch) and accepted
    count = sum(len(batch) for batch in batches)
    print(
        f"Frozen dependency audit: {count} registry versions, {len(batches)} batches, {'passed' if accepted else 'failed'}"
    )
    return 0 if accepted else 1


def main() -> None:
    """Audit the workspace lockfile from any package invocation directory."""
    root = Path(__file__).resolve().parents[5]
    raise SystemExit(run(root))


if __name__ == "__main__":
    main()
