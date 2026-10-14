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
def custody() -> _Custody:
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


def test_actual_reader_and_partial_producer_custody(custody: _Custody) -> None:
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
