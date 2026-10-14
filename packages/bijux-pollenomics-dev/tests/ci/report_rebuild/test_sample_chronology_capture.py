"""Refuse lost or relabelled public-reader and partial source-producer custody."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures import (
    sample_chronology_capture as capture,
)

_Custody = tuple[dict[str, Any], dict[str, Path], dict[str, Any], dict[str, str]]


@pytest.fixture
def actual_custody() -> _Custody:
    repository = next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "packages/bijux-pollenomics-dev/pyproject.toml").is_file()
    )
    path = repository / capture.CURRENT_CAPTURE_PATH
    packet = json.loads(path.read_bytes())
    members = {row["path"]: path.parent / row["path"] for row in packet["files"]}
    review = json.loads(members[packet["independent_review"]["member"]].read_bytes())
    inputs = {
        **packet["source_footprint"],
        **{
            name: resource["sha256"]
            for name, resource in packet["runtime_resources"].items()
        },
    }
    return packet, members, review, inputs


def test_partial_producer_custody(custody: _Custody) -> None:
    capture._validate_current_reader_custody(*custody)


@pytest.mark.parametrize(
    "group", ["current_reader_reference", "reused_source_producer_reference"]
)
def test_absent_reference_group_refuses(custody: _Custody, group: str) -> None:
    packet, members, review, inputs = custody
    del packet[group]
    with pytest.raises(ReportRebuildError, match="reference coverage differs"):
        capture._validate_current_reader_custody(packet, members, review, inputs)


@pytest.mark.parametrize(
    "group,role",
    [
        ("current_reader_reference", "reader"),
        ("current_reader_reference", "observer"),
        ("reused_source_producer_reference", "producer-import-origins"),
    ],
)
def test_independent_reference_digest_refuses(
    custody: _Custody, group: str, role: str
) -> None:
    packet, members, review, inputs = custody
    review[group][role]["sha256"] = "0" * 64
    with pytest.raises(ReportRebuildError, match="reference digest differs"):
        capture._validate_current_reader_custody(packet, members, review, inputs)


@pytest.mark.parametrize(
    "target,field,value,message",
    [
        (
            "current/terminal",
            "native_exit_code",
            True,
            "current reader native execution",
        ),
        (
            "current/terminal",
            "protected_inputs_unchanged",
            False,
            "current reader native execution",
        ),
        ("reused/terminal", "native_exit_code", 0, "partial native result"),
        (
            "reused/terminal",
            "protected_inputs_unchanged",
            False,
            "partial native result",
        ),
        ("current/reader", "new_locality_records", 548, "source membership"),
        (
            "current/observer",
            "all_reader_cases_joined_to_exact_source_membership",
            False,
            "source membership",
        ),
        (
            "current/observer",
            "original_sample_producer_sha256",
            "0" * 64,
            "source membership",
        ),
        ("reused/producer-import-origins", "actual_origins", [], "origins are absent"),
    ],
)
def test_rehashed_native_claim_change_refuses(
    custody: _Custody,
    tmp_path: Path,
    target: str,
    field: str,
    value: Any,
    message: str,
) -> None:
    packet, members, review, inputs = custody
    group, role = target.split("/")
    key = (
        "current_reader_reference"
        if group == "current"
        else "reused_source_producer_reference"
    )
    member = packet[key][role]
    changed = json.loads(members[member].read_bytes())
    changed[field] = value
    retained = tmp_path / "retained.json"
    retained.write_text(json.dumps(changed) + "\n", encoding="utf-8")
    digest = hashlib.sha256(retained.read_bytes()).hexdigest()
    members[member] = retained
    review[key][role]["sha256"] = digest
    # Preserve outer digest links to exercise semantic validation after rehashing.
    if group == "reused" and role == "terminal":
        plan_member = packet["current_reader_reference"]["plan"]
        plan = json.loads(members[plan_member].read_bytes())
        if group == "reused":
            plan["reused_source_producer"]["original_terminal_sha256"] = digest
        replacement = tmp_path / "plan.json"
        replacement.write_text(json.dumps(plan) + "\n", encoding="utf-8")
        members[plan_member] = replacement
        plan_digest = hashlib.sha256(replacement.read_bytes()).hexdigest()
        review["current_reader_reference"]["plan"]["sha256"] = plan_digest
        terminal_member = packet["current_reader_reference"]["terminal"]
        terminal = json.loads(members[terminal_member].read_bytes())
        terminal["plan_sha256"] = plan_digest
        replacement = tmp_path / "terminal.json"
        replacement.write_text(json.dumps(terminal) + "\n", encoding="utf-8")
        members[terminal_member] = replacement
        review["current_reader_reference"]["terminal"]["sha256"] = hashlib.sha256(
            replacement.read_bytes()
        ).hexdigest()
    with pytest.raises(ReportRebuildError, match=message):
        capture._validate_current_reader_custody(packet, members, review, inputs)


def test_reused_producer_import_source_change_refuses(custody: _Custody) -> None:
    packet, members, review, inputs = custody
    inputs = copy.copy(inputs)
    origins = json.loads(
        members[
            packet["reused_source_producer_reference"]["producer-import-origins"]
        ].read_bytes()
    )
    first = origins["actual_origins"][0]
    relative = Path(first["path"]).relative_to(origins["source_root"]).as_posix()
    inputs[relative] = "0" * 64
    with pytest.raises(ReportRebuildError, match="captured source differs"):
        capture._validate_current_reader_custody(packet, members, review, inputs)


def _same_run_custody(custody: _Custody, tmp_path: Path) -> _Custody:
    """Build a controlled direct producer/reader/observer protocol from exact inputs."""
    packet, original_members, original_review, inputs = custody
    packet, review = copy.deepcopy(packet), copy.deepcopy(original_review)
    members = dict(original_members)
    current = packet["current_reader_reference"]
    reused = packet["reused_source_producer_reference"]
    plan = json.loads(members[current["plan"]].read_bytes())
    terminal = json.loads(members[current["terminal"]].read_bytes())
    prior_plan = json.loads(members[reused["plan"]].read_bytes())
    prior_terminal = json.loads(members[reused["terminal"]].read_bytes())
    if plan.get("reader_custody_mode") != "same-run-source-producer":
        plan["stages"] = [prior_plan["stages"][0], *plan["stages"]]
        terminal["stages"] = [prior_terminal["stages"][0], *terminal["stages"]]
    plan["reader_custody_mode"] = "same-run-source-producer"
    plan.pop("reused_source_producer", None)
    plan_path = tmp_path / "controlled-direct-plan.json"
    plan_path.write_text(json.dumps(plan) + "\n", encoding="utf-8")
    terminal["plan_sha256"] = hashlib.sha256(plan_path.read_bytes()).hexdigest()
    terminal_path = tmp_path / "controlled-direct-terminal.json"
    terminal_path.write_text(json.dumps(terminal) + "\n", encoding="utf-8")
    for role, path in (("plan", plan_path), ("terminal", terminal_path)):
        members[current[role]] = path
        reused[role] = current[role]
        for key in ("current_reader_reference", "reused_source_producer_reference"):
            review[key][role]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return packet, members, review, inputs


def _rewrite_direct_member(
    custody: _Custody, tmp_path: Path, role: str, changed: dict[str, Any]
) -> None:
    """Reseal native outer digests so negative controls reach custody semantics."""
    packet, members, review, _ = custody
    current = packet["current_reader_reference"]
    path = tmp_path / ("rehashed-direct-" + role + ".json")
    path.write_text(json.dumps(changed) + "\n", encoding="utf-8")
    members[current[role]] = path
    for key in ("current_reader_reference", "reused_source_producer_reference"):
        review[key][role]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    if role == "plan":
        terminal = json.loads(members[current["terminal"]].read_bytes())
        terminal["plan_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        _rewrite_direct_member(custody, tmp_path, "terminal", terminal)


def test_same_run_source_producer_reader_and_observer(
    custody: _Custody, tmp_path: Path
) -> None:
    capture._validate_current_reader_custody(*_same_run_custody(custody, tmp_path))


@pytest.mark.parametrize(
    "change,message",
    [
        ("unknown_mode", "custody mode"),
        ("missing_mode", "current reader native execution"),
        ("failed_producer", "current reader native execution"),
        ("boolean_producer_exit", "current reader native execution"),
        ("producer_argv", "current reader native execution"),
        ("swapped_stage_roles", "same-run producer native result"),
        ("source_directory", "same-run producer native result"),
        ("producer_output", "same-run producer native result"),
        ("reused_partial_claim", "same-run producer native result"),
        ("protected_source_digest", "protected source"),
        ("duplicate_protected_pin", "protected source"),
    ],
)
def test_rehashed_same_run_native_claim_refuses(
    custody: _Custody, tmp_path: Path, change: str, message: str
) -> None:
    direct = _same_run_custody(custody, tmp_path)
    packet, members, _, _ = direct
    current = packet["current_reader_reference"]
    plan = json.loads(members[current["plan"]].read_bytes())
    terminal = json.loads(members[current["terminal"]].read_bytes())
    if change == "unknown_mode":
        plan["reader_custody_mode"] = "unqualified-route"
    elif change == "missing_mode":
        del plan["reader_custody_mode"]
    elif change == "failed_producer":
        terminal["stages"][0]["native_exit_code"] = 1
    elif change == "boolean_producer_exit":
        terminal["stages"][0]["native_exit_code"] = True
    elif change == "producer_argv":
        terminal["stages"][0]["actual_argv"] = ["unexecuted"]
    elif change == "swapped_stage_roles":
        plan["stages"][0], plan["stages"][1] = plan["stages"][1], plan["stages"][0]
        terminal["stages"][0], terminal["stages"][1] = (
            terminal["stages"][1],
            terminal["stages"][0],
        )
    elif change == "source_directory":
        plan["source_directory"] += "/different-source"
    elif change == "producer_output":
        plan["reader_products"]["locality_producer"] += ".unexecuted"
    elif change == "reused_partial_claim":
        plan["reused_source_producer"] = {}
    elif change == "protected_source_digest":
        origins = json.loads(
            members[
                packet["reused_source_producer_reference"]["producer-import-origins"]
            ].read_bytes()
        )
        first = origins["actual_origins"][0]
        matching = next(
            row for row in plan["protected_inputs"] if row["path"] == first["path"]
        )
        matching["sha256"] = "0" * 64
    else:
        assert change == "duplicate_protected_pin"
        plan["protected_inputs"].append(copy.deepcopy(plan["protected_inputs"][0]))
    _rewrite_direct_member(direct, tmp_path, "terminal", terminal)
    _rewrite_direct_member(direct, tmp_path, "plan", plan)
    with pytest.raises(ReportRebuildError, match=message):
        capture._validate_current_reader_custody(*direct)


def _partial_custody(custody: _Custody, tmp_path: Path) -> _Custody:
    """Keep partial-result compatibility controls independent of the active packet route."""
    packet, original_members, original_review, inputs = custody
    current = packet["current_reader_reference"]
    original_plan = json.loads(original_members[current["plan"]].read_bytes())
    if original_plan.get("reader_custody_mode") != "same-run-source-producer":
        return custody
    packet, review = copy.deepcopy(packet), copy.deepcopy(original_review)
    members = dict(original_members)
    current = packet["current_reader_reference"]
    plan = copy.deepcopy(original_plan)
    terminal = json.loads(members[current["terminal"]].read_bytes())
    old_plan = copy.deepcopy(plan)
    old_plan.pop("reader_custody_mode")
    old_plan_path = tmp_path / "controlled-partial-producer-plan.json"
    old_plan_path.write_text(json.dumps(old_plan) + "\n", encoding="utf-8")
    old_terminal = copy.deepcopy(terminal)
    old_terminal.update(
        native_exit_code=1,
        status="failed",
        plan_sha256=hashlib.sha256(old_plan_path.read_bytes()).hexdigest(),
    )
    old_terminal["stages"] = old_terminal["stages"][:2]
    old_terminal["stages"][1]["native_exit_code"] = 1
    old_terminal_path = tmp_path / "controlled-partial-producer-terminal.json"
    old_terminal_path.write_text(json.dumps(old_terminal) + "\n", encoding="utf-8")
    plan.pop("reader_custody_mode")
    plan["stages"] = plan["stages"][1:]
    plan["reused_source_producer"] = {
        "original_plan": str(old_plan_path),
        "original_terminal": str(old_terminal_path),
        "original_plan_sha256": hashlib.sha256(old_plan_path.read_bytes()).hexdigest(),
        "original_terminal_sha256": hashlib.sha256(
            old_terminal_path.read_bytes()
        ).hexdigest(),
        "source_directory": plan["source_directory"],
        "reused_source_producer_stage": old_terminal["stages"][0],
        "reused_source_producer_proof_sha256": hashlib.sha256(
            members[current["locality-producer"]].read_bytes()
        ).hexdigest(),
    }
    plan_path = tmp_path / "controlled-partial-reader-plan.json"
    plan_path.write_text(json.dumps(plan) + "\n", encoding="utf-8")
    terminal["stages"] = terminal["stages"][1:]
    terminal["plan_sha256"] = hashlib.sha256(plan_path.read_bytes()).hexdigest()
    terminal_path = tmp_path / "controlled-partial-reader-terminal.json"
    terminal_path.write_text(json.dumps(terminal) + "\n", encoding="utf-8")
    for group, role, path in (
        ("current_reader_reference", "plan", plan_path),
        ("current_reader_reference", "terminal", terminal_path),
        ("reused_source_producer_reference", "plan", old_plan_path),
        ("reused_source_producer_reference", "terminal", old_terminal_path),
    ):
        name = "controlled-partial/" + path.name
        packet[group][role] = name
        members[name] = path
        review[group][role]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return packet, members, review, inputs


@pytest.fixture
def custody(actual_custody: _Custody, tmp_path: Path) -> _Custody:
    return _partial_custody(actual_custody, tmp_path)


def test_actual_current_packet_reader_custody(actual_custody: _Custody) -> None:
    capture._validate_current_reader_custody(*actual_custody)


def test_partial_route_remains_qualified_from_direct_source_inputs(
    actual_custody: _Custody, tmp_path: Path
) -> None:
    direct = _same_run_custody(actual_custody, tmp_path)
    capture._validate_current_reader_custody(*_partial_custody(direct, tmp_path))
