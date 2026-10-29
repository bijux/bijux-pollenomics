"""Admit exact original NFI dictionary/header/area/date metadata without exposing tree outcomes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry

from ...contracts import JsonObject, ReportRebuildError
from ...ownership import ReportOwnershipError, _regular_confined_file

CAPTURE = "data/validation/nfi-measurement-metadata-capture/capture.json"
CAPTURE_SHA256 = "bcff46b3478f3ad80d2253c96773b63b054f8cce81d9d84c5917b9ae731ba41a"
OWNER = "validation/empd2-nfi-pairing/measurement-schema"
GUIDE = "validation/empd2-nfi-pairing/calibration-guide"
REPORT = "docs/report/validation/empd2-nfi-pairing/nfi-measurement-schema.json"
PRODUCT_SHA256 = "5b4d5bb087501af7b223ffa8c5494a8ad4073a0503906b47aa36a2748a8e1505"
ORIGINAL_CANDIDATE = "60bf419979bdc682ef227fb01e42a4f5ed6e2722"
ASSEMBLY_CANDIDATE = "d027effd6c0ac91512cd586c3a51db987ea46d54"
RECEIPTS = {
    "plan.json": "22fb7f1d219ee2adf9f98bf682615199df8c18d3fc681f28decf3209bb46c601",
    "terminal.json": "9566b49bea315fc5ec410749fc0280e86b4ce0985c4fe897fe7f109b534fc090",
    "nfi-metadata-terminal.json": "02bfafe6c10f7a17a81f0ff165373e0f1fa0ff4ed93da03094459d9fe318a543",
    "independent-metadata-review.json": "b4f19bc9d5345959fdc1472609ee4c3691b3c70f8399c0dee7f53bd5f6eecb29",
}


def _require(value: object, message: str) -> None:
    if not value:
        raise ReportRebuildError(message)


def _object(value: object) -> dict[str, Any]:
    _require(
        isinstance(value, dict) and all(isinstance(k, str) for k in value),
        "NFI capture record must be an object",
    )
    assert isinstance(value, dict)
    return value


def _name(value: object) -> str:
    _require(
        isinstance(value, str) and bool(value), "NFI member must be a nonempty path"
    )
    assert isinstance(value, str)
    path = PurePosixPath(value)
    _require(
        not path.is_absolute()
        and ".." not in path.parts
        and path.as_posix() == value
        and "\\" not in value,
        "NFI member escapes its capsule",
    )
    return value


def _exact(a: Any, b: Any) -> None:
    _require(type(a) is type(b), "NFI metadata type differs")
    if isinstance(a, dict):
        _require(set(a) == set(b), "NFI metadata key membership differs")
        for key in a:
            _exact(a[key], b[key])
    elif isinstance(a, list):
        _require(len(a) == len(b), "NFI metadata list membership differs")
        for left, right in zip(a, b, strict=True):
            _exact(left, right)
    else:
        _require(a == b, "NFI metadata value differs")


def _file(repository: Path, name: str) -> Path:
    try:
        return _regular_confined_file(
            repository, name, "NFI retained measurement metadata"
        )
    except (OSError, ReportOwnershipError) as error:
        raise ReportRebuildError(
            "NFI retained file missing, linked or unconfined"
        ) from error


def _json(path: Path) -> dict[str, Any]:
    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in values:
            _require(key not in value, "NFI duplicate JSON key")
            value[key] = item
        return value

    try:
        value = json.loads(path.read_bytes(), object_pairs_hook=pairs)
        json.dumps(value, allow_nan=False)
        return _object(value)
    except (OSError, ValueError) as error:
        raise ReportRebuildError("NFI retained JSON is invalid") from error


def _native_records(
    plan: dict[str, Any],
    common: dict[str, Any],
    outer: dict[str, Any],
    review: dict[str, Any],
) -> None:
    _require(
        all(
            row.get("candidate") == ORIGINAL_CANDIDATE
            for row in (plan, common, outer, review)
        ),
        "NFI original execution epoch differs",
    )
    _require(
        all(
            row.get("plan_sha256") == RECEIPTS["plan.json"]
            for row in (common, outer, review)
        ),
        "NFI original execution plan differs",
    )
    for value in (
        common.get("actual_exit"),
        outer.get("actual_exit"),
        outer.get("common_actual_exit"),
        review.get("actual_exit"),
        review.get("actual_maintained_producer_native_exit"),
    ):
        _exact(value, 0)
    _require(
        common.get("canonical_before")
        == common.get("canonical_after")
        == plan.get("canonical_identity")
        and common.get("before_pin_mismatches")
        == common.get("after_pin_mismatches")
        == []
        and common.get("absent_input_paths_unchanged") is True,
        "NFI original before-after input custody differs",
    )
    _require(
        _object(outer.get("common_terminal")).get("sha256") == RECEIPTS["terminal.json"]
        and outer.get("memory_bound_pass") is True
        and outer.get("storage_bound_pass") is True,
        "NFI original resource/terminal binding differs",
    )
    intended, actual = plan.get("stages"), common.get("stages")
    _require(
        isinstance(intended, list)
        and isinstance(actual, list)
        and len(intended) == len(actual) == 2,
        "NFI two-stage execution membership differs",
    )
    assert isinstance(intended, list) and isinstance(actual, list)
    for expected_raw, observed_raw in zip(intended, actual, strict=True):
        expected, observed = _object(expected_raw), _object(observed_raw)
        _exact(observed.get("actual_exit"), 0)
        _require(
            expected.get("id") == observed.get("id")
            and expected.get("argv") == observed.get("argv")
            and observed.get("timed_out") is False,
            "NFI original native argv/status differs",
        )
    _exact(review.get("plot_year_rows"), 43892)
    _exact(review.get("metadata_cells_decoded"), 131676)
    _exact(review.get("measurement_outcome_cells_decoded"), 0)
    _require(
        review.get("benchmark_admission") == "no_measured_pairs_admitted"
        and _object(review.get("calibration_guide")).get("retained_owner_admitted")
        is False,
        "NFI outcome/guide scope differs",
    )


def validated_nfi_measurement_capture(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Transport one byte-exact metadata product; retain original private input identities only."""
    rows = [row for row in owners if row.get("owner_id") == OWNER]
    if (
        not any(row.get("role") == "retained_source" for row in rows)
        and not (repository / CAPTURE).exists()
    ):
        return (), {}
    _require(
        len(rows) == 1
        and rows[0].get("role") == "retained_source"
        and rows[0].get("paths") == [REPORT]
        and rows[0].get("producer_paths") == []
        and rows[0].get("producer_inputs") == [],
        "NFI exact retained owner declaration differs",
    )
    path = _file(repository, CAPTURE)
    _require(
        hashlib.sha256(path.read_bytes()).hexdigest() == CAPTURE_SHA256,
        "NFI retained capsule authority differs",
    )
    capture = _json(path)
    _require(
        capture.get("schema_version") == "nfi-original-measurement-metadata-capture.v1"
        and capture.get("owner_id") == OWNER
        and capture.get("publication_path") == REPORT
        and capture.get("publication_member")
        == "publication/nfi-measurement-schema.json"
        and capture.get("original_execution_candidate") == ORIGINAL_CANDIDATE
        and capture.get("metadata_assembly_candidate") == ASSEMBLY_CANDIDATE,
        "NFI retained source/metadata epochs differ",
    )
    _exact(capture.get("member_count"), 2168)
    _exact(capture.get("public_first_party_source_members"), 2139)
    _exact(capture.get("actual_native_metadata_stage_exits"), [0, 0])
    _require(
        capture.get("private_workbook_payload_included") is False
        and capture.get("runtime_payloads_included") is False
        and capture.get("calibration_guide_provider_or_copy_receipt_admitted") is False,
        "NFI private/runtime/guide scope expanded",
    )
    prefix = path.parent.relative_to(repository).as_posix()
    members = _object(capture.get("members"))
    _require(len(members) == 2168, "NFI capsule member count differs")
    for name, raw in members.items():
        member = _file(repository, prefix + "/" + _name(name))
        record = _object(raw)
        _exact(member.stat().st_size, record.get("bytes"))
        _require(
            hashlib.sha256(member.read_bytes()).hexdigest() == record.get("sha256"),
            "NFI capsule member bytes differ",
        )
    physical = set()
    for item in path.parent.rglob("*"):
        _require(
            not item.is_symlink() and (item.is_file() or item.is_dir()),
            "NFI capsule contains alias/special file",
        )
        if item.is_file():
            physical.add(item.relative_to(path.parent).as_posix())
    _require(
        physical == set(members) | {"capture.json"},
        "NFI complete physical capsule membership differs",
    )
    records = []
    for name, digest in RECEIPTS.items():
        file = _file(repository, prefix + "/execution/" + name)
        _require(
            hashlib.sha256(file.read_bytes()).hexdigest() == digest,
            "NFI native receipt differs",
        )
        records.append(_json(file))
    plan, common, outer, review = records
    _native_records(plan, common, outer, review)
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
            for name, digest in RECEIPTS.items()
        },
    )
    _exact(
        capture.get("metadata_semantics"),
        {
            "original_workbook_sha256": "862d13f26b868e3b32504f0f714f369018e700e54b245fcd2e16c80640316294",
            "plot_year_rows": 43892,
            "selected_metadata_cells": 131676,
            "selected_columns": ["D", "G", "H"],
            "measurement_outcome_cells_decoded": 0,
            "benchmark_admission": "no_measured_pairs_admitted",
        },
    )
    custody = capture.get("original_input_custody")
    _require(
        isinstance(custody, list) and len(custody) == 33005,
        "NFI original input membership differs",
    )
    assert isinstance(custody, list)
    _exact([_object(row).get("original") for row in custody], plan.get("input_pins"))
    counts: dict[str, int] = {}
    by_source = {}
    for raw in custody:
        row = _object(raw)
        scope = row["scope"]
        counts[scope] = counts.get(scope, 0) + 1
        source = _object(row["original"])
        by_source[source["path"]] = row
        if row["member"] is not None:
            _exact(
                members.get(_name(row["member"])),
                {key: source[key] for key in ("sha256", "bytes")},
            )
        else:
            _require(
                scope
                in (
                    "private_identity_only",
                    "runtime_identity_only",
                    "existing_public_metadata_identity_only",
                ),
                "NFI input omission is undeclared",
            )
    _exact(capture.get("original_input_scope_counts"), counts)
    _exact(counts["full_declared_first_party_source"], 2139)
    origins = _json(_file(repository, prefix + "/execution/loaded-source-origins.json"))
    _exact(len(origins), 1161)
    for raw in origins.values():
        origin = _object(raw)
        origin_row = by_source.get(origin.get("path"))
        _require(
            origin_row is not None
            and origin_row["scope"] == "full_declared_first_party_source"
            and origin_row["member"] in members,
            "NFI observed source origin is absent",
        )
        assert origin_row is not None
        _exact(origin_row["original"], origin)
    product = _file(repository, REPORT)
    retained = _file(repository, prefix + "/publication/nfi-measurement-schema.json")
    native = _file(repository, prefix + "/execution/nfi-measurement-schema.json")
    _require(
        product.read_bytes() == retained.read_bytes() == native.read_bytes()
        and hashlib.sha256(product.read_bytes()).hexdigest() == PRODUCT_SHA256,
        "NFI current/native metadata bytes differ",
    )
    entry = tracked_by_path.get(REPORT)
    _require(
        entry is not None
        and entry.kind == "file"
        and entry.sha256 == PRODUCT_SHA256
        and entry.size == 2537,
        "NFI tracked product inventory differs",
    )
    assert entry is not None
    return (entry,), {
        "owner_id": OWNER,
        "capture_sha256": CAPTURE_SHA256,
        "original_execution_candidate": ORIGINAL_CANDIDATE,
        "metadata_assembly_candidate": ASSEMBLY_CANDIDATE,
        "original_native_stages": [0, 0],
        "paths": [entry.path],
        "selected_metadata_cells": 131676,
        "plot_year_rows": 43892,
        "observed_source_origins": 1161,
        "measurement_outcome_cells_decoded": 0,
        "benchmark_admission": "no_measured_pairs_admitted",
        "guide_provider_or_copy_receipt_admitted": False,
        "scope": "Exact original committed selected metadata and complete original source/control custody, with a separately qualified metadata assembly epoch. Whole worksheet XML was streamed by the original producer; only dictionary/header/date/area/land-use metadata was selected. No current whole-tree numerical execution, tree outcome/vegetation accuracy, original guide retrieval/copy, human or official release acceptance.",
    }
