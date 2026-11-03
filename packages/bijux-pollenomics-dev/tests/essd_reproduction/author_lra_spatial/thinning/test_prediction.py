"""Nine-owner interpolation and unchanged native forward-equation controls."""

from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import math
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial.thinning import (
    prediction,
)


def prediction_fixture(axis: int = 30) -> tuple[dict[str, Any], list[str]]:
    """Return a small complete source closure; none of the values are source data."""
    taxa = [f"taxon-{index}" for index in range(axis)]
    locals_ = [f"owner:{index}" for index in range(8)]
    groups = [f"group:{index}" for index in range(8)]
    training = [*locals_, "anchor"]
    target = "held"
    fold = {
        "fold_id": "synthetic-nine-to-one",
        "train_record_ids": training,
        "test_record_ids": [target],
        "train_group_ids": [*groups, "anchor-group"],
        "test_group_ids": ["held-group"],
    }
    predictors = [
        {
            "record_id": owner,
            "group_id": group,
            "covers_by_ring": [
                [1.0, 0.0, *([0.0] * (axis - 2))],
                [index / 7, 1 - index / 7, *([0.0] * (axis - 2))],
            ],
            "request_sha256": f"{index + 1:064x}",
            "selected_attempt_sha256s": [f"{index + 20:064x}", f"{index + 40:064x}"],
            "fit_refs": [f"fit:{index}:0", f"fit:{index}:1"],
            "scientific_parent_ids": [owner, "anchor"],
        }
        for index, (owner, group) in enumerate(zip(locals_, groups, strict=True))
    ]
    context = {
        "context_id": "author-thinning:synthetic",
        "kind": "outer",
        "outer_target": target,
        "target": target,
        "anchor": "anchor",
        "fold": fold,
        "predictors": predictors,
        "scientific_refs": {
            "training_record_ids": list(training),
            "forbidden_record_ids": [
                target,
                *(f"excluded:{index}" for index in range(5)),
            ],
            "selected_fit_ids": [row["fit_refs"][1] for row in predictors],
            "regional_owner_id": "anchor",
            "support_id": "synthetic-source-support",
            "target_geometry_id": "experiment-geometry:" + "a" * 64,
        },
        "forward": {
            "outer_fold": deepcopy(fold),
            "regional_anchor_record_id": "anchor",
            "regional_anchor_group_id": "anchor-group",
            "regional_value_source_record_ids": ["anchor"],
            "regional_identity_source_record_ids": list(training),
            "regional_identity_policy": "conservative_all_training_fit_receipts",
            "predictor_group_ids": groups,
            "distances_km": dict(
                zip(groups, [1.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0], strict=True)
            ),
            "target_geometry_sha256": "a" * 64,
            "forward_inputs": {
                "taxa": taxa,
                "regional_deposition": [1.0, 2.0, *([0.0] * (axis - 2))],
                "local_k": [
                    [2.0, 1.0, *([1.0] * (axis - 2))],
                    [1.0, 4.0, *([1.0] * (axis - 2))],
                ],
                "terrestrial_fraction": [0.5, 0.25],
                "ppe": [2.0, 3.0, *([1.0] * (axis - 2))],
            },
        },
    }
    return context, taxa


def _predict(context: dict[str, Any], taxa: list[str]) -> list[dict[str, Any]]:
    return prediction.predict_context(context, taxa, [20.0, 100.0])


@pytest.mark.parametrize("axis", [2, 3, 30])
def test_five_complete_predictions_use_ring_one_and_native_equation(axis: int) -> None:
    context, taxa = prediction_fixture(axis)
    original = deepcopy(context)
    rows = _predict(context, taxa)
    assert [row["method_id"] for row in rows] == list(prediction.METHODS)
    assert [row["length_scale_km"] for row in rows] == [None, None, None, 20.0, 100.0]
    for row in rows:
        assert row["status"] == "predicted"
        assert row["uncertainty_status"] == "point_model_only"
        assert len(row["weights"]) == 8
        assert sum(row["weights"].values()) == pytest.approx(1.0)
        first = row["vegetation_fraction"][0]
        assert row["vegetation_fraction"] == pytest.approx(
            [first, 1 - first, *([0.0] * (axis - 2))]
        )
        local = [2.5 * first, 4.5 * (1 - first), *([0.0] * (axis - 2))]
        total = [1 + local[0], 2 + local[1], *([0.0] * (axis - 2))]
        assert row["local_deposition"] == pytest.approx(local)
        assert row["total_deposition"] == pytest.approx(total)
        assert row["pollen_fraction"] == pytest.approx(
            [value / sum(total) for value in total]
        )
        assert len(row["scientific_input_sha256"]) == 64
    assert rows[0]["vegetation_fraction"][0] == pytest.approx(0.5)
    assert rows[1]["vegetation_fraction"][0] == pytest.approx(1 / 14)
    distances = [1, 1, 2, 3, 4, 5, 6, 7]
    weights = [Fraction(1, distance**2) for distance in distances]
    expected = sum(
        Fraction(index, 7) * weight for index, weight in enumerate(weights)
    ) / sum(weights)
    assert rows[2]["vegetation_fraction"][0] == pytest.approx(float(expected))
    assert rows[3]["vegetation_fraction"] != rows[4]["vegetation_fraction"]
    assert context == original


def test_equal_distance_hellinger_has_known_nonarithmetic_mean() -> None:
    context, taxa = prediction_fixture(3)
    context["forward"]["distances_km"] = dict.fromkeys(
        context["forward"]["distances_km"], 2.0
    )
    for index, row in enumerate(context["predictors"]):
        row["covers_by_ring"][1] = [1.0, 0.0, 0.0] if index == 0 else [0.0, 1.0, 0.0]
    rows = _predict(context, taxa)
    assert rows[0]["vegetation_fraction"] == [1 / 8, 7 / 8, 0.0]
    assert rows[3]["vegetation_fraction"] == pytest.approx([1 / 50, 49 / 50, 0.0])
    assert rows[4]["vegetation_fraction"] == rows[3]["vegetation_fraction"]


def test_owner_permutation_and_metadata_labels_do_not_change_predictions_or_digest() -> (
    None
):
    context, taxa = prediction_fixture()
    expected = _predict(context, taxa)
    context["predictors"].reverse()
    for key in ("training_record_ids", "forbidden_record_ids", "selected_fit_ids"):
        context["scientific_refs"][key].reverse()
    context["retained_reference_predictions"] = {"old_full_fifteen": "changed"}
    context["held_outcome"] = [999999, 0]
    context["excluded_owner_metadata"] = {"excluded:0": "changed label"}
    context["all_source_accounting_sha256"] = "f" * 64
    assert _predict(context, taxa) == expected


def test_unselected_ring_values_are_not_new_predictor_inputs() -> None:
    context, taxa = prediction_fixture()
    expected = _predict(context, taxa)
    for row in context["predictors"]:
        row["covers_by_ring"][0] = [0.0, 1.0, *([0.0] * (len(taxa) - 2))]
    assert _predict(context, taxa) == expected


@pytest.mark.parametrize("parent", ["held", "excluded:0", "foreign"])
def test_forbidden_quantitative_parent_refuses_before_forward(
    parent: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    context, taxa = prediction_fixture()
    context["predictors"][0]["scientific_parent_ids"][1] = parent

    def forbidden_forward(*args: Any, **kwargs: Any) -> Any:
        pytest.fail("Malformed source ancestry reached native forward")

    monkeypatch.setattr(prediction, "forward_deposition", forbidden_forward)
    with pytest.raises(ValueError, match="quantitative parent"):
        _predict(context, taxa)


@pytest.mark.parametrize(
    "change",
    [
        "training",
        "anchor",
        "old_regional",
        "duplicate",
        "fit",
        "group",
        "target_geometry",
        "fold",
    ],
)
def test_changed_source_owner_or_old_full_cohort_is_not_accepted(change: str) -> None:
    context, taxa = prediction_fixture()
    if change == "training":
        context["scientific_refs"]["training_record_ids"][0] = "held"
    elif change == "anchor":
        context["scientific_refs"]["regional_owner_id"] = "excluded:0"
    elif change == "old_regional":
        context["forward"]["regional_identity_source_record_ids"] = [
            *context["scientific_refs"]["training_record_ids"],
            "excluded:0",
        ]
    elif change == "duplicate":
        context["predictors"][0] = deepcopy(context["predictors"][1])
    elif change == "fit":
        context["scientific_refs"]["selected_fit_ids"][0] = "old-full-cohort-fit"
    elif change == "group":
        context["fold"]["train_group_ids"][0] = "held-group"
    elif change == "target_geometry":
        context["scientific_refs"]["target_geometry_id"] = (
            "experiment-geometry:" + "b" * 64
        )
    else:
        context["forward"]["outer_fold"]["test_record_ids"] = ["foreign"]
    with pytest.raises(ValueError):
        _predict(context, taxa)


@pytest.mark.parametrize(
    "change",
    [
        "missing_local",
        "extra_local",
        "axis",
        "missing_ring",
        "extra_refs",
        "distance_group",
    ],
)
def test_wrong_population_and_source_axis_raise_contract_error(change: str) -> None:
    context, taxa = prediction_fixture()
    if change == "missing_local":
        context["predictors"].pop()
    elif change == "extra_local":
        context["predictors"].append(deepcopy(context["predictors"][0]))
    elif change == "axis":
        context["predictors"][0]["covers_by_ring"][1].pop()
    elif change == "missing_ring":
        context["predictors"][0]["covers_by_ring"].pop(0)
    elif change == "extra_refs":
        context["scientific_refs"]["all_bank_sha256"] = "b" * 64
    else:
        context["forward"]["distances_km"]["foreign"] = 2.0
    with pytest.raises(ValueError):
        _predict(context, taxa)


@pytest.mark.parametrize(
    "scales", [[100.0, 20.0], [20.0], [10.0, 100.0], [False, 100.0], [math.nan, 100.0]]
)
def test_prescribed_unselected_scales_only(scales: list[float]) -> None:
    context, taxa = prediction_fixture()
    with pytest.raises(ValueError, match="prescribed"):
        prediction.predict_context(context, taxa, scales)


def test_nearest_and_idw_average_only_exact_zero_or_nearest_ties() -> None:
    context, taxa = prediction_fixture()
    groups = list(context["forward"]["distances_km"])
    context["forward"]["distances_km"] = {
        group: 0.0 if index < 2 else 1.0 for index, group in enumerate(groups)
    }
    rows = _predict(context, taxa)
    for row in rows[1:3]:
        assert row["vegetation_fraction"][0] == pytest.approx(1 / 14)
        assert list(row["weights"].values()) == [0.5, 0.5, 0, 0, 0, 0, 0, 0]
    context["forward"]["distances_km"][groups[0]] = 1.0
    context["forward"]["distances_km"][groups[1]] = 1.0 + 2**-52
    for group in groups[2:]:
        context["forward"]["distances_km"][group] = 2.0
    assert _predict(context, taxa)[1]["vegetation_fraction"][0] == 0.0


@pytest.mark.parametrize(
    "field", ["ppe", "local_k", "terrestrial_fraction", "regional_deposition"]
)
def test_native_forward_domain_failure_preserves_all_five_slots(field: str) -> None:
    context, taxa = prediction_fixture()
    values = context["forward"]["forward_inputs"][field]
    if field == "local_k":
        values[0].pop()
    else:
        values[0] = -1.0
    rows = _predict(context, taxa)
    assert len(rows) == 5
    assert all(
        row["status"] == "refused"
        and row["reason"] == "forward_model_domain"
        and row["native_reason_code"]
        for row in rows
    )
    assert all("pollen_fraction" not in row for row in rows)


@pytest.mark.parametrize(
    "domain", ["negative_cover", "unclosed_cover", "negative_distance", "underflow"]
)
def test_metric_and_gaussian_refusals_are_explicit_without_fallback(
    domain: str,
) -> None:
    context, taxa = prediction_fixture()
    if domain == "negative_cover":
        context["predictors"][0]["covers_by_ring"][1][:2] = [-0.1, 1.1]
    elif domain == "unclosed_cover":
        context["predictors"][0]["covers_by_ring"][1][:2] = [0.2, 0.2]
    elif domain == "negative_distance":
        context["forward"]["distances_km"]["group:0"] = -1.0
    else:
        context["forward"]["distances_km"]["group:7"] = 1e6
    rows = _predict(context, taxa)
    refused = rows[3:] if domain == "underflow" else rows
    assert all(row["status"] == "refused" for row in refused)
    assert all("pollen_fraction" not in row for row in refused)
    if domain == "underflow":
        assert all(row["status"] == "predicted" for row in rows[:3])
        assert all(row["reason"] == "hellinger_weight_underflow" for row in refused)


def test_unexpected_program_error_is_not_a_scientific_refusal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context, taxa = prediction_fixture()

    def broken_forward(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("synthetic implementation error")

    monkeypatch.setattr(prediction, "forward_deposition", broken_forward)
    with pytest.raises(RuntimeError, match="implementation error"):
        _predict(context, taxa)
