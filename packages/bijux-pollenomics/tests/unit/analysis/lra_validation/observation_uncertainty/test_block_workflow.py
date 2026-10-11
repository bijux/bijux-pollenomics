"""Block parent admission keeps every predicted/refused/not-run unit."""

from dataclasses import replace
import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from bijux_pollenomics.analysis.lra_validation.contracts import (
    ValidationRefusal,
    canonical_json,
)
from bijux_pollenomics.analysis.lra_validation.observation_uncertainty import (
    block_workflow,
)
from bijux_pollenomics.analysis.lra_validation.observation_uncertainty.block_contracts import (
    BlockEffortDeclaration,
    BlockObservationUncertaintyPlan,
)


def _entry(record: str, method: str) -> BlockEffortDeclaration:
    return BlockEffortDeclaration(
        "block:a",
        record,
        "bin",
        method,
        ("Alnus", "Betula"),
        100,
        len(record + method),
        record + ".json",
        "a" * 64,
    )


def _fixture(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[BlockObservationUncertaintyPlan, dict[tuple[str, str, str], str]]:
    methods = ("model", "training_mean")
    records = ("p1", "p2")
    predictions = {
        ("block:a", "p1", "model"): {
            "fold_id": "block:a",
            "record_id": "p1",
            "method": "model",
            "bin_id": "bin",
            "pollen_fraction": {"Alnus": 0.6, "Betula": 0.4},
            "prediction_manifest_sha256": "c" * 64,
        },
        ("block:a", "p1", "training_mean"): {
            "fold_id": "block:a",
            "record_id": "p1",
            "method": "training_mean",
            "bin_id": "bin",
            "pollen_fraction": {"Alnus": 0.5, "Betula": 0.5},
            "prediction_manifest_sha256": "d" * 64,
        },
    }
    failures = [
        {
            "fold_id": "block:a",
            "record_id": "p2",
            "method": "model",
            "status": "refused",
            "reason_code": "fit_refused",
        },
        {
            "fold_id": "block:a",
            "record_id": "p2",
            "method": "training_mean",
            "status": "not_run",
            "reason_code": "interrupted",
        },
    ]
    scientific = {
        "failures": failures,
        "generated_predictions": 2,
        "refused_predictions": 1,
        "not_run_predictions": 1,
    }
    product = SimpleNamespace(manifest_sha256="b" * 64)
    manifest = {"scientific_payload": scientific}
    folds = {"block:a": {"test_record_ids": list(records)}}

    def read_predictions(*args: object, **kwargs: object) -> object:
        return product, manifest, folds, predictions, methods

    def read_member(_product: object, name: str) -> object:
        assert name == "experiment.json"
        return {
            "request": {
                "request_template": {
                    "taxa": ["Alnus", "Betula"],
                    "temporal_matching": {"bins": [{"bin_id": "bin"}]},
                }
            }
        }

    monkeypatch.setattr(
        block_workflow,
        "read_spatial_block_predictions",
        read_predictions,
    )
    monkeypatch.setattr(block_workflow, "read_member", read_member)
    plan = BlockObservationUncertaintyPlan(
        "b" * 64,
        tuple(_entry(record, method) for record in records for method in methods),
        10,
        0.9,
    )
    return plan, {
        ("block:a", "p1", "model"): "predicted",
        ("block:a", "p1", "training_mean"): "predicted",
        ("block:a", "p2", "model"): "refused",
        ("block:a", "p2", "training_mean"): "not_run",
    }


def test_parent_reader_preserves_exact_three_way_denominator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan, expected = _fixture(monkeypatch)
    _, _, _, statuses = block_workflow.validate_block_plan_parent(tmp_path, plan)
    assert statuses == expected


def test_missing_target_method_cell_refuses_before_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan, _ = _fixture(monkeypatch)
    with pytest.raises(ValidationRefusal, match="fold, target record and method"):
        block_workflow.validate_block_plan_parent(
            tmp_path, replace(plan, entries=plan.entries[:-1])
        )


def test_counting_design_is_bound_to_exact_canonical_source_bytes() -> None:
    value = {
        "schema_version": "lra-synthetic-counting-design.v1",
        "data_kind": "synthetic",
        "record_id": "p1",
        "bin_id": "bin",
        "planned_effort": 100,
        "effort_unit": "pollen_grains",
        "timing_declaration": "before_outcome_access",
        "declaration_provenance": "prospective fixture",
    }
    digest = hashlib.sha256((canonical_json(value) + "\n").encode()).hexdigest()
    entry = replace(_entry("p1", "model"), evidence_sha256=digest)
    block_workflow._validate_counting_design(value, entry)
    with pytest.raises(ValidationRefusal, match="retained evidence"):
        block_workflow._validate_counting_design(
            {**value, "declaration_provenance": "forged"}, entry
        )
