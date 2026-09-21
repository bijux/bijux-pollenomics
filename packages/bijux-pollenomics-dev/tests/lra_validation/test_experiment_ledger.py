"""Behavioral checks for the append-only local development ledger."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_pollenomics_dev.lra_validation.experiment_ledger import (
    ExperimentLedgerError,
    finish_development_attempt,
    read_development_attempts,
    start_development_attempt,
)


def _spec(run_id: str = "trial-1") -> dict[str, object]:
    return {
        "run_id": run_id,
        "policy_sha256": "a" * 64,
        "input_hashes": {"pollen": "b" * 64, "folds": "c" * 64},
        "target": "local_pollen_available",
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


def test_rejects_final_access_and_detects_tampering(tmp_path: Path) -> None:
    root = tmp_path / "ledger"
    final = {**_spec(), "target": "final_test"}
    with pytest.raises(ExperimentLedgerError, match="invalid_target"):
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


def test_rejects_missing_provenance_and_unsafe_identity(tmp_path: Path) -> None:
    with pytest.raises(ExperimentLedgerError, match="invalid_input_hashes"):
        start_development_attempt(tmp_path, {**_spec(), "input_hashes": {"pollen": ""}})
    with pytest.raises(ExperimentLedgerError, match="invalid_run_id"):
        start_development_attempt(tmp_path, _spec("../outside"))
    start_development_attempt(tmp_path, {**_spec("baseline"), "hyperparameters": {}})
