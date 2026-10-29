"""Admit finite executed author LOVE cohort products without fitting models."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry

from ...contracts import JsonObject, ReportRebuildError
from ...ownership import _regular_confined_file
from ..author_development.admission import INPUT_PREFIX, _read
from ..optimizer_inputs.cohort_outputs import validate_saved_outputs

PREFIX = "docs/report/pollen-reconstruction/author-lra-constrained/cohort-development/"
OWNER = (
    "pollen-reconstruction/author-lra-constrained/cohort-development/report-products"
)
AUTHORITY = "reports/science/source-cohorts/author-love-cohort-development.json"
AUTHORITY_SHA256: str | None = (
    "41ba3a2d8765d9cd9feaf86a7d6c9232bfc1898e12ffb0da523d7a235b3e0c23"
)
PRODUCTS = {
    "report": "report.json",
    "training": "training.json",
    "trials": "trials.jsonl",
    "prediction_freeze": "prediction-freeze.json",
    "outcome_access": "outcome-access.jsonl",
}


def validated_author_cohort_capture(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Authenticate exact ownership, execution, input closure and saved arithmetic."""
    declared = [row for row in owners if row.get("owner_id") == OWNER]
    if not declared and not (repository / AUTHORITY).exists():
        return (), {}
    if AUTHORITY_SHA256 is None:
        raise ReportRebuildError("Actual author cohort execution authority required")
    authority_path = _regular_confined_file(
        repository, AUTHORITY, "author cohort authority"
    )
    authority = json.loads(
        _read(repository, AUTHORITY, AUTHORITY_SHA256, authority_path.stat().st_size)
    )
    execution = authority["execution"]
    candidate = authority.get("source_candidate")
    if (
        authority.get("schema_version") != "author-love-cohort-execution-authority.v1"
        or not isinstance(candidate, str)
        or re.fullmatch(r"[a-f0-9]{40}", candidate) is None
        or execution.get("candidate") != candidate
        or any(
            type(execution.get(key)) is not int or execution[key] != 0
            for key in ("native_exit", "common_exit", "outer_exit")
        )
        or any(
            execution.get(key) is not True
            for key in (
                "source_before_after_equal",
                "inputs_before_after_equal",
                "runtime_before_after_equal",
            )
        )
    ):
        raise ReportRebuildError("Actual successful author cohort execution required")
    products = authority["products"]
    names = sorted(PREFIX + name for name in PRODUCTS.values())
    if (
        set(products) != set(PRODUCTS)
        or any(products[role].get("name") != name for role, name in PRODUCTS.items())
        or len(declared) != 1
        or declared[0].get("role") != "retained_source"
        or declared[0].get("paths") != names
        or declared[0].get("producer_paths") != []
        or declared[0].get("producer_inputs") != []
    ):
        raise ReportRebuildError("Exact author cohort five-product ownership required")
    protocol_pin = authority["protocol"]
    protocol = json.loads(
        _read(
            repository,
            PREFIX + "protocol.json",
            protocol_pin["sha256"],
            protocol_pin["bytes"],
        )
    )
    sources = authority["producer_sources"]
    if len(sources) != 2 or {row["name"] for row in sources} != {
        "replay.py",
        "pool.py",
    }:
        raise ReportRebuildError("Exact cohort producer and pool source required")
    for row in sources:
        _read(repository, PREFIX + row["name"], row["sha256"], row["bytes"])
    helper = next(row for row in sources if row["name"] == "pool.py")
    if protocol["pool_helper"] != {
        "path": "pool.py",
        "sha256": helper["sha256"],
        "bytes": helper["bytes"],
    }:
        raise ReportRebuildError("Cohort pool helper differs from executed protocol")
    if (
        len(protocol["source_pins"]) != 77
        or len(protocol["prior_evidence"]) != 8
        or len(protocol["inputs"]) != 37
    ):
        raise ReportRebuildError(
            "Finite cohort77 source/eight prior/37 input contract required"
        )
    for row in protocol["source_pins"]:
        _read(repository, row["path"], row["sha256"], row["bytes"])
    bodies: dict[str, bytes] = {}
    pins: dict[str, dict[str, Any]] = {}
    accepted = []
    for role, row in products.items():
        name = PREFIX + row["name"]
        reference = row["original_reference"]
        entry = tracked_by_path.get(name)
        if (
            entry is None
            or entry.sha256 != reference["sha256"]
            or entry.size != reference["bytes"]
        ):
            raise ReportRebuildError("Author cohort Git product identity differs")
        bodies[role] = _read(repository, name, reference["sha256"], reference["bytes"])
        pins[role] = reference
        accepted.append(entry)
    for role, row in protocol["prior_evidence"].items():
        bodies[role] = _read(repository, row["path"], row["sha256"], row["bytes"])
        pins[role] = row
    inputs = {
        row["path"]: _read(
            repository, INPUT_PREFIX + row["path"], row["sha256"], row["bytes"]
        )
        for row in protocol["inputs"]
    }
    if len(inputs) != 37:
        raise ReportRebuildError("Cohort input membership must be unique")
    result = validate_saved_outputs(bodies, pins, protocol, inputs)
    return tuple(accepted), {
        "owner_id": OWNER,
        "authority_sha256": AUTHORITY_SHA256,
        "executed_source_candidate": candidate,
        **result,
    }
