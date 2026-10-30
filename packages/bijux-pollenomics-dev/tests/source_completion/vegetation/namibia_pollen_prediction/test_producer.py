"""All folds, failures, scores and summaries fit one bounded scientific table."""

from __future__ import annotations

import csv
from dataclasses import replace
import io
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.vegetation.namibia_pollen_prediction import (
    comparison as model,
)
from bijux_pollenomics_dev.source_completion.vegetation.namibia_pollen_prediction import (
    producer,
)
from bijux_pollenomics_dev.source_completion.vegetation.namibia_pollen_prediction.inputs import (
    GROUPS,
    RADII,
)

from .fixtures import synthetic_source


def mocked_rows(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    def fit(_sites: Any) -> Any:
        return {
            "fit_status": "converged",
            "fit_stop_reason": "controlled",
            "fit_steps": 0,
            "fit_score_residual": 0.0,
            "fit_relative_count_residual": 0.0,
        }, (1.0,) * 5

    monkeypatch.setattr(model, "fit_training", fit)
    source = synthetic_source()
    return model.score_predictions(source, model.predict(source))


def test_all_declared_attempts_and_predictions_remain_in_one_csv(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = mocked_rows(monkeypatch)
    payload = producer.render(rows)
    loaded = list(csv.DictReader(io.StringIO(payload.decode())))
    assert len(loaded) == 150 and len({row["fit_id"] for row in loaded}) == 135
    assert len(payload) < 1024**2
    assert loaded[0]["area_m2_Acacia"] == "1.00"
    assert tuple(loaded[0]) == model.CSV_FIELDS
    assert all(row["empirical_status"] == "computed" for row in loaded)
    assert all(row["response_multiplier_Combretaceae"] == "1.0" for row in loaded)
    shared = [row for row in loaded if row["heldout_group"] == "Namibia_T4|Namibia_T5"]
    assert len(shared) == 30 and len({row["fit_id"] for row in shared}) == 15


@pytest.mark.parametrize("kind", ["missing", "duplicate", "wrong_fit_id", "budget"])
def test_population_and_size_defects_refuse_before_publication(
    monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    rows = mocked_rows(monkeypatch)
    if kind == "missing":
        rows.pop()
    elif kind == "duplicate":
        rows[-1] = rows[0].copy()
    elif kind == "wrong_fit_id":
        rows[0]["fit_id"] = rows[1]["fit_id"]
    else:
        monkeypatch.setattr(producer, "MAX_OUTPUT_BYTES", 1)
    with pytest.raises(ValueError, match="population|MiB"):
        producer.render(rows)


def test_site_and_group_means_keep_the_t4_t5_dependency_visible(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = mocked_rows(monkeypatch)
    summary = model.summarize(rows)
    assert tuple(summary) == RADII
    selected = [row for row in rows if row["radius_label_m"] == 100]
    first = summary[100]
    for method in model.METHODS:
        assert first["methods"][method]["scored_sites"] == 10
        expected = sum(row[f"{method}_mean_nll"] for row in selected) / 10
        assert first["methods"][method]["site_mean_mean_nll"] == pytest.approx(expected)
        grouped = (
            sum(
                sum(
                    row[f"{method}_mean_nll"]
                    for row in selected
                    if row["heldout_site"] in group
                )
                / len(group)
                for group in GROUPS
            )
            / 9
        )
        assert first["methods"][method]["group_mean_mean_nll"] == pytest.approx(grouped)
    for baseline in model.BASELINES:
        for metric in model.METRICS:
            values = first["contrasts"][baseline][metric]
            assert values["paired_sites"] == 10
            assert values["better"] + values["tie"] + values["poorer"] == 10
    # Mathematical equality does not force binary64 equality after distinct
    # log-space/direct arithmetic; even tiny nonzero contrasts stay nonzero.
    differences = [row["empirical_minus_area_only_mean_nll"] for row in selected]
    assert first["contrasts"]["area_only"]["mean_nll"]["tie"] == sum(
        value == 0 for value in differences
    )
    assert first["contrasts"]["area_only"]["mean_nll"]["poorer"] == sum(
        value > 0 for value in differences
    )


def test_failed_predictions_do_not_create_a_better_partial_support_mean(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = mocked_rows(monkeypatch)
    row = rows[0]
    for metric in model.METRICS:
        row[f"empirical_{metric}"] = ""
        for baseline in model.BASELINES:
            row[f"empirical_minus_{baseline}_{metric}"] = ""
    summary = model.summarize(rows)[100]
    assert summary["methods"]["empirical"]["scored_sites"] == 9
    assert summary["methods"]["empirical"]["site_mean_mean_nll"] is None
    assert summary["methods"]["empirical"]["group_mean_mean_nll"] is None
    assert summary["methods"]["training_mean"]["scored_sites"] == 10
    assert summary["contrasts"]["training_mean"]["mean_nll"]["paired_sites"] == 9


def test_source_change_refuses_before_any_csv_is_written(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    artifact = tmp_path / "artifacts"
    artifact.mkdir()
    output = artifact / "predictions.csv"
    source = synthetic_source()
    second = synthetic_source()
    second = replace(
        second,
        area_tokens={**second.area_tokens, ("Namibia_T1", 100): ("changed",) * 5},
    )
    (tmp_path / "source-store").mkdir()
    calls = iter([source, second])
    monkeypatch.setattr(producer, "revision", lambda _: "controlled-source")
    monkeypatch.setattr(producer, "load", lambda *_: next(calls))
    rows = mocked_rows(monkeypatch)
    monkeypatch.setattr(producer, "predict", lambda _: rows)
    monkeypatch.setattr(producer, "score_predictions", lambda *_: rows)
    with pytest.raises(ValueError, match="changed during"):
        producer.run(tmp_path, tmp_path / "source-store", output)
    assert not output.exists()
