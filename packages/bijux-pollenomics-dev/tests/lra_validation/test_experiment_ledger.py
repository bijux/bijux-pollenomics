"""Behavioral checks for the append-only local development ledger."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.lra_validation.experiment_ledger import (
    ExperimentLedgerError,
    finish_development_attempt,
    read_development_attempts,
    start_development_attempt,
)


def _canonical(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _admission() -> tuple[str, str, str]:
    scope_sha256 = "d" * 64
    payload = {
        "profile": "pollenomics-reviewed-evaluation-cohort.v1",
        "decision_manifest_sha256": "a" * 64,
        "candidate_source_manifest_sha256": "b" * 64,
        "admission_id": "review:declared-cohort",
        "reviewer_id": "reviewer:declared",
        "reviewer_authority": "declared_not_authenticated",
        "decision_date": "2026-09-24",
        "admitted_record_ids": ["record:a"],
        "refused_record_ids": ["record:refused"],
        "outcome_access_status": "not_started",
        "scope_id": "scope:development",
        "scope_sha256": scope_sha256,
        "empirical_evaluation_performed": False,
        "scientific_acceptance": "not_evaluated",
    }
    canonical = _canonical(payload)
    return canonical, hashlib.sha256(canonical.encode()).hexdigest(), scope_sha256


def _spec(run_id: str = "trial-1") -> dict[str, Any]:
    admission, admission_sha256, scope_sha256 = _admission()
    split_sha256 = "c" * 64
    return {
        "schema_version": "lra-development-attempt.v2",
        "run_id": run_id,
        "policy_sha256": "a" * 64,
        "input_hashes": {"pollen": "b" * 64, "split_manifest": split_sha256},
        "evaluation_binding": {
            "canonical_cohort_admission_json": admission,
            "cohort_admission_sha256": admission_sha256,
            "scope_sha256": scope_sha256,
            "split_manifest_sha256": split_sha256,
            "split_kind": "leave_one_site_group_out",
            "experiment": "local_pollen_available",
            "target": "vegetation_cover",
        },
        "fold_id": "sweden-block-01",
        "model": "reveals-baseline",
        "configuration": {
            "method": "REVEALS",
            "transport": "Sugita-B1",
            "taxon_profile": "taxa-review-v1",
            "ppe_profile": "ppe-published-v1",
            "basin_scenario": "basin-175m",
            "spatial_support": "5km",
            "temporal_support": "500BP",
            "uncertainty": "bootstrap-100",
        },
        "hyperparameters": {"ppe": {"pinus": 1.2}, "radius_m": 5000},
        "seed": 7,
        "backend": "python-0.1",
        "budget": {"seconds": 300, "threads": 1},
    }


def test_retains_success_refusal_and_interrupted_attempts(tmp_path: Path) -> None:
    root = tmp_path / "ledger"
    start_development_attempt(root, _spec("success"))
    start_development_attempt(root, _spec("refused"))
    start_development_attempt(root, _spec("interrupted"))
    finish_development_attempt(
        root,
        "success",
        {
            "status": "completed",
            "elapsed_seconds": 2.5,
            "metrics": {"vegetation_mae": 0.12},
            "reason_code": None,
        },
    )
    finish_development_attempt(
        root,
        "refused",
        {
            "status": "refused",
            "elapsed_seconds": 0.1,
            "metrics": {},
            "reason_code": "no_admitted_pollen",
        },
    )
    rows = read_development_attempts(root)
    assert len(rows) == 3
    assert {row["start"]["run_id"] for row in rows} == {
        "success",
        "refused",
        "interrupted",
    }
    assert (
        next(row for row in rows if row["start"]["run_id"] == "interrupted")["result"]
        is None
    )
    assert (
        next(row for row in rows if row["start"]["run_id"] == "refused")["result"][
            "reason_code"
        ]
        == "no_admitted_pollen"
    )
    with pytest.raises(ExperimentLedgerError, match="run_id_already_exists"):
        start_development_attempt(root, _spec("success"))
    with pytest.raises(ExperimentLedgerError, match="record_already_exists"):
        finish_development_attempt(
            root,
            "success",
            {
                "status": "completed",
                "elapsed_seconds": 9,
                "metrics": {"vegetation_mae": 0.9},
                "reason_code": None,
            },
        )


def test_rejects_invalid_experiment_target_and_detects_tampering(
    tmp_path: Path,
) -> None:
    root = tmp_path / "ledger"
    spec = _spec()
    binding = dict(spec["evaluation_binding"])
    binding["target"] = "pollen_composition"
    final = {**spec, "evaluation_binding": binding}
    with pytest.raises(ExperimentLedgerError, match="invalid_experiment_target"):
        start_development_attempt(root, final)
    bad_metric = {
        "status": "completed",
        "elapsed_seconds": 1.0,
        "metrics": {"score": float("nan")},
        "reason_code": None,
    }
    start_development_attempt(root, _spec())
    with pytest.raises(ExperimentLedgerError, match="completed_without_metrics"):
        finish_development_attempt(
            root,
            "trial-1",
            {
                "status": "completed",
                "elapsed_seconds": 1,
                "metrics": {},
                "reason_code": None,
            },
        )
    with pytest.raises(ExperimentLedgerError, match="non_json_or_nonfinite_value"):
        finish_development_attempt(root, "trial-1", bad_metric)
    path = root / "trial-1" / "start.json"
    altered = json.loads(path.read_text(encoding="utf-8"))
    altered["payload"]["seed"] = 999
    path.write_text(json.dumps(altered), encoding="utf-8")
    with pytest.raises(ExperimentLedgerError, match="invalid_ledger_record"):
        read_development_attempts(root)


@pytest.mark.parametrize(
    ("experiment", "target"),
    [
        ("local_pollen_available", "vegetation_cover"),
        ("all_target_pollen_withheld", "vegetation_cover"),
        ("all_target_pollen_withheld", "pollen_composition"),
    ],
)
def test_accepts_each_declared_experiment_target(
    tmp_path: Path, experiment: str, target: str
) -> None:
    spec = _spec(f"{experiment}-{target}")
    binding = dict(spec["evaluation_binding"])
    binding.update(experiment=experiment, target=target)
    start_development_attempt(tmp_path, {**spec, "evaluation_binding": binding})


def test_rejects_missing_provenance_and_unsafe_identity(tmp_path: Path) -> None:
    with pytest.raises(ExperimentLedgerError, match="invalid_input_hashes"):
        start_development_attempt(tmp_path, {**_spec(), "input_hashes": {"pollen": ""}})
    with pytest.raises(ExperimentLedgerError, match="invalid_run_id"):
        start_development_attempt(tmp_path, _spec("../outside"))
    spec = _spec("no-binding")
    del spec["evaluation_binding"]
    with pytest.raises(ExperimentLedgerError, match="invalid_start_fields"):
        start_development_attempt(tmp_path, spec)
    start_development_attempt(tmp_path, {**_spec("baseline"), "hyperparameters": {}})


def test_cohort_scope_split_and_decision_identities_are_bound(tmp_path: Path) -> None:
    spec = _spec()
    binding = dict(spec["evaluation_binding"])
    binding["cohort_admission_sha256"] = "f" * 64
    with pytest.raises(ExperimentLedgerError, match="invalid_cohort_admission"):
        start_development_attempt(
            tmp_path / "bad-cohort", {**spec, "evaluation_binding": binding}
        )

    binding = dict(spec["evaluation_binding"])
    binding["scope_sha256"] = "e" * 64
    with pytest.raises(ExperimentLedgerError, match="cohort_scope_mismatch"):
        start_development_attempt(
            tmp_path / "bad-scope", {**spec, "evaluation_binding": binding}
        )

    binding = dict(spec["evaluation_binding"])
    binding["split_manifest_sha256"] = "e" * 64
    with pytest.raises(ExperimentLedgerError, match="split_manifest_input_mismatch"):
        start_development_attempt(
            tmp_path / "bad-split", {**spec, "evaluation_binding": binding}
        )

    binding = dict(spec["evaluation_binding"])
    admission = json.loads(binding["canonical_cohort_admission_json"])
    admission["decision_manifest_sha256"] = "e" * 64
    binding["canonical_cohort_admission_json"] = _canonical(admission)
    with pytest.raises(ExperimentLedgerError, match="invalid_cohort_admission"):
        start_development_attempt(
            tmp_path / "stale-decision", {**spec, "evaluation_binding": binding}
        )


def test_legacy_unversioned_start_record_remains_readable(tmp_path: Path) -> None:
    root = tmp_path / "ledger"
    trial = root / "legacy"
    trial.mkdir(parents=True)
    payload = {
        "run_id": "legacy",
        "policy_sha256": "a" * 64,
        "input_hashes": {"folds": "b" * 64},
        "target": "withheld_pollen_prediction",
        "fold_id": "development-block-1",
        "model": "training-mean",
        "configuration": {
            "method": "training-mean",
            "transport": "none",
            "taxon_profile": "review-pending",
            "ppe_profile": "review-pending",
            "basin_scenario": "none",
            "spatial_support": "declared-block",
            "temporal_support": "declared-window",
            "uncertainty": "none",
        },
        "hyperparameters": {},
        "seed": 1,
        "backend": "python-test",
        "budget": {"seconds": 3},
    }
    payload_bytes = _canonical(payload).encode()
    envelope = {
        "payload": payload,
        "sha256": hashlib.sha256(payload_bytes).hexdigest(),
    }
    (trial / "start.json").write_text(_canonical(envelope) + "\n", encoding="utf-8")
    assert read_development_attempts(root)[0]["start"] == payload
    with pytest.raises(ExperimentLedgerError, match="invalid_start_fields"):
        start_development_attempt(tmp_path / "new", payload)
    versioned_v1 = _spec("explicit-v1")
    versioned_v1["schema_version"] = "lra-development-attempt.v1"
    with pytest.raises(ExperimentLedgerError, match="invalid_start_version"):
        start_development_attempt(tmp_path / "explicit-v1", versioned_v1)
