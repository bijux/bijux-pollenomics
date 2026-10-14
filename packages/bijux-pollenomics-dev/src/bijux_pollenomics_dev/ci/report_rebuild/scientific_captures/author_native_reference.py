"""Transport the source-qualified Python comparison to retained tagged-R draws."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry

from ..contracts import JsonObject, ReportRebuildError, canonical_json_sha256
from ..ownership import ReportOwnershipError, _regular_confined_file

CAPTURE = (
    "data/method-certification/author-native-comparison-source-capture/capture.json"
)
CAPTURE_SHA256 = "b5c8e7cb4a1f7a12b99b8d79c9230d0d2b1ba1f7e52cda6ab2afe31622cb95d0"
EXPECTED_MEMBERS = 2209
EXECUTIONS = {
    "native-comparison": (
        "cacf5c5d956f379cf21b94b64791e1daf7650f1a",
        "a8d5006746679caede8c332d6cf1307a6878bed73245db37772b1e9912b936b0",
        "11e284eb7c4280fc2cb04fbb4bea2979acd7bfb4c964f8c4c222fd68ea903ab4",
        "independent-author-development-input-review.json",
        "bb46e0feb51b08fbc5bbb22a4bc48316a6fed23b36c73dc6dcc4f6fe2bef2e94",
    )
}
OWNERS = {
    "method-certification/petrkunes-r-comparison/report-products": (
        "docs/report/method-certification/petrkunes-r-comparison/",
        1,
    )
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
                "author-site-terminal.json",
                observer_name,
            ]
        )
        if (
            hashlib.sha256((root / "plan.json").read_bytes()).hexdigest() != plan_sha
            or hashlib.sha256(
                (root / "author-site-terminal.json").read_bytes()
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
            or len(stages) != 5
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
            review.get("historical_native_comparison_byte_exact") is not True
            or review.get("optimizer_R_or_new_prediction_executed") is not False
            or not _zero(review.get("actual_exit"))
        ):
            raise ReportRebuildError(
                "Retained Python reference comparison source/scientific witness differs"
            )


def validated_author_native_reference_capture(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Admit the completed Python reference comparison with its original execution epoch."""
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
            "Author Python reference comparison owner declarations differ"
        )
    path = _file(repository, CAPTURE)
    if hashlib.sha256(path.read_bytes()).hexdigest() != CAPTURE_SHA256:
        raise ReportRebuildError(
            "Author Python reference comparison retained capture authority differs"
        )
    capture = _json(path)
    raw_members = capture.get("members")
    if (
        capture.get("schema_version")
        != "retained-author-native-comparison-source-capture.v1"
        or not isinstance(raw_members, list)
        or type(capture.get("member_count")) is not int
        or capture["member_count"] != len(raw_members)
        or len(raw_members) != EXPECTED_MEMBERS
    ):
        raise ReportRebuildError(
            "Author Python reference comparison capture membership differs"
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
                "Author Python reference comparison retained member bytes differ"
            )
        members[name] = row
    physical_names: set[str] = set()
    for physical in path.parent.rglob("*"):
        if physical.is_symlink():
            raise ReportRebuildError(
                "Author Python reference comparison packet contains a link"
            )
        if physical.is_file():
            physical_names.add(physical.relative_to(path.parent).as_posix())
    if physical_names != set(members) | {"capture.json"}:
        raise ReportRebuildError(
            "Author Python reference comparison physical packet membership differs"
        )
    _native_references(path.parent, capture)
    projection = capture.get("current_scientific_source_projection")
    if not isinstance(projection, list) or len(projection) != 69:
        raise ReportRebuildError(
            "Author Python reference comparison current scientific source projection differs"
        )
    for raw in projection:
        row = _object(raw)
        name = _member_name(row.get("path"))
        current = _file(repository, name)
        if (
            current.stat().st_size != row.get("bytes")
            or hashlib.sha256(current.read_bytes()).hexdigest() != row.get("sha256")
            or not any(
                members.get(f"executions/{lane}/first-party-inputs/{name}", {}).get(
                    "sha256"
                )
                == row.get("sha256")
                for lane in EXECUTIONS
            )
        ):
            raise ReportRebuildError(
                "Author Python reference comparison scientific implementation changed"
            )
    products = capture.get("report_outputs")
    if not isinstance(products, list) or len(products) != 1:
        raise ReportRebuildError(
            "Author Python reference comparison needs exactly one Python report product"
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
                "Author Python reference comparison report ownership differs"
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
                "Author Python reference comparison published report bytes differ"
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
                "Author Python reference comparison exact owner path membership differs"
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
                "Author Python reference comparison retained ownership overlaps"
            )
    return tuple(accepted), {
        "owner_ids": sorted(OWNERS),
        "capture_sha256": CAPTURE_SHA256,
        "executed_source_candidates": {
            lane: values[0] for lane, values in EXECUTIONS.items()
        },
        "report_outputs": 1,
        "current_scientific_projection": 69,
        "paths_sha256": canonical_json_sha256(sorted(names)),
        "scope": "One actual prior-exposed English nine-site Python historical REVEALS comparison uses exact retained tagged-R reference draws. This transports the completed Python report and unchanged scientific implementation/reference inputs; it executes no R/model/optimizer and does not admit the separate historical R reference owner, ecological accuracy, source rights or human release acceptance.",
    }
