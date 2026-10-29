"""Confine source-bound Swedish direct-pollen preparation and fixed-baseline replay."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
SOURCE = Path(__file__).resolve().parent
FAMILIES = ("swedish-lake-transfer", "swedish-neotoma-holdout")
POLICY = "configs/ci/report-ownership.json"
PRIVATE = Path("/Users/bijan/bijux/-bijux-pollenomics-data/landclim/author-reference")
LOOKUP = PRIVATE / "author/LANDCLIM.ALLEUROPE.taxa.LUT.080219.csv"
MODULES = {
    "contracts.py",
    "independent.py",
    "execute_source.py",
    "observe.py",
    "prepare.py",
    "run.py",
    "check_contracts.py",
    "source_runtime.py",
    "runtime_contracts.py",
    "runtime_guarded_runner.py",
    "common_runner.py",
}
PREPARED = (
    "input-manifest.json",
    "inputs/metadata-SE.json.gz",
    "inputs/training-SE.json.gz",
    "sealed-outcomes/outcomes-SE.json.gz",
)
PREDICTED = ("predictions-SE.json.gz",)
SCORED = (
    "coverage.csv",
    "report.json",
    "scores.csv",
    "site-scores.csv",
    "taxon-diagnostics.csv",
)


def report(family: str) -> str:
    require(family in FAMILIES, "Unknown Swedish study")
    return "docs/report/regions/nordic/" + family


def producer(family: str) -> str:
    require(family in FAMILIES, "Unknown Swedish study")
    return (
        "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/"
        + family.replace("-", "_")
        + ".py"
    )


PACKAGE_ROOTS = [
    ROOT / "packages" / name / "src"
    for name in (
        "bijux-pollenomics",
        "bijux-pollenomics-dev",
        "bijux-pollenomics-lra",
        "pollenomics",
    )
]


def require(value: object, message: str) -> None:
    if not value:
        raise ValueError(message)


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def pin(path: Path) -> dict[str, Any]:
    require(
        path.is_file()
        and path.is_absolute()
        and path == path.resolve()
        and not any(p.is_symlink() for p in (path, *path.parents)),
        "Physical regular input required: " + str(path),
    )
    return {"path": str(path), "sha256": sha(path), "bytes": path.stat().st_size}


def exact(a: Any, b: Any) -> bool:
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(exact(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(
            (exact(x, y) for x, y in zip(a, b, strict=True))
        )
    return bool(a == b)


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
    require(
        not path.exists() and (not path.is_symlink()),
        "No receipt replacement: " + str(path),
    )
    with path.open("x") as stream:
        stream.write(json.dumps(value, indent=2, allow_nan=False) + "\n")


def output_root(path: Path, *, absent: bool = False) -> Path:
    require(
        path.is_absolute()
        and path == path.resolve()
        and path.is_relative_to(ROOT / "artifacts")
        and (not any(p.is_symlink() for p in (path, *path.parents))),
        "Physical normalized artifact output required",
    )
    if absent:
        require(not path.exists() and (not path.is_symlink()), "Absent output required")
    return path


def namespace() -> None:
    for p in SOURCE.iterdir():
        require(
            not p.is_symlink() and (p.is_dir() or p.is_file()),
            "Alias/special controller entry",
        )
        require(
            not p.is_dir() or p.name == "preflight", "Unexpected controller directory"
        )
        if p.suffix in {".py", ".pyc", ".so"}:
            require(p.name in MODULES, "Unexpected importable controller")


def identity() -> dict[str, str]:

    def git(*args: str) -> bytes:
        return subprocess.check_output(["git", *args], cwd=ROOT)

    return {
        "candidate": git("rev-parse", "HEAD").decode().strip(),
        "status": git("status", "--porcelain").decode(),
        "tracked_inventory_sha256": hashlib.sha256(
            git("ls-files", "-s", "-z")
        ).hexdigest(),
    }


def union(*groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for group in groups:
        for row in group:
            require(
                set(row) == {"path", "sha256", "bytes"} and type(row["bytes"]) is int,
                "Malformed expected pin",
            )
            name = row["path"]
            require(
                name not in rows or exact(rows[name], row),
                "Conflicting original input pin: " + name,
            )
            rows[name] = dict(row)
    return [rows[k] for k in sorted(rows)]


def first_party_snapshot() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    from runtime_contracts import namespace_snapshot

    trees = []
    files: list[dict[str, Any]] = []
    for root in PACKAGE_ROOTS:
        tree = namespace_snapshot(root, [])
        require(
            all(v["kind"] != "symlink" for v in tree["entries"].values()),
            "First-party source alias is not declared",
        )
        trees.append(tree)
        files.extend(
            (
                pin(root / name)
                for name, v in tree["entries"].items()
                if v["kind"] == "file"
            )
        )
    return (trees, files)


def verify_inputs(plan: dict[str, Any]) -> None:
    from runtime_contracts import verify_absences, verify_base_namespaces, verify_pin

    namespace()
    for row in plan["input_pins"]:
        verify_pin(row)
    verify_base_namespaces(plan["first_party_namespaces"])
    verify_absences(plan["absent_input_paths"])
