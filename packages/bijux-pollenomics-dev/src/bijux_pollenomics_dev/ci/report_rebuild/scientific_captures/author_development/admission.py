"""Admit a genuinely executed author LOVE development fold without refitting."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time
from typing import Any

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry

from ...contracts import JsonObject, ReportRebuildError, require_relative_path
from ...ownership import _regular_confined_file
from ...retained_source import read_source_path, source_revision
from ...retained_source.objects import hexadecimal, physical, query
from ..author_love_starts import BASELINE, BASELINE_SHA256
from ..optimizer_inputs.withheld_fold import validate_saved_outputs

PREFIX = "docs/report/pollen-reconstruction/author-lra-constrained/development-fold/"
OWNER = "pollen-reconstruction/author-lra-constrained/development-fold/report-products"
AUTHORITY = "reports/science/source-cohorts/author-love-development-fold.json"
AUTHORITY_SHA256: str | None = (
    "4d3a460c94fefaf19641c77fef465bb35abd0bd8e46b7251d1def9356d2bef37"
)
INPUT_PREFIX = "data/method-certification/author-optimizer-diagnostic-source-capture/executions/optimizer-diagnostics/controlled-inputs/artifacts/science/current-author-development-inputs/constrained-inputs/"
ORIGINAL_SOURCE_REVISION = "f0383c0bfcbbb7baac3f1cd974052550896f0867"
GENERATED_SOURCE = (
    "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/_build_version.py"
)

RUNTIME_SOURCE = (
    "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/_build_version.py"
)
RUNTIME_CAPTURE_MEMBER = (
    "data/method-certification/author-optimizer-diagnostic-source-capture/executions/optimizer-diagnostics/first-party-inputs/"
    + RUNTIME_SOURCE
)
RUNTIME_SHA256 = "84040f998392398c91779befcbac6807d107b3d1c62a57e4b440dbf1fcc680c5"
RUNTIME_BYTES = 539


def _read(repository: Path, name: str, expected: str, size: int) -> bytes:
    if name == RUNTIME_SOURCE:
        if expected != RUNTIME_SHA256 or type(size) is not int or size != RUNTIME_BYTES:
            raise ReportRebuildError("Author LOVE generated source identity differs")
        raw = read_source_path(repository, RUNTIME_CAPTURE_MEMBER)
        if len(raw) != size or hashlib.sha256(raw).hexdigest() != expected:
            raise ReportRebuildError("Author LOVE generated source bytes differ")
        return raw
    path = _regular_confined_file(repository, name, "author LOVE development evidence")
    if (
        path.stat().st_nlink != 1
        or path.stat().st_size != size
        or not 0 <= size <= 16 * 1024**2
    ):
        raise ReportRebuildError(
            "Author LOVE development evidence size or alias differs"
        )
    raw = path.read_bytes()
    if len(raw) != size or hashlib.sha256(raw).hexdigest() != expected:
        raise ReportRebuildError("Author LOVE development evidence identity differs")
    return raw


def _validate_original_sources(repository: Path, sources: list[dict[str, Any]]) -> str:
    """Authenticate the executed source epoch without admitting live numerical reuse."""
    if (
        len(sources) != 76
        or any(
            set(row) != {"path", "sha256", "bytes"}
            or type(row["path"]) is not str
            or not hexadecimal(row["sha256"], 64)
            or type(row["bytes"]) is not int
            or not 0 <= row["bytes"] <= 16 * 1024**2
            for row in sources
        )
        or len({row["path"] for row in sources}) != 76
        or GENERATED_SOURCE not in {row["path"] for row in sources}
        or sum(row["bytes"] for row in sources) > 16 * 1024**2
    ):
        raise ReportRebuildError("Exact original author development sources required")
    for row in sources:
        require_relative_path(row["path"], "original author development source")
    physical(repository)
    physical(repository / ".git")
    grafts = repository / ".git/info/grafts"
    physical(grafts)
    if grafts.exists():
        raise ReportRebuildError("Original author source ancestry cannot use grafts")
    revision = source_revision(repository, ORIGINAL_SOURCE_REVISION)
    deadline = time.monotonic() + 180
    query(
        repository,
        ["merge-base", "--is-ancestor", revision, "HEAD"],
        0,
        deadline,
    )
    tracked = {row["path"]: row for row in sources if row["path"] != GENERATED_SOURCE}
    tree = query(
        repository,
        ["ls-tree", "-r", "-l", "-z", revision, "--", *sorted(tracked)],
        128 * 1024,
        deadline,
    )
    seen = set()
    for record in tree.split(b"\0"):
        if not record:
            continue
        identity, path = record.split(b"\t", 1)
        mode, kind, blob, size = identity.decode("ascii").split()
        name = path.decode("utf-8")
        if (
            mode not in {"100644", "100755"}
            or kind != "blob"
            or name not in tracked
            or name in seen
            or not hexadecimal(blob, 40)
            or int(size) != tracked[name]["bytes"]
        ):
            raise ReportRebuildError("Original author development Git source differs")
        seen.add(name)
        raw = query(repository, ["cat-file", "blob", blob], int(size) + 1, deadline)
        if (
            len(raw) != int(size)
            or hashlib.sha256(raw).hexdigest() != tracked[name]["sha256"]
        ):
            raise ReportRebuildError("Original author development source bytes differ")
    if seen != set(tracked):
        raise ReportRebuildError(
            "Original author development source population differs"
        )
    generated = next(row for row in sources if row["path"] == GENERATED_SOURCE)
    raw = read_source_path(
        repository, "data/atlas/source-view-capture/source/" + GENERATED_SOURCE
    )
    if (
        len(raw) != generated["bytes"]
        or hashlib.sha256(raw).hexdigest() != generated["sha256"]
    ):
        raise ReportRebuildError("Original author development version bytes differ")
    return revision


def validated_author_development_capture(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Authenticate saved products and their original execution, without refitting."""
    declared = [row for row in owners if row.get("owner_id") == OWNER]
    if not declared and not (repository / AUTHORITY).exists():
        return (), {}
    if AUTHORITY_SHA256 is None:
        raise ReportRebuildError(
            "Actual author development execution authority required"
        )
    authority_path = _regular_confined_file(
        repository, AUTHORITY, "author development authority"
    )
    authority = json.loads(
        _read(repository, AUTHORITY, AUTHORITY_SHA256, authority_path.stat().st_size)
    )
    execution = authority["execution"]
    if (
        authority.get("schema_version")
        != "author-love-development-execution-authority.v1"
        or authority.get("source_candidate") != ORIGINAL_SOURCE_REVISION
        or execution.get("candidate") != authority.get("source_candidate")
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
        raise ReportRebuildError(
            "Actual successful author development source/runtime execution required"
        )
    products = authority["products"]
    names = sorted(PREFIX + row["name"] for row in products.values())
    if (
        len(declared) != 1
        or declared[0].get("role") != "retained_source"
        or declared[0].get("paths") != names
        or declared[0].get("producer_paths") != []
        or declared[0].get("producer_inputs") != []
    ):
        raise ReportRebuildError("Exact author development product ownership required")
    protocol_pin = authority["protocol"]
    protocol = json.loads(
        _read(
            repository,
            PREFIX + "protocol.json",
            protocol_pin["sha256"],
            protocol_pin["bytes"],
        )
    )
    for source in authority["producer_sources"]:
        _read(repository, PREFIX + source["name"], source["sha256"], source["bytes"])
    storage_revision = _validate_original_sources(repository, protocol["source_pins"])
    bodies: dict[str, bytes] = {}
    pins: dict[str, dict[str, Any]] = {}
    accepted_entries = []
    for role, row in products.items():
        name = PREFIX + row["name"]
        reference = row["original_reference"]
        entry = tracked_by_path.get(name)
        if (
            entry is None
            or entry.sha256 != reference["sha256"]
            or entry.size != reference["bytes"]
        ):
            raise ReportRebuildError("Author development Git product identity differs")
        bodies[role] = _read(repository, name, reference["sha256"], reference["bytes"])
        pins[role] = reference
        accepted_entries.append(entry)
    for reference in protocol["prior_evidence"].values():
        _read(repository, reference["path"], reference["sha256"], reference["bytes"])
    for role, old in (("prior_report", "report"), ("prior_trials", "trials")):
        reference = protocol["prior_evidence"][old]
        bodies[role] = _read(
            repository, reference["path"], reference["sha256"], reference["bytes"]
        )
        pins[role] = reference
    baseline_path = _regular_confined_file(
        repository, BASELINE, "author optimizer baseline"
    )
    bodies["baseline"] = _read(
        repository, BASELINE, BASELINE_SHA256, baseline_path.stat().st_size
    )
    pins["baseline"] = {
        "path": BASELINE,
        "sha256": BASELINE_SHA256,
        "bytes": len(bodies["baseline"]),
    }
    for reference in protocol["before_prediction_freeze"]:
        _read(
            repository,
            INPUT_PREFIX + reference["path"],
            reference["sha256"],
            reference["bytes"],
        )
    if "prediction_freeze" in products:
        reference = protocol["outcome"]
        bodies["outcome"] = _read(
            repository,
            INPUT_PREFIX + reference["path"],
            reference["sha256"],
            reference["bytes"],
        )
        pins["outcome"] = reference
    result = validate_saved_outputs(bodies, pins, protocol)
    return tuple(accepted_entries), {
        "owner_id": OWNER,
        "authority_sha256": AUTHORITY_SHA256,
        "executed_source_candidate": authority["source_candidate"],
        "original_source_storage_revision": storage_revision,
        "source_authentication_role": "original_execution_only",
        "current_source_or_numerical_reuse_claimed": False,
        **result,
    }
