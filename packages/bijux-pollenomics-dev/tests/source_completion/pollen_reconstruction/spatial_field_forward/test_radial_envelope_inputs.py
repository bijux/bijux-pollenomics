"""Bind the old qualification while keeping scored targets out of phase one."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward import (
    radial_envelope_workflow as workflow,
)


@pytest.fixture
def metadata(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    repository = Path(__file__).resolve().parents[6]
    protocol = json.loads((repository / workflow.PROTOCOL).read_text())
    original_body = b'{"physical": {"regional_extent_m": 100000.0}}'
    original = tmp_path / protocol["original_protocol"]
    original.parent.mkdir(parents=True)
    original.write_bytes(original_body)
    prediction = {
        "schema_version": "spatial-field-forward-predictions.v1",
        "source_commit": protocol["prior_producer_source_commit"],
        "axis": list(workflow.AXIS),
        "geometry": [{"core": core} for core in workflow.CORES],
        "contexts": [{"context_id": f"source_context_{i}"} for i in range(18)],
    }
    verification = {
        "source_rows": 147,
        "selected_samples": 59,
        "source_contexts": 18,
        "scores": {"scored_rows": 54, "refused_rows": 0},
        "predictions_sha256": protocol["repository_inputs"][
            protocol["source_prediction"]
        ]["sha256"],
        "result_sha256": protocol["repository_inputs"][protocol["source_result"]][
            "sha256"
        ],
    }
    execution = {
        "source_commit": protocol["prior_observer_source_commit"],
        "exit_code": 0,
        "pytest_passed": 1,
        "source_results": {
            key: verification[key] for key in ("predictions_sha256", "result_sha256")
        },
    }
    values = {
        protocol["source_prediction"]: prediction,
        protocol["source_verification"]: verification,
        protocol["source_execution"]: execution,
    }
    requested = []

    def declared_files(_: Path, pins: dict[str, Any]) -> dict[str, bytes]:
        assert protocol["source_result"] not in pins
        requested.append(set(pins))
        return {key: json.dumps(values[key]).encode() for key in pins}

    monkeypatch.setattr(workflow, "bound_files", declared_files)
    monkeypatch.setattr(
        subprocess, "check_output", lambda *_args, **_kwargs: original_body
    )
    return {
        "repository": tmp_path,
        "protocol": protocol,
        "prediction": prediction,
        "verification": verification,
        "execution": execution,
        "requested": requested,
    }


def test_prediction_phase_reads_qualification_without_scored_result(
    metadata: dict[str, Any],
) -> None:
    prediction, original = workflow.read_prediction_inputs(
        metadata["repository"], metadata["protocol"]
    )
    assert prediction == metadata["prediction"]
    assert original["physical"]["regional_extent_m"] == 100000
    assert len(metadata["requested"]) == 1


@pytest.mark.parametrize(
    ("owner", "key", "value"),
    [
        ("prediction", "source_commit", "different"),
        ("verification", "selected_samples", 58),
        ("execution", "exit_code", 1),
        ("execution", "pytest_passed", 0),
    ],
)
def test_changed_qualification_refuses(
    metadata: dict[str, Any], owner: str, key: str, value: Any
) -> None:
    metadata[owner][key] = value
    with pytest.raises(ValueError, match="qualification differs"):
        workflow.read_prediction_inputs(metadata["repository"], metadata["protocol"])


def test_changed_original_geometry_protocol_refuses(
    metadata: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(subprocess, "check_output", lambda *_args, **_kwargs: b"{}")
    with pytest.raises(ValueError, match="Original geometry protocol changed"):
        workflow.read_prediction_inputs(metadata["repository"], metadata["protocol"])


def test_changed_prospective_call_population_refuses_before_read(
    metadata: dict[str, Any],
) -> None:
    metadata["protocol"]["design"]["fixed_homogeneous_ring_calls"] = 769
    with pytest.raises(ValueError, match="Prospective design"):
        workflow.read_prediction_inputs(metadata["repository"], metadata["protocol"])
    assert metadata["requested"] == []
