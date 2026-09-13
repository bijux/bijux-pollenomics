"""Rehashed aggregate and access receipts cannot contradict the admitted row universe."""

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra_validation import ValidationRefusal, manifest_sha256
from bijux_pollenomics.analysis.lra_validation.experiments.outputs import (
    ExperimentProduct,
)

from .test_scores import evidence_for, scored_pair


@pytest.mark.parametrize(
    "kind",
    [
        "denominator",
        "mean",
        "independence",
        "coverage",
        "paired",
        "access",
        "duplicate_summary",
    ],
)
def test_retained_ledger_contradictions_refuse(tmp_path: Path, kind: str) -> None:
    prediction, score = scored_pair(tmp_path)
    manifest: dict[str, Any] = json.loads(
        (score.directory / "manifest.json").read_text()
    )
    member = "summaries.json"
    if kind == "access":
        member = "outcome_access.json"
    elif kind == "paired":
        member = "paired_baseline_differences.json"
    rows = json.loads((score.directory / member).read_text())
    if kind == "denominator":
        rows[0]["requested"] -= 1
    elif kind == "mean":
        rows[0]["mean_mae_fraction"] += 0.01
    elif kind == "independence":
        rows[0]["independence"] = "independent_external_cohort"
    elif kind == "coverage":
        rows[0]["interval_coverage"] = 0.95
    elif kind == "paired":
        rows[0]["mae_improvement_fraction"] += 0.01
    elif kind == "duplicate_summary":
        rows.append(rows[0].copy())
    else:
        rows.pop()
    (score.directory / member).write_text(json.dumps(rows) + "\n")
    if member != "outcome_access.json":
        manifest["scientific_payload"][member.removesuffix(".json")] = rows
    manifest["files"][member] = hashlib.sha256(
        (score.directory / member).read_bytes()
    ).hexdigest()
    manifest["scientific_content_sha256"] = manifest_sha256(
        manifest["scientific_payload"]
    )
    path = score.directory / "manifest.json"
    path.write_text(json.dumps(manifest) + "\n")
    changed = ExperimentProduct(
        score.directory,
        hashlib.sha256(path.read_bytes()).hexdigest(),
        manifest["scientific_content_sha256"],
    )
    with pytest.raises(ValidationRefusal):
        evidence_for(prediction, changed)


def test_incomplete_caller_constructed_evidence_refuses_before_readiness() -> None:
    from bijux_pollenomics.analysis.lra_validation.contracts import canonical_json
    from bijux_pollenomics.analysis.lra_validation.experiments.reading import (
        ScoredExperimentEvidence,
    )

    payload = {
        "schema_version": "pollenomics-scored-evidence.v1",
        "scientific_acceptance": "not_evaluated",
    }
    with pytest.raises(ValidationRefusal):
        ScoredExperimentEvidence(canonical_json(payload), manifest_sha256(payload))
