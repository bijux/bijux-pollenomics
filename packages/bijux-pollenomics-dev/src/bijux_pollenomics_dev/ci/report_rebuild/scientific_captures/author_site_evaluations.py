"""Transport source-qualified author evaluations without rerunning scientific models."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any

from bijux_pollenomics.reporting.presentation.report_portal.scientific_accounts import (
    authored_reader,
    parse_routes,
    render_route,
)
from bijux_pollenomics.reporting.presentation.report_portal.scientific_qualifications import (
    validate_evidence,
)
from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry

from ..contracts import JsonObject, ReportRebuildError, canonical_json_sha256
from ..ownership import ReportOwnershipError, _regular_confined_file
from ..retained_source.descriptor import normalize_members
from ..retained_source.generated import reconstruct
from ..retained_source.index import SourceCapsule, validated_descriptor
from .controlled_numerical.author_evaluations import (
    validated_author_score_qualification,
    validated_consumed_source_pair,
)
from .spatial_source_exports import (
    SPATIAL_EXPORT_SOURCE,
    spatial_export_extension_matches,
)

CAPTURE = "data/method-certification/author-site-evaluation-source-capture/capture.json"
CAPTURE_SHA256 = "76617093d6c0802273453bd9c4cdc68d2486e04baa146c4893ae7e441a090f7b"
EXPECTED_MEMBERS = 2406
EXECUTIONS = {
    "uncertainty": (
        "1180a97d7d7356d0f7a6b05d116f342587861997",
        "4cbf712fb818e926dac0193c1c8d59d5c712421864540e4230a454ccd7b64f53",
        "5d219a86ff4b052594c388f77391866d1e5930fd151a19876826f2f20c09127c",
        "independent-author-review.json",
        "bdde25827b73ea9077e3a2e462098c92824f7b6c86a4a60f8210bf57a63b44a0",
    ),
    "profile": (
        "0cca6d4e9cd4df7fa5c844e440c78aceaa162d1b",
        "7c638aeacc285efaf098097102d573c292ade5dfb0a80e3f462b6f0dc84ce5c3",
        "d1310069079fd00f411e588e0551e7f0bb6311530b9872ab29f52bf1de613ea4",
        "independent-author-review.json",
        "baee780d11c9dd4beaf0a68330c46f7bcafdcbec2002c3c52652dd238003961c",
    ),
    "holdout": (
        "cacf5c5d956f379cf21b94b64791e1daf7650f1a",
        "5686bb075723611f3830cfe567374546110be0750fe40f5934a80d104a880e74",
        "371671d61496cf5c72ab9fe03a7bb4bb4caa8375358d4f5cf2e14d8ab83e87ae",
        "independent-author-holdout-review.json",
        "fde90b06321c9d1daf83f6d48b1df09b90505ad7961382e77ea5a82bea0202c2",
    ),
}
OWNERS = {
    "method-certification/author-site-uncertainty/report-products": (
        "docs/report/method-certification/author-site-uncertainty/",
        3,
    ),
    "method-certification/author-site-profile-comparison/report-products": (
        "docs/report/method-certification/author-site-profile-comparison/",
        1,
    ),
    "pollen-reconstruction/author-example-site-mean-holdout/report-products": (
        "docs/report/pollen-reconstruction/author-example-site-mean-holdout/",
        4,
    ),
}


VERSION_SOURCE = (
    "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/_build_version.py"
)
VERSION_SHA256 = "84040f998392398c91779befcbac6807d107b3d1c62a57e4b440dbf1fcc680c5"
VERSION_BYTES = 539
MANAGED_READER = (
    "docs/report/pollen-reconstruction/author-example-site-mean-holdout/REPORT.md"
)
ROUTE_RESOURCE = "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/presentation/report_portal/scientific_accounts.json"
SPATIAL_HISTORICAL_BYTES = 497
SPATIAL_HISTORICAL_SHA256 = (
    "3403cfda5c5791b95312b0293e87d20b8fe3d6f89e9a9814d405d80fb339e6ac"
)


PROFILE_OWNER = "method-certification/author-site-profile-comparison/report-products"

ORIGINAL_PROFILE_OWNER: JsonObject = {
    "owner_id": "method-certification/author-site-profile-comparison/report-products",
    "role": "unresolved",
    "paths": [
        "docs/report/method-certification/author-site-profile-comparison/report.json"
    ],
    "producer_paths": [
        "docs/report/method-certification/author-site-profile-comparison/replay.py",
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction/joint_site_draws.py",
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction/publication.py",
    ],
    "producer_inputs": [
        "docs/report/method-certification/author-site-uncertainty/draws.json",
        "docs/report/method-certification/author-site-uncertainty/report.json",
    ],
    "verification": "Run the documented replay with --repository ., --source-root bound "
    "to the authenticated author release and an absent artifacts output; "
    "compare report.json. Six private LRAready site-count tables listed "
    "in input_identities must close with exact lawful custody first. "
    "Retained author-site-uncertainty report/draw inputs do not replace "
    "those original table bytes or qualify empirical ecology.",
}

PROFILE_POLICY_OWNER: JsonObject = {
    "owner_id": "method-certification/author-site-profile-comparison/report-products",
    "role": "unresolved",
    "paths": [
        "docs/report/method-certification/author-site-profile-comparison/report.json"
    ],
    "producer_paths": [
        "docs/report/method-certification/author-site-profile-comparison/replay.py",
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction/publication.py",
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction/uncertainty/joint_site_draws.py",
    ],
    "producer_inputs": [
        "docs/report/method-certification/author-site-uncertainty/draws.json",
        "docs/report/method-certification/author-site-uncertainty/report.json",
    ],
    "verification": "Run the documented replay with --repository ., --source-root bound "
    "to the authenticated author release and an absent artifacts output; "
    "compare report.json. Six private LRAready site-count tables listed "
    "in input_identities must close with exact lawful custody first. "
    "Retained author-site-uncertainty report/draw inputs do not replace "
    "those original table bytes or qualify empirical ecology.",
}


def _validate_author_owner_partition(owners: list[JsonObject]) -> None:
    """Keep one original unresolved criterion separate from the two retained owners."""
    selected = [row for row in owners if row.get("owner_id") in OWNERS]
    if len(selected) != len(OWNERS) or {row.get("owner_id") for row in selected} != set(
        OWNERS
    ):
        raise ReportRebuildError("Author evaluation exact owner partition differs")
    names: set[str] = set()
    for row in selected:
        if row["owner_id"] == PROFILE_OWNER:
            if row != PROFILE_POLICY_OWNER:
                raise ReportRebuildError(
                    "Author profile original lawful-custody criterion differs"
                )
        elif (
            row.get("role") != "retained_source"
            or row.get("producer_paths") != []
            or row.get("producer_inputs") != []
        ):
            raise ReportRebuildError("Other author evaluation retained owner differs")
        paths = row.get("paths")
        if not isinstance(paths, list) or any(
            not isinstance(path, str) for path in paths
        ):
            raise ReportRebuildError("Author evaluation owner paths differ")
        if names.intersection(paths):
            raise ReportRebuildError("Author evaluation owners overlap")
        names.update(paths)
    for row in owners:
        if row in selected:
            continue
        paths = row.get("paths", [])
        if (
            not isinstance(paths, list)
            or any(not isinstance(path, str) for path in paths)
            or names.intersection(paths)
        ):
            raise ReportRebuildError("Author evaluation owner partition overlaps")


def _file(repository: Path, name: str) -> Path:
    try:
        return _regular_confined_file(repository, name, "retained author evaluation")
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
            or len(stages) != 2
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
            review.get("R_executed") is not False
            or review.get("source_snapshot_members") != 193
            or review.get(
                "all_scientific_typed_values_exact",
                review.get("scientific_typed_values_exact_to_original"),
            )
            is not True
            or review.get(
                "all_source_inputs_exact", review.get("source_private_members_exact")
            )
            is not True
        ):
            raise ReportRebuildError(
                "Retained author source/scientific comparison differs"
            )


def _historical_version_metadata(
    source_buffer: SourceCapsule,
    projection: dict[str, Any],
    members: dict[str, dict[str, Any]],
) -> None:
    """Bind every declared historical version alias without current-file authority."""
    expected = {
        f"executions/{lane}/first-party-inputs/{VERSION_SOURCE}" for lane in EXECUTIONS
    }
    generated = source_buffer.descriptor.generated
    if (
        len(generated) != len(expected)
        or any(type(row) is not dict for row in generated)
        or {row.get("member") for row in generated} != expected
        or type(projection.get("bytes")) is not int
        or projection.get("bytes") != VERSION_BYTES
        or projection.get("sha256") != VERSION_SHA256
    ):
        raise ReportRebuildError(
            "Historical author generated metadata declaration differs"
        )
    for row in generated:
        member = row["member"]
        identity = members.get(member, {})
        if (
            type(identity.get("bytes")) is not int
            or identity.get("bytes") != VERSION_BYTES
            or identity.get("sha256") != VERSION_SHA256
        ):
            raise ReportRebuildError(
                "Historical author generated member identity differs"
            )
        body = source_buffer.read_source(member)
        if (
            len(body) != VERSION_BYTES
            or hashlib.sha256(body).hexdigest() != VERSION_SHA256
            or reconstruct(row, identity) != body
        ):
            raise ReportRebuildError(
                "Historical author generated member content differs"
            )


def _current_managed_reader(
    repository: Path, name: str, historical: bytes, current: bytes
) -> bool:
    """Preserve this authored report while verifying its current qualified route."""
    if name != MANAGED_READER:
        return False
    try:
        routes = parse_routes(
            _file(repository, ROUTE_RESOURCE).read_text(encoding="utf-8")
        )
        route = routes.get(name)
        if route is None or route.qualification is None:
            return False
        validate_evidence(repository, route.qualification, portal=False)
        return (
            authored_reader(historical) == authored_reader(current)
            and render_route(current, route) == current
        )
    except (ValueError, OSError):
        return False


def validated_author_site_evaluation_captures(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Admit the three completed Python evaluations with separate execution epochs."""
    rows = [row for row in owners if row.get("owner_id") in OWNERS]
    if (
        not any(row.get("role") == "retained_source" for row in rows)
        and not (repository / CAPTURE).exists()
    ):
        return (), {}
    _validate_author_owner_partition(owners)
    path = _file(repository, CAPTURE)
    if hashlib.sha256(path.read_bytes()).hexdigest() != CAPTURE_SHA256:
        raise ReportRebuildError("Author evaluation retained capture authority differs")
    capture = _json(path)
    raw_members = capture.get("members")
    if (
        capture.get("schema_version")
        != "retained-author-site-evaluation-source-capture.v1"
        or not isinstance(raw_members, list)
        or type(capture.get("member_count")) is not int
        or capture["member_count"] != len(raw_members)
        or len(raw_members) != EXPECTED_MEMBERS
    ):
        raise ReportRebuildError("Author evaluation capture membership differs")
    members: dict[str, dict[str, Any]] = {}
    prefix = path.parent.relative_to(repository).as_posix()
    for raw in raw_members:
        row = _object(raw)
        name = _member_name(row.get("path"))
        if name in members or type(row.get("bytes")) is not int or row["bytes"] < 0:
            raise ReportRebuildError(
                "Author evaluation retained member identity differs"
            )
        members[name] = row
    source_buffer = validated_descriptor(
        repository, prefix, normalize_members(raw_members)
    )
    _native_references(path.parent, capture)
    projection = capture.get("current_scientific_source_projection")
    if not isinstance(projection, list) or len(projection) != 178:
        raise ReportRebuildError(
            "Author evaluation current scientific source projection differs"
        )
    historical_generated = 0
    spatial_export_role_applied = False
    consumed_correspondences: list[JsonObject] = []
    counting_correspondences: list[JsonObject] = []
    for raw in projection:
        row = _object(raw)
        name = _member_name(row.get("path"))
        if not any(
            members.get(f"executions/{lane}/first-party-inputs/{name}", {}).get(
                "sha256"
            )
            == row.get("sha256")
            for lane in EXECUTIONS
        ):
            raise ReportRebuildError(
                "Author evaluation original scientific source membership differs"
            )
        if name == VERSION_SOURCE:
            _historical_version_metadata(source_buffer, row, members)
            historical_generated += 1
        else:
            current = _file(repository, name)
            if current.stat().st_size != row.get("bytes") or hashlib.sha256(
                current.read_bytes()
            ).hexdigest() != row.get("sha256"):
                historical_member = next(
                    f"executions/{lane}/first-party-inputs/{name}"
                    for lane in EXECUTIONS
                    if members.get(
                        f"executions/{lane}/first-party-inputs/{name}", {}
                    ).get("sha256")
                    == row.get("sha256")
                )
                if name in {
                    "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/api.py",
                    "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/__init__.py",
                }:
                    from .source_correspondence import (
                        validated_current_scientific_source,
                    )

                    role = validated_current_scientific_source(
                        repository, row, historical_member, source_buffer
                    )
                    if (
                        role is None
                        or role.get("classification") != "finite_counting_api_addition"
                    ):
                        raise ReportRebuildError(
                            "Author counting API correspondence differs"
                        )
                    counting_correspondences.append(role)
                    continue
                if name == SPATIAL_EXPORT_SOURCE:
                    historical = source_buffer.read_source(historical_member)
                    if (
                        current.stat().st_nlink != 1
                        or not 0 < current.stat().st_size <= 4096
                        or row.get("bytes") != SPATIAL_HISTORICAL_BYTES
                        or row.get("sha256") != SPATIAL_HISTORICAL_SHA256
                        or len(historical) != SPATIAL_HISTORICAL_BYTES
                        or hashlib.sha256(historical).hexdigest()
                        != SPATIAL_HISTORICAL_SHA256
                        or not spatial_export_extension_matches(
                            historical, current.read_bytes()
                        )
                    ):
                        raise ReportRebuildError(
                            "Author evaluation scientific implementation changed"
                        )
                    spatial_export_role_applied = True
                elif (
                    name
                    != "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/lra_validation/metrics.py"
                ):
                    raise ReportRebuildError(
                        "Author evaluation scientific implementation changed"
                    )
                consumed_correspondences.append(
                    validated_consumed_source_pair(
                        repository, row, historical_member, source_buffer.read_source
                    )
                )
    if historical_generated != 1:
        raise ReportRebuildError(
            "Author evaluation historical generated projection differs"
        )
    consumed_qualification = (
        validated_author_score_qualification(
            repository, consumed_correspondences, source_buffer.read_source
        )
        if consumed_correspondences
        else {}
    )
    products = capture.get("report_outputs")
    if not isinstance(products, list) or len(products) != 8:
        raise ReportRebuildError(
            "Author evaluation needs exactly eight report products"
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
            raise ReportRebuildError("Author evaluation report ownership differs")
        expected = _object(product.get("published"))
        retained = members.get("published/" + name)
        entry = tracked_by_path.get(name)
        current = _file(repository, name)
        current_body = current.read_bytes()
        historical_body = source_buffer.read_source("published/" + name)
        raw_current_exact = len(current_body) == expected.get(
            "bytes"
        ) and hashlib.sha256(current_body).hexdigest() == expected.get("sha256")
        if (
            retained is None
            or retained.get("sha256") != expected.get("sha256")
            or retained.get("bytes") != expected.get("bytes")
            or len(historical_body) != expected.get("bytes")
            or hashlib.sha256(historical_body).hexdigest() != expected.get("sha256")
            or entry is None
            or entry.kind != "file"
            or entry.sha256 != hashlib.sha256(current_body).hexdigest()
            or entry.size != len(current_body)
            or not (
                raw_current_exact
                or _current_managed_reader(
                    repository, name, historical_body, current_body
                )
            )
        ):
            raise ReportRebuildError("Author evaluation published report bytes differ")
        by_owner[owner].append(name)
        accepted.append(entry)
    for row in rows:
        owner = str(row["owner_id"])
        if (
            row.get("paths") != sorted(by_owner[owner])
            or len(by_owner[owner]) != OWNERS[owner][1]
        ):
            raise ReportRebuildError(
                "Author evaluation exact owner path membership differs"
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
            raise ReportRebuildError("Author evaluation retained ownership overlaps")
    profile_paths = PROFILE_POLICY_OWNER["paths"]
    assert isinstance(profile_paths, list)
    retained_entries = tuple(
        entry for entry in accepted if "docs/report/" + entry.path not in profile_paths
    )
    if len(retained_entries) != 7:
        raise ReportRebuildError(
            "Exactly seven other qualified author entries required"
        )
    source_buffer.fresh()
    return retained_entries, {
        "owner_ids": sorted(set(OWNERS) - {PROFILE_OWNER}),
        "observed_owner_ids": sorted(OWNERS),
        "selected_retained_entries": 7,
        "profile_owner_remains_unresolved": True,
        "profile_original_acceptance_discharged": False,
        "profile_original_acceptance_criterion": ORIGINAL_PROFILE_OWNER["verification"],
        "profile_producer_path_only_relocation": True,
        "capture_sha256": CAPTURE_SHA256,
        "executed_source_candidates": {
            lane: values[0] for lane, values in EXECUTIONS.items()
        },
        "report_outputs": 8,
        "current_scientific_projection": 177,
        "ordinary_current_byte_exact_members": 177
        - len(consumed_correspondences)
        - len(counting_correspondences),
        "finite_counting_api_correspondences": counting_correspondences,
        "reviewed_unconsumed_source_deltas": consumed_correspondences,
        "current_saved_score_qualification": consumed_qualification,
        "named_spatial_export_correspondence_members": int(spatial_export_role_applied),
        "managed_reader_projection": MANAGED_READER,
        "historical_generated_metadata_members": 1,
        "historical_generated_logical_aliases": 3,
        "historical_generated_metadata_sha256": VERSION_SHA256,
        "paths_sha256": canonical_json_sha256(
            sorted("docs/report/" + entry.path for entry in retained_entries)
        ),
        "observed_eight_paths_sha256": canonical_json_sha256(sorted(names)),
        "scope": "Three actual prior-exposed English author Python evaluations with original private-source authority retained separately. This authenticates all eight saved products while admitting only the seven other qualified outputs; the profile owner and its exact six-private-table lawful-custody criterion remain unresolved. The declared projection is177 current members. Changed metrics and old497 spatial export sources require their two finite consumed-definition proofs and the retained177-group/425-disposition MAE/TV qualification; the separately listed counting API additions preserve their original whole bytes outside four new bindings and one capability, and all other current members remain byte-exact. The spatial export extension also retains its separately reviewed named import/export predicate. This does not establish whole-current source equality or Hellinger equivalence. One separately authenticated historical539 version identity spans three aliases without current ignored-file equality. The named holdout Markdown report preserves its exact authored bytes and current independently qualified managed footer; the historical whole report remains exact in the capture. This transports completed native products; it executes no R/model/optimizer and grants no ecological, Nordic, rights or human release acceptance.",
    }
