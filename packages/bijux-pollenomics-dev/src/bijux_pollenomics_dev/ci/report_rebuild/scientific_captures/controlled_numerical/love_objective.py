"""Authenticate one conditional LOVE objective workload, preserving three actual job histories."""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
from typing import Any

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry
from bijux_pollenomics_dev.ci.report_rebuild.contracts import (
    JsonObject,
    ReportRebuildError,
)
from bijux_pollenomics_dev.ci.report_rebuild.ownership import (
    ReportOwnershipError,
    _regular_confined_file,
)

from ...retained_source import validate_capsule

CAPTURE = "data/method-certification/love-objective-parity-source-capture/capture.json"
REPORT = "docs/report/method-certification/love-objective-parity/report.json"
OWNER = "method-certification/love-objective-parity/report-products"
SOURCE_CANDIDATE = "123c7811e49cc692c32015826c029b8ad99e96d8"
CAPTURE_SHA256 = "3296ca7d44a2a96ea70f984f411296534f57d474117d523d15cfcc63930d6504"
R_ROLE = "source-R-thirty-two-candidate-replay"
PYTHON_ROLE = "public-Python-thirty-two-candidate-replay"
OBSERVER_ROLE = "independent-shared-input-and-all-vector-observer"

EXPECTED_EXECUTIONS: dict[str, dict[str, str]] = {
    "R": {
        "plan.json": "2af00a74117e7b8e0d6e46d017076b9f8c0d49742f8f0732b383b9e881376826",
        "terminal.json": "ffbd908d393e5c56b8673516bc5f861c3a35ea7d8ea17e01cba9ef76f5c462c7",
        "love-parity-terminal.json": "d797f572081ce3e0eaacf445c3815a25d885f96e6917bdf54dc42dd68b2d7d82",
        "runtime-custody-terminal.json": "735f334413b7543f8c9ab0a60bbd98dd8d6e140de1e367526483ceba46454c55",
    },
    "Python": {
        "plan.json": "383704f82627e9291ef2706b130dc8aa72cc3c425b9e5c133c5616dcb3d5e388",
        "terminal.json": "dcb18ec5c33eb904b5044666b7f6546679955ee380ea5a1c8d6311b5595db9d2",
        "love-parity-terminal.json": "2031142baf0e256e42d272f48f079fa2cbaa46141bb580e8ce877595806ae53e",
        "runtime-custody-terminal.json": "e799032c319425bd90af606f47df8a4396c7f80ad21418b90b580de10253c8a7",
    },
    "observer": {
        "plan.json": "e5824cfcc904c3a5d715a555ecea599811652d24fdbde3afebff9da4cabff3c7",
        "terminal.json": "70aff974d7b26d043d386ce1623f3b62ff6ef2dd15aa0ecc3898729bdb2faf31",
        "love-parity-terminal.json": "8c15e3f92115ed59ef589de910c77213312e94602809f9e74eacc42ed9839223",
        "runtime-custody-terminal.json": "6b6e4c4d10f40ffbce209baa216ec51dec670ad6c977df08b676aee688d0dfce",
        "independent-review.json": "0b7cf3c2c1afeadfcdfb2c181497ed35098da3b6b38d80a8d626bcf90c2a40b3",
    },
}


def require(value: object, reason: str) -> None:
    """Refuse a retained source or scope inconsistency."""
    if not value:
        raise ValueError(reason)


def zero(value: object) -> bool:
    """Require a literal successful exit without Boolean aliases."""
    return type(value) is int and value == 0


def stages(
    declared: list[dict[str, Any]],
    actual: list[dict[str, Any]],
    roles: tuple[str, ...],
    exits: tuple[int, ...],
) -> None:
    """Bind original stage membership, exits and input custody."""
    require(len(actual) == len(roles) == len(exits), "Native stage population differs")
    require(len(declared) >= len(actual), "Native stage declaration missing")
    for planned, result, role, code in zip(
        declared, actual, roles, exits, strict=False
    ):
        require(
            planned["id"] == result["id"] == role
            and planned["must_succeed"] is result["must_succeed"] is True
            and type(result["actual_exit"]) is int
            and result["actual_exit"] == code
            and result["timed_out"] is False
            and all(planned[key] == result[key] for key in ("argv", "timeout_seconds")),
            "Native argv/status/timeout or role differs",
        )


def qualify_scope(
    R_plan: Mapping[str, Any],
    R_common: Mapping[str, Any],
    Python_plan: Mapping[str, Any],
    Python_common: Mapping[str, Any],
    observer_plan: Mapping[str, Any],
    observer_common: Mapping[str, Any],
    independent: Mapping[str, Any],
) -> None:
    """Preserve both failed whole jobs; require only the separate saved observer0.

    This pure component is not packet authentication. A maintained caller must
    first authenticate sealed hashes, exact full receipt/plan/resource/log
    populations, ordered original inputs and retained source members. Future
    observer receipts cannot be supplied until a registered actual run completes.
    """
    require(
        type(R_common["actual_exit"]) is int and R_common["actual_exit"] == 1,
        "Original R job whole1 must remain literal",
    )
    require(
        type(Python_common["actual_exit"]) is int and Python_common["actual_exit"] == 1,
        "Original Python job whole1 must remain literal",
    )
    require(len(R_plan["stages"]) == 3, "Original R job declaration differs")
    stages(R_plan["stages"], R_common["stages"], (R_ROLE, PYTHON_ROLE), (0, 1))
    require(len(Python_plan["stages"]) == 2, "Original Python job declaration differs")
    stages(
        Python_plan["stages"],
        Python_common["stages"],
        (PYTHON_ROLE, OBSERVER_ROLE),
        (0, 1),
    )
    require(
        len(observer_plan["stages"]) == 1 and zero(observer_common["actual_exit"]),
        "Separate sole-observer native0 required",
    )
    stages(observer_plan["stages"], observer_common["stages"], (OBSERVER_ROLE,), (0,))
    candidate = R_plan["candidate"]
    for plan, common in (
        (R_plan, R_common),
        (Python_plan, Python_common),
        (observer_plan, observer_common),
    ):
        require(
            plan["candidate"] == common["candidate"] == candidate
            and common["canonical_before"]
            == common["canonical_after"]
            == plan["canonical_identity"]
            and common["before_pin_mismatches"] == common["after_pin_mismatches"] == []
            and common["absent_input_paths_unchanged"] is True,
            "Original execution source/custody differs; adoption epoch is separate",
        )
    require(
        independent["candidate"] == candidate and zero(independent["actual_exit"]),
        "Independent saved observation did not genuinely pass",
    )
    saved_R = observer_plan["retained_completed_R"]
    saved_Python = observer_plan["retained_completed_Python"]
    require(
        saved_R["original_whole_actual_exit"]
        == saved_Python["original_whole_actual_exit"]
        == 1
        and type(saved_R["original_whole_actual_exit"]) is int
        and type(saved_Python["original_whole_actual_exit"]) is int
        and saved_R["original_candidate"]
        == saved_Python["original_candidate"]
        == candidate
        and saved_R["original_stage_actual_exits"]
        == saved_Python["original_stage_actual_exits"]
        == [0, 1]
        and saved_R["retained_completed_R_stage"] == R_common["stages"][0]
        and saved_Python["retained_completed_Python_stage"]
        == Python_common["stages"][0],
        "Separate completed producer receipt reuse differs",
    )
    require(
        independent["retained_completed_R"] == saved_R
        and independent["retained_completed_Python"] == saved_Python
        and independent["actual_R_command"] == R_common["stages"][0]["argv"]
        and independent["actual_Python_command"] == Python_common["stages"][0]["argv"],
        "Observer must bind actual original producer commands, not its own argv",
    )
    contract = independent["numerical_contract"]
    require(
        contract
        == R_plan["numerical_contract"]
        == Python_plan["numerical_contract"]
        == observer_plan["numerical_contract"]
        and type(contract["candidate_rows"]) is int
        and contract["candidate_rows"] == 32
        and type(contract["active_optimizer_calls"]) is int
        and contract["active_optimizer_calls"] == 8
        and contract["absolute_tolerance"] == 3e-10
        and contract["relative_tolerance"] == 1e-10,
        "Original predeclared numerical contract changed",
    )
    objective_events = independent["Python_objective_events"]
    require(
        all(
            type(objective_events.get(k)) is int
            for k in (
                "search_returns_compared_to_R",
                "solver_certification_returns",
                "all_Python_tf_returns",
                "complete_actual_contexts",
                "observer_objective_calls",
            )
        )
        and objective_events.get("selected_first_finite_minimum_certified") is True
        and objective_events
        == {
            "search_returns_compared_to_R": 256,
            "solver_certification_returns": 8,
            "all_Python_tf_returns": 264,
            "complete_actual_contexts": 264,
            "selected_first_finite_minimum_certified": True,
            "observer_objective_calls": 0,
        },
        "Complete search/certification scope differs",
    )
    calls = independent["per_call_objectives"]
    require(len(calls) == 8, "All active objective calls required")
    for index, call in enumerate(calls, 1):
        require(
            type(call["call"]) is int
            and call["call"] == index
            and type(call["vectors_compared"]) is int
            and call["vectors_compared"] == 32
            and type(call["selected_index_one_based"]) is int
            and 1 <= call["selected_index_one_based"] <= 32,
            "Per-vector/selection population differs",
        )
    products = independent["products"]
    require(
        set(products) == {"cover", "pollen", "objective", "k"},
        "Complete output roles required",
    )
    for name, shape in (
        ("cover", [10, 10]),
        ("pollen", [10, 10]),
        ("objective", [10, 2]),
        ("k", [36, 10]),
    ):
        row = products[name]
        require(row["shape"] == shape, "Actual product shape differs")
        cells = shape[0] * shape[1]
        require(
            type(row["finite_pairs"]) is int
            and type(row["NaN_pairs"]) is int
            and 0 <= row["finite_pairs"] <= cells
            and 0 <= row["NaN_pairs"] <= cells
            and row["finite_pairs"] + row["NaN_pairs"] <= cells,
            "Actual finite/missing denominator invalid",
        )
        error = row["maximum_absolute_finite_error"]
        require(
            error is None
            or (type(error) in (float, int) and math.isfinite(error) and error >= 0),
            "Actual observed error metadata is invalid",
        )
    require(
        independent["old56_source_gate_waived"] is False
        and independent["historical_performance_reproduced"] is False
        and independent["new_CPP_adopted"] is False
        and independent["optimizer_convergence_tested"] is False,
        "Numerical correspondence expanded to historical/performance/adoption scope",
    )


def report_projection(
    review: dict[str, Any], histories: dict[str, Any]
) -> dict[str, Any]:
    """Use only actual observed cells/errors; no historical measurement substitution."""
    require(
        type(review["actual_exit"]) is int and review["actual_exit"] == 0,
        "No completed independent observation",
    )
    return {
        "schema_version": "love-objective-source-correspondence.v1",
        "source_candidate": SOURCE_CANDIDATE,
        "native_histories": histories,
        "numerical_contract": review["numerical_contract"],
        "shared_inputs": review["shared_inputs"],
        "per_call_objectives": review["per_call_objectives"],
        "objective_argument_comparison": review["objective_argument_comparison"],
        "Python_objective_events": review["Python_objective_events"],
        "products": review["products"],
        "actual_R_command": review["actual_R_command"],
        "actual_Python_command": review["actual_Python_command"],
        "historical_56_source_gate_waived": False,
        "historical_performance_reproduced": False,
        "optimizer_convergence_tested": False,
        "CPP_adoption_claimed": False,
        "ecological_rights_or_human_acceptance_claimed": False,
        "scope": "One captured conditional32-vector source/software comparison; fixed samplers, original calK/rounding and undefined rings preserved. No R/Python model rerun or observer objective calls during retention.",
    }


def finalize_product(
    row: dict[str, Any], raw: bytes, root: Path, terminal_sha: str, status: str
) -> dict[str, Any]:
    """Preserve the catalog prefix; accept only common906's exact one-line tail."""
    require(type(row["bytes"]) is int, "Catalog size must be an integer")
    if row["path"] == str(root / "runtime-delegate.stdout"):
        tail = (
            json.dumps(
                {
                    "terminal": str(root / "terminal.json"),
                    "sha256": terminal_sha,
                    "status": status,
                }
            )
            + "\n"
        ).encode()
        require(
            len(raw) == row["bytes"] + len(tail)
            and hashlib.sha256(raw[: row["bytes"]]).hexdigest() == row["sha256"]
            and (raw[row["bytes"] :] == tail),
            "Final common stream prefix/tail differs",
        )
    else:
        require(
            len(raw) == row["bytes"]
            and hashlib.sha256(raw).hexdigest() == row["sha256"],
            "Completed product differs",
        )
    return {
        "path": row["path"],
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
    }


def native_outer(
    plan: dict[str, Any],
    common: dict[str, Any],
    inner: dict[str, Any],
    outer: dict[str, Any],
    plan_sha: str,
    expected_exit: int,
) -> None:
    """Preserve original native resource and terminal observations."""
    for result in (common, inner, outer):
        require(
            result["plan_sha256"] == plan_sha
            and type(result["actual_exit"]) is int
            and (result["actual_exit"] == expected_exit),
            "Actual execution reference/whole differs",
        )
    require(plan["candidate"] == SOURCE_CANDIDATE, "Original source epoch differs")
    require(
        inner["candidate"] == outer["source_candidate"] == plan["candidate"]
        and inner["after_input_error"] is None
        and (inner["timed_out"] is False)
        and (inner["common_actual_exit"] == expected_exit),
        "Inner source custody differs",
    )
    require(
        outer["before_runtime_error"] is None
        and outer["after_runtime_error"] is None
        and (outer["timed_out"] is False)
        and (outer["delegate_actual_exit"] == expected_exit)
        and (outer["output_measurement_error"] is None)
        and (outer["resource_bounds_met"] is (expected_exit == 0)),
        "Native runtime/resource scope differs",
    )


def _typed_equal(left: Any, right: Any) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(
            _typed_equal(left[k], right[k]) for k in left
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(
            _typed_equal(a, b) for a, b in zip(left, right, strict=True)
        )
    return bool(left == right)


def _name(value: str) -> str:
    path = PurePosixPath(value)
    require(
        bool(value)
        and bool(path.parts)
        and not path.is_absolute()
        and ".." not in path.parts
        and path.as_posix() == value
        and "\\" not in value,
        "Capsule member escapes",
    )
    return value


def _object(path: Path) -> dict[str, Any]:
    def pairs(rows: list[tuple[str, Any]]) -> dict[str, Any]:
        require(len(rows) == len({key for key, _ in rows}), "Duplicate JSON key")
        return dict(rows)

    result = json.loads(path.read_bytes(), object_pairs_hook=pairs)
    json.dumps(result, allow_nan=False)
    require(isinstance(result, dict), "JSON object required")
    assert isinstance(result, dict)
    return result


def _file(repository: Path, name: str) -> Path:
    try:
        return _regular_confined_file(
            repository, _name(name), "Captured LOVE objective correspondence"
        )
    except (OSError, ReportOwnershipError) as error:
        raise ReportRebuildError(
            "LOVE captured member missing, aliased or unconfined"
        ) from error


def _validate_members(root: Path, members: dict[str, Any]) -> None:
    prefix = Path(CAPTURE).parent.as_posix()
    require(root.as_posix().endswith("/" + prefix), "Exact capsule prefix required")
    repository = root.parents[len(PurePosixPath(prefix).parts) - 1]
    require(repository / prefix == root, "Exact repository capsule required")
    for name, expected in members.items():
        _name(name)
        require(
            name == "payloads/" + expected["sha256"],
            "Content-addressed public member identity differs",
        )
    try:
        validate_capsule(repository, prefix, members)
    except ReportRebuildError as error:
        raise ValueError(str(error)) from error


def _records(
    root: Path, packet: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    members = packet["members"]
    documents = {}
    allowed = {
        "retained_first_party_source_or_resource",
        "retained_public_control_or_declared_input",
        "omitted_runtime_or_dependency_identity_only",
        "omitted_bytecode_identity_only",
        "retained_incremental_public_control_or_product",
    }
    for label, job in packet["jobs"].items():
        require(label in {"R", "Python", "observer"}, "Unknown native history")
        require(
            set(job["references"]) == set(EXPECTED_EXECUTIONS[label]),
            "Exact original native reference population differs",
        )
        for filename, member in job["references"].items():
            require(
                members[member]["sha256"] == EXPECTED_EXECUTIONS[label][filename],
                "Exact original native reference SHA differs",
            )
        records = {
            name: _object(root / _name(member))
            for name, member in job["references"].items()
        }
        plan = records["plan.json"]
        inputs = plan["input_pins"]
        roles: dict[int, tuple[str, str | None]] = {}
        counts: dict[str, int] = {}
        for group in job["original_input_roles"]:
            scope = group["scope"]
            require(
                scope in allowed and scope not in counts, "Unknown/repeated role group"
            )
            require(
                len(group["indices"]) == len(group["members"]),
                "Input role/member axes differ",
            )
            counts[scope] = len(group["indices"])
            for index, member in zip(group["indices"], group["members"], strict=True):
                require(
                    type(index) is int
                    and 0 <= index < len(inputs)
                    and index not in roles,
                    "Original input index differs/repeats",
                )
                roles[index] = (scope, member)
        require(
            len(roles)
            == len(inputs)
            == {"R": 115389, "Python": 115446, "observer": 115489}[label],
            "Original ordered input population differs",
        )
        for index, original in enumerate(inputs):
            scope, member = roles[index]
            if scope.startswith("omitted_"):
                require(member is None, "Runtime/bytecode identity acquired payload")
            else:
                require(
                    members[member] == {k: original[k] for k in ("sha256", "bytes")},
                    "Original public source identity differs",
                )
        require(
            counts.get("retained_first_party_source_or_resource") == 2169
            and counts.get("retained_public_control_or_declared_input") == 71
            and counts.get("omitted_runtime_or_dependency_identity_only") == 108402
            and counts.get("omitted_bytecode_identity_only") == 4747
            and counts.get("retained_incremental_public_control_or_product", 0)
            == {"R": 0, "Python": 57, "observer": 100}[label],
            "Closed original source/omission counts differ",
        )
        documents[label] = records
    require(
        set(documents) == {"R", "Python", "observer"},
        "All three actual histories required",
    )
    r, p, o = documents["R"], documents["Python"], documents["observer"]
    review = o["independent-review.json"]
    qualify_scope(
        r["plan.json"],
        r["terminal.json"],
        p["plan.json"],
        p["terminal.json"],
        o["plan.json"],
        o["terminal.json"],
        review,
    )
    for label, records in documents.items():
        common, inner, outer = (
            records["terminal.json"],
            records["love-parity-terminal.json"],
            records["runtime-custody-terminal.json"],
        )
        expected = 0 if label == "observer" else 1
        checksum = members[packet["jobs"][label]["references"]["plan.json"]]["sha256"]
        require(
            all(
                type(row["actual_exit"]) is int
                and row["actual_exit"] == expected
                and row["plan_sha256"] == checksum
                for row in (common, inner, outer)
            ),
            "Actual whole/plan reference differs",
        )
        require(
            inner["after_input_error"] is None
            and inner["timed_out"] is False
            and outer["before_runtime_error"] is None
            and outer["after_runtime_error"] is None
            and outer["timed_out"] is False
            and outer["output_measurement_error"] is None,
            "Original native source/runtime custody failed",
        )
        native_outer(records["plan.json"], common, inner, outer, checksum, expected)
        require(
            packet["jobs"][label]["source_candidate"]
            == records["plan.json"]["candidate"],
            "Declared captured source differs",
        )
        products = packet["jobs"][label]["products"]
        require(
            len(products) == len(common["products"]),
            "Complete original product catalog differs",
        )
        for product, original in zip(products, common["products"], strict=True):
            require(
                product["original_catalog_pin"] == original,
                "Original product pin rewritten",
            )
            raw = (root / _name(product["member"])).read_bytes()
            final = finalize_product(
                original,
                raw,
                Path(records["plan.json"]["output"]),
                members[packet["jobs"][label]["references"]["terminal.json"]]["sha256"],
                "passed" if label == "observer" else "failed",
            )
            require(
                members[product["member"]]
                == {k: final[k] for k in ("sha256", "bytes")},
                "Final product identity differs",
            )
        # Both completed producer argv come from actual stage receipts, never the metadata assembler.
        require(
            packet["jobs"][label]["whole_actual_exit"] == common["actual_exit"]
            and packet["jobs"][label]["native_stage_actual_exits"]
            == [s["actual_exit"] for s in common["stages"]],
            "Declared native history differs",
        )
    histories = {
        label: {
            key: packet["jobs"][label][key]
            for key in (
                "source_candidate",
                "whole_actual_exit",
                "native_stage_actual_exits",
            )
        }
        for label in documents
    }
    return review, report_projection(review, histories)


def validated_love_objective_capture(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Admit only the sealed new conditional workload report, without rewriting old owners."""
    selected = [row for row in owners if row.get("owner_id") == OWNER]
    if not selected and not (repository / CAPTURE).exists():
        return (), {}
    try:
        require(
            len(CAPTURE_SHA256) == 64
            and all(c in "0123456789abcdef" for c in CAPTURE_SHA256),
            "Actual metadata assembly constant not frozen",
        )
        require(len(selected) == 1, "Exactly one LOVE objective owner required")
        owner = selected[0]
        require(
            owner.get("role") == "retained_source"
            and owner.get("paths") == [REPORT]
            and owner.get("producer_paths") == []
            and owner.get("producer_inputs") == [],
            "Closed LOVE objective ownership differs",
        )
        for other in owners:
            other_paths = other.get("paths", [])
            require(
                isinstance(other_paths, list)
                and all(isinstance(path, str) for path in other_paths),
                "Owner path schema differs",
            )
            assert isinstance(other_paths, list)
            require(
                other is owner or REPORT not in other_paths,
                "Overlapping LOVE report ownership",
            )
        path = _file(repository, CAPTURE)
        require(
            hashlib.sha256(path.read_bytes()).hexdigest() == CAPTURE_SHA256,
            "Sealed LOVE capsule differs",
        )
        packet = _object(path)
        require(
            packet["schema_version"] == "love-objective-execution-source-capture.v1"
            and packet["owner_id"] == OWNER
            and packet["source_candidate"] == SOURCE_CANDIDATE
            and packet["runtime_private_bytecode_payloads_included"] is False
            and packet["original_source_retention_not_native_execution"] is True,
            "LOVE packet source/scope differs",
        )
        _validate_members(path.parent, packet["members"])
        _, expected_report = _records(path.parent, packet)
        publication = _file(repository, REPORT)
        require(
            _typed_equal(_object(publication), expected_report),
            "Published LOVE report differs from genuine saved observation",
        )
        entry = tracked_by_path.get(REPORT)
        require(entry is not None, "Tracked LOVE report required")
        assert entry is not None
        with publication.open("rb") as stream:
            checksum = hashlib.file_digest(stream, "sha256").hexdigest()
        require(
            entry.path == REPORT.removeprefix("docs/report/")
            and entry.kind == "file"
            and entry.sha256 == checksum
            and entry.size == publication.stat().st_size,
            "Tracked LOVE publication identity differs",
        )
        return (entry,), {
            "owner_id": OWNER,
            "paths": [entry.path],
            "capture_sha256": CAPTURE_SHA256,
            "source_candidate": SOURCE_CANDIDATE,
            "original_whole_actual_exits": [1, 1],
            "saved_observer_actual_exit": 0,
            "original_execution_only": True,
            "current_numerical_reuse": False,
            "scope": expected_report["scope"],
        }
    except (KeyError, TypeError, ValueError, OSError) as error:
        raise ReportRebuildError(
            "LOVE retained execution/source admission refused: " + str(error)
        ) from error
