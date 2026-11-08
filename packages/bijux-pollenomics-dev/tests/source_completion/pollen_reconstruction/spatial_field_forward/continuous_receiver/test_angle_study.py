"""Real synthetic producer/observer transport and fail-closed six-owner accounting."""

from __future__ import annotations

from dataclasses import asdict
from fractions import Fraction as F
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.angle_moments import (
    observe,
    study,
    transport,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.angle_moments.inputs import (
    FrozenInputs,
    identity,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.angle_moments.population import (
    MomentPopulation,
    enclose_population,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.kernel import (
    Geometry,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.verification.contracts import (
    OWNERS,
    RESOURCE_LIMITS,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.verification.receiver_angles import (
    verify_angle_certificate,
)


@pytest.fixture(scope="module")
def synthetic_population() -> MomentPopulation:
    """Evaluate one source-free five-domain geometry, never the frozen six cases."""
    geometry = Geometry(F(1, 2), F(1), F(4), (F(1000), F(0)), (F(2000), F(0)))
    population = enclose_population((geometry,), max_leaves=5)
    return MomentPopulation(
        population.results * 6,
        population.refusals * 6,
        population.budgets * 6,
        population.elapsed_seconds,
    )


def configure(
    root: Path, monkeypatch: pytest.MonkeyPatch, population: MomentPopulation
) -> Path:
    result = population.results[0]
    assert result is not None
    model = result.partition.geometry
    geometry = {
        "coefficient_A": str(model.coefficient),
        "receiver_radius_m": str(model.receiver),
        "outer_radius_m": str(model.outer),
        "first_anchor_xy_m": [str(x) for x in model.first],
        "second_anchor_xy_m": [str(x) for x in model.second],
    }
    frozen = {
        "source_commit": "retained-unit-law",
        "cases": [
            {"core": core, "taxon": taxon, "geometry": geometry}
            for core, taxon in OWNERS
        ],
    }
    inputs = FrozenInputs(
        {
            "law": {"unit_control": True},
            "limits": "synthetic control only",
            "independent_resources": {"wall_seconds": 180},
        },
        frozen,
        (model,) * 6,
        {"unit-control": identity(b"exact synthetic law")},
    )
    guard = transport.SourceGuard("committed-unit-control", "index-control", ())
    for module in (study, observe):
        monkeypatch.setattr(module, "read_inputs", lambda *args: inputs)
        monkeypatch.setattr(
            module, "environment", lambda *args: {"synthetic_control": True}
        )
        monkeypatch.setattr(module, "source_guard", lambda *args: guard)
        monkeypatch.setattr(
            module,
            "check_terminal",
            lambda *args: {
                "source_and_index_unchanged": True,
                "inputs_unchanged": True,
                "elapsed_seconds": 0,
                "peak_rss_bytes": 1,
            },
        )
    monkeypatch.setattr(study, "enclose_population", lambda *args: population)
    return root / "unit-control.json"


def test_actual_synthetic_serialization_replays_independently(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    synthetic_population: MomentPopulation,
) -> None:
    protocol = configure(tmp_path, monkeypatch, synthetic_population)
    producer = tmp_path / "artifacts/producer"
    native = study.run_study(tmp_path, protocol, producer)
    assert native["status"] == "refuse_unresolved"
    assert native["complete_cases"] == 6
    assert native["certified_widths"] < 18
    result = observe.run_observer(
        tmp_path, protocol, producer, tmp_path / "artifacts/observer"
    )
    assert result["accounting_verified"] is True
    assert result["status"] == "refuse_unresolved"
    assert result["complete_cases"] == 6
    assert result["completed_leaves"] == 30
    assert result["independent_certified_widths"] < 18
    assert all(row["initial_domains"] == 5 for row in result["cases"])
    assert all("independent_bounds" in row for row in result["cases"])
    assert native["native_prefix_recaptured"] is False


@pytest.mark.parametrize(
    "fault",
    ["source", "input", "resource", "owner", "certificate-index", "certificate-bytes"],
)
def test_observer_refuses_changed_identity_owner_or_certificate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    synthetic_population: MomentPopulation,
    fault: str,
) -> None:
    protocol = configure(tmp_path, monkeypatch, synthetic_population)
    producer = tmp_path / "artifacts/producer"
    study.run_study(tmp_path, protocol, producer)
    path = producer / "result.json"
    result = json.loads(path.read_bytes())
    if fault == "source":
        result["source_commit"] = "foreign"
    elif fault == "input":
        result["input_identities"] = {}
    elif fault == "resource":
        result["resource_limits"]["wall_seconds"] = 181
    elif fault == "owner":
        result["cases"][0]["core"] = "foreign"
    elif fault == "certificate-index":
        result["cases"][0]["certificate_index"] = 1
    else:
        (producer / "certificates.json").write_bytes(b"[]")
    path.write_text(json.dumps(result))
    output = tmp_path / "artifacts/observer"
    with pytest.raises(ValueError):
        observe.run_observer(tmp_path, protocol, producer, output)
    failed = json.loads((output / "independent-check.json").read_bytes())
    assert failed["status"] == "failed"
    assert len(failed["cases"]) == 6
    assert failed["error"]


def test_producer_failure_keeps_all_original_owner_slots(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    synthetic_population: MomentPopulation,
) -> None:
    protocol = configure(tmp_path, monkeypatch, synthetic_population)

    def fail(*args: object) -> None:
        raise ValueError("source mismatch control")

    monkeypatch.setattr(study, "source_guard", fail)
    output = tmp_path / "artifacts/producer"
    with pytest.raises(ValueError, match="source mismatch"):
        study.run_study(tmp_path, protocol, output)
    result = json.loads((output / "result.json").read_bytes())
    assert result["status"] == "failed"
    assert [(row["core"], row["taxon"]) for row in result["cases"]] == list(OWNERS)
    assert all(row["complete"] is False for row in result["cases"])


def test_work_minimum_and_one_dimensional_reservation_checks() -> None:
    work = {
        "attempted_panels": 5,
        "reserved_node_evaluations": 35,
        "completed_node_evaluations": 35,
        "derivative_boxes": 5,
        "leaf_reservations": 5,
    }
    minima = {
        "minimum_attempted_panels": 5,
        "minimum_completed_nodes": 35,
        "minimum_derivative_boxes": 5,
        "leaves": 5,
    }
    assert observe._work({"work": work}, minima) == work
    for name, value in (
        ("reserved_node_evaluations", 34),
        ("derivative_boxes", 4),
        ("leaf_reservations", 4),
        ("attempted_panels", True),
    ):
        changed = {**work, name: value}
        with pytest.raises(ValueError):
            observe._work({"work": changed}, minima)


def test_output_owner_is_fresh_bounded_and_does_not_follow_symbols(
    tmp_path: Path,
) -> None:
    output = transport.fresh_output(tmp_path, tmp_path / "artifacts/output")
    raw = transport.write_json(output, "receipt.json", {"scope": "control"})
    assert identity(raw)["bytes"] == len(raw)
    with pytest.raises(ValueError):
        transport.fresh_output(tmp_path, output)
    with pytest.raises(ValueError):
        transport.write_json(output, "receipt.json", {})
    with pytest.raises(ValueError):
        transport.write_json(output, "../escape.json", {})
    with pytest.raises(ValueError, match="allocation"):
        transport.write_json(output, "oversize.json", "x" * 4_850_000)
    (tmp_path / "artifacts/alias").symlink_to(output, target_is_directory=True)
    with pytest.raises(ValueError):
        transport.fresh_output(tmp_path, tmp_path / "artifacts/alias/child")


def test_source_guard_serialization_keeps_exact_closure() -> None:
    guard = transport.SourceGuard("source", "index", (("owned.py", "digest"),))
    assert json.loads(json.dumps(asdict(guard))) == {
        "head": "source",
        "index_sha256": "index",
        "files": [["owned.py", "digest"]],
    }
    assert RESOURCE_LIMITS["integration_work_seconds"] == 160


@pytest.mark.parametrize(
    "field", ["status", "q_bound", "global_series_remainder_radius"]
)
def test_observer_binds_reported_status_and_series_witness(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    synthetic_population: MomentPopulation,
    field: str,
) -> None:
    protocol = configure(tmp_path, monkeypatch, synthetic_population)
    producer = tmp_path / "artifacts/producer"
    study.run_study(tmp_path, protocol, producer)
    path = producer / "result.json"
    result = json.loads(path.read_bytes())
    result["cases"][0][field] = "foreign"
    path.write_text(json.dumps(result))
    output = tmp_path / "artifacts/observer"
    with pytest.raises(ValueError, match="mathematical flags"):
        observe.run_observer(tmp_path, protocol, producer, output)
    failed = json.loads((output / "independent-check.json").read_bytes())
    assert failed["cases"][0]["independent_bounds"]
    assert failed["progress"]["completed_leaves"] == 5
    assert failed["cases"][1]["status"] == "not_replayed"


def test_terminal_producer_failure_keeps_closed_cases_and_certificates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    synthetic_population: MomentPopulation,
) -> None:
    protocol = configure(tmp_path, monkeypatch, synthetic_population)

    def fail(*args: object) -> None:
        raise ValueError("terminal source mismatch control")

    monkeypatch.setattr(study, "check_terminal", fail)
    output = tmp_path / "artifacts/producer"
    with pytest.raises(ValueError, match="terminal source"):
        study.run_study(tmp_path, protocol, output)
    result = json.loads((output / "result.json").read_bytes())
    assert result["status"] == "failed"
    assert result["complete_cases"] == 6
    assert all(
        row["complete"] is True and row["saved_leaves"] == 5 for row in result["cases"]
    )
    assert result["certificate_identity"] == identity(
        (output / "certificates.json").read_bytes()
    )


def test_later_observer_failure_retains_replayed_prefix_and_current_owner(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    synthetic_population: MomentPopulation,
) -> None:
    protocol = configure(tmp_path, monkeypatch, synthetic_population)
    producer = tmp_path / "artifacts/producer"
    study.run_study(tmp_path, protocol, producer)
    original = verify_angle_certificate
    calls = 0

    def stop(*args: Any) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise ValueError("later replay refusal control")
        return original(*args)

    monkeypatch.setattr(observe, "verify_angle_certificate", stop)
    output = tmp_path / "artifacts/observer"
    with pytest.raises(ValueError, match="later replay"):
        observe.run_observer(tmp_path, protocol, producer, output)
    result = json.loads((output / "independent-check.json").read_bytes())
    assert result["status"] == "failed"
    assert result["complete_cases"] == 1
    assert result["cases"][0]["status"] == "fixed_leaf_replayed"
    assert result["cases"][1]["status"] == "replay_started"
    assert result["cases"][2]["status"] == "not_replayed"
    assert result["progress"]["current_case"] == ["BOKE", "Ulmus"]
    assert result["progress"]["completed_leaves"] == 5
