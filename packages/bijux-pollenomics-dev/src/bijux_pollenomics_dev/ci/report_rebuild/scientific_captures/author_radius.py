"""Retain the source-bound radius forward experiment and genuine downstream paired join."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any, TypedDict, cast

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry

from ..contracts import JsonObject, ReportRebuildError, canonical_json_sha256
from ..ownership import ReportOwnershipError, _regular_confined_file
from ..retained_source import validated_descriptor

CAPTURE = "data/method-certification/author-radius-source-capture/capture.json"
CAPTURE_SHA256 = "e7d813c70f4a15befd4d99cd5ca02aa062075cad5e28081aed9aa28ec56b7e41"
EXPECTED_MEMBERS = 5382


class ExecutionAuthority(TypedDict):
    """Identify the retained radius execution and its declared evidence scope."""

    candidate: str
    plan_sha256: str
    outer_file: str
    outer_sha256: str
    observer: str
    observer_sha256: str
    pins: int
    stages: int


EXECUTIONS: dict[str, ExecutionAuthority] = {
    "radius-forward": {
        "candidate": "2784d4eae839e4a4e43f80ec77fd26bd0172aff0",
        "plan_sha256": "0442ab3ec6a44b2ed57a4e4078a3aa2bcb690c51b79a1d08e7bdeb074ea7065e",
        "outer_file": "radius-terminal.json",
        "outer_sha256": "3c4b7c6ffc7bb3242894fdf9f06ad3e88d5dd55022da4643858320a654289957",
        "observer": "independent-radius-comparison-review.json",
        "observer_sha256": "262e6e4b49e6f0779349509ad15ead6a5277ab3964d2ea8952eef149f1b63792",
        "pins": 34271,
        "stages": 3,
    },
    "paired-comparison": {
        "candidate": "aed78f8befdf0449789249e780ad80f13f44e086",
        "plan_sha256": "8ab1ec873ded81bec4475fb2e8065dc3a5be9d6d5e6bcf3d2e88446dee6bc829",
        "outer_file": "paired-terminal.json",
        "outer_sha256": "f88092285b224c771f6b48c1f4af6e51f83eb92fd0682b46a874c1f68a8f2183",
        "observer": "independent-paired-review.json",
        "observer_sha256": "7581607b981a3c2bd917293c5dc2812ddb4242dddeeb9d460a365f56d6547bac",
        "pins": 34313,
        "stages": 2,
    },
}
FAMILY = "docs/report/pollen-reconstruction/author-lra-constrained/radius-sensitivity/"
OWNER = (
    "pollen-reconstruction/author-lra-constrained/radius-sensitivity/report-products"
)
PAIRED_OWNER = (
    "pollen-reconstruction/author-lra-constrained/radius-sensitivity/paired-comparison"
)
OWNERS = {OWNER: (FAMILY, 3)}
OUTPUTS = {
    "frozen/predictions.json": ("radius-forward", "frozen/predictions.json", OWNER),
    "scored/report.json": ("radius-forward", "scored/report.json", OWNER),
    "scored/scores.csv": ("radius-forward", "scored/scores.csv", OWNER),
    "paired/report.json": ("paired-comparison", "paired/report.json", PAIRED_OWNER),
    "paired/paired-scores.csv": (
        "paired-comparison",
        "paired/paired-scores.csv",
        PAIRED_OWNER,
    ),
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


def _native_references(repository: Path, packet: Path, capture: JsonObject) -> None:
    histories = _object(capture.get("original_execution_custody"))
    if set(histories) != set(EXECUTIONS):
        raise ReportRebuildError("Radius execution membership differs")
    resolver = validated_descriptor(
        repository,
        Path(CAPTURE).parent.as_posix(),
        {row["path"]: row for row in cast(list[dict[str, Any]], capture["members"])},
    )
    for lane, spec in EXECUTIONS.items():
        root = packet / "executions" / lane
        paths = [
            root / n
            for n in [
                "plan.json",
                "terminal.json",
                spec["outer_file"],
                spec["observer"],
            ]
        ]
        plan, common, outer, review = [_json(p) for p in paths]
        if any(
            hashlib.sha256(p.read_bytes()).hexdigest() != expected
            for p, expected in [
                (paths[0], spec["plan_sha256"]),
                (paths[2], spec["outer_sha256"]),
                (paths[3], spec["observer_sha256"]),
            ]
        ):
            raise ReportRebuildError("Radius original native authority changed")
        _validate_native(plan, common, outer, review, spec)
        if (
            _object(outer.get("common_terminal")).get("sha256")
            != hashlib.sha256(paths[1].read_bytes()).hexdigest()
        ):
            raise ReportRebuildError("Radius common terminal changed")
        history = _object(histories[lane])
        custody = history.get("input_custody")
        if (
            not isinstance(custody, list)
            or len(custody) != spec["pins"]
            or history.get("original_input_count") != spec["pins"]
            or [_object(r).get("original") for r in custody] != plan.get("input_pins")
            or history.get("candidate") != spec["candidate"]
            or history.get("original_plan_sha256") != spec["plan_sha256"]
        ):
            raise ReportRebuildError("Radius complete original input custody changed")
        public = history.get("public_first_party_inputs")
        if not isinstance(public, list):
            raise ReportRebuildError("Radius original source table absent")
        for value in public:
            row = _object(value)
            source = packet / _member_name(row.get("captured_path"))
            source_raw = resolver.read_source(source.relative_to(packet).as_posix())
            if len(source_raw) != row.get("bytes") or hashlib.sha256(
                source_raw
            ).hexdigest() != row.get("sha256"):
                raise ReportRebuildError("Radius historical source bytes changed")


def _validate_native(
    plan: JsonObject,
    common: JsonObject,
    outer: JsonObject,
    review: JsonObject,
    spec: ExecutionAuthority,
) -> None:
    if (
        any(
            r.get("candidate") != spec["candidate"]
            for r in [plan, common, outer, review]
        )
        or common.get("plan_sha256") != spec["plan_sha256"]
        or outer.get("plan_sha256") != spec["plan_sha256"]
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
        raise ReportRebuildError("Radius original numerical execution did not pass")
    stages, intended = common.get("stages"), plan.get("stages")
    if (
        not isinstance(stages, list)
        or not isinstance(intended, list)
        or len(stages) != spec["stages"]
        or len(intended) != spec["stages"]
    ):
        raise ReportRebuildError("Radius original native stage population differs")
    for a, b in zip(stages, intended, strict=True):
        actual, expected = _object(a), _object(b)
        if (
            actual.get("id") != expected.get("id")
            or actual.get("argv") != expected.get("argv")
            or not _zero(actual.get("actual_exit"))
            or actual.get("timed_out") is not False
        ):
            raise ReportRebuildError("Radius original native argv/status differs")
    expected_launch = [
        plan.get("qualified_python"),
        plan.get("common_runner"),
        "--plan",
        str(PurePosixPath(str(plan.get("output"))) / "plan.json"),
        "--registered-plan-sha256",
        spec["plan_sha256"],
    ]
    if common.get("actual_launch_argv") != expected_launch:
        raise ReportRebuildError("Radius original actual launch differs")
    if spec["stages"] == 3:
        if (
            any(
                review.get(k) is not True
                for k in [
                    "all_historical_scientific_values_types_and_orders_exact",
                    "scores_CSV_byte_exact",
                    "original_33336_inputs_reauthenticated",
                    "complete_900_file_work_reauthenticated",
                ]
            )
            or any(
                type(review.get(k)) is not int or review[k] != n
                for k, n in [
                    ("training_attempts", 195),
                    ("training_completed", 192),
                    ("training_refused", 3),
                    ("frozen_rows", 126),
                    ("scored_sites", 14),
                ]
            )
            or review.get("refused_site") != "author:BECKHAM"
        ):
            raise ReportRebuildError(
                "Radius original source/scientific population differs"
            )
    elif (
        any(
            review.get(k) is not True
            for k in [
                "all_paired_scientific_values_types_orders_exact",
                "paired_CSV_byte_exact",
                "all_126_raw_observation_prediction_and_arithmetic_joins_exact",
            ]
        )
        or any(
            type(review.get(k)) is not int or review[k] != n
            for k, n in [("paired_rows", 126), ("paired_sites", 14)]
        )
        or review.get("excluded_site") != "author:BECKHAM"
        or review.get("new_fit_forward_R_or_optimizer_executed") is not False
    ):
        raise ReportRebuildError("Paired radius original science differs")


def _work_scope(
    packet: Path, capture: JsonObject, members: dict[str, dict[str, Any]]
) -> None:
    root = (
        packet
        / "controlled-inputs/artifacts/science/current-constrained-author-complete-source"
    )
    authority = {
        "plan.json": "7a75256e79a577280d8bd828380ebb8438b80914e3aa8c5ddc390fa428e6428c",
        "constrained-author-terminal.json": "c4ab7b6a50c989cd646454ae2b52020df2bbdc749a4806077a45917117fc1539",
        "independent-constrained-author-review.json": "93f0c05d69b2bd9a59a9b05759e757f8815a48390c0208c72d86c85e0b04cb9f",
    }
    if any(
        hashlib.sha256((root / n).read_bytes()).hexdigest() != expected
        for n, expected in authority.items()
    ):
        raise ReportRebuildError("Radius original195-fit source authority differs")
    plan, common, outer, review = [
        _json(root / n)
        for n in [
            "plan.json",
            "terminal.json",
            "constrained-author-terminal.json",
            "independent-constrained-author-review.json",
        ]
    ]
    if (
        plan.get("candidate") != "22c6e480ba4690cc508202925a8773afe95ab36e"
        or not all(
            _zero(v) for v in [common.get("actual_exit"), outer.get("actual_exit")]
        )
        or _object(outer.get("common_terminal")).get("sha256")
        != hashlib.sha256((root / "terminal.json").read_bytes()).hexdigest()
    ):
        raise ReportRebuildError("Radius original source execution differs")
    if (
        any(
            type(review.get(k)) is not int or review[k] != n
            for k, n in [
                ("native_training_items", 195),
                ("native_completed", 192),
                ("native_refused", 3),
            ]
        )
        or review.get("historical_3d6_terminal_available") is not False
    ):
        raise ReportRebuildError("Radius original195/192/3 scope differs")
    native = review.get("completed_native_products_current_code_and_inventory_verified")
    if not isinstance(native, list) or len(native) != 192:
        raise ReportRebuildError("Radius original completed native population differs")
    native_root = PurePosixPath(str(plan.get("retained_work")))
    original_repo = PurePosixPath(str(plan.get("repository")))
    raw_products = common.get("products")
    if not isinstance(raw_products, list):
        raise ReportRebuildError("Radius original complete work proof absent")
    work = {
        _object(r).get("path"): _object(r)
        for r in raw_products
        if isinstance(_object(r).get("path"), str)
        and PurePosixPath(_object(r)["path"]).is_relative_to(native_root)
    }
    if len(work) != 900:
        raise ReportRebuildError("Radius original work population differs")
    history = _object(
        _object(capture.get("original_execution_custody")).get("radius-forward")
    )
    custody = history.get("input_custody")
    if not isinstance(custody, list):
        raise ReportRebuildError("Radius original input history absent")
    old = {
        _object(_object(r).get("original")).get("path"): _object(
            _object(r).get("original")
        )
        for r in custody
    }
    for name, row in work.items():
        if not isinstance(name, str):
            raise ReportRebuildError("Radius original work path invalid")
        target = (
            "controlled-inputs/"
            + PurePosixPath(name).relative_to(original_repo).as_posix()
        )
        member = members.get(target)
        if (
            old.get(name) != row
            or member is None
            or member.get("sha256") != row.get("sha256")
            or member.get("bytes") != row.get("bytes")
        ):
            raise ReportRebuildError("Radius complete900native work bytes differ")


def validated_author_radius_capture(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Admit three retained radius outputs and authenticate the separate generated paired join."""
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
        raise ReportRebuildError("Radius source experiment owner declarations differ")
    path = _file(repository, CAPTURE)
    if hashlib.sha256(path.read_bytes()).hexdigest() != CAPTURE_SHA256:
        raise ReportRebuildError(
            "Radius source experiment retained capture authority differs"
        )
    capture = _json(path)
    raw_members = capture.get("members")
    if (
        capture.get("schema_version") != "retained-author-radius-source-capture.v1"
        or not isinstance(raw_members, list)
        or type(capture.get("member_count")) is not int
        or capture["member_count"] != len(raw_members)
        or len(raw_members) != EXPECTED_MEMBERS
    ):
        raise ReportRebuildError("Radius source experiment capture membership differs")
    members: dict[str, dict[str, Any]] = {}
    prefix = path.parent.relative_to(repository).as_posix()
    for raw in raw_members:
        row = _object(raw)
        name = _member_name(row.get("path"))
        if name in members:
            raise ReportRebuildError("Duplicate retained source member")
        members[name] = row
    resolver = validated_descriptor(repository, prefix, members)
    _native_references(repository, path.parent, capture)
    paired_producer = _file(repository, FAMILY + "paired_comparison.py")
    captured_producer = resolver.read_source(
        "executions/paired-comparison/actual-producer.py"
    )
    expected_producer = (
        "dba9fac988376d95da7b6aa802674828d410d2e70d0fcb839362084dc5d969e8"
    )
    if any(
        hashlib.sha256(raw).hexdigest() != expected_producer
        for raw in [paired_producer.read_bytes(), captured_producer]
    ):
        raise ReportRebuildError(
            "Radius current paired producer differs from actual owned producer"
        )
    _work_scope(path.parent, capture, members)
    projection = capture.get("current_scientific_source_projection")
    if not isinstance(projection, list) or len(projection) != 2136:
        raise ReportRebuildError(
            "Radius historical scientific source projection differs"
        )
    source_names: set[str] = set()
    for raw in projection:
        row = _object(raw)
        name = _member_name(row.get("path"))
        if name in source_names:
            raise ReportRebuildError("Radius historical source projection duplicates")
        source_names.add(name)
        if (
            set(row) != {"path", "sha256", "bytes"}
            or type(row.get("bytes")) is not int
            or row["bytes"] < 0
            or not any(
                members.get(f"executions/{lane}/first-party-inputs/{name}", {}).get(
                    "sha256"
                )
                == row.get("sha256")
                and members.get(f"executions/{lane}/first-party-inputs/{name}", {}).get(
                    "bytes"
                )
                == row["bytes"]
                for lane in EXECUTIONS
            )
        ):
            raise ReportRebuildError("Radius retained scientific source is unbound")
    products = capture.get("report_outputs")
    if not isinstance(products, list) or len(products) != 5:
        raise ReportRebuildError("Radius needs exactly five genuine produced outputs")
    accepted: list[InventoryEntry] = []
    by_owner: dict[str, list[str]] = {key: [] for key in OWNERS}
    seen: set[str] = set()
    for raw in products:
        product = _object(raw)
        name = _member_name(product.get("path"))
        suffix = name.removeprefix(FAMILY)
        if suffix not in OUTPUTS or name in seen:
            raise ReportRebuildError("Radius output membership differs")
        seen.add(name)
        lane, raw_name, owner = OUTPUTS[suffix]
        if (
            product.get("owner_id") != owner
            or product.get("execution_lane") != lane
            or product.get("raw_name") != raw_name
        ):
            raise ReportRebuildError("Radius product native role differs")
        expected = _object(product.get("produced"))
        retained = members.get("products/" + name)
        native = _object(product.get("raw"))
        native_member = members.get(f"executions/{lane}/products/{raw_name}")
        common = _json(path.parent / "executions" / lane / "terminal.json")
        proofs = common.get("products")
        if (
            not isinstance(proofs, list)
            or len([p for p in proofs if _object(p).get("path") == native.get("path")])
            != 1
            or native not in proofs
            or product.get("native_terminal_product_proof") != native
        ):
            raise ReportRebuildError("Radius native produced bytes not authorized")
        entry = tracked_by_path.get(name)
        current = _file(repository, name)
        if (
            retained is None
            or native_member is None
            or native.get("sha256") != expected.get("sha256")
            or native.get("bytes") != expected.get("bytes")
            or any(
                r.get("sha256") != expected.get("sha256")
                or r.get("bytes") != expected.get("bytes")
                for r in [retained, native_member]
            )
            or entry is None
            or entry.kind != "file"
            or entry.sha256 != expected.get("sha256")
            or entry.size != expected.get("bytes")
            or hashlib.sha256(current.read_bytes()).hexdigest()
            != expected.get("sha256")
            or current.stat().st_size != expected.get("bytes")
        ):
            raise ReportRebuildError("Radius current output bytes differ")
        if owner in OWNERS:
            by_owner[owner].append(name)
            accepted.append(entry)
    paired = [r for r in owners if r.get("owner_id") == PAIRED_OWNER]
    if (
        len(paired) != 1
        or paired[0].get("role") != "generated_owner"
        or paired[0].get("paths")
        != sorted(
            FAMILY + n
            for n, (lane, _, _) in OUTPUTS.items()
            if lane == "paired-comparison"
        )
    ):
        raise ReportRebuildError("Radius paired owner is a separate generated producer")
    for row in rows:
        owner = str(row["owner_id"])
        if (
            row.get("paths") != sorted(by_owner[owner])
            or len(by_owner[owner]) != OWNERS[owner][1]
        ):
            raise ReportRebuildError(
                "Radius source experiment exact owner path membership differs"
            )
    names = {name for values in by_owner.values() for name in values}
    for other in owners:
        other_paths = other.get("paths")
        if (
            other not in rows
            and isinstance(other_paths, list)
            and names.intersection(other_paths)
        ):
            raise ReportRebuildError(
                "Radius source experiment retained ownership overlaps"
            )
    resolver.fresh()
    return tuple(accepted), {
        "owner_ids": sorted(OWNERS),
        "capture_sha256": CAPTURE_SHA256,
        "executed_source_candidates": {
            lane: values["candidate"] for lane, values in EXECUTIONS.items()
        },
        "report_outputs": 3,
        "authenticated_generated_paired_outputs": 2,
        "historical_scientific_source_projection": 2136,
        "current_execution_qualified": False,
        "current_source_equivalence_claimed": False,
        "original_projection_members_retained_unchanged": 2136,
        "paths_sha256": canonical_json_sha256(sorted(names)),
        "scope": "Three genuine source-bound fixed-vegetation radius products and separate generated paired2 retain fourteen exposed English sites, three methods/factors, exact195/192/3 training source custody and BECKHAM refusal. Both original execution epochs and full historicalsource/resources stay explicit; no refit/R, physicalradius, vegetation-accuracy, equal-information independent ranking, Nordic/ecological/rights/human acceptance. The 2136 original source identities are authenticated through retained capsule/Git correspondence independently of current source edits. Current numerical execution and scientific-source equivalence are not qualified; the separately generated paired join retains its own producer contract.",
    }
