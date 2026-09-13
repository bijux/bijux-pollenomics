"""Readiness never turns retrospective synthetic scores into final acceptance."""

import json
from pathlib import Path

import pytest

from bijux_pollenomics.analysis.lra_validation import ValidationRefusal
from bijux_pollenomics.analysis.lra_validation.evaluation.api import (
    audit_scored_evaluation_readiness,
)
from bijux_pollenomics.analysis.lra_validation.experiments.reading.scores import (
    read_scored_experiment_evidence,
)

from ..experiments.reading.test_scores import scored_pair


def test_complete_targets_and_missing_final_prerequisites_are_preserved(
    tmp_path: Path,
) -> None:
    prediction, score = scored_pair(tmp_path)
    evidence = read_scored_experiment_evidence(
        prediction.directory,
        expected_prediction_manifest_sha256=prediction.manifest_sha256,
        scores=score.directory,
        expected_scores_manifest_sha256=score.manifest_sha256,
    )
    audit = audit_scored_evaluation_readiness(
        (evidence,),
        frozen_evaluation_binding={"review_reference": "unverified caller declaration"},
    )
    value = json.loads(audit.canonical_audit_json)
    assert value["final_evaluation_performed"] is False
    assert value["review_authenticity_verified"] is False
    assert value["scientific_acceptance"] == "not_evaluated"
    assert (
        value["frozen_binding_verification"] == "not_performed_no_prospective_protocol"
    )
    assert (
        value["products"][0]["fixed_model_resampling_eligibility"]
        == "refused_overlapping_training_folds_not_fixed_model_external_cohort"
    )
    assert len(value["rows"]) == sum(
        target["requested"] for target in value["targets"].values()
    )
    assert {row["target"] for row in value["rows"]} == {
        "vegetation_cover",
        "pollen_composition",
    }
    assert all("metric_unit" not in row for row in value["rows"])
    assert all(row["composition_error_unit"] == "fraction" for row in value["rows"])
    pollen = next(row for row in value["rows"] if row["target"] == "pollen_composition")
    assert pollen["source_metric"]["observed_total_count"] > 0
    assert "count_conditioned_deviance" in pollen["source_metric"]
    assert all(row["final_eligibility"] == "ineligible" for row in value["rows"])
    with pytest.raises(ValidationRefusal) as duplicate:
        audit_scored_evaluation_readiness((evidence, evidence))
    assert duplicate.value.reason_code == "duplicate_scored_evidence"


def test_empty_evidence_is_not_an_empty_success() -> None:
    with pytest.raises(ValidationRefusal) as empty:
        audit_scored_evaluation_readiness(())
    assert empty.value.reason_code == "empty_scored_evidence"
