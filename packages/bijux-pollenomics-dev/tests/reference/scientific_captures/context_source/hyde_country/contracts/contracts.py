"""Confine HYDE modeled country source replay and preserve its refusals."""

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
    "metadata.py",
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
    expected = {
        "schema_version": "hyde-source-reported-nordic-cropland.v1",
        "measure": "HYDE source-reported country cropland area in km2; modeled land use",
        "source_family": "HYDE 3.5 local gbc2025_7apr release",
        "country_codes": {"DK": "208", "FI": "246", "NO": "578", "SE": "752"},
        "source_year_ce_labels": [500, 1000, 1500, 1700, 1900, 2000, 2025],
        "scenarios": ["base", "lower", "upper"],
        "rows": 84,
        "country_years": 28,
        "rights": "Local Yoda metadata and License.txt say CC BY-NC 4.0; README and NetCDF declarations say CC BY 3.0. Derived summary retained under restrictive interpretation; redistribution review pending.",
        "interpretation": "These are native source country totals, not a new grid-country overlay, independent observed vegetation, uncertainty intervals, or pollen covariates. CE labels are retained without BP/NetCDF calendar conversion. The 2025 column exists in these tables while release coverage prose conflicts.",
        "remaining": [
            "unreviewed_grid_variables_and_years",
            "release_rights_reconciliation",
            "time_mapping_for_pollen_study",
            "paired_no_hyde_hyde_ablation",
        ],
    }
    require(set(report) == {*expected, "inputs"}, "Complete HYDE report schema differs")
    for key, value in expected.items():
        require(exact(report[key], value), "HYDE scope differs: " + key)
    rows = report["inputs"]
    require(
        type(rows) is list and len(rows) == 4, "Four source country inputs required"
    )
    require(
        [row["path"] for row in rows]
        == [
            "original/general_files.zip",
            *[
                "original/gbc2025_7apr_" + scenario + "/txt/cropland_c.txt"
                for scenario in ["base", "lower", "upper"]
            ],
        ],
        "Source input order differs",
    )
    for row in rows:
        require(
            set(row) == {"path", "sha256"}
            and type(row["sha256"]) is str
            and len(row["sha256"]) == 64
            and all(c in "0123456789abcdef" for c in row["sha256"]),
            "Source identity differs",
        )


def validate_products(
    actual: dict[str, Any],
    actual_csv: bytes,
    historical: dict[str, Any],
    historical_csv: bytes,
    expected: dict[str, Any],
    expected_csv: bytes,
) -> None:
    """Bind every output value and serialization to source joins and retained products."""
    for report in (actual, historical, expected):
        validate_scope(report)
    require(
        exact(actual, expected) and exact(actual, historical),
        "Complete source-joined report differs",
    )
    require(
        actual_csv == expected_csv == historical_csv,
        "Complete84 source arithmetic CSV bytes differ",
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
