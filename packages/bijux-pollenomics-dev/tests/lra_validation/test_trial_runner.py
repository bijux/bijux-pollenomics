"""A numerical command cannot run without a durable development attempt."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

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


def _plan(root: Path, *, run_id: str, command: list[str]) -> dict[str, object]:
    return {
        "schema_version": "lra-development-trial.v2",
        "ledger_root": str(root / "ledger"),
        "timeout_seconds": 3,
        "spec": {
            "schema_version": "lra-development-attempt.v2",
            "run_id": run_id,
            "policy_sha256": "a" * 64,
            "input_hashes": {"split_manifest": "b" * 64, "pollen": "c" * 64},
            "evaluation_binding": _cohort_binding(),
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
            "hyperparameters": {"radius_m": 1000},
            "seed": 42,
            "backend": "python-test",
            "budget": {"seconds": 3, "threads": 1},
            "invocation": {
                "argv": command,
                "cwd": str(root),
                "environment": {},
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
    missing = _plan(
        tmp_path, run_id="missing", command=[sys.executable, "-c", "print('ran')"]
    )
    assert run_development_trial(missing) == 2
    output = tmp_path / "nonzero.score.json"
    script = (
        "import json,pathlib,sys; "
        f"pathlib.Path({str(output)!r}).write_text(json.dumps("
        "{'status':'completed','metrics':{'pollen_mae':0.1},'reason_code':None})); "
        "sys.exit(7)"
    )
    nonzero = _plan(tmp_path, run_id="nonzero", command=[sys.executable, "-c", script])
    assert run_development_trial(nonzero) == 7
    rows = {
        row["start"]["run_id"]: row["result"]
        for row in read_development_attempts(tmp_path / "ledger")
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
    plan = _plan(
        tmp_path,
        run_id="timeout",
        command=[sys.executable, "-c", "import time; time.sleep(0.5)"],
    )
    plan["timeout_seconds"] = 0.02
    assert run_development_trial(plan) == 124
    row = read_development_attempts(tmp_path / "ledger")[0]
    assert row["result"]["reason_code"] == "trial_timeout"


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


def test_invalid_evaluation_binding_cannot_launch_child(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    launched = False

    def launch(*args: object, **kwargs: object) -> None:
        nonlocal launched
        launched = True

    monkeypatch.setattr(
        "bijux_pollenomics_dev.lra_validation.trial_runner.subprocess.run", launch
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
