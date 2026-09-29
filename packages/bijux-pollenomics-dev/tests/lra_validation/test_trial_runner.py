"""A numerical command cannot run without a durable development attempt."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import signal
import sys
import time
from typing import Any

import pytest

from bijux_pollenomics_dev.lra_validation.experiment_ledger import (
    ExperimentLedgerError,
    read_development_attempts,
)
from bijux_pollenomics_dev.lra_validation.trial_runner import (
    TrialPlanError,
    run_development_trial,
)


def _cohort_binding() -> dict[str, object]:
    scope_sha256 = "d" * 64
    split_sha256 = "b" * 64
    payload = {
        "profile": "pollenomics-reviewed-evaluation-cohort.v1",
        "decision_manifest_sha256": "a" * 64,
        "candidate_source_manifest_sha256": "b" * 64,
        "admission_id": "review:declared-cohort",
        "reviewer_id": "reviewer:declared",
        "reviewer_authority": "declared_not_authenticated",
        "decision_date": "2026-09-24",
        "admitted_record_ids": ["record:a"],
        "refused_record_ids": [],
        "outcome_access_status": "not_started",
        "scope_id": "scope:development",
        "scope_sha256": scope_sha256,
        "empirical_evaluation_performed": False,
        "scientific_acceptance": "not_evaluated",
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return {
        "canonical_cohort_admission_json": canonical,
        "cohort_admission_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
        "scope_sha256": scope_sha256,
        "split_manifest_sha256": split_sha256,
        "split_kind": "predefined_block",
        "experiment": "all_target_pollen_withheld",
        "target": "pollen_composition",
    }


def _design(
    binding: dict[str, object], command: list[str], cwd: Path
) -> dict[str, str]:
    configuration = {
        "method": "training-mean",
        "transport": "none",
        "taxon_profile": "review-pending",
        "ppe_profile": "review-pending",
        "basin_scenario": "none",
        "spatial_support": "declared-block",
        "temporal_support": "declared-window",
        "uncertainty": "none",
    }
    payload = {
        "schema_version": "lra-development-design.v1",
        "status": "frozen",
        "cohort_admission_sha256": binding["cohort_admission_sha256"],
        "scope_sha256": binding["scope_sha256"],
        "split_manifest_sha256": binding["split_manifest_sha256"],
        "experiment_targets": [
            {
                "experiment": "all_target_pollen_withheld",
                "target": "pollen_composition",
            }
        ],
        "fold_ids": ["development-block-1"],
        "candidates": [
            {
                "candidate_id": "training-mean-radius-1000",
                "model": "training-mean",
                "configuration": configuration,
                "hyperparameters": {"radius_m": 1000},
                "backend": "python-test",
                "invocation": {
                    "argv": command,
                    "cwd": str(cwd),
                    "environment": {
                        "MKL_NUM_THREADS": "1",
                        "NUMEXPR_NUM_THREADS": "1",
                        "OMP_NUM_THREADS": "1",
                        "OPENBLAS_NUM_THREADS": "1",
                        "VECLIB_MAXIMUM_THREADS": "1",
                    },
                    "executable_sha256": hashlib.sha256(
                        Path(command[0]).read_bytes()
                    ).hexdigest(),
                },
            }
        ],
        "seeds": [42],
        "metric_ids": {"pollen_composition": ["pollen_mae"]},
        "selection_rule": {
            "primary_metric_by_target": {"pollen_composition": "pollen_mae"},
            "direction_by_metric": {"pollen_mae": "minimize"},
            "tie_breakers": ["candidate_id"],
            "minimum_completed_folds": 1,
        },
        "resource_budget": {
            "maximum_trials": 20,
            "maximum_seconds_per_trial": 3,
            "maximum_declared_threads_per_trial": 1,
            "maximum_total_declared_cpu_seconds": 60,
        },
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return {
        "canonical_design_json": canonical,
        "design_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
    }


def _plan(root: Path, *, run_id: str, command: list[str]) -> dict[str, Any]:
    binding = _cohort_binding()
    return {
        "schema_version": "lra-development-trial.v2",
        "ledger_root": str(root / "ledger"),
        "timeout_seconds": 3,
        "spec": {
            "schema_version": "lra-development-attempt.v3",
            "run_id": run_id,
            "development_design": _design(binding, command, root),
            "input_hashes": {"split_manifest": "b" * 64, "pollen": "c" * 64},
            "evaluation_binding": binding,
            "fold_id": "development-block-1",
            "candidate_id": "training-mean-radius-1000",
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
            "hyperparameters": {"radius_m": 1000},
            "seed": 42,
            "backend": "python-test",
            "budget": {"seconds": 3, "threads": 1},
            "invocation": {
                "argv": command,
                "cwd": str(root),
                "environment": {
                    "MKL_NUM_THREADS": "1",
                    "NUMEXPR_NUM_THREADS": "1",
                    "OMP_NUM_THREADS": "1",
                    "OPENBLAS_NUM_THREADS": "1",
                    "VECLIB_MAXIMUM_THREADS": "1",
                },
                "result_path": str(root / f"{run_id}.score.json"),
            },
        },
    }


def test_success_is_reserved_before_command_and_terminal_is_immutable(
    tmp_path: Path,
) -> None:
    output = tmp_path / "success.score.json"
    start = tmp_path / "ledger" / "success" / "start.json"
    script = (
        "import json,pathlib; "
        f"assert pathlib.Path({str(start)!r}).is_file(); "
        f"pathlib.Path({str(output)!r}).write_text(json.dumps("
        "{'status':'completed','metrics':{'pollen_mae':0.25},'reason_code':None}))"
    )
    plan = _plan(tmp_path, run_id="success", command=[sys.executable, "-c", script])
    assert run_development_trial(plan) == 0
    row = read_development_attempts(tmp_path / "ledger")[0]
    assert row["start"]["invocation"]["argv"] == [sys.executable, "-c", script]
    assert row["result"]["metrics"] == {"pollen_mae": 0.25}
    with pytest.raises(TrialPlanError, match="trial_result_already_exists"):
        run_development_trial(plan)


def test_missing_result_and_nonzero_command_are_failed_not_silent(
    tmp_path: Path,
) -> None:
    missing_root = tmp_path / "missing-case"
    missing_root.mkdir()
    missing = _plan(
        missing_root,
        run_id="missing",
        command=[sys.executable, "-c", "print('ran')"],
    )
    assert run_development_trial(missing) == 2
    nonzero_root = tmp_path / "nonzero-case"
    nonzero_root.mkdir()
    output = nonzero_root / "nonzero.score.json"
    script = (
        "import json,pathlib,sys; "
        f"pathlib.Path({str(output)!r}).write_text(json.dumps("
        "{'status':'completed','metrics':{'pollen_mae':0.1},'reason_code':None})); "
        "sys.exit(7)"
    )
    nonzero = _plan(
        nonzero_root, run_id="nonzero", command=[sys.executable, "-c", script]
    )
    assert run_development_trial(nonzero) == 7
    rows = {
        row["start"]["run_id"]: row["result"]
        for root in (missing_root, nonzero_root)
        for row in read_development_attempts(root / "ledger")
    }
    assert rows["missing"]["reason_code"] == "missing_trial_result"
    assert rows["nonzero"]["reason_code"] == "nonzero_command_exit"
    assert all(row["status"] == "failed" for row in rows.values())


def test_invalid_metric_and_credential_environment_are_refused(
    tmp_path: Path,
) -> None:
    output = tmp_path / "invalid.score.json"
    script = f"open({str(output)!r},'w').write('{{bad-json')"
    plan = _plan(tmp_path, run_id="invalid", command=[sys.executable, "-c", script])
    assert run_development_trial(plan) == 2
    row = read_development_attempts(tmp_path / "ledger")[0]
    assert row["result"]["reason_code"] == "invalid_trial_result"
    secret = _plan(tmp_path, run_id="secret", command=[sys.executable, "-c", "pass"])
    secret["spec"]["invocation"]["environment"] = {"API_TOKEN": "never-record"}
    with pytest.raises(
        ExperimentLedgerError, match="credential_environment_not_recordable"
    ):
        run_development_trial(secret)
    assert len(read_development_attempts(tmp_path / "ledger")) == 1


def test_timeout_retains_terminal_failure(tmp_path: Path) -> None:
    escaped = tmp_path / "escaped-descendant.txt"
    descendant = (
        "import pathlib,time; time.sleep(0.2); "
        f"pathlib.Path({str(escaped)!r}).write_text('escaped')"
    )
    script = (
        "import subprocess,sys,time; "
        f"subprocess.Popen([sys.executable,'-c',{descendant!r}]); "
        "time.sleep(5)"
    )
    plan = _plan(
        tmp_path,
        run_id="timeout",
        command=[sys.executable, "-c", script],
    )
    plan["timeout_seconds"] = 0.02
    plan["spec"]["budget"]["seconds"] = 0.02
    assert run_development_trial(plan) == 124
    row = read_development_attempts(tmp_path / "ledger")[0]
    assert row["result"]["reason_code"] == "trial_timeout"
    time.sleep(0.3)
    assert not escaped.exists()


def test_result_output_cannot_replace_append_only_ledger(tmp_path: Path) -> None:
    plan = _plan(tmp_path, run_id="overlap", command=[sys.executable, "-c", "pass"])
    plan["spec"]["invocation"]["result_path"] = str(
        tmp_path / "ledger" / "overlap" / "result.json"
    )
    with pytest.raises(TrialPlanError, match="trial_result_overlaps_ledger"):
        run_development_trial(plan)
    assert read_development_attempts(tmp_path / "ledger") == ()


def test_legacy_trial_plan_is_refused_before_reservation(tmp_path: Path) -> None:
    plan = _plan(tmp_path, run_id="legacy", command=[sys.executable, "-c", "pass"])
    plan["schema_version"] = "lra-development-trial.v1"
    with pytest.raises(TrialPlanError, match="invalid_trial_plan_version"):
        run_development_trial(plan)
    assert read_development_attempts(tmp_path / "ledger") == ()


def test_timeout_and_thread_limits_must_match_declared_budget(tmp_path: Path) -> None:
    timeout = _plan(tmp_path, run_id="timeout-budget", command=[sys.executable])
    timeout["timeout_seconds"] = 2
    with pytest.raises(TrialPlanError, match="trial_timeout_differs_from_budget"):
        run_development_trial(timeout)

    threads = _plan(tmp_path, run_id="thread-budget", command=[sys.executable])
    threads["spec"]["invocation"]["environment"]["OMP_NUM_THREADS"] = "2"
    with pytest.raises(
        ExperimentLedgerError, match="invocation_thread_budget_not_enforced"
    ):
        run_development_trial(threads)
    assert read_development_attempts(tmp_path / "ledger") == ()


def test_invalid_evaluation_binding_cannot_launch_child(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    launched = False

    def launch(*args: object, **kwargs: object) -> None:
        nonlocal launched
        launched = True

    monkeypatch.setattr(
        "bijux_pollenomics_dev.lra_validation.trial_runner.subprocess.Popen", launch
    )
    plan = _plan(
        tmp_path,
        run_id="invalid-binding",
        command=[sys.executable, "-c", "pass"],
    )
    spec_value = plan["spec"]
    assert isinstance(spec_value, dict)
    spec = dict(spec_value)
    binding_value = spec["evaluation_binding"]
    assert isinstance(binding_value, dict)
    binding = dict(binding_value)
    binding["experiment"] = "local_pollen_available"
    spec["evaluation_binding"] = binding
    plan["spec"] = spec

    with pytest.raises(ExperimentLedgerError, match="invalid_experiment_target"):
        run_development_trial(plan)
    assert launched is False
    assert read_development_attempts(tmp_path / "ledger") == ()
    invocation = spec["invocation"]
    assert isinstance(invocation, dict)
    result_path_value = invocation["result_path"]
    assert isinstance(result_path_value, str)
    result_path = Path(result_path_value)
    assert not result_path.exists()


def test_undeclared_command_cannot_launch_child(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    launched = False

    def launch(*args: object, **kwargs: object) -> None:
        nonlocal launched
        launched = True

    monkeypatch.setattr(
        "bijux_pollenomics_dev.lra_validation.trial_runner.subprocess.Popen", launch
    )
    plan = _plan(tmp_path, run_id="changed-command", command=[sys.executable])
    plan["spec"]["invocation"]["argv"] = [sys.executable, "-c", "pass"]

    with pytest.raises(ExperimentLedgerError, match="trial_invocation_not_declared"):
        run_development_trial(plan)
    assert launched is False
    assert read_development_attempts(tmp_path / "ledger") == ()

    plan = _plan(tmp_path, run_id="changed-environment", command=[sys.executable])
    plan["spec"]["invocation"]["environment"]["MODEL_MODE"] = "undeclared"
    with pytest.raises(ExperimentLedgerError, match="trial_invocation_not_declared"):
        run_development_trial(plan)
    assert launched is False
    assert read_development_attempts(tmp_path / "ledger") == ()


def test_signal_during_process_creation_terminates_returned_group(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class Process:
        pid = 99999997
        terminated = False

        def poll(self) -> int | None:
            return 143 if self.terminated else None

    process = Process()

    def launch(*args: object, **kwargs: object) -> Process:
        signal.raise_signal(signal.SIGTERM)
        return process

    def terminate(target: Process) -> None:
        target.terminated = True

    monkeypatch.setattr(
        "bijux_pollenomics_dev.lra_validation.trial_runner.subprocess.Popen", launch
    )
    monkeypatch.setattr(
        "bijux_pollenomics_dev.lra_validation.trial_runner._terminate_process_group",
        terminate,
    )
    plan = _plan(tmp_path, run_id="creation-signal", command=[sys.executable])

    assert run_development_trial(plan) == 128 + signal.SIGTERM
    assert process.terminated is True
    row = read_development_attempts(tmp_path / "ledger")[0]
    assert row["result"]["reason_code"] == "trial_runner_interrupted"
