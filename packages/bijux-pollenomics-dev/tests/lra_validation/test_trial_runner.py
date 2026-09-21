"""A numerical command cannot run without a durable development attempt."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from bijux_pollenomics_dev.lra_validation.experiment_ledger import (
    ExperimentLedgerError,
    read_development_attempts,
)
from bijux_pollenomics_dev.lra_validation.trial_runner import (
    TrialPlanError,
    run_development_trial,
)


def _plan(root: Path, *, run_id: str, command: list[str]) -> dict[str, object]:
    return {
        "schema_version": "lra-development-trial.v1",
        "ledger_root": str(root / "ledger"),
        "timeout_seconds": 3,
        "spec": {
            "run_id": run_id,
            "policy_sha256": "a" * 64,
            "input_hashes": {"folds": "b" * 64, "pollen": "c" * 64},
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
