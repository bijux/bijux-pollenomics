"""Admit the executed Linux R source epoch while retaining historical refusal."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry

from ..contracts import JsonObject, ReportRebuildError, canonical_json_sha256
from ..ownership import ReportOwnershipError, _regular_confined_file

OWNER = "method-certification/linux-r-oracle/report-products"
FAMILY = "docs/report/method-certification/linux-r-oracle/"
CAPTURE = "data/method-certification/linux-r-source-capture/capture.json"
CAPTURE_SHA256 = "fa6e9a4fa9c12013a04cc461fef52d0fd54044d517e132e802a9c176def2a913"
SOURCE_CANDIDATE = "6d8f1c5beffc2627b14e3330f8567e60f0fc8c36"


def _file(repository: Path, name: str, label: str) -> Path:
    try:
        return _regular_confined_file(repository, name, label)
    except (ReportOwnershipError, OSError) as error:
        raise ReportRebuildError(
            "Linux retained file is missing, linked or unconfined"
        ) from error


def _object(value: object, reason: str) -> dict[str, Any]:
    if not isinstance(value, dict) or any(not isinstance(k, str) for k in value):
        raise ReportRebuildError(reason)
    return value


def _json(path: Path) -> dict[str, Any]:
    try:
        return _object(json.loads(path.read_bytes()), "Linux capture must be an object")
    except (OSError, ValueError) as error:
        raise ReportRebuildError("Linux capture JSON is invalid") from error


def _zero(value: object) -> bool:
    return type(value) is int and value == 0


def _native_references(packet: Path, capture: JsonObject) -> None:
    references = capture.get("execution_references")
    expected = {
        "plan": "execution/plan.json",
        "common_terminal": "execution/terminal.json",
        "outer_terminal": "execution/linux-source-terminal.json",
        "independent_numerical_review": "execution/independent-review.json",
        "source_reference": "execution/source-reference.json",
    }
    if references != expected:
        raise ReportRebuildError("Linux execution reference membership differs")
    plan, common, outer, review, source = (
        _json(packet / expected[name]) for name in expected
    )
    if (
        capture.get("schema_version") != "retained-linux-r-source-capture.v1"
        or capture.get("source_candidate") != SOURCE_CANDIDATE
        or any(
            item.get("candidate") != SOURCE_CANDIDATE
            for item in (plan, common, outer, review)
        )
        or source.get("base_candidate") != SOURCE_CANDIDATE
        or common.get("plan_sha256")
        != hashlib.sha256((packet / expected["plan"]).read_bytes()).hexdigest()
        or outer.get("registered_plan_sha256") != common.get("plan_sha256")
        or not all(
            _zero(value)
            for value in (
                common.get("actual_exit"),
                outer.get("actual_exit"),
                outer.get("common_actual_exit"),
            )
        )
        or outer.get("all_protected_inputs_unchanged") is not True
        or outer.get("memory_bound_passed") is not True
        or outer.get("storage_bound_passed") is not True
        or common.get("canonical_before") != common.get("canonical_after")
        or common.get("canonical_before") != plan.get("canonical_identity")
        or common.get("before_pin_mismatches") != []
        or common.get("after_pin_mismatches") != []
        or review.get("core_cases") != 43
        or review.get("source_domain_cases") != 23
        or review.get("all_complete_source_runtime_output_joins_passed") is not True
        or review.get("release_certificate") is not False
    ):
        raise ReportRebuildError("Linux execution epoch or native evidence differs")
    stages, intended = common.get("stages"), plan.get("stages")
    if (
        not isinstance(stages, list)
        or not isinstance(intended, list)
        or len(stages) != len(intended)
        or len(stages) != 2
    ):
        raise ReportRebuildError("Linux execution must retain both native stages")
    for actual_raw, intended_raw in zip(stages, intended, strict=True):
        actual = _object(actual_raw, "Linux native stage malformed")
        declared = _object(intended_raw, "Linux intended stage malformed")
        if (
            not _zero(actual.get("actual_exit"))
            or actual.get("timed_out") is not False
            or actual.get("argv") != declared.get("argv")
        ):
            raise ReportRebuildError("Linux native stage did not pass exactly")
    comparisons = review.get("independent_comparisons")
    source_files = source.get("source_files")
    if (
        not isinstance(comparisons, list)
        or len(comparisons) != 66
        or not isinstance(source_files, dict)
        or len(source_files) != 2148
    ):
        raise ReportRebuildError("Linux independent/source membership differs")
    for name, digest in source_files.items():
        if (
            not isinstance(name, str)
            or PurePosixPath(name).is_absolute()
            or ".." in PurePosixPath(name).parts
            or not isinstance(digest, str)
            or hashlib.sha256((packet / "source" / name).read_bytes()).hexdigest()
            != digest
        ):
            raise ReportRebuildError("Linux executed source bytes differ")


def validated_linux_r_reference_capture(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Transport exactly 137 outputs from the captured source-built Linux R run."""
    rows = [r for r in owners if r.get("owner_id") == OWNER]
    active = (
        any(r.get("role") == "retained_source" for r in rows)
        or (repository / CAPTURE).exists()
    )
    if not active:
        return (), {}
    if len(rows) != 1:
        raise ReportRebuildError("Linux capture needs exactly one owner")
    owner = rows[0]
    if (
        owner.get("role") != "retained_source"
        or owner.get("producer_paths") != []
        or owner.get("producer_inputs") != []
    ):
        raise ReportRebuildError("Linux capture owner declaration differs")
    path = _file(repository, CAPTURE, "Linux capture")
    if hashlib.sha256(path.read_bytes()).hexdigest() != CAPTURE_SHA256:
        raise ReportRebuildError("Linux capture authority bytes differ")
    capture = _json(path)
    members = capture.get("members")
    if (
        not isinstance(members, list)
        or type(capture.get("member_count")) is not int
        or capture["member_count"] != len(members)
        or len(members) != 2311
    ):
        raise ReportRebuildError("Linux retained member count differs")
    packet = path.parent
    files: dict[str, dict[str, Any]] = {}
    for raw in members:
        member = _object(raw, "Linux member malformed")
        name, digest, size = (
            member.get("path"),
            member.get("sha256"),
            member.get("bytes"),
        )
        if (
            not isinstance(name, str)
            or not name
            or PurePosixPath(name).is_absolute()
            or ".." in PurePosixPath(name).parts
            or PurePosixPath(name).as_posix() != name
            or name in files
            or type(size) is not int
            or size < 0
            or not isinstance(digest, str)
        ):
            raise ReportRebuildError("Linux member identity differs")
        physical = _file(
            repository,
            path.parent.relative_to(repository).as_posix() + "/" + name,
            "Linux member",
        )
        body = physical.read_bytes()
        if len(body) != size or hashlib.sha256(body).hexdigest() != digest:
            raise ReportRebuildError("Linux retained member bytes differ")
        files[name] = member
    physical_names: set[str] = set()
    for member_path in packet.rglob("*"):
        if member_path.is_symlink():
            raise ReportRebuildError("Linux retained member is a link")
        if member_path.is_file():
            physical_names.add(member_path.relative_to(packet).as_posix())
    if physical_names != set(files) | {"capture.json"}:
        raise ReportRebuildError("Linux retained physical membership differs")
    _native_references(packet, capture)
    projection = _object(
        capture.get("current_scientific_source_projection"),
        "Linux source projection missing",
    )
    scientific = projection.get("members")
    if not isinstance(scientific, list) or len(scientific) != 127:
        raise ReportRebuildError("Linux scientific projection differs")
    for raw in scientific:
        item = _object(raw, "Linux source projection malformed")
        name = item.get("relative_path")
        if not isinstance(name, str) or not name.startswith(
            (
                "packages/bijux-pollenomics-lra/",
                "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/",
            )
        ):
            raise ReportRebuildError("Linux scientific source owner differs")
        current = _file(repository, name, "Linux current scientific source")
        if (
            current.stat().st_size != item.get("bytes")
            or hashlib.sha256(current.read_bytes()).hexdigest() != item.get("sha256")
            or files.get("source/" + name, {}).get("sha256") != item.get("sha256")
        ):
            raise ReportRebuildError("Linux current scientific implementation changed")
    lock_name = "configs/ci/lra-r-source-lock.v1.json"
    current_lock = _file(repository, lock_name, "Linux current R source lock")
    if hashlib.sha256(current_lock.read_bytes()).hexdigest() != files.get(
        "source/" + lock_name, {}
    ).get("sha256"):
        raise ReportRebuildError("Linux current R dependency lock changed")
    authority = _object(
        capture.get("current_report_owner"), "Linux output authority missing"
    )
    outputs = authority.get("outputs")
    if (
        authority.get("owner_id") != OWNER
        or not isinstance(outputs, list)
        or len(outputs) != 137
    ):
        raise ReportRebuildError("Linux output membership differs")
    accepted: list[InventoryEntry] = []
    names: list[str] = []
    for raw in outputs:
        item = _object(raw, "Linux output malformed")
        name = item.get("path")
        if not isinstance(name, str) or not name.startswith(FAMILY) or name in names:
            raise ReportRebuildError("Linux output path differs")
        names.append(name)
        expected = files.get("retained/" + name.removeprefix(FAMILY))
        entry = tracked_by_path.get(name)
        physical = _file(repository, name, "Linux report")
        if (
            expected is None
            or item.get("sha256") != expected["sha256"]
            or item.get("bytes") != expected["bytes"]
            or entry is None
            or entry.kind != "file"
            or entry.sha256 != expected["sha256"]
            or entry.size != expected["bytes"]
            or hashlib.sha256(physical.read_bytes()).hexdigest() != expected["sha256"]
            or physical.stat().st_size != expected["bytes"]
        ):
            raise ReportRebuildError("Linux current report bytes differ")
        accepted.append(entry)
    if owner.get("paths") != sorted(names):
        raise ReportRebuildError("Linux exact137 owner path set differs")
    for other in owners:
        other_paths = other.get("paths")
        if (
            other is not owner
            and other.get("role") == "retained_source"
            and isinstance(other_paths, list)
            and set(names).intersection(other_paths)
        ):
            raise ReportRebuildError("Linux retained output ownership overlaps")
    return tuple(accepted), {
        "owner_id": OWNER,
        "capture_sha256": CAPTURE_SHA256,
        "executed_source_candidate": SOURCE_CANDIDATE,
        "assembly_candidate": capture.get("assembly_candidate"),
        "source_files": 2148,
        "scientific_current_projection": 127,
        "retained_execution_files": 140,
        "report_outputs": 137,
        "paths_sha256": canonical_json_sha256(sorted(names)),
        "historical_source_gap_retained": True,
        "scope": "Captured local ARM64 R4.6 source oracle,43core+23source-domain cases and independentDecimal50 comparison. Current127scientific source and metadata members unchanged; no claim the entire current executable source tree equals the captured execution. Original1661source missing4 epoch stays separate. Transport executes noR, optimizer, browser, acquisition or ecological/human/rights/hostedx86_64 release acceptance.",
    }
