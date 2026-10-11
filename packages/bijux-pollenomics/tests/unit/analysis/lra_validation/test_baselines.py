"""Synthetic ten-site checks prove isolation, not empirical LRA accuracy."""

from typing import Any, Literal

import pytest

from bijux_pollenomics.analysis.lra_validation import (
    Fold,
    SiteRecord,
    ValidationRefusal,
    grouped_leave_one_out,
    predict_spatial_baseline,
    score_pollen,
    score_vegetation,
)


def ten_sites() -> tuple[list[SiteRecord], tuple[Fold, ...]]:
    records = [SiteRecord(f"p{i}", f"site:{i}") for i in range(1, 11)]
    return records, grouped_leave_one_out(records)


def inputs_for(fold: Fold, folds: tuple[Fold, ...]) -> dict[str, dict[str, float]]:
    group_by_record = {
        other.test_record_ids[0]: other.test_group_ids[0] for other in folds
    }
    return {
        group_by_record[record]: {
            "tree": int(record[1:]) / 11,
            "grass": 1 - int(record[1:]) / 11,
        }
        for record in fold.train_record_ids
    }


def test_ten_site_outer_folds_exclude_target_from_fit_and_score_targets_separately() -> (
    None
):
    records, folds = ten_sites()
    graph = {record.record_id: () for record in records}
    assert len(folds) == 10
    assert {fold.test_record_ids[0] for fold in folds} == set(graph)
    for fold in folds:
        assert len(fold.train_record_ids) == 9
        training = inputs_for(fold, folds)
        first = predict_spatial_baseline(
            fold,
            training,
            method="training_mean",
            input_ids=fold.train_record_ids,
            dependency_graph=graph,
        )
        first_cover = dict(first.fractions)
        first_scores = (
            score_vegetation(first_cover, {"tree": 0.1, "grass": 0.9}),
            score_pollen(first_cover, {"tree": 1, "grass": 9}),
        )
        # Withheld outcomes are only supplied after the immutable prediction exists.
        perturbed_scores = (
            score_vegetation(first_cover, {"tree": 0.9, "grass": 0.1}),
            score_pollen(first_cover, {"tree": 9, "grass": 1}),
        )
        second = predict_spatial_baseline(
            fold,
            training,
            method="training_mean",
            input_ids=fold.train_record_ids,
            dependency_graph=graph,
        )
        assert first == second
        assert first_scores != perturbed_scores
        assert first_scores[0].target == "vegetation_cover"
        assert first_scores[1].target == "pollen_composition"


def test_nearest_baseline_ties_are_deterministic_and_missing_geometry_refuses() -> None:
    _, folds = ten_sites()
    fold = folds[0]
    training = inputs_for(fold, folds)
    kwargs: dict[str, Any] = {
        "input_ids": fold.train_record_ids,
        "dependency_graph": dict.fromkeys(fold.train_record_ids, ()),
    }
    with pytest.raises(ValidationRefusal, match="requires admitted site distances"):
        predict_spatial_baseline(fold, training, method="nearest_site", **kwargs)
    result = predict_spatial_baseline(
        fold,
        training,
        method="nearest_site",
        distances_km=dict.fromkeys(training, 1.0),
        **kwargs,
    )
    assert result.selected_group_ids == tuple(sorted(training))
    assert result.nearest_training_distance_km == 1
    assert dict(result.fractions) == pytest.approx(
        dict(
            predict_spatial_baseline(
                fold, training, method="training_mean", **kwargs
            ).fractions
        )
    )


def test_baseline_rejects_target_compositions_and_hidden_target_lineage() -> None:
    _, folds = ten_sites()
    fold = folds[0]
    training = inputs_for(fold, folds)
    graph: dict[str, tuple[str, ...]] = dict.fromkeys(fold.train_record_ids, ())
    with pytest.raises(ValidationRefusal, match="one composition per training"):
        predict_spatial_baseline(
            fold,
            {**training, fold.test_group_ids[0]: {"tree": 1}},
            method="training_mean",
            input_ids=fold.train_record_ids,
            dependency_graph=graph,
        )
    graph[fold.train_record_ids[0]] = (fold.test_record_ids[0],)
    with pytest.raises(ValidationRefusal) as error:
        predict_spatial_baseline(
            fold,
            training,
            method="training_mean",
            input_ids=fold.train_record_ids,
            dependency_graph=graph,
        )
    assert error.value.reason_code == "withheld_input_leakage"


def test_fit_identity_captures_dependency_edges_not_only_closure_nodes() -> None:
    _, folds = ten_sites()
    fold = folds[0]
    training = inputs_for(fold, folds)
    graph: dict[str, tuple[str, ...]] = dict.fromkeys(fold.train_record_ids, ())
    graph["external"] = ()
    graph[fold.train_record_ids[0]] = ("external",)
    first = predict_spatial_baseline(
        fold,
        training,
        method="training_mean",
        input_ids=fold.train_record_ids,
        dependency_graph=graph,
        admitted_external_ids=["external"],
    )
    graph[fold.train_record_ids[1]] = ("external",)
    second = predict_spatial_baseline(
        fold,
        training,
        method="training_mean",
        input_ids=fold.train_record_ids,
        dependency_graph=graph,
        admitted_external_ids=["external"],
    )
    assert first.fractions == second.fractions
    assert first.training_manifest_sha256 != second.training_manifest_sha256


def test_inverse_distance_squared_has_hand_calculated_weights_and_bound_identity() -> (
    None
):
    fold = Fold("fixed", ("a", "b"), ("c",), ("A", "B"), ("C",))
    training = {"A": {"tree": 1.0, "grass": 0.0}, "B": {"tree": 0.0, "grass": 1.0}}
    kwargs: dict[str, Any] = {
        "method": "inverse_distance_squared",
        "input_ids": fold.train_record_ids,
        "dependency_graph": {"a": (), "b": ()},
    }
    first = predict_spatial_baseline(
        fold, training, distances_km={"A": 1.0, "B": 2.0}, **kwargs
    )
    assert dict(first.fractions) == pytest.approx({"tree": 0.8, "grass": 0.2})
    assert first.selected_group_ids == ("A", "B")
    for scale in (1e-300, 1e300):
        scaled = predict_spatial_baseline(
            fold, training, distances_km={"A": scale, "B": 2 * scale}, **kwargs
        )
        assert scaled.fractions == first.fractions
        assert scaled.training_manifest_sha256 != first.training_manifest_sha256
    changed = predict_spatial_baseline(
        fold, training, distances_km={"A": 1.0, "B": 3.0}, **kwargs
    )
    assert dict(changed.fractions) == pytest.approx({"tree": 0.9, "grass": 0.1})
    assert changed.training_manifest_sha256 != first.training_manifest_sha256
    with pytest.raises(ValidationRefusal, match="requires admitted site distances"):
        predict_spatial_baseline(fold, training, **kwargs)


def test_inverse_distance_squared_averages_only_exact_colocated_ties() -> None:
    fold = Fold("fixed", ("a", "b", "c"), ("d",), ("A", "B", "C"), ("D",))
    training = {
        "A": {"tree": 1.0, "grass": 0.0},
        "B": {"tree": 0.0, "grass": 1.0},
        "C": {"tree": 0.9, "grass": 0.1},
    }
    kwargs: dict[str, Any] = {
        "method": "inverse_distance_squared",
        "input_ids": fold.train_record_ids,
        "dependency_graph": dict.fromkeys(fold.train_record_ids, ()),
        "distances_km": {"A": 0.0, "B": 0.0, "C": 1e-300},
    }
    first = predict_spatial_baseline(fold, training, **kwargs)
    assert dict(first.fractions) == {"tree": 0.5, "grass": 0.5}
    assert first.selected_group_ids == ("A", "B")
    assert first.nearest_training_distance_km == 0
    assert (
        predict_spatial_baseline(
            fold, dict(reversed(tuple(training.items()))), **kwargs
        )
        == first
    )
    kwargs["dependency_graph"]["a"] = ("d",)
    with pytest.raises(ValidationRefusal) as error:
        predict_spatial_baseline(fold, training, **kwargs)
    assert error.value.reason_code == "withheld_input_leakage"


@pytest.mark.parametrize("distance", [-1.0, float("inf"), float("nan"), True])
def test_inverse_distance_squared_refuses_invalid_distance(distance: float) -> None:
    fold = Fold("fixed", ("a",), ("b",), ("A",), ("B",))
    with pytest.raises(ValidationRefusal):
        predict_spatial_baseline(
            fold,
            {"A": {"tree": 1.0}},
            method="inverse_distance_squared",
            input_ids=("a",),
            dependency_graph={"a": ()},
            distances_km={"A": distance},
        )


@pytest.mark.parametrize(
    "method", ["training_mean", "nearest_site", "inverse_distance_squared"]
)
def test_explicit_local_predictors_keep_regional_anchor_in_training_lineage(
    method: Literal["training_mean", "nearest_site", "inverse_distance_squared"],
) -> None:
    fold = Fold(
        "outer",
        ("anchor", "local-a", "local-b"),
        ("target",),
        ("ga", "gb", "gr"),
        ("gt",),
    )
    graph = dict.fromkeys(fold.train_record_ids, ())
    result = predict_spatial_baseline(
        fold,
        {"ga": {"tree": 0.2, "grass": 0.8}, "gb": {"tree": 0.8, "grass": 0.2}},
        method=method,
        input_ids=fold.train_record_ids,
        dependency_graph=graph,
        distances_km={"ga": 1.0, "gb": 2.0},
        predictor_group_ids=("ga", "gb"),
    )
    assert "gr" not in result.selected_group_ids
    with pytest.raises(ValidationRefusal) as raised:
        predict_spatial_baseline(
            fold,
            {"ga": {"tree": 0.2, "grass": 0.8}, "gb": {"tree": 0.8, "grass": 0.2}},
            method=method,
            input_ids=("local-a", "local-b"),
            dependency_graph=graph,
            distances_km={"ga": 1.0, "gb": 2.0},
            predictor_group_ids=("ga", "gb"),
        )
    assert raised.value.reason_code == "incomplete_training_lineage"


@pytest.mark.parametrize("subset", [(), ("ga", "ga"), ("gt",), ("unknown",)])
def test_invalid_predictor_subset_does_not_relax_outer_split(
    subset: tuple[str, ...],
) -> None:
    fold = Fold("outer", ("anchor", "local"), ("target",), ("ga", "gr"), ("gt",))
    with pytest.raises(ValidationRefusal) as raised:
        predict_spatial_baseline(
            fold,
            {"ga": {"tree": 0.2, "grass": 0.8}},
            method="training_mean",
            input_ids=fold.train_record_ids,
            dependency_graph=dict.fromkeys(fold.train_record_ids, ()),
            predictor_group_ids=subset,
        )
    assert raised.value.reason_code == "invalid_predictor_groups"
