"""Authenticate the two produced optimizer diagnostics without admitting their historical references."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry

from ..contracts import JsonObject, ReportRebuildError, canonical_json_sha256
from ..ownership import ReportOwnershipError, _regular_confined_file
from .source_correspondence import validated_metadata_source_correspondence

CAPTURE = (
    "data/method-certification/author-optimizer-diagnostic-source-capture/capture.json"
)
CAPTURE_SHA256 = "f865795aac7585e56c4cf44faac84496d339e1c176fc6ee111cba3cbc9b4ce93"
EXPECTED_MEMBERS = 2222
EXECUTIONS = {
    "optimizer-diagnostics": (
        "19642380cc6051ed9d6cfc3fbddfdb56b4feeba7",
        "fb37c521a0e1e92bb5e9369f2a0da84b1474183fbca350ca0c957cde12bf22f5",
        "5aec38e2319d4615a4a6210dd5776e547a1686cec334a90684eab9fbf54b9906",
        "independent-diagnostic-review.json",
        "d36511f2a2c26c223294a79fe5307548b02cf8e3ab1bb78bb496290ee1ccf798",
    )
}
OWNERS = {
    "pollen-reconstruction/author-lra-constrained/optimizer-gradient/report-products": (
        "docs/report/pollen-reconstruction/author-lra-constrained/optimizer-gradient/",
        1,
    ),
    "pollen-reconstruction/author-lra-optimized-feasibility/report-products": (
        "docs/report/pollen-reconstruction/author-lra-optimized-feasibility/",
        1,
    ),
}
UNRESOLVED = {
    "pollen-reconstruction/author-lra-constrained/optimizer-gradient/baseline-reference": "docs/report/pollen-reconstruction/author-lra-constrained/optimizer-gradient/baseline.json",
    "pollen-reconstruction/author-lra-optimized-feasibility/attempt-report": "docs/report/pollen-reconstruction/author-lra-optimized-feasibility/report.json",
}


def _file(repository: Path, name: str) -> Path:
    try:
        return _regular_confined_file(
            repository, name, "retained author Python reference comparison"
        )
    except (ReportOwnershipError, OSError) as error:
        raise ReportRebuildError(
            "Retained author file is missing, linked or unconfined"
        ) from error


def _object(value: object) -> dict[str, Any]:
    if not isinstance(value, dict) or any(not isinstance(k, str) for k in value):
        raise ReportRebuildError("Retained author record must be an object")
    return value


def _json(path: Path) -> dict[str, Any]:
    try:
        return _object(json.loads(path.read_bytes()))
    except (OSError, ValueError) as error:
        raise ReportRebuildError("Retained author JSON is invalid") from error


def _zero(value: object) -> bool:
    return type(value) is int and value == 0


def _member_name(value: object) -> str:
    if (
        not isinstance(value, str)
        or not value
        or PurePosixPath(value).is_absolute()
        or ".." in PurePosixPath(value).parts
        or PurePosixPath(value).as_posix() != value
    ):
        raise ReportRebuildError("Retained author path is unconfined")
    return value


def _native_references(packet: Path, capture: JsonObject) -> None:
    histories = _object(capture.get("original_execution_custody"))
    if set(histories) != set(EXECUTIONS):
        raise ReportRebuildError("Retained author execution membership differs")
    for lane, (
        candidate,
        plan_sha,
        outer_sha,
        observer_name,
        observer_sha,
    ) in EXECUTIONS.items():
        root = packet / "executions" / lane
        plan, common, outer, review = (
            _json(root / name)
            for name in [
                "plan.json",
                "terminal.json",
                "diagnostic-terminal.json",
                observer_name,
            ]
        )
        if (
            hashlib.sha256((root / "plan.json").read_bytes()).hexdigest() != plan_sha
            or hashlib.sha256(
                (root / "diagnostic-terminal.json").read_bytes()
            ).hexdigest()
            != outer_sha
            or hashlib.sha256((root / observer_name).read_bytes()).hexdigest()
            != observer_sha
        ):
            raise ReportRebuildError(
                "Retained author original execution authorities differ"
            )
        if (
            any(
                item.get("candidate") != candidate
                for item in [plan, common, outer, review]
            )
            or common.get("plan_sha256") != plan_sha
            or outer.get("plan_sha256") != plan_sha
            or not all(
                _zero(v)
                for v in [
                    common.get("actual_exit"),
                    outer.get("actual_exit"),
                    outer.get("common_actual_exit"),
                ]
            )
            or common.get("status") != "passed"
            or common.get("canonical_before") != common.get("canonical_after")
            or common.get("canonical_before") != plan.get("canonical_identity")
            or common.get("before_pin_mismatches") != []
            or common.get("after_pin_mismatches") != []
            or common.get("absent_input_paths_unchanged") is not True
            or outer.get("memory_bound_pass") is not True
            or outer.get("storage_bound_pass") is not True
        ):
            raise ReportRebuildError("Retained author execution did not pass exactly")
        if (
            _object(outer.get("common_terminal")).get("sha256")
            != hashlib.sha256((root / "terminal.json").read_bytes()).hexdigest()
        ):
            raise ReportRebuildError("Retained author common terminal binding differs")
        stages, intended = common.get("stages"), plan.get("stages")
        if (
            not isinstance(stages, list)
            or not isinstance(intended, list)
            or len(stages) != len(intended)
            or len(stages) != 3
        ):
            raise ReportRebuildError("Retained author needs both actual native stages")
        for actual_raw, expected_raw in zip(stages, intended, strict=True):
            actual, expected = _object(actual_raw), _object(expected_raw)
            if (
                not _zero(actual.get("actual_exit"))
                or actual.get("timed_out") is not False
                or actual.get("argv") != expected.get("argv")
                or actual.get("id") != expected.get("id")
            ):
                raise ReportRebuildError("Retained author native stage differs")
        history = _object(histories[lane])
        input_custody = history.get("input_custody")
        if (
            not isinstance(input_custody, list)
            or [_object(row).get("original") for row in input_custody]
            != plan.get("input_pins")
            or history.get("original_plan_sha256") != plan_sha
            or history.get("candidate") != candidate
            or history.get("original_input_count") != len(input_custody)
        ):
            raise ReportRebuildError("Retained author original source custody differs")
        if (
            review.get("all_complete_diagnostic_typed_values_exact") is not True
            or review.get("all_original_baselines_and_refusals_exact") is not True
            or review.get("actual_diagnostic_optimizers_run") is not True
            or review.get("full_experiment_fit_or_new_prediction_executed") is not False
            or review.get("R_executed") is not False
            or not _zero(review.get("held_out_prediction_count"))
            or review.get("scientific_or_official_release_acceptance") is not False
            or history.get("original_input_count") != 33320
            or history.get("original_controller_members") != 8
            or history.get("exact_derived_input_files") != 47
        ):
            raise ReportRebuildError("Optimizer diagnostic native scope differs")


def validated_author_optimizer_diagnostic_capture(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Admit only produced diagnostic reports; preserve unresolved reference and attempt roles."""
    rows = [row for row in owners if row.get("owner_id") in OWNERS]
    if (
        not any(row.get("role") == "retained_source" for row in rows)
        and not (repository / CAPTURE).exists()
    ):
        return (), {}
    if (
        len(rows) != len(OWNERS)
        or {r.get("owner_id") for r in rows} != set(OWNERS)
        or any(
            row.get("role") != "retained_source"
            or row.get("producer_paths") != []
            or row.get("producer_inputs") != []
            for row in rows
        )
    ):
        raise ReportRebuildError(
            "Author optimizer diagnostic owner declarations differ"
        )
    for unresolved_owner, name in UNRESOLVED.items():
        declared = [row for row in owners if row.get("owner_id") == unresolved_owner]
        if (
            len(declared) != 1
            or declared[0].get("role") != "unresolved"
            or declared[0].get("paths") != [name]
        ):
            raise ReportRebuildError(
                "Optimizer reference/attempt ownership must remain unresolved"
            )
    baseline_name = UNRESOLVED[next(iter(UNRESOLVED))]
    baseline = _file(repository, baseline_name)
    if (
        hashlib.sha256(baseline.read_bytes()).hexdigest()
        != "68afb09419754130f482783397f58b12c7c06ee041430b24d264dc7f9c30e009"
    ):
        raise ReportRebuildError("Optimizer read baseline differs")
    path = _file(repository, CAPTURE)
    if hashlib.sha256(path.read_bytes()).hexdigest() != CAPTURE_SHA256:
        raise ReportRebuildError(
            "Author optimizer diagnostic retained capture authority differs"
        )
    capture = _json(path)
    raw_members = capture.get("members")
    if (
        capture.get("schema_version")
        != "retained-author-optimizer-diagnostic-source-capture.v1"
        or not isinstance(raw_members, list)
        or type(capture.get("member_count")) is not int
        or capture["member_count"] != len(raw_members)
        or len(raw_members) != EXPECTED_MEMBERS
    ):
        raise ReportRebuildError(
            "Author optimizer diagnostic capture membership differs"
        )
    members: dict[str, dict[str, Any]] = {}
    prefix = path.parent.relative_to(repository).as_posix()
    for raw in raw_members:
        row = _object(raw)
        name = _member_name(row.get("path"))
        physical = _file(repository, prefix + "/" + name)
        if (
            name in members
            or type(row.get("bytes")) is not int
            or row["bytes"] < 0
            or physical.stat().st_size != row["bytes"]
            or hashlib.sha256(physical.read_bytes()).hexdigest() != row.get("sha256")
        ):
            raise ReportRebuildError(
                "Author optimizer diagnostic retained member bytes differ"
            )
        members[name] = row
    physical_names: set[str] = set()
    for physical in path.parent.rglob("*"):
        if physical.is_symlink():
            raise ReportRebuildError(
                "Author optimizer diagnostic packet contains a link"
            )
        if physical.is_file():
            physical_names.add(physical.relative_to(path.parent).as_posix())
    if physical_names != set(members) | {"capture.json"}:
        raise ReportRebuildError(
            "Author optimizer diagnostic physical packet membership differs"
        )
    _native_references(path.parent, capture)
    projection = capture.get("current_scientific_source_projection")
    if not isinstance(projection, list) or len(projection) != 2072:
        raise ReportRebuildError(
            "Author optimizer diagnostic current scientific source projection differs"
        )
    current_metadata_correspondences = []
    for raw in projection:
        row = _object(raw)
        name = _member_name(row.get("path"))
        current = _file(repository, name)
        retained_candidates = [
            path.parent / f"executions/{lane}/first-party-inputs/{name}"
            for lane in EXECUTIONS
            if members.get(f"executions/{lane}/first-party-inputs/{name}", {}).get(
                "sha256"
            )
            == row.get("sha256")
        ]
        if not retained_candidates:
            raise ReportRebuildError(
                "Author optimizer diagnostic retained scientific source is unbound"
            )
        if current.stat().st_size != row.get("bytes") or hashlib.sha256(
            current.read_bytes()
        ).hexdigest() != row.get("sha256"):
            current_metadata_correspondences.append(
                validated_metadata_source_correspondence(
                    repository, row, retained_candidates[0]
                )
            )
    products = capture.get("report_outputs")
    if not isinstance(products, list) or len(products) != 2:
        raise ReportRebuildError(
            "Author optimizer diagnostic needs exactly two produced diagnostic reports"
        )
    accepted: list[InventoryEntry] = []
    by_owner: dict[str, list[str]] = {key: [] for key in OWNERS}
    for raw in products:
        product = _object(raw)
        name = _member_name(product.get("path"))
        owner = product.get("owner_id")
        if (
            not isinstance(owner, str)
            or owner not in OWNERS
            or not name.startswith(OWNERS[owner][0])
            or name in {"docs/report/" + r.path for r in accepted}
        ):
            raise ReportRebuildError(
                "Author optimizer diagnostic report ownership differs"
            )
        lane = product.get("execution_lane")
        raw_name = product.get("raw_name")
        if lane != "optimizer-diagnostics" or raw_name not in {
            "gradient.json",
            "finite.json",
        }:
            raise ReportRebuildError("Optimizer produced role differs")
        raw_record = _object(product.get("raw"))
        common = _json(path.parent / "executions" / lane / "terminal.json")
        native_products = common.get("products")
        if (
            not isinstance(native_products, list)
            or raw_record not in native_products
            or product.get("native_terminal_product_proof") != raw_record
        ):
            raise ReportRebuildError("Optimizer raw output has no native product proof")
        expected = _object(product.get("published"))
        if (raw_record.get("sha256"), raw_record.get("bytes")) != (
            expected.get("sha256"),
            expected.get("bytes"),
        ):
            raise ReportRebuildError(
                "Optimizer published output differs from native bytes"
            )
        retained = members.get("published/" + name)
        entry = tracked_by_path.get(name)
        current = _file(repository, name)
        if (
            retained is None
            or retained.get("sha256") != expected.get("sha256")
            or retained.get("bytes") != expected.get("bytes")
            or entry is None
            or entry.kind != "file"
            or entry.sha256 != expected.get("sha256")
            or entry.size != expected.get("bytes")
            or hashlib.sha256(current.read_bytes()).hexdigest()
            != expected.get("sha256")
            or current.stat().st_size != expected.get("bytes")
        ):
            raise ReportRebuildError(
                "Author optimizer diagnostic published report bytes differ"
            )
        by_owner[owner].append(name)
        accepted.append(entry)
    for row in rows:
        owner = str(row["owner_id"])
        if (
            row.get("paths") != sorted(by_owner[owner])
            or len(by_owner[owner]) != OWNERS[owner][1]
        ):
            raise ReportRebuildError(
                "Author optimizer diagnostic exact owner path membership differs"
            )
    names = {name for values in by_owner.values() for name in values}
    for other in owners:
        other_paths = other.get("paths")
        if (
            other not in rows
            and other.get("role") == "retained_source"
            and isinstance(other_paths, list)
            and names.intersection(other_paths)
        ):
            raise ReportRebuildError(
                "Author optimizer diagnostic retained ownership overlaps"
            )
    return tuple(accepted), {
        "owner_ids": sorted(OWNERS),
        "capture_sha256": CAPTURE_SHA256,
        "executed_source_candidates": {
            lane: values[0] for lane, values in EXECUTIONS.items()
        },
        "report_outputs": 2,
        "current_scientific_projection": 2072,
        "current_projection_byteequal_members": 2072
        - len(current_metadata_correspondences),
        "current_metadata_source_correspondences": current_metadata_correspondences,
        "original_projection_members_retained_unchanged": 2072,
        "paths_sha256": canonical_json_sha256(sorted(names)),
        "scope": "Two actual bounded prior-exposed English optimizer diagnostic JSON reports. Exact original source, reference baseline and negative convergence are retained. The baseline is read input and historical feasibility attempt report remains unresolved. No full experiment fit, held-out prediction, R, ecology, Nordic, rights, human or official release acceptance is admitted.",
    }
