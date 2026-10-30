"""Exercise freeze, native outcome retention and fair paired summaries artificially."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.physical_forward import (
    prediction,
    producer,
)
from bijux_pollenomics_dev.essd_reproduction.physical_forward.inputs import (
    Core,
    normalize,
)


@pytest.fixture
def data(
    artificial_sources: tuple[dict[str, Any], dict[str, Any]], protocol: dict[str, Any]
) -> tuple[tuple[Core, ...], dict[str, Any]]:
    return normalize(*artificial_sources, protocol), protocol


def artificial_score(predicted: dict[str, float], counts: dict[str, int]) -> Any:
    return SimpleNamespace(
        status="scored",
        observed_total_count=sum(counts.values()),
        taxon_count=len(counts),
        mae_fraction=0.25,
        total_variation=0.5,
    )


def test_complete_artificial_run_freezes_before_any_score(
    tmp_path: Path,
    data: tuple[tuple[Core, ...], dict[str, Any]],
    fake_points: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cores, protocol = data
    (tmp_path / "artifacts").mkdir()
    output = tmp_path / "artifacts/result"
    monkeypatch.setattr(producer, "load", lambda repository: (cores, protocol, []))
    calls = []

    def score(predicted: dict[str, float], counts: dict[str, int]) -> Any:
        freeze = json.loads((output / "prediction-freeze.json").read_bytes())
        assert len(freeze["contexts"]) == 154
        calls.append((predicted, counts))
        return artificial_score(predicted, counts)

    monkeypatch.setattr(producer, "_score", score)
    report = producer.run(tmp_path, output, "a" * 40)
    assert report["completed"] is True
    assert report["prediction_contexts"] == 154 and report["family_outcomes"] == 308
    assert report["status_counts"] == {"prediction_refused": 108, "scored": 200}
    assert len(calls) == 200 and report["matched"]["matched_target_windows"] == 26
    assert report["uncertainty_evaluated"] is False
    assert {p.name for p in output.iterdir()} == {
        "report.json",
        "scores.json",
        "prediction-freeze.json",
    }


def test_unequal_window_counts_still_weight_physical_targets_equally(
    data: tuple[tuple[Core, ...], dict[str, Any]],
    fake_points: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cores, protocol = data
    rows, _ = prediction.predictions(cores, protocol)
    monkeypatch.setattr(producer, "_score", artificial_score)
    scores, complete = producer.score_rows(rows, cores, enabled=True)
    assert complete
    for row in scores:
        core = row["identity"]["core"]
        if core in {"BOKE", "BUS"} and row["status"] == "scored":
            row["mae_fraction"] = 0.0 if core == "BOKE" else 1.0
            if core == "BUS" and row["identity"]["window_cal_bp"] != [0.0, 100.0]:
                row["status"] = "artificial_refusal"
    summary = producer.matched_summary(scores)
    assert summary["matched_target_windows"] == 14
    assert all(
        row["mae_fraction"] == 0.5
        for row in summary["scope_family_site_macros"].values()
    )


def test_zero_target_projection_is_unavailable_not_zero_error(
    data: tuple[tuple[Core, ...], dict[str, Any]],
    fake_points: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cores, protocol = data
    changed = tuple(
        replace(core, cells=tuple(replace(c, counts=(0, 99, 0)) for c in core.cells))
        if core.id == "BOKE"
        else core
        for core in cores
    )
    rows, complete = prediction.predictions(changed, protocol)
    assert complete
    monkeypatch.setattr(producer, "_score", artificial_score)
    scores, complete = producer.score_rows(rows, changed, enabled=True)
    assert complete
    selected = [row for row in scores if row["identity"]["core"] == "BOKE"]
    assert all(
        row["status"] == "unavailable_zero_target_panel" and row["mae_fraction"] is None
        for row in selected
    )


@pytest.mark.parametrize("unknown", [False, True])
def test_known_score_refusal_and_unknown_fault_remain_distinct(
    data: tuple[tuple[Core, ...], dict[str, Any]],
    fake_points: None,
    monkeypatch: pytest.MonkeyPatch,
    unknown: bool,
) -> None:
    from bijux_pollenomics.analysis.lra_validation.contracts import ValidationRefusal

    cores, protocol = data
    rows, _ = prediction.predictions(cores, protocol)

    def score(predicted: dict[str, float], counts: dict[str, int]) -> Any:
        if unknown:
            raise RuntimeError("Artificial unknown fault")
        raise ValidationRefusal("artificial_score_refusal", "Artificial known refusal")

    monkeypatch.setattr(producer, "_score", score)
    scores, complete = producer.score_rows(rows, cores, enabled=True)
    assert len(scores) == 308 and complete is not unknown
    if unknown:
        index = next(i for i, row in enumerate(scores) if row["status"] == "fatal")
        assert all(
            row["status"] == "not_run_after_fatal" for row in scores[index + 1 :]
        )
    else:
        assert sum(row["status"] == "refused_validation" for row in scores) == 200


def test_existing_output_refuses_before_source_loading(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "artifacts/result"
    output.mkdir(parents=True)

    def forbidden(repository: Path) -> Any:
        raise AssertionError("Must refuse output before reading inputs")

    monkeypatch.setattr(producer, "load", forbidden)
    with pytest.raises(ValueError, match="Absent confined"):
        producer.run(tmp_path, output, "a" * 40)


def test_frozen_prediction_tampering_cannot_be_admitted(
    tmp_path: Path,
    data: tuple[tuple[Core, ...], dict[str, Any]],
    fake_points: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cores, protocol = data
    (tmp_path / "artifacts").mkdir()
    output = tmp_path / "artifacts/result"
    monkeypatch.setattr(producer, "load", lambda repository: (cores, protocol, []))

    def mutate(predicted: dict[str, float], counts: dict[str, int]) -> Any:
        path = output / "prediction-freeze.json"
        path.write_bytes(path.read_bytes() + b" ")
        return artificial_score(predicted, counts)

    monkeypatch.setattr(producer, "_score", mutate)
    with pytest.raises(ValueError, match="identity"):
        producer.run(tmp_path, output, "a" * 40)
