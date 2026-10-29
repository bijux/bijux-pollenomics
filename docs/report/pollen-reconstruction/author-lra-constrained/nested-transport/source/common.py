"""Finite scientific identities and exclusive files for the nested transport diagnostic."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import runpy
from typing import Any

METHODS = ("gpm neutral", "gpm unstable", "lsm unstable", "lsm unstable low", "1overd")
SOURCE_NAMES = {"common.py", "requests.py", "training.py", "selection.py", "replay.py"}
PREFIX = "docs/report/pollen-reconstruction/author-lra-constrained/"


def decode(raw: bytes) -> Any:
    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        result = {}
        for key, value in values:
            if key in result:
                raise ValueError("Duplicate scientific metadata key")
            result[key] = value
        return result

    def refuse(_value: str) -> None:
        raise ValueError("Nonfinite scientific metadata")

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=refuse)


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def checked(root: Path, row: dict[str, Any]) -> bytes:
    name = Path(row["path"])
    path = root / name
    if (
        ".." in name.parts
        or any(p.is_symlink() for p in (path, *path.parents))
        or not path.is_file()
        or path.stat().st_nlink != 1
    ):
        raise ValueError("Physical declared scientific member required")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != row["sha256"] or len(raw) != row["bytes"]:
        raise ValueError("Scientific member changed: " + str(path))
    return raw


def write(path: Path, value: Any) -> dict[str, Any]:
    raw = (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return {
        "path": str(path),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
    }


def module(directory: Path, protocol: dict[str, Any], name: str) -> dict[str, Any]:
    row = next(row for row in protocol["execution_sources"] if row["path"] == name)
    checked(directory, row)
    return runpy.run_path(str(directory / name))


def guard(
    repository: Path, prepared: Path, directory: Path, protocol: dict[str, Any]
) -> None:
    if (
        protocol["schema_version"] != "author-love-nested-transport-protocol.v1"
        or tuple(protocol["methods"]) != METHODS
        or protocol["counts"]
        != {
            "outer_folds": 15,
            "inner_folds": 210,
            "unique_requests_per_method": 39,
            "logical_requests_per_method": 2715,
            "prior_attempts_reused": 1728,
            "nominal_new_attempts": 768,
            "additional_transport_new_attempts": 9984,
            "max_new_attempts": 10752,
            "candidate_prediction_slots": 3375,
            "selected_outer_prediction_slots": 45,
        }
        or protocol["optimizer"]
        != {
            "rings": 2,
            "starts_per_ring": 32,
            "maxiter": 300,
            "max_search_evaluations": 16000,
            "ftol": 1e-8,
            "seed": 7,
        }
    ):
        raise ValueError("Exact finite scientific transport protocol required")
    if {p.name for p in directory.iterdir()} != SOURCE_NAMES or any(
        p.is_symlink() or not p.is_file() for p in directory.iterdir()
    ):
        raise ValueError("Exact five-source diagnostic namespace required")
    for row in protocol["execution_sources"]:
        checked(directory, row)
    if (
        len(protocol["execution_sources"]) != 5
        or {row["path"] for row in protocol["execution_sources"]} != SOURCE_NAMES
    ):
        raise ValueError("Exact five-source identities required")
    if (
        len(protocol["inputs"]) != 37
        or {p.name for p in prepared.iterdir()}
        != {row["path"] for row in protocol["inputs"]}
        or any(Path(row["path"]).name != row["path"] for row in protocol["inputs"])
    ):
        raise ValueError("Exact original37 scientific input namespace required")
    for row in protocol["inputs"]:
        checked(prepared, row)
    for row in protocol["source_pins"]:
        checked(repository, row)
    for row in protocol["prior_evidence"].values():
        checked(repository, row)
    checked(repository, protocol["source_snapshot"])
    from importlib.metadata import version

    for name, expected in protocol["versions"].items():
        if version(name) != expected:
            raise ValueError("Qualified numerical/source-engine version changed")
    previous = decode(
        checked(repository, protocol["prior_evidence"]["cohort_protocol"])
    )
    if (
        previous["source_pins"] != protocol["reused_source_pins"]
        or previous["versions"] != protocol["versions"]
        or previous["inputs"] != protocol["inputs"]
        or previous["runtime_reference_sha256"] != protocol["runtime_reference_sha256"]
    ):
        raise ValueError("Prior numeric source/runtime/input equivalence differs")


def libraries(repository: Path) -> dict[str, dict[str, Any]]:
    return {
        name: runpy.run_path(str(repository / PREFIX / path))
        for name, path in {
            "original": "optimizer-gradient/replay.py",
            "starts": "optimizer-start-sensitivity/replay.py",
            "math": "development-fold/training.py",
            "pool": "cohort-development/pool.py",
            "cohort": "cohort-development/replay.py",
        }.items()
    }
