"""Behavioral checks for the append-only local development ledger."""

from __future__ import annotations

import hashlib
import json
import sys
from concurrent.futures import ThreadPoolExecutor
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


def _design(binding: dict[str, object]) -> dict[str, str]:
    payload = {
        "schema_version": "lra-development-design.v1",
        "status": "frozen",
        "cohort_admission_sha256": binding["cohort_admission_sha256"],
        "scope_sha256": binding["scope_sha256"],
        "split_manifest_sha256": binding["split_manifest_sha256"],
        "experiment_targets": [
            {
                "experiment": "local_pollen_available",
                "target": "vegetation_cover",
            },
            {
                "experiment": "all_target_pollen_withheld",
                "target": "vegetation_cover",
            },
            {
                "experiment": "all_target_pollen_withheld",
                "target": "pollen_composition",
            },
        ],
        "fold_ids": ["sweden-block-01"],
        "candidates": [
            {
                "candidate_id": "reveals-baseline-5000m",
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
                "backend": "python-0.1",
                "invocation": {
                    "argv": [sys.executable, "-c", "raise SystemExit(0)"],
                    "cwd": str(Path.cwd()),
                    "environment": {
                        "MKL_NUM_THREADS": "1",
                        "NUMEXPR_NUM_THREADS": "1",
                        "OMP_NUM_THREADS": "1",
                        "OPENBLAS_NUM_THREADS": "1",
                        "VECLIB_MAXIMUM_THREADS": "1",
                    },
                    "executable_sha256": hashlib.sha256(
                        Path(sys.executable).read_bytes()
                    ).hexdigest(),
                },
            }
        ],
        "seeds": [7],
        "metric_ids": {
            "vegetation_cover": ["vegetation_mae"],
            "pollen_composition": ["pollen_mae"],
        },
        "selection_rule": {
            "primary_metric_by_target": {
                "vegetation_cover": "vegetation_mae",
                "pollen_composition": "pollen_mae",
            },
            "direction_by_metric": {
                "vegetation_mae": "minimize",
                "pollen_mae": "minimize",
            },
            "tie_breakers": ["candidate_id"],
            "minimum_completed_folds": 1,
        },
        "resource_budget": {
            "maximum_trials": 20,
            "maximum_seconds_per_trial": 300,
            "maximum_declared_threads_per_trial": 1,
            "maximum_total_declared_cpu_seconds": 6000,
        },
    }
    canonical = _canonical(payload)
    return {
        "canonical_design_json": canonical,
        "design_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
    }


def _spec(run_id: str = "trial-1") -> dict[str, Any]:
    admission, admission_sha256, scope_sha256 = _admission()
    split_sha256 = "c" * 64
    binding = {
        "canonical_cohort_admission_json": admission,
        "cohort_admission_sha256": admission_sha256,
        "scope_sha256": scope_sha256,
        "split_manifest_sha256": split_sha256,
        "split_kind": "leave_one_site_group_out",
        "experiment": "local_pollen_available",
        "target": "vegetation_cover",
    }
    return {
        "schema_version": "lra-development-attempt.v3",
        "run_id": run_id,
        "development_design": _design(binding),
        "input_hashes": {"pollen": "b" * 64, "split_manifest": split_sha256},
        "evaluation_binding": binding,
        "fold_id": "sweden-block-01",
        "candidate_id": "reveals-baseline-5000m",
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
        "invocation": {
            "argv": [sys.executable, "-c", "raise SystemExit(0)"],
            "cwd": str(Path.cwd()),
            "environment": {
                "MKL_NUM_THREADS": "1",
                "NUMEXPR_NUM_THREADS": "1",
                "OMP_NUM_THREADS": "1",
                "OPENBLAS_NUM_THREADS": "1",
                "VECLIB_MAXIMUM_THREADS": "1",
            },
            "result_path": str(
                Path.cwd() / "artifacts" / "development-ledger-tests" / f"{run_id}.json"
            ),
        },
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
        "metrics": {"vegetation_mae": float("nan")},
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
    with pytest.raises(ExperimentLedgerError, match="invalid_metrics"):
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
    start_development_attempt(
        tmp_path,
        {
            **spec,
            "development_design": _design(binding),
            "evaluation_binding": binding,
        },
    )


def test_rejects_missing_provenance_and_unsafe_identity(tmp_path: Path) -> None:
    with pytest.raises(ExperimentLedgerError, match="invalid_input_hashes"):
        start_development_attempt(tmp_path, {**_spec(), "input_hashes": {"pollen": ""}})
    with pytest.raises(ExperimentLedgerError, match="invalid_run_id"):
        start_development_attempt(tmp_path, _spec("../outside"))
    spec = _spec("no-binding")
    del spec["evaluation_binding"]
    with pytest.raises(ExperimentLedgerError, match="invalid_start_fields"):
        start_development_attempt(tmp_path, spec)
    spec = _spec("baseline")
    with pytest.raises(ExperimentLedgerError, match="trial_candidate_content_mismatch"):
        start_development_attempt(tmp_path, {**spec, "hyperparameters": {}})


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
    with pytest.raises(ExperimentLedgerError, match="legacy_records_in_active_ledger"):
        start_development_attempt(root, _spec("new-after-legacy"))
    with pytest.raises(ExperimentLedgerError, match="invalid_start_fields"):
        start_development_attempt(tmp_path / "new", payload)
    versioned_v1 = _spec("explicit-v1")
    versioned_v1["schema_version"] = "lra-development-attempt.v2"
    with pytest.raises(ExperimentLedgerError, match="invalid_start_version"):
        start_development_attempt(tmp_path / "explicit-v1", versioned_v1)


def test_rejects_undeclared_seed_fold_candidate_and_budget(tmp_path: Path) -> None:
    for field, value, reason in (
        ("seed", 8, "trial_seed_not_declared"),
        ("fold_id", "sweden-block-02", "trial_fold_not_declared"),
        ("candidate_id", "unreviewed", "trial_candidate_not_declared"),
        ("budget", {"seconds": 301, "threads": 1}, "trial_budget_exceeds_design"),
    ):
        spec = _spec(f"bad-{field}")
        spec[field] = value
        with pytest.raises(ExperimentLedgerError, match=reason):
            start_development_attempt(tmp_path / field, spec)


def test_terminal_metrics_must_match_predeclared_target(tmp_path: Path) -> None:
    start_development_attempt(tmp_path, _spec())
    with pytest.raises(
        ExperimentLedgerError, match="terminal_metrics_differ_from_design"
    ):
        finish_development_attempt(
            tmp_path,
            "trial-1",
            {
                "status": "completed",
                "elapsed_seconds": 1,
                "metrics": {"unreviewed_metric": 0.1},
                "reason_code": None,
            },
        )
    with pytest.raises(ExperimentLedgerError, match="invalid_metrics"):
        finish_development_attempt(
            tmp_path,
            "trial-1",
            {
                "status": "completed",
                "elapsed_seconds": 1,
                "metrics": {"vegetation_mae": "not-a-number"},
                "reason_code": None,
            },
        )
    with pytest.raises(ExperimentLedgerError, match="noncompleted_with_metrics"):
        finish_development_attempt(
            tmp_path,
            "trial-1",
            {
                "status": "failed",
                "elapsed_seconds": 1,
                "metrics": {"vegetation_mae": 0.2},
                "reason_code": "failed_with_outcome",
            },
        )


def test_design_digest_and_declared_compute_budget_are_enforced(
    tmp_path: Path,
) -> None:
    bad = _spec("bad-digest")
    bad_design = dict(bad["development_design"])
    bad_design["design_sha256"] = "f" * 64
    with pytest.raises(ExperimentLedgerError, match="design_digest_mismatch"):
        start_development_attempt(
            tmp_path / "bad-digest", {**bad, "development_design": bad_design}
        )

    first = _spec("first")
    design_binding = dict(first["development_design"])
    payload = json.loads(design_binding["canonical_design_json"])
    payload["resource_budget"]["maximum_total_declared_cpu_seconds"] = 300
    canonical = _canonical(payload)
    constrained = {
        "canonical_design_json": canonical,
        "design_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
    }
    first["development_design"] = constrained
    start_development_attempt(tmp_path / "budget", first)
    second = _spec("second")
    second["development_design"] = constrained
    with pytest.raises(
        ExperimentLedgerError, match="development_declared_cpu_budget_exhausted"
    ):
        start_development_attempt(tmp_path / "budget", second)


def test_parallel_starts_cannot_overrun_trial_budget(tmp_path: Path) -> None:
    specs = [_spec("parallel-a"), _spec("parallel-b")]
    design_binding = dict(specs[0]["development_design"])
    payload = json.loads(design_binding["canonical_design_json"])
    payload["resource_budget"].update(
        maximum_trials=1, maximum_total_declared_cpu_seconds=300
    )
    canonical = _canonical(payload)
    constrained = {
        "canonical_design_json": canonical,
        "design_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
    }
    for spec in specs:
        spec["development_design"] = constrained

    def reserve(spec: dict[str, Any]) -> str:
        try:
            return start_development_attempt(tmp_path / "parallel", spec)
        except ExperimentLedgerError as exc:
            return exc.reason_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(reserve, specs))
    assert sum(result.startswith("parallel-") for result in results) == 1
    assert set(results) & {
        "ledger_reservation_busy",
        "development_trial_budget_exhausted",
    }
    assert len(read_development_attempts(tmp_path / "parallel")) == 1


def test_dead_reservation_and_incomplete_attempt_are_preserved_but_recoverable(
    tmp_path: Path,
) -> None:
    root = tmp_path / "ledger"
    start_development_attempt(root, _spec("complete-row"))
    crashed = root / ".development-reservation-active-99999999-1-evidence"
    crashed.write_text(
        _canonical({"created_unix_ns": 1, "pid": 99999999}) + "\n",
        encoding="utf-8",
    )
    incomplete = root / ".development-attempt-incomplete-crash-evidence"
    incomplete.mkdir()
    (incomplete / "start.json").write_text("incomplete", encoding="utf-8")
    assert [row["start"]["run_id"] for row in read_development_attempts(root)] == [
        "complete-row"
    ]
    start_development_attempt(root, _spec("after-recovery"))

    assert [row["start"]["run_id"] for row in read_development_attempts(root)] == [
        "after-recovery",
        "complete-row",
    ]
    assert incomplete.is_dir()
    assert any(
        path.name.startswith(".development-reservation-stale-99999999-")
        for path in root.iterdir()
    )

    malformed_root = tmp_path / "malformed-ledger"
    malformed_root.mkdir()
    malformed = malformed_root / ".development-reservation-active-malformed"
    malformed.write_text("partial", encoding="utf-8")
    with pytest.raises(
        ExperimentLedgerError, match="ledger_reservation_recovery_required"
    ):
        read_development_attempts(malformed_root)
    with pytest.raises(
        ExperimentLedgerError, match="ledger_reservation_recovery_required"
    ):
        start_development_attempt(malformed_root, _spec("refused-recovery"))
    assert malformed.read_text(encoding="utf-8") == "partial"

    interrupted_root = tmp_path / "interrupted-publication-ledger"
    interrupted_root.mkdir()
    interrupted = interrupted_root / ".development-reservation-evidence-orphan"
    interrupted.write_text(
        _canonical({"created_unix_ns": 2, "pid": 99999998}) + "\n",
        encoding="utf-8",
    )
    assert read_development_attempts(interrupted_root) == ()
    start_development_attempt(interrupted_root, _spec("after-publication-recovery"))
    assert any(
        path.name.startswith(".development-reservation-stale-99999998-")
        for path in interrupted_root.iterdir()
    )
