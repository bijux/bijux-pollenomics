"""Public immutable evidence cannot contradict its preserved raw projection inputs."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from bijux_pollenomics.analysis.lra_validation import ValidationRefusal, manifest_sha256
from bijux_pollenomics.analysis.lra_validation.contracts import canonical_json
from bijux_pollenomics.analysis.lra_validation.evaluation.api import (
    audit_scored_evaluation_readiness,
)
from bijux_pollenomics.analysis.lra_validation.experiments.reading import (
    ScoredExperimentEvidence,
)
from bijux_pollenomics.analysis.lra_validation.experiments.scoring import (
    score_experiment_predictions,
)

from ..test_assimilation import synthetic_local_product
from .test_scores import evidence_for


@pytest.mark.parametrize(
    "mutation",
    [
        "diagnostic",
        "metric",
        "status",
        "parent",
        "authentication",
        "role",
        "values",
        "fitted_id",
        "interval",
        "upstream",
        "scientific_body",
        "score_parent",
        "manifest_status",
        "manifest_digest",
        "duplicate_manifest",
        "catalogue_projection",
        "inventory_projection",
        "access_projection",
        "member_bytes",
        "duplicate_member",
    ],
)
def test_rehashed_constructor_projections_refuse(tmp_path: Path, mutation: str) -> None:
    prediction, inventory = synthetic_local_product(tmp_path)
    score = score_experiment_predictions(
        prediction.directory,
        expected_manifest_sha256=prediction.manifest_sha256,
        outcome_root=tmp_path / "inputs",
        outcome_inventory=inventory,
        destination=tmp_path / "scores",
    )
    value = evidence_for(prediction, score)
    original = ScoredExperimentEvidence(canonical_json(value), manifest_sha256(value))
    assert (
        json.loads(audit_scored_evaluation_readiness((original,)).canonical_audit_json)[
            "targets"
        ]["pollen_composition"]["in_sample_diagnostics"]
        == 4
    )
    changed = deepcopy(value)
    unit = next(
        row for row in changed["units"] if row["target"] == "pollen_composition"
    )
    if mutation == "diagnostic":
        unit["eligible_target_kind"] = True
    elif mutation == "metric":
        unit["metric"]["mae_fraction"] = 123
    elif mutation == "status":
        unit["status"] = "prediction_failed"
    elif mutation == "parent":
        changed["prediction_manifest_sha256"] = "f" * 64
    elif mutation == "score_parent":
        changed["score_manifest_sha256"] = "e" * 64
    elif mutation in {"manifest_status", "manifest_digest", "duplicate_manifest"}:
        manifest = json.loads(changed["score_manifest_json"])
        if mutation == "manifest_status":
            manifest["status"] = "empirical_verified"
        elif mutation == "manifest_digest":
            manifest["scientific_content_sha256"] = "f" * 64
        text = json.dumps(manifest)
        if mutation == "duplicate_manifest":
            text = text[:-1] + ',"status":"generated_exploratory"}'
        changed["score_manifest_json"] = text
        changed["score_manifest_sha256"] = hashlib.sha256(text.encode()).hexdigest()
    elif mutation == "catalogue_projection":
        changed["source_catalogue"]["local_support_radius_m"] = 999999
    elif mutation == "inventory_projection":
        records = changed["outcome_inventory"]["records"]
        records[next(iter(records))]["sha256"] = "a" * 64
    elif mutation == "access_projection":
        changed["outcome_access"][0]["ordering"] = "before_predictions"
    elif mutation == "member_bytes":
        changed["retained_member_json"]["prediction/experiment.json"] += " "
    elif mutation == "duplicate_member":
        text = changed["retained_member_json"]["score/outcome_inventory.json"].rstrip()
        changed["retained_member_json"]["score/outcome_inventory.json"] = (
            text[:-1] + ',"data_kind":"synthetic"}'
        )
        manifest = json.loads(changed["score_manifest_json"])
        manifest["files"]["outcome_inventory.json"] = hashlib.sha256(
            changed["retained_member_json"]["score/outcome_inventory.json"].encode()
        ).hexdigest()
        changed["score_manifest_json"] = json.dumps(manifest)
        changed["score_manifest_sha256"] = hashlib.sha256(
            changed["score_manifest_json"].encode()
        ).hexdigest()
    elif mutation == "authentication":
        changed["source_authentication"] = "independent_measured_source_verified"
    elif mutation == "role":
        unit["evaluation_role"] = "heldout_prediction"
    elif mutation == "values":
        unit["prediction"] = {"Alnus": 0.99, "Betula": 0.01}
    elif mutation == "fitted_id":
        unit["fitted_model_sha256"] = "f" * 64
    elif mutation == "interval":
        unit["interval"] = {"coverage": 0.95}
    elif mutation == "upstream":
        unit["upstream_prediction"]["pollen_fraction"] = {"Alnus": 0.99, "Betula": 0.01}
    else:
        changed["score_scientific_payload"]["scientific_acceptance"] = "accepted"
    payload = canonical_json(changed)
    with pytest.raises(ValidationRefusal):
        ScoredExperimentEvidence(payload, manifest_sha256(changed))
    # Even deliberate frozen-dataclass bypass is revalidated by the audit facade.
    object.__setattr__(original, "canonical_evidence_json", payload)
    object.__setattr__(original, "evidence_sha256", manifest_sha256(changed))
    with pytest.raises(ValidationRefusal):
        audit_scored_evaluation_readiness((original,))
