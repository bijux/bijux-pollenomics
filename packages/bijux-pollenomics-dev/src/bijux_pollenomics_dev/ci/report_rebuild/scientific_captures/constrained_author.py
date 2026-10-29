"""Retain the complete source-bound constrained author experiment and its refusals."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry

from ..contracts import JsonObject, ReportRebuildError, canonical_json_sha256
from ..ownership import ReportOwnershipError, _regular_confined_file
from ..retained_source import validated_descriptor
from .source_correspondence import validated_current_scientific_source

CAPTURE = "data/method-certification/constrained-author-source-capture/capture.json"
CAPTURE_SHA256 = "fa46f5757af2acfb647f82162314b11c5e9401fbd7ecdbff585b70a687b9080c"
EXPECTED_MEMBERS = 3163
EXECUTIONS = {
    "complete-constrained": (
        "22c6e480ba4690cc508202925a8773afe95ab36e",
        "7a75256e79a577280d8bd828380ebb8438b80914e3aa8c5ddc390fa428e6428c",
        "c4ab7b6a50c989cd646454ae2b52020df2bbdc749a4806077a45917117fc1539",
        "independent-constrained-author-review.json",
        "93f0c05d69b2bd9a59a9b05759e757f8815a48390c0208c72d86c85e0b04cb9f",
    )
}
OWNERS = {
    "pollen-reconstruction/author-lra-constrained/report-products": (
        "docs/report/pollen-reconstruction/author-lra-constrained/",
        11,
    )
}


def _file(repository: Path, name: str) -> Path:
    try:
        return _regular_confined_file(
            repository, name, "retained constrained author experiment"
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
                "constrained-author-terminal.json",
                observer_name,
            ]
        )
        if (
            hashlib.sha256((root / "plan.json").read_bytes()).hexdigest() != plan_sha
            or hashlib.sha256(
                (root / "constrained-author-terminal.json").read_bytes()
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
            or len(stages) != 2
        ):
            raise ReportRebuildError(
                "Retained author needs both actual execution stages"
            )
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
        _native_scope(review, history, plan, common)


def _native_scope(
    review: JsonObject, history: JsonObject, plan: JsonObject, common: JsonObject
) -> None:
    counts = {
        "native_training_items": 195,
        "native_completed": 192,
        "native_refused": 3,
    }
    if any(type(review.get(k)) is not int or review[k] != n for k, n in counts.items()):
        raise ReportRebuildError("Constrained author native attempt population differs")
    if (
        review.get("all_eleven_products_scientific_values_equal") is not True
        or type(review.get("target_exclusion_and_prediction_chain_verified")) is not int
        or review.get("target_exclusion_and_prediction_chain_verified") != 42
        or review.get("historical_3d6_terminal_available") is not False
        or review.get("R_or_new_solver_or_ecological_or_official_release_acceptance")
        is not False
        or type(history.get("original_input_count")) is not int
        or history.get("original_input_count") != 33336
        or type(history.get("retained_complete_work_files")) is not int
        or history.get("retained_complete_work_files") != 900
    ):
        raise ReportRebuildError("Constrained author native/source witness differs")
    native = review.get("completed_native_products_current_code_and_inventory_verified")
    if not isinstance(native, list) or len(native) != 192:
        raise ReportRebuildError(
            "Constrained author native product review population differs"
        )
    for value in native:
        row = _object(value)
        if set(row) != {
            "item",
            "request_sha256",
            "product_manifest_sha256",
            "scientific_content_sha256",
        } or not isinstance(row.get("item"), str):
            raise ReportRebuildError(
                "Constrained author native product review fields differ"
            )
        for key in (
            "request_sha256",
            "product_manifest_sha256",
            "scientific_content_sha256",
        ):
            digest = row[key]
            if (
                not isinstance(digest, str)
                or len(digest) != 64
                or any(c not in "0123456789abcdef" for c in digest)
            ):
                raise ReportRebuildError(
                    "Constrained author native product review identity differs"
                )
    proofs = history.get("complete_work_proofs")
    products = common.get("products")
    if (
        not isinstance(proofs, list)
        or not isinstance(products, list)
        or len(proofs) != 900
    ):
        raise ReportRebuildError("Constrained author complete work population differs")
    root = PurePosixPath(str(plan.get("retained_work")))
    actual = {
        _object(p).get("path"): p
        for p in products
        if isinstance(_object(p).get("path"), str)
        and PurePosixPath(_object(p)["path"]).is_relative_to(root)
    }
    if (
        len(actual) != 900
        or len({_object(p).get("path") for p in proofs}) != 900
        or any(actual.get(_object(p).get("path")) != p for p in proofs)
    ):
        raise ReportRebuildError("Constrained author complete work receipts differ")


def validated_constrained_author_capture(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Admit eleven reports with complete original source and native execution custody."""
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
            "Constrained author experiment owner declarations differ"
        )
    path = _file(repository, CAPTURE)
    if hashlib.sha256(path.read_bytes()).hexdigest() != CAPTURE_SHA256:
        raise ReportRebuildError(
            "Constrained author experiment retained capture authority differs"
        )
    capture = _json(path)
    raw_members = capture.get("members")
    if (
        capture.get("schema_version") != "retained-constrained-author-source-capture.v1"
        or not isinstance(raw_members, list)
        or type(capture.get("member_count")) is not int
        or capture["member_count"] != len(raw_members)
        or len(raw_members) != EXPECTED_MEMBERS
    ):
        raise ReportRebuildError(
            "Constrained author experiment capture membership differs"
        )
    members: dict[str, dict[str, Any]] = {}
    prefix = path.parent.relative_to(repository).as_posix()
    for raw in raw_members:
        row = _object(raw)
        name = _member_name(row.get("path"))
        if name in members:
            raise ReportRebuildError("Duplicate retained source member")
        members[name] = row
    resolver = validated_descriptor(repository, prefix, members)
    _native_references(path.parent, capture)
    projection = capture.get("current_scientific_source_projection")
    if not isinstance(projection, list) or len(projection) != 2136:
        raise ReportRebuildError(
            "Constrained author experiment current scientific source projection differs"
        )
    current_metadata_correspondences: list[JsonObject] = []
    current_presentation_correspondences: list[JsonObject] = []
    current_author_profile_correspondences: list[JsonObject] = []
    current_intake_guard_correspondences: list[JsonObject] = []
    for raw in projection:
        row = _object(raw)
        name = _member_name(row.get("path"))
        retained_candidates = [
            f"executions/{lane}/first-party-inputs/{name}"
            for lane in EXECUTIONS
            if members.get(f"executions/{lane}/first-party-inputs/{name}", {}).get(
                "sha256"
            )
            == row.get("sha256")
            and members.get(f"executions/{lane}/first-party-inputs/{name}", {}).get(
                "bytes"
            )
            == row.get("bytes")
        ]
        if type(row.get("bytes")) is not int or not retained_candidates:
            raise ReportRebuildError("Retained scientific source is unbound")
        correspondence = validated_current_scientific_source(
            repository, row, retained_candidates[0], resolver
        )
        if correspondence is not None:
            current_metadata_correspondences.append(correspondence)
    products = capture.get("report_outputs")
    if not isinstance(products, list) or len(products) != 11:
        raise ReportRebuildError(
            "Constrained author experiment needs exactly eleven report products"
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
                "Constrained author experiment report ownership differs"
            )
        expected = _object(product.get("published"))
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
                "Constrained author experiment published report bytes differ"
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
                "Constrained author experiment exact owner path membership differs"
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
                "Constrained author experiment retained ownership overlaps"
            )
    resolver.fresh()
    return tuple(accepted), {
        "owner_ids": sorted(OWNERS),
        "capture_sha256": CAPTURE_SHA256,
        "executed_source_candidates": {
            lane: values[0] for lane, values in EXECUTIONS.items()
        },
        "report_outputs": 11,
        "logical_scientific_projection": 2136,
        "current_scientific_projection": 2136
        - sum(
            item.get("classification")
            in {
                "historical_private_control_current_absence",
                "historical_generated_version_metadata",
            }
            for item in current_metadata_correspondences
        ),
        "historical_only_projection_roles": [
            item
            for item in current_metadata_correspondences
            if item.get("classification")
            in {
                "historical_private_control_current_absence",
                "historical_generated_version_metadata",
            }
        ],
        "current_projection_byteequal_members": 2136
        - len(current_metadata_correspondences)
        - len(current_presentation_correspondences)
        - len(current_author_profile_correspondences)
        - len(current_intake_guard_correspondences),
        "current_metadata_source_correspondences": current_metadata_correspondences,
        "current_presentation_source_correspondences": current_presentation_correspondences,
        "current_author_profile_source_correspondences": current_author_profile_correspondences,
        "current_intake_guard_source_correspondences": current_intake_guard_correspondences,
        "original_projection_members_retained_unchanged": 2136,
        "paths_sha256": canonical_json_sha256(sorted(names)),
        "scope": "Eleven genuine constrained author products retain the complete 195-attempt source experiment,192 completed/3 refused training items and14 scored/BECKHAM refused folds. Original source/resources and original900-file work are retained byteexact. Current source matches except explicitly returned Nordic metadata, atlas-presentation, author-profile owner-criterion or archive-intake guard correspondences; no whole-current-tree equality is claimed; historical presentation, absent retired private control, generated version metadata, named documentation and finite IO/export roles are explicitly returned. This transports actual numerical evidence without refitting/scoring/R and supplies no ecological validation, new untouched cohort, Nordic transfer, rights or qualified human/release decision.",
    }
