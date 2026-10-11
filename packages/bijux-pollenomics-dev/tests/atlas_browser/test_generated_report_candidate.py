"""Fail-closed contracts for receipt-bound generated report candidates."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path

import pytest

from bijux_pollenomics_dev.ci.atlas_browser.contracts import (
    NORDIC_SOURCE_CHRONOLOGY_PROFILE,
    AtlasBrowserContractError,
    AtlasGeneratedReportCandidate,
    BrowserVerificationPlan,
)
from bijux_pollenomics_dev.ci.atlas_browser.generated_report_candidate import (
    audit_generated_report_candidate,
    verify_generated_report_served_bytes,
)

from .generated_report_fixtures import generated_report_plan


def test_v4_roundtrip_and_profile_isolation(tmp_path: Path) -> None:
    plan = generated_report_plan(tmp_path)

    assert plan.as_json()["schema_version"] == "atlas-browser-verification-plan.v4"
    assert BrowserVerificationPlan.from_json(plan.as_json()) == plan
    with pytest.raises(AtlasBrowserContractError, match="requires one Nordic RAÄ"):
        replace(plan, verification_profile=NORDIC_SOURCE_CHRONOLOGY_PROFILE)
    with pytest.raises(AtlasBrowserContractError, match="fields must be exact"):
        AtlasGeneratedReportCandidate.from_json(
            {**plan.candidate.as_json(), "atlas_output_commit": "c" * 40}
        )


def test_receipt_inventory_and_required_served_bytes(tmp_path: Path) -> None:
    plan = generated_report_plan(tmp_path)
    observed = audit_generated_report_candidate(plan)
    report = {"served_artifact_bytes": observed["files"], "refused_artifact_reads": []}

    verify_generated_report_served_bytes(plan, observed, report)
    with pytest.raises(AtlasBrowserContractError, match="required generated-report"):
        verify_generated_report_served_bytes(
            plan, observed, {**report, "served_artifact_bytes": []}
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("read_set_unchanged", False),
        ("termination", "killed"),
        ("input_tree", "0" * 40),
        ("outputs", []),
    ],
)
def test_self_rehashed_receipt_mutations_refuse(
    tmp_path: Path, field: str, value: object
) -> None:
    plan = generated_report_plan(tmp_path)
    assert isinstance(plan.candidate, AtlasGeneratedReportCandidate)
    receipt_path = tmp_path / plan.candidate.generator_receipt
    receipt = json.loads(receipt_path.read_bytes())
    receipt[field] = value
    receipt_path.write_text(json.dumps(receipt, sort_keys=True), encoding="utf-8")
    candidate = replace(
        plan.candidate,
        generator_receipt_sha256=hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
    )

    with pytest.raises(AtlasBrowserContractError):
        audit_generated_report_candidate(replace(plan, candidate=candidate))


def test_rehashed_scientific_posture_mutation_refuses(tmp_path: Path) -> None:
    plan = generated_report_plan(tmp_path)
    assert isinstance(plan.candidate, AtlasGeneratedReportCandidate)
    status_path = (
        tmp_path
        / plan.candidate.presentation_root
        / "regions/nordic/raa_atlas_input_status.json"
    )
    status = json.loads(status_path.read_bytes())
    status["propagation_eligible"] = True
    status_path.write_text(json.dumps(status, sort_keys=True), encoding="utf-8")

    with pytest.raises(AtlasBrowserContractError):
        audit_generated_report_candidate(plan)
