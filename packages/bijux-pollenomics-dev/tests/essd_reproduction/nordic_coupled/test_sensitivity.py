"""Artificial complete source cohorts and protocol-bound scenario accounting."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.nordic_coupled import (
    inputs,
    sensitivity,
    workflow,
)

from . import test_workflow
from .test_inputs import fixture as source_fixture


def inventory(root: Path, destination: Path) -> str:
    rows = []
    for path in sorted(root.rglob("*.json")):
        raw = path.read_bytes()
        rows.append(
            {
                "path": path.relative_to(root).as_posix(),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "bytes": len(raw),
            }
        )
    destination.write_bytes(sensitivity.encoded(rows))
    return hashlib.sha256(destination.read_bytes()).hexdigest()


@pytest.fixture
def cohort(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Construct protocol-bound artificial counts without copying source files."""
    repository = tmp_path / "repository"
    cores, protocol = source_fixture()
    baseline_raw = sensitivity.encoded(protocol)
    baseline_sha = hashlib.sha256(baseline_raw).hexdigest()
    monkeypatch.setattr(workflow, "PROTOCOL_SHA256", baseline_sha)
    scenario_protocol = {
        "schema_version": sensitivity.SCHEMA,
        "baseline_protocol_sha256": baseline_sha,
        "axis": list(inputs.AXIS),
        "nominal_ppe": {key: str(value) for key, value in sensitivity.NOMINAL.items()},
        "ppe_sd": {key: str(value) for key, value in sensitivity.SD.items()},
        "scenarios": [
            {"id": key, "taxon": value[0], "ppe": value[1]}
            for key, value in sensitivity.SCENARIOS.items()
        ],
    }
    scenario_raw = sensitivity.encoded(scenario_protocol)
    for relative, body in (
        (inputs.PROTOCOL, baseline_raw),
        (sensitivity.PROTOCOL, scenario_raw),
    ):
        target = repository / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body)
    nominal = tmp_path / "nominal"
    inputs.project(cores, protocol, nominal)
    (nominal / "source-pins.json").write_text("[]\n")
    manifest = tmp_path / "nominal-members.json"
    checksum = inventory(nominal, manifest)
    return {
        "repository": repository,
        "nominal": nominal,
        "manifest": manifest,
        "sha256": checksum,
        "protocol_sha256": hashlib.sha256(scenario_raw).hexdigest(),
    }


@pytest.mark.parametrize("scenario_id", tuple(sensitivity.SCENARIOS))
def test_complete_scenario_real_readers_and_byte_preservation(
    cohort: dict[str, Any], tmp_path: Path, scenario_id: str
) -> None:
    output, manifest = tmp_path / "scenario", tmp_path / "scenario-members.json"
    result = sensitivity.materialize(
        cohort["repository"],
        cohort["nominal"],
        cohort["manifest"],
        cohort["sha256"],
        output,
        manifest,
        scenario_id=scenario_id,
        protocol_sha256=cohort["protocol_sha256"],
    )
    assert result["reader_admission"] == {
        "geometry_reads": 18,
        "training_pair_requests": 18,
        "engine_calls": 0,
    }
    rows, pins = workflow.input_scope(
        output, manifest, result["input_manifest"]["sha256"]
    )
    assert len(rows) == 6 and len(pins) == 80
    taxon, endpoint = sensitivity.SCENARIOS[scenario_id]
    for name in workflow.NAMES:
        payload = json.loads((output / name / "experiment.json").read_bytes())
        means = {
            p["taxon"]: p["ppe"] for p in payload["request_template"]["parameters"]
        }
        assert means == {**sensitivity.NOMINAL, taxon: float(endpoint)}
        params = json.loads((output / name / "parameters.json").read_bytes())
        assert params["PPE"] == [means[t] for t in inputs.AXIS]
        decision = json.loads((output / name / "decision.json").read_bytes())
        assert decision["protocol"]["schema_version"] == sensitivity.SCHEMA
        assert decision["sensitivity"]["protocol"] == result["protocol"]
        for member in (
            "chronology",
            "taxa",
            "dependency_lock",
            "projection",
            "BOKE-raw",
            "BUS-raw",
            "SOLSOE83-raw",
            "BOKE-geometry",
            "BUS-geometry",
            "SOLSOE83-geometry",
        ):
            assert (output / name / (member + ".json")).read_bytes() == (
                cohort["nominal"] / name / (member + ".json")
            ).read_bytes()
    assert (output / "source-pins.json").read_bytes() == (
        cohort["nominal"] / "source-pins.json"
    ).read_bytes()


def test_changed_nominal_parameter_refused_before_output(
    cohort: dict[str, Any], tmp_path: Path
) -> None:
    path = cohort["nominal"] / workflow.NAMES[0] / "parameters.json"
    value = json.loads(path.read_bytes())
    value["PPE"][0] = 1.0
    path.write_bytes(sensitivity.encoded(value))
    checksum = inventory(cohort["nominal"], cohort["manifest"])
    with pytest.raises(ValueError, match="Nominal parameter/decision"):
        sensitivity.materialize(
            cohort["repository"],
            cohort["nominal"],
            cohort["manifest"],
            checksum,
            tmp_path / "scenario",
            tmp_path / "members.json",
            scenario_id="betula-lower",
            protocol_sha256=cohort["protocol_sha256"],
        )
    assert not (tmp_path / "scenario").exists()


def test_changed_declared_endpoint_refused(cohort: dict[str, Any]) -> None:
    path = cohort["repository"] / sensitivity.PROTOCOL
    value = json.loads(path.read_bytes())
    value["scenarios"][0]["ppe"] = "0"
    path.write_bytes(sensitivity.encoded(value))
    with pytest.raises(ValueError, match="Declared PPE protocol"):
        sensitivity.derive(
            cohort["repository"],
            cohort["nominal"],
            cohort["manifest"],
            cohort["sha256"],
            "betula-lower",
            hashlib.sha256(path.read_bytes()).hexdigest(),
        )


def test_rehashed_target_change_refused_before_batch(
    cohort: dict[str, Any], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output, manifest = tmp_path / "scenario", tmp_path / "members.json"
    sensitivity.materialize(
        cohort["repository"],
        cohort["nominal"],
        cohort["manifest"],
        cohort["sha256"],
        output,
        manifest,
        scenario_id="ulmus-upper",
        protocol_sha256=cohort["protocol_sha256"],
    )
    path = output / workflow.NAMES[-1] / "BOKE-raw.json"
    value = json.loads(path.read_bytes())
    value["sample"]["counts"][0] += 1
    path.write_bytes(sensitivity.encoded(value))
    checksum = inventory(output, manifest)

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        pytest.fail("Changed target reached numerical batch")

    monkeypatch.setattr(workflow, "batch", forbidden)
    with pytest.raises(ValueError, match="Scenario derivation differs"):
        sensitivity.run_scenario(
            cohort["repository"],
            cohort["nominal"],
            cohort["manifest"],
            cohort["sha256"],
            output,
            manifest,
            checksum,
            tmp_path / "prediction",
            scenario_id="ulmus-upper",
            protocol_sha256=cohort["protocol_sha256"],
            phase="prepare",
            execution_epoch="0" * 40,
        )


def test_new_batch_protocol_and_mixed_dispositions(
    cohort: dict[str, Any], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    controls = test_workflow.TestWorkflow()
    controls.setUp()
    controls.root = tmp_path
    protocol_path = cohort["repository"] / sensitivity.PROTOCOL
    binding = sensitivity.pin(protocol_path, protocol_path.read_bytes())
    actual_read = workflow.read

    def read(path: Path, checksum: str, maximum: int) -> tuple[bytes, Any]:
        return (
            actual_read(path, checksum, maximum)
            if path == protocol_path
            else (b"", controls.payload)
        )

    monkeypatch.setattr(workflow, "read", read)
    monkeypatch.setattr(workflow, "input_scope", lambda *args: (controls.rows, []))
    monkeypatch.setattr(workflow, "apis", lambda: controls.api)
    result = workflow.batch(
        tmp_path / "inputs",
        tmp_path / "members",
        "a" * 64,
        tmp_path / "predictions",
        phase="prepare",
        execution_epoch="0" * 40,
        protocol_binding=binding,
    )
    assert (
        result["protocol_sha256"]
        == cohort["protocol_sha256"]
        != workflow.PROTOCOL_SHA256
    )
    assert result["protocol_binding"] == binding
    assert result["all_bins_accounted"] is True
    assert len(result["bins"]) == 6
    for row in result["bins"]:
        assert row["prediction"]["status_counts"] == {"predicted": 6, "refused": 3}


def test_score_cannot_cross_protocol_binding(
    cohort: dict[str, Any], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    controls = test_workflow.TestWorkflow()
    controls.setUp()
    protocol_path = cohort["repository"] / sensitivity.PROTOCOL
    binding = sensitivity.pin(protocol_path, protocol_path.read_bytes())
    prior = {
        "schema_version": "nordic-coupled-batch.v1",
        "all_bins_accounted": True,
        "protocol_sha256": cohort["protocol_sha256"],
        "protocol_binding": {**binding, "bytes": binding["bytes"] + 1},
    }
    actual_read = workflow.read

    def read(path: Path, checksum: str, maximum: int) -> tuple[bytes, Any]:
        return (
            actual_read(path, checksum, maximum)
            if path == protocol_path
            else (b"", prior)
        )

    monkeypatch.setattr(workflow, "read", read)
    monkeypatch.setattr(workflow, "input_scope", lambda *args: (controls.rows, []))
    monkeypatch.setattr(workflow, "apis", lambda: controls.api)
    with pytest.raises(ValueError, match="Incomplete prediction batch"):
        workflow.batch(
            tmp_path / "inputs",
            tmp_path / "members",
            "a" * 64,
            tmp_path / "scores",
            phase="score",
            execution_epoch="0" * 40,
            prediction_index=tmp_path / "predictions/batch.json",
            prediction_index_sha256="b" * 64,
            protocol_binding=binding,
        )
    assert controls.calls == []
