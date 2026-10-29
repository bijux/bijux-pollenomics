"""Certify the exact baseline read by a completed diagnostic, without producing it."""

from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
from typing import Any

from ...contracts import ReportRebuildError
from ...retained_source import validated_descriptor

BASELINE = "docs/report/pollen-reconstruction/author-lra-constrained/optimizer-gradient/baseline.json"
CAPTURE = (
    "data/method-certification/author-optimizer-diagnostic-source-capture/capture.json"
)
CAPTURE_SHA = "f865795aac7585e56c4cf44faac84496d339e1c176fc6ee111cba3cbc9b4ce93"
BASELINE_PIN: dict[str, Any] = {
    "sha256": "68afb09419754130f482783397f58b12c7c06ee041430b24d264dc7f9c30e009",
    "bytes": 2090,
}
OWNER = (
    "pollen-reconstruction/author-lra-constrained/optimizer-gradient/baseline-reference"
)
ORIGINAL_OWNER: dict[str, Any] = {
    "owner_id": OWNER,
    "role": "unresolved",
    "paths": [BASELINE],
    "producer_paths": [],
    "producer_inputs": [],
    "verification": "Read baseline input, not produced by the bounded optimizer diagnostic.",
}
WITNESS = "reports/science/source-cohorts/optimizer-baseline-input.json"
CANDIDATE = "19642380cc6051ed9d6cfc3fbddfdb56b4feeba7"
PREFIX = "executions/optimizer-diagnostics/"
PLAN_SHA = "fb37c521a0e1e92bb5e9369f2a0da84b1474183fbca350ca0c957cde12bf22f5"
COMMON_SHA = "629bf03b2c1eb8b77388be4de39e04d3cdb2fc38a9a73678aed7affb5d133401"
OUTER_SHA = "5aec38e2319d4615a4a6210dd5776e547a1686cec334a90684eab9fbf54b9906"
REVIEW_SHA = "d36511f2a2c26c223294a79fe5307548b02cf8e3ab1bb78bb496290ee1ccf798"
SOURCE = BASELINE.removesuffix("baseline.json") + "replay.py"
SOURCE_SHA = "6383372379623ced187c8b8b5dd43f813dd5ec384a467f872bb99b579e2d1e38"
READ_LIMIT = 64 * 1024**2


def require(value: object, reason: str) -> None:
    """Refuse retained evidence that violates its declared contract."""
    if not value:
        raise ValueError("Optimizer input certificate: " + reason)


def exact(left: Any, right: Any) -> None:
    """Compare source values without coercing native types or missing values."""
    require(type(left) is type(right), "Metadata type differs")
    if isinstance(left, dict):
        require(list(left) == list(right), "Metadata keys/order differ")
        for key in left:
            exact(left[key], right[key])
    elif isinstance(left, list):
        require(len(left) == len(right), "Metadata list differs")
        for a, b in zip(left, right, strict=True):
            exact(a, b)
    else:
        require(left == right, "Metadata value differs")


def load(raw: bytes) -> Any:
    """Decode retained JSON while preserving declared member identities."""

    def pairs(rows: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in rows:
            require(key not in result, "Duplicate JSON key")
            result[key] = value
        return result

    def refuse(token: str) -> None:
        raise ValueError("Nonfinite JSON token: " + token)

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=refuse)


def physical_file(repository: Path, name: str) -> Path:
    """Resolve only the exact ordinary file within the retained source root."""
    logical = PurePosixPath(name)
    require(
        bool(logical.parts)
        and not logical.is_absolute()
        and logical.as_posix() == name
        and ".." not in logical.parts
        and "\\" not in name,
        "Normalized relative file required",
    )
    path = repository / name
    require(
        repository.is_absolute()
        and repository == repository.resolve()
        and not any(p.is_symlink() for p in (path, *path.parents))
        and stat.S_ISREG(path.lstat().st_mode),
        "Physical regular file without aliases required",
    )
    return path


def owner_projection(owners: list[dict[str, Any]]) -> bool:
    """Extract the exact input and output roles of the declared report owner."""
    selected = [row for row in owners if row.get("owner_id") == OWNER]
    require(len(selected) == 1, "One exact baseline owner required")
    retained = deepcopy(ORIGINAL_OWNER)
    retained["role"] = "retained_source"
    require(
        selected[0] in (ORIGINAL_OWNER, retained),
        "Original full input-reference criterion required",
    )
    exact(
        selected[0],
        retained if selected[0]["role"] == "retained_source" else ORIGINAL_OWNER,
    )
    require(
        all(
            other is selected[0] or BASELINE not in other.get("paths", [])
            for other in owners
        ),
        "Baseline owner overlap",
    )
    return bool(selected[0]["role"] == "retained_source")


def exact_namespace(root: Path, members: set[str]) -> None:
    """The existing public packet admits only its exact regular members and parents."""
    allowed = members | {"capture.json"}
    directories = {
        str(parent)
        for name in members
        for parent in PurePosixPath(name).parents
        if str(parent) != "."
    }
    pending = [root]
    found: set[str] = set()
    while pending:
        directory = pending.pop()
        for child in directory.iterdir():
            name = child.relative_to(root).as_posix()
            mode = child.lstat().st_mode
            require(not child.is_symlink(), "Packet alias")
            if stat.S_ISDIR(mode):
                require(name in directories, "Unexpected packet directory")
                pending.append(child)
            else:
                require(
                    stat.S_ISREG(mode) and name in allowed,
                    "Unexpected packet member or special",
                )
                found.add(name)
    exact(sorted(found), sorted(allowed))


def record_join(
    capture: dict[str, Any],
    plan: dict[str, Any],
    common: dict[str, Any],
    outer: dict[str, Any],
    review: dict[str, Any],
) -> dict[str, Any]:
    """Authenticate original input role and completed consumption, never its generation."""
    exact(
        capture["schema_version"],
        "retained-author-optimizer-diagnostic-source-capture.v1",
    )
    history = capture["original_execution_custody"]["optimizer-diagnostics"]
    for doc in (plan, common, outer, review, history):
        exact(doc["candidate"], CANDIDATE)
    exact(common["plan_sha256"], PLAN_SHA)
    exact(outer["plan_sha256"], PLAN_SHA)
    exact(outer["common_terminal"]["sha256"], COMMON_SHA)
    exact(common["canonical_before"], plan["canonical_identity"])
    exact(common["canonical_after"], plan["canonical_identity"])
    exact(common["before_pin_mismatches"], [])
    exact(common["after_pin_mismatches"], [])
    exact(common["absent_input_paths_unchanged"], True)
    exact(common["status"], "passed")
    for value in (
        common["actual_exit"],
        outer["actual_exit"],
        outer["common_actual_exit"],
    ):
        exact(value, 0)
    exact(outer["memory_bound_pass"], True)
    exact(outer["storage_bound_pass"], True)
    exact(len(common["stages"]), 3)
    exact(len(plan["stages"]), 3)
    for actual, declared in zip(common["stages"], plan["stages"], strict=True):
        for key in ("id", "argv", "timeout_seconds", "must_succeed"):
            exact(actual[key], declared[key])
        exact(actual["actual_exit"], 0)
        exact(actual["timed_out"], False)
    exact(len(plan["input_pins"]), 33320)
    exact(len({row["path"] for row in plan["input_pins"]}), 33320)
    exact(history["original_input_count"], 33320)
    exact(history["original_plan_sha256"], PLAN_SHA)
    exact([row["original"] for row in history["input_custody"]], plan["input_pins"])
    baseline = plan["gradient_baseline"]
    exact({k: baseline[k] for k in BASELINE_PIN}, BASELINE_PIN)
    exact(baseline["path"], str(Path(plan["repository"]) / BASELINE))
    exact(
        [row for row in plan["input_pins"] if row["path"] == baseline["path"]],
        [baseline],
    )
    exact(
        capture["reference_inputs"],
        [
            {
                "path": BASELINE,
                "record": baseline,
                "classification": "Read input; not produced by this diagnostic execution",
            }
        ],
    )
    require(
        all(row["path"] != BASELINE for row in capture["report_outputs"]),
        "Read baseline cannot be a produced report",
    )
    exact(history["original_controller_members"], 8)
    exact(history["exact_derived_input_files"], 47)
    for key in (
        "all_complete_diagnostic_typed_values_exact",
        "all_original_baselines_and_refusals_exact",
        "actual_diagnostic_optimizers_run",
    ):
        exact(review[key], True)
    for key in (
        "full_experiment_fit_or_new_prediction_executed",
        "R_executed",
        "scientific_or_official_release_acceptance",
    ):
        exact(review[key], False)
    exact(review["held_out_prediction_count"], 0)
    return {
        "schema_version": "optimizer-retained-baseline-input-certificate.v1",
        "capture": {"path": CAPTURE, "sha256": CAPTURE_SHA},
        "baseline": {"path": BASELINE, **BASELINE_PIN},
        "source_candidate": CANDIDATE,
        "plan_sha256": PLAN_SHA,
        "native_stage_exits": [0, 0, 0],
        "common_and_outer_exits": [0, 0],
        "original_input_count": 33320,
        "baseline_role": "read_input",
        "baseline_produced_by_diagnostic": False,
        "original_baseline_generation_recovered": False,
        "new_optimizer_or_R_execution": False,
        "historical_attempt_admitted": False,
        "new_heldout_scientific_rights_human_or_LRA_admission": False,
    }


def certificate(repository: Path) -> dict[str, Any]:
    """Read only the named public certificate closure, bounded before any payload read."""
    consumed = 0
    observed: list[tuple[str, str, int]] = []

    def read(name: str, checksum: str, size: int | None = None) -> bytes:
        nonlocal consumed
        path = physical_file(repository, name)
        length = path.stat().st_size
        require(size is None or length == size, "Expected file length differs")
        require(consumed + length <= READ_LIMIT, "Certificate metadata budget exceeded")
        raw = path.read_bytes()
        consumed += len(raw)
        require(
            len(raw) == length and hashlib.sha256(raw).hexdigest() == checksum,
            "Same-buffer source identity differs",
        )
        observed.append((name, checksum, length))
        return raw

    capture = load(read(CAPTURE, CAPTURE_SHA, 24065564))
    members = {
        row["path"]: {k: row[k] for k in ("sha256", "bytes")}
        for row in capture["members"]
    }
    exact(len(members), 2222)
    exact(len(capture["members"]), 2222)
    try:
        source_buffer = validated_descriptor(
            repository, str(PurePosixPath(CAPTURE).parent), members
        )
    except ReportRebuildError as error:
        raise ValueError(str(error)) from error

    def member(name: str, checksum: str) -> bytes:
        require(name in members, "Missing public certificate member")
        exact(members[name]["sha256"], checksum)
        nonlocal consumed
        expected_size = members[name]["bytes"]
        require(
            consumed + expected_size <= READ_LIMIT,
            "Certificate metadata budget exceeded",
        )
        raw = source_buffer.read_source(name)
        consumed += len(raw)
        require(
            len(raw) == expected_size and hashlib.sha256(raw).hexdigest() == checksum,
            "Same-buffer source identity differs",
        )
        return raw

    documents = [
        load(member(PREFIX + name, checksum))
        for name, checksum in (
            ("plan.json", PLAN_SHA),
            ("terminal.json", COMMON_SHA),
            ("diagnostic-terminal.json", OUTER_SHA),
            ("independent-diagnostic-review.json", REVIEW_SHA),
        )
    ]
    plan, common, outer, review = documents
    result = record_join(capture, plan, common, outer, review)
    raw = member(PREFIX + "first-party-inputs/" + BASELINE, BASELINE_PIN["sha256"])
    exact(len(raw), BASELINE_PIN["bytes"])
    exact(read(BASELINE, BASELINE_PIN["sha256"], BASELINE_PIN["bytes"]), raw)
    source_name = PREFIX + "first-party-inputs/" + SOURCE
    source = member(source_name, SOURCE_SHA)
    source_pin = next(
        row
        for row in plan["input_pins"]
        if row["path"] == str(Path(plan["repository"]) / SOURCE)
    )
    exact({key: source_pin[key] for key in ("sha256", "bytes")}, members[source_name])
    assignments = [
        ast.unparse(node)
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Assign)
    ]
    require(
        "BASELINE = Path(__file__).with_name('baseline.json')" in assignments
        and "baseline = json.loads(BASELINE.read_text())" in assignments,
        "Exact original source baseline read missing",
    )
    for name, checksum, size in observed.copy():
        read(name, checksum, size)
    try:
        source_buffer.validate()
    except ReportRebuildError as error:
        raise ValueError(str(error)) from error
    return result


def validated_optimizer_input_reference(
    repository: Path, owners: list[dict[str, Any]]
) -> dict[str, Any]:
    """Legacy unresolved input may remain; published certificate cannot silently disappear."""
    retained = owner_projection(owners)
    witness = repository / WITNESS
    present = witness.exists() or witness.is_symlink()
    if not retained and not present:
        return {}
    require(
        retained and present,
        "Published baseline certificate needs its exact retained input owner",
    )
    expected = certificate(repository)
    path = physical_file(repository, WITNESS)
    require(path.stat().st_size <= 16384, "Bounded scientific witness required")
    exact(load(path.read_bytes()), expected)
    return expected
