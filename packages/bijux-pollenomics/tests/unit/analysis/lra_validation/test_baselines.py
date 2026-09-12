"""Synthetic ten-site checks prove isolation, not empirical LRA accuracy."""

from typing import Any

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
