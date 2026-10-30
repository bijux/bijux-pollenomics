"""Prove forward response calibration and exclusion on constructed data."""

from __future__ import annotations

from dataclasses import replace
import math
from types import SimpleNamespace
from typing import Any, cast

import pytest

from bijux_pollenomics_dev.source_completion.vegetation.namibia_pollen_prediction import (
    comparison as model,
)
from bijux_pollenomics_dev.source_completion.vegetation.namibia_pollen_prediction.inputs import (
    GROUPS,
    SITES,
    TAXA,
)
from bijux_pollenomics_lra.models.errors import ValidationError

from .fixtures import synthetic_source


def training() -> list[model.TrainingSite]:
    return [
        model.TrainingSite("B", (10, 20, 30, 40, 10), (1.0,) * 5, (0.0, 1.0)),
        model.TrainingSite("A", (20, 40, 60, 80, 20), (1.0,) * 5, (0.0, -1.0)),
    ]


def target() -> model.TargetSite:
    return model.TargetSite(
        "target", (2.0, 1.0, 1.0, 1.0, 2.0), ("2", "1", "1", "1", "2"), (0.0, 0.0)
    )


def test_known_response_weights_predict_forward_rather_than_inverse() -> None:
    diagnostics, weights = model.fit_training(training())
    assert diagnostics["fit_status"] == "converged"
    assert weights == pytest.approx((1, 2, 3, 4, 1), abs=1e-10)
    row = model.predict_group(training(), [target()], 100)[0]
    assert tuple(row[f"empirical_{taxon}"] for taxon in TAXA) == pytest.approx(
        tuple(x / 13 for x in (2, 2, 3, 4, 2)), abs=1e-10
    )
    assert tuple(row[f"area_only_{taxon}"] for taxon in TAXA) == pytest.approx(
        (2 / 7, 1 / 7, 1 / 7, 1 / 7, 2 / 7)
    )
    assert tuple(row[f"training_mean_{taxon}"] for taxon in TAXA) == pytest.approx(
        (1 / 11, 2 / 11, 3 / 11, 4 / 11, 1 / 11)
    )
    assert row["nearest_site"] == "A"  # Exact geographic tie uses event ID.
    assert all(row[f"observed_{taxon}"] == "" for taxon in TAXA)
    assert not hasattr(target(), "counts")


def test_site_area_unit_scalings_cancel_without_changing_response_estimand() -> None:
    original = training()
    scaled = [
        model.TrainingSite(
            site.site,
            site.counts,
            tuple(a * (17 if i else 0.125) for a in site.areas),
            site.coordinate,
        )
        for i, site in enumerate(original)
    ]
    _, first = model.fit_training(original)
    _, second = model.fit_training(scaled)
    assert second == pytest.approx(first, abs=1e-10)


def test_native_grain_effort_is_not_replaced_by_equal_site_fraction_weight() -> None:
    sites = [
        model.TrainingSite("low", (1, 1, 1, 1, 6), (1.0,) * 5, (0.0, 0.0)),
        model.TrainingSite("high", (60, 10, 10, 10, 10), (1.0,) * 5, (0.0, 1.0)),
    ]
    _, weights = model.fit_training(sites)
    assert weights is not None
    prediction = model.forward((1.0,) * 5, weights)
    assert prediction == pytest.approx(
        tuple(n / 110 for n in (61, 11, 11, 11, 16)), abs=1e-10
    )
    assert prediction[0] != pytest.approx((0.1 + 0.6) / 2)


@pytest.mark.parametrize("value", [True, 1.5, None, "10"])
def test_native_integer_input_cannot_be_coerced_before_optimizer(value: Any) -> None:
    site = model.TrainingSite("bad", (value, 2, 3, 4, 5), (1.0,) * 5, (0.0, 0.0))
    diagnostics, weights = model.fit_training([site])
    assert weights is None and diagnostics["fit_status"] == "refused"


@pytest.mark.parametrize("kind", ["nonconverged", "exception"])
def test_failed_fit_withholds_model_and_scores_but_preserves_baselines(
    monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    def fail(*_args: Any, **_kwargs: Any) -> Any:
        if kind == "exception":
            raise ValidationError("controlled numerical refusal")
        return SimpleNamespace(
            converged=False,
            stop_reason="maximum_steps",
            steps=200,
            score_residual=0.01,
            relative_count_residual=0.1,
            minimum_relative_information=1.0,
            information_resolution_floor=2e-16,
            hessian_condition_number=10.0,
        )

    monkeypatch.setattr(model, "fit_multisite_likelihood", fail)
    row = model.predict_group(training(), [target()], 100)[0]
    assert row["fit_status"] == (
        "not_converged" if kind == "nonconverged" else "refused"
    )
    assert row["empirical_Acacia"] == row["response_multiplier_Acacia"] == ""
    assert all(row[f"{method}_Acacia"] > 0 for method in model.BASELINES)
    assert all(
        row[f"empirical_minus_{baseline}_mean_nll"] == ""
        for baseline in model.BASELINES
    )


def test_whole_group_exclusion_and_prediction_freeze_need_no_target_counts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = synthetic_source()
    calls = []

    def fit(sites: Any) -> Any:
        calls.append(tuple(site.site for site in sites))
        return {"fit_status": "converged", "fit_stop_reason": "controlled"}, (1.0,) * 5

    monkeypatch.setattr(model, "fit_training", fit)
    rows = model.predict(source, radii=[100])
    assert len(rows) == 10 and len(calls) == 9
    for group, seen in zip(GROUPS, calls, strict=True):
        assert seen == tuple(site for site in SITES if site not in group)
    shared = [
        row for row in rows if row["heldout_site"] in {"Namibia_T4", "Namibia_T5"}
    ]
    assert shared[0]["fit_id"] == shared[1]["fit_id"]
    assert shared[0]["training_sites"] == shared[1]["training_sites"]
    assert all(row[f"observed_{taxon}"] == "" for row in rows for taxon in TAXA)
    with pytest.raises(TypeError):
        cast(Any, rows[0])["empirical_Acacia"] = 0


def test_holdout_counts_cannot_change_fit_or_prediction_inputs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen = []

    def fit(sites: Any) -> Any:
        seen.append(tuple((site.site, site.counts) for site in sites))
        return {"fit_status": "converged", "fit_stop_reason": "controlled"}, (1.0,) * 5

    monkeypatch.setattr(model, "fit_training", fit)
    first = model.predict_group(training(), [target()], 100)
    # TargetSite deliberately has no outcome field; changing a scorer's outcomes
    # cannot enter these immutable predictor arguments.
    second = model.predict_group(training(), [target()], 100)
    assert first == second and seen[0] == seen[1]
    source = synthetic_source()
    source = replace(source, counts={**source.counts, "target": (1, 2, 3, 4, 5)})
    scores = model.score_predictions(source, first)
    source = replace(source, counts={**source.counts, "target": (100, 2, 3, 4, 5)})
    changed = model.score_predictions(source, first)
    assert scores[0]["empirical_mean_nll"] != changed[0]["empirical_mean_nll"]
    assert scores[0]["empirical_Acacia"] == changed[0]["empirical_Acacia"]


def test_scores_use_cross_entropy_and_squared_hellinger_not_distance() -> None:
    result = model.score((4, 1, 1, 1, 1), (0.5, 0.125, 0.125, 0.125, 0.125))
    assert result["mean_nll"] == pytest.approx(math.log(4))
    assert result["mae"] == result["hellinger_squared"] == 0
    different = model.score((4, 1, 1, 1, 1), (0.2,) * 5)
    assert different["mae"] == pytest.approx(0.12)
    assert different["hellinger_squared"] == pytest.approx(
        (
            (math.sqrt(0.5) - math.sqrt(0.2)) ** 2
            + 4 * (math.sqrt(0.125) - math.sqrt(0.2)) ** 2
        )
        / 2
    )


def test_overlapping_training_target_identity_refuses() -> None:
    with pytest.raises(ValueError, match="Disjoint"):
        model.predict_group(
            training(), [model.TargetSite("A", (1.0,) * 5, ("1",) * 5, (0.0, 0.0))], 100
        )
