"""Confine a source replay while preserving the normalized registry's refusal."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

BASE = Path(
    "/opt/homebrew/Cellar/python@3.11/3.11.13/Frameworks/Python.framework/Versions/3.11/bin/python3.11"
)
BASE_SHA = "92019a8331209d7247702193bbdfbe359807d7ee1df92566fcf31935f6b273d4"
PREFIX = BASE.parents[1]
SOURCE = Path(__file__).resolve().parent
ROOT = SOURCE.parents[2]
MODULES = {
    "contracts.py",
    "runtime.py",
    "common_runner.py",
    "execute_source.py",
    "prepare.py",
    "run.py",
    "observe.py",
    "check_contracts.py",
}


def require(value: object, reason: str) -> None:
    if not value:
        raise ValueError(reason)


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def pin(path: Path) -> dict[str, Any]:
    require(
        path.is_file() and not path.is_symlink(),
        "Physical regular input required: " + str(path),
    )
    return {"path": str(path), "sha256": sha(path), "bytes": path.stat().st_size}


def exact(left: Any, right: Any) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(
            exact(left[k], right[k]) for k in left
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(
            exact(a, b) for a, b in zip(left, right, strict=True)
        )
    return bool(left == right)


def load(path: Path) -> Any:
    def pairs(rows: list[tuple[str, Any]]) -> dict[str, Any]:
        require(len(rows) == len({k for k, _ in rows}), "Duplicate JSON key")
        return dict(rows)

    def constant(value: str) -> None:
        raise ValueError("Nonfinite JSON constant: " + value)

    return json.loads(
        path.read_bytes(), object_pairs_hook=pairs, parse_constant=constant
    )


def dump(path: Path, value: Any) -> None:
    require(not path.is_symlink(), "Receipt alias refused")
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    )


def confined_output(path: Path, *, absent: bool = False) -> Path:
    path = path.absolute()
    require(
        path == path.resolve()
        and path.is_relative_to(ROOT / "artifacts")
        and not any(p.is_symlink() for p in (path, *path.parents)),
        "Physical artifact output required",
    )
    if absent:
        require(not path.exists(), "Fresh output required")
    return path


def source_namespace() -> None:
    for p in SOURCE.iterdir():
        require(
            not p.is_symlink() and (p.is_file() or p.is_dir()),
            "Alias/special controller member",
        )
        require(
            not p.is_dir() or p.name == "preflight",
            "Unexpected controller import directory",
        )
        if p.suffix in {".py", ".pyc", ".so"}:
            require(p.name in MODULES, "Unexpected importable controller")


def validate_scope(report: dict[str, Any]) -> None:
    for k, v in {
        "schema_version": "svar-normalized-export-custody.v1",
        "export_generated_on": "2026-09-08",
        "export_lake_count_claim": 40565,
        "review_source_lake_count_claim": 40523,
        "review_subset_feature_count": 99,
        "current_ranked_candidate_count": 0,
        "source_population_reconciled": False,
        "raw_wfs_capture_bound_to_export": False,
        "qualified_review_accepted": False,
        "ranking_admitted": False,
    }.items():
        require(exact(report[k], v), "Source/refusal scope differs: " + k)
    require(
        len(report["inputs"]) == 6, "Exact private/public input membership required"
    )


def frozen_pin_union(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep original declared identities; an overlapping role cannot replace a pin."""
    by_path: dict[str, dict[str, Any]] = {}
    for row in rows:
        require(set(row) == {"path", "sha256", "bytes"}, "Pin fields differ")
        require(
            type(row["path"]) is str and type(row["bytes"]) is int, "Pin types differ"
        )
        previous = by_path.get(row["path"])
        require(previous is None or exact(previous, row), "Conflicting input roles")
        by_path[row["path"]] = dict(row)
    return [by_path[key] for key in sorted(by_path)]


def verify_frozen_pins(rows: list[dict[str, Any]]) -> None:
    """Compare against the frozen census rather than recording changed bytes anew."""
    for row in rows:
        require(
            exact(pin(Path(row["path"])), row), "Frozen input changed: " + row["path"]
        )


def output_products(output: Path) -> list[dict[str, Any]]:
    """Count every regular output and refuse every alias or special entry."""
    products = []
    for path in sorted(output.rglob("*")):
        require(
            not path.is_symlink() and (path.is_file() or path.is_dir()),
            "Output alias/special refused",
        )
        if path.is_file():
            products.append(pin(path))
    return products
