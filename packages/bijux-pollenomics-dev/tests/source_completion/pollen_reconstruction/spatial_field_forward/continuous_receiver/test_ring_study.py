"""Fake-frontier execution checks closed prediction order and complete refusals."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver import (
    ring_study as study,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.quadrature import (
    WorkBudget,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.ring_bounds import (
    RingCaseResult,
    RingPopulationResult,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.ring_inputs import (
    PROTOCOL,
    RingInputs,
    select_geometry,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.study_inputs import (
    decode_json,
)

from .test_ring_inputs import ring_packets
from .test_ring_predictions import prediction_packets


def _setup(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, *, contribution: bool = False
) -> tuple[Path, Path]:
    public, original, capture, source_prediction, protocol = ring_packets()
    geometries, edges = select_geometry(
        public, original, capture, source_prediction, protocol
    )
    if contribution:
        protocol["frontier"] = {
            "priority": "coefficient_contribution",
            "q_uncertainty_full_width_exact": "1/16000000000",
        }
    prediction, scored = prediction_packets()
    scored_path = tmp_path / "old-scored.json"
    scored_path.write_text(json.dumps(scored))
    inputs = RingInputs(
        protocol, prediction, original, capture, geometries, edges, scored_path
    )
    monkeypatch.setattr(study, "read_ring_inputs", lambda *_: inputs)
    monkeypatch.setattr(study, "source_guard", lambda *_: ("f" * 40, "index", (), ()))
    monkeypatch.setattr(study, "_peak_rss", lambda: 1000)
    population = RingPopulationResult(
        tuple(
            RingCaseResult(
                (None,) * 129,
                ("not_executed",) * 129,
                None,
                "incomplete_endpoint_population:wall_seconds",
            )
            for _ in range(6)
        ),
        tuple(WorkBudget() for _ in range(6)),
        0.0,
    )

    def frontier(*_args: object, **kwargs: object) -> RingPopulationResult:
        assert kwargs["priority"] == (
            "coefficient_contribution" if contribution else "raw_width"
        )
        return population

    monkeypatch.setattr(study, "enclose_ring_population", frontier)
    destination = tmp_path / "incomplete-study"
    decode = decode_json

    def read_after_close(raw: bytes) -> dict[str, object]:
        assert (destination / "certificates.json").is_file()
        packet = json.loads((destination / "prediction-ranges.json").read_text())
        assert len(packet["contexts"]) == 18
        assert packet["source_prediction_commit"] == prediction["source_commit"]
        return decode(raw)

    monkeypatch.setattr(study, "decode_json", read_after_close)
    return destination, Path(PROTOCOL).with_name(
        "coefficient-contribution.json"
    ) if contribution else Path(PROTOCOL)


def test_incomplete_frontier_retains_774_endpoints_and_54_family_slots(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    destination, protocol = _setup(monkeypatch, tmp_path)
    result = study.run_study(Path.cwd(), protocol, destination)
    assert result["counts"] == {
        "cases": 6,
        "endpoint_slots": 774,
        "contexts": 18,
        "family_slots": 54,
    }
    assert result["status"] == "refuse_incomplete"
    assert result["all_endpoint_partitions_complete"] is False
    assert result["all_774_raw_endpoint_widths_pass"] is False
    assert result["all_18_coefficient_widths_pass"] is False
    cases = json.loads((destination / "certificates.json").read_text())["cases"]
    assert len(cases) == 6 and all(len(c["endpoints"]) == 129 for c in cases)
    assert all(
        c["coefficient_bounds"] is None and not c["positive_bounds_usable"]
        for c in cases
    )
    with pytest.raises(ReportRebuildError):
        study.run_study(Path.cwd(), protocol, destination)


def test_source_drift_refuses_result_after_closed_predictions(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    destination, protocol = _setup(monkeypatch, tmp_path)
    calls = 0

    def guard(*_args: object) -> tuple[str]:
        nonlocal calls
        calls += 1
        return ("f" * 40 if calls == 1 else "e" * 40,)

    monkeypatch.setattr(study, "source_guard", guard)
    with pytest.raises(ValueError, match="source/input/index"):
        study.run_study(Path.cwd(), protocol, destination)
    assert (destination / "prediction-ranges.json").exists()
    assert not (destination / "result.json").exists()


def test_contribution_profile_keeps_incomplete_diagnostics_explicit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    destination, protocol = _setup(monkeypatch, tmp_path, contribution=True)
    result = study.run_study(Path.cwd(), protocol, destination)
    assert result["status"] == "refuse_incomplete"
    cases = json.loads((destination / "certificates.json").read_text())["cases"]
    assert all(
        row["q_uncertainty_spreads_exact"] is None
        and row["q_uncertainty_target_pass"] is False
        for row in cases
    )
