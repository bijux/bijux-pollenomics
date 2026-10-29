"""Transport eleven completed controlled LRA products without rerunning R or claiming ecology."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry

from ...contracts import JsonObject, ReportRebuildError
from ...ownership import ReportOwnershipError, _regular_confined_file
from .native_execution import (
    FAMILIES,
    ORIGINAL_CANDIDATE,
    ORIGINAL_IDENTITIES,
    _exact,
    _require,
    native_records,
)

CAPTURE = (
    "data/method-certification/controlled-lra-numerical-source-capture/capture.json"
)
CAPTURE_SHA256 = "ca9663b47d791a1f56f77b27067c99ed9c6004ad93349055074ce491a8a82c40"
ASSEMBLY_CANDIDATE = "d027effd6c0ac91512cd586c3a51db987ea46d54"
OWNERS = {
    "method-certification/" + family + "/report-products": family for family in FAMILIES
}


def _object(value: object) -> dict[str, Any]:
    _require(
        isinstance(value, dict) and all(isinstance(k, str) for k in value),
        "Controlled numerical capture record must be an object",
    )
    assert isinstance(value, dict)
    return value


def _name(value: object) -> str:
    _require(
        isinstance(value, str) and bool(value),
        "Controlled numerical member must be a nonempty path",
    )
    assert isinstance(value, str)
    path = PurePosixPath(value)
    _require(
        not path.is_absolute()
        and ".." not in path.parts
        and (path.as_posix() == value)
        and ("\\" not in value),
        "Controlled numerical member escapes its capsule",
    )
    return value


def _file(repository: Path, name: str) -> Path:
    try:
        return _regular_confined_file(
            repository, name, "Controlled numerical retained measurement metadata"
        )
    except (OSError, ReportOwnershipError) as error:
        raise ReportRebuildError(
            "Controlled numerical retained file missing, linked or unconfined"
        ) from error


def _json(path: Path) -> dict[str, Any]:

    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in values:
            _require(key not in value, "Controlled numerical duplicate JSON key")
            value[key] = item
        return value

    try:
        value = json.loads(path.read_bytes(), object_pairs_hook=pairs)
        json.dumps(value, allow_nan=False)
        return _object(value)
    except (OSError, ValueError) as error:
        raise ReportRebuildError(
            "Controlled numerical retained JSON is invalid"
        ) from error


def validated_controlled_lra_comparison_capture(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Admit the exact two bounded report populations from their native source epoch."""
    rows = [row for row in owners if row.get("owner_id") in OWNERS]
    if not any(row.get("role") == "retained_source" for row in rows) and (
        not (repository / CAPTURE).exists()
    ):
        return ((), {})
    _require(
        len(rows) == 2 and {row.get("owner_id") for row in rows} == set(OWNERS),
        "Controlled LRA two-owner membership differs",
    )
    for row in rows:
        family = OWNERS[str(row["owner_id"])]
        expected = sorted(
            "docs/report/method-certification/" + family + "/" + name
            for name in FAMILIES[family]
        )
        _require(
            row.get("role") == "retained_source"
            and row.get("paths") == expected
            and (row.get("producer_paths") == [])
            and (row.get("producer_inputs") == []),
            "Controlled LRA exact owner paths/role differ",
        )
    path = _file(repository, CAPTURE)
    _require(
        hashlib.sha256(path.read_bytes()).hexdigest() == CAPTURE_SHA256,
        "Controlled LRA sealed capsule differs",
    )
    capture = _json(path)
    prefix = path.parent.relative_to(repository).as_posix()
    _require(
        capture.get("schema_version") == "controlled-lra-numerical-source-capture.v1"
        and capture.get("owner_ids") == list(OWNERS)
        and (capture.get("original_execution_candidate") == ORIGINAL_CANDIDATE)
        and (capture.get("metadata_assembly_candidate") == ASSEMBLY_CANDIDATE),
        "Controlled LRA source/metadata epoch differs",
    )
    _exact(capture.get("actual_original_native_stage_exits"), [0, 0, 0])
    _exact(capture.get("member_count"), 2282)
    _require(
        capture.get("runtime_payloads_included") is False
        and capture.get("private_payloads_included") is False
        and (capture.get("historical_execution_proofs_recovered") is False)
        and (capture.get("fresh_ecological_acceptance") == "not_evaluated"),
        "Controlled LRA scope expanded",
    )
    members = _object(capture.get("members"))
    _require(len(members) == 2282, "Controlled LRA member population differs")
    for name, raw in members.items():
        body = _file(repository, prefix + "/" + _name(name))
        record = _object(raw)
        _exact(body.stat().st_size, record.get("bytes"))
        _require(
            hashlib.sha256(body.read_bytes()).hexdigest() == record.get("sha256"),
            "Controlled LRA member bytes differ",
        )
    physical = set()
    for file in path.parent.rglob("*"):
        _require(
            not file.is_symlink() and (file.is_file() or file.is_dir()),
            "Controlled LRA packet alias/special file",
        )
        if file.is_file():
            physical.add(file.relative_to(path.parent).as_posix())
    _require(
        physical == set(members) | {"capture.json"},
        "Controlled LRA complete physical member set differs",
    )
    records = []
    for name, digest in ORIGINAL_IDENTITIES.items():
        original = _file(repository, prefix + "/execution/" + name)
        _require(
            hashlib.sha256(original.read_bytes()).hexdigest() == digest,
            "Controlled LRA original native receipt differs",
        )
        records.append(_json(original))
    plan, common, outer, review = records
    native_records(plan, common, outer, review)
    _exact(
        capture.get("original_execution_receipts"),
        {
            name: {
                "path": str(Path(plan["output"]) / name),
                "sha256": digest,
                "bytes": _file(repository, prefix + "/execution/" + name)
                .stat()
                .st_size,
            }
            for name, digest in ORIGINAL_IDENTITIES.items()
        },
    )
    custody = capture.get("original_input_custody")
    _require(
        isinstance(custody, list) and len(custody) == 44722,
        "Controlled LRA original input membership differs",
    )
    assert isinstance(custody, list)
    _exact([_object(row).get("original") for row in custody], plan.get("input_pins"))
    counts: dict[str, int] = {}
    for raw in custody:
        input_record = _object(raw)
        scope = input_record["scope"]
        _require(isinstance(scope, str), "Controlled LRA custody scope must be text")
        assert isinstance(scope, str)
        counts[scope] = counts.get(scope, 0) + 1
        source = _object(input_record["original"])
        if input_record["member"] is not None:
            _exact(
                members.get(_name(input_record["member"])),
                {key: source[key] for key in ("sha256", "bytes")},
            )
        else:
            _require(
                scope == "runtime_identity_only",
                "Controlled LRA unreviewed input omission",
            )
    _exact(capture.get("original_input_scope_counts"), counts)
    _exact(
        counts,
        {
            "runtime_identity_only": 42484,
            "public_original_source_control_or_evidence": 99,
            "full_declared_first_party_source": 2139,
        },
    )
    _exact(
        capture.get("controlled_limits"),
        {
            "optimizer_cases": 3,
            "cross_evaluation_threshold": 1e-10,
            "known_optimum_gap_threshold": 0.0001,
            "R_iteration_cap_not_convergence": True,
            "paired_cells": 400,
            "paired_finite": 120,
            "paired_missing": 280,
            "paired_absolute_tolerance": 3e-10,
            "same_seed_trajectory_claim": False,
        },
    )
    publications = {
        f"docs/report/method-certification/{family}/{name}": f"publication/{family}/{name}"
        for family, names in FAMILIES.items()
        for name in names
    }
    _exact(capture.get("publication_members"), publications)
    accepted = []
    for name, member in publications.items():
        product = _file(repository, name)
        retained = _file(repository, prefix + "/" + member)
        family, short = member.split("/")[1:]
        native = _file(repository, prefix + "/execution/" + family + "/" + short)
        authority = next(
            _object(row)["current"]
            for row in review["eleven_complete_public_product_comparisons"]
            if _object(row).get("family") == family
            and _object(row).get("path") == short
        )
        authority = _object(authority)
        _require(
            product.read_bytes() == retained.read_bytes() == native.read_bytes()
            and hashlib.sha256(product.read_bytes()).hexdigest() == authority["sha256"],
            "Controlled LRA native/public raw product differs",
        )
        entry = tracked_by_path.get(name)
        _require(
            entry is not None
            and entry.kind == "file"
            and (entry.sha256 == authority["sha256"])
            and (entry.size == authority["bytes"]),
            "Controlled LRA tracked product inventory differs",
        )
        assert entry is not None
        accepted.append(entry)
    for family in FAMILIES:
        observed = _file(
            repository, prefix + "/execution/" + family + "/same-process-runtime.json"
        )
        authority = _object(review["findings"][family]["same_process_runtime"])
        _require(
            hashlib.sha256(observed.read_bytes()).hexdigest() == authority["sha256"]
            and observed.stat().st_size == authority["bytes"],
            "Controlled LRA actual runtime observation differs",
        )
        runtime = _json(observed)
        _exact(runtime.get("numerical_exit"), 0)
        _exact(runtime.get("metadata_exit"), 0)
        _require(
            runtime.get("metadata_only") is False,
            "Controlled LRA runtime observation is not numerical",
        )
        for side in ("before", "after"):
            snapshot = _object(runtime.get(side))
            _exact(len(snapshot["namespaces"]), 40)
            _exact(len(snapshot["DLLs"]), 29)
        for key in ("canonical_python", "owned_python", "canonical_R", "R_wrapper"):
            authority = _object(plan["maintained_replays"][family][key])
            _require(
                any(
                    _object(row).get("original") == authority
                    and _object(row).get("member") is not None
                    for row in custody
                ),
                "Controlled LRA executed/canonical source is missing from packet",
            )
    _require(len(accepted) == 11, "Controlled LRA eleven report products are required")
    return (
        tuple(accepted),
        {
            "owner_ids": list(OWNERS),
            "capture_sha256": CAPTURE_SHA256,
            "original_execution_candidate": ORIGINAL_CANDIDATE,
            "metadata_assembly_candidate": ASSEMBLY_CANDIDATE,
            "actual_original_native_stages": [0, 0, 0],
            "products": 11,
            "original_source_members": 2139,
            "runtime_observations": 2,
            "optimizer_cases": 3,
            "paired_finite": 120,
            "paired_missing": 280,
            "R_iteration_cap_not_convergence": True,
            "historical_execution_proofs_recovered": False,
            "fresh_ecological_acceptance": "not_evaluated",
            "paths": [entry.path for entry in accepted],
            "scope": "Exact current-source controlled R/Python execution and its complete original source/input/runtime observations are retained under a separately qualified metadata epoch. One three-objective study and one explicit-draw ten-taxon fixture; R400iteration cap is not convergence, missing positions are preserved, no equal-seed stream/physical vegetation/old missing proof/human/hosted/release acceptance.",
        },
    )
