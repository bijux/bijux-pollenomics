"""Field question custody and returned-evidence controls, without review claims."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
from types import ModuleType
from typing import Any

import pytest

RECORD_ROOT = Path(__file__).resolve().parents[4]
SOURCE_ROOT = next(
    parent for parent in Path(__file__).resolve().parents if (parent / ".git").exists()
)


def _module() -> ModuleType:
    path = (
        RECORD_ROOT
        / "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/reader_reports/field_decisions.py"
    )
    spec = importlib.util.spec_from_file_location("field_decisions", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def record(tmp_path: Path) -> dict[str, Any]:
    loaded: dict[str, Any] = json.loads(
        (RECORD_ROOT / "reports/needed/field-decisions.json").read_text()
    )
    for pin in loaded["source_pins"]:
        target = tmp_path / pin["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SOURCE_ROOT / pin["path"], target)
    return loaded


def test_five_unranked_leads_and_forty_unanswered_questions(
    tmp_path: Path, record: dict[str, Any]
) -> None:
    result = _module().validate(tmp_path, record)
    assert result == {
        "named_leads": 5,
        "questions": 40,
        "received_field_records": 0,
        "governed_candidates": 0,
    }


@pytest.mark.parametrize(
    "corruption",
    [
        "source",
        "identity",
        "uppakra",
        "rank",
        "candidate",
        "duplicate",
        "missing_question",
        "resolver",
        "trigger",
        "received",
        "invented_field",
        "observation_date",
        "register_count",
    ],
)
def test_false_field_authority_or_lost_question_refuses(
    tmp_path: Path, record: dict[str, Any], corruption: str
) -> None:
    damaged = copy.deepcopy(record)
    if corruption == "source":
        damaged["source_pins"][0]["sha256"] = "0" * 64
    elif corruption == "identity":
        damaged["leads"][0]["modern_reference"]["retained_registry_id"] = "wrong"
    elif corruption == "uppakra":
        damaged["leads"][-1]["modern_reference"]["retained_registry_id"] = "gullakra"
    elif corruption == "rank":
        damaged["leads"][0]["rank"] = 1
    elif corruption == "candidate":
        damaged["leads"][0]["governed_field_candidate"] = True
    elif corruption == "duplicate":
        damaged["questions"][-1] = copy.deepcopy(damaged["questions"][0])
    elif corruption == "missing_question":
        damaged["questions"].pop()
    elif corruption == "resolver":
        damaged["questions"][0]["responsible_external_resolver"] = ""
    elif corruption == "trigger":
        damaged["questions"][0]["reopening_condition"] = ""
    elif corruption == "received":
        damaged["questions"][0]["decision_status"] = "accepted_scoped"
    elif corruption == "invented_field":
        damaged["rights_approved"] = True
    elif corruption == "observation_date":
        damaged["fact_observation_date"] = damaged["prepared_on"]
    else:
        damaged["preserved_registers"]["reports/needed/scientific-review.csv"][
            "row_count"
        ] = 35
    with pytest.raises(ValueError):
        _module().validate(tmp_path, damaged)


def test_returned_scoped_evidence_requires_physical_custody(
    tmp_path: Path, record: dict[str, Any]
) -> None:
    evidence = tmp_path / "reports/needed/controlled-reply.md"
    evidence.write_text(
        "Controlled fixture reply; no actual field permission or review.\n"
    )
    question = record["questions"][0]
    question.update(
        {
            "decision_status": "accepted_with_conditions",
            "reviewer_assignment": "Controlled fixture resolver",
            "decision_date": "2026-10-14",
            "returned_fact": "Controlled fixture identity only; no field authorization.",
            "decision_evidence": {
                "path": "reports/needed/controlled-reply.md",
                "sha256": hashlib.sha256(evidence.read_bytes()).hexdigest(),
                "resolver_qualification": "Controlled fixture role; not a real reviewer",
                "decision_scope": "One fixture identity question",
                "remaining_conditions": "All real identity, access, permission and safety facts remain unreceived",
            },
        }
    )
    assert _module().validate(tmp_path, record)["received_field_records"] == 1
    assert record["leads"][0]["field_decision"] == "not_received"
    evidence.write_text("Changed fixture reply.\n")
    with pytest.raises(ValueError):
        _module().validate(tmp_path, record)


def test_evidence_traversal_and_symlink_refuse(tmp_path: Path) -> None:
    source = tmp_path / "safe.md"
    source.write_text("fixture")
    (tmp_path / "alias.md").symlink_to(source)
    for path in ["../outside.md", "/outside.md", "alias.md", "sub/../safe.md"]:
        with pytest.raises(ValueError):
            _module()._file(tmp_path, path)
