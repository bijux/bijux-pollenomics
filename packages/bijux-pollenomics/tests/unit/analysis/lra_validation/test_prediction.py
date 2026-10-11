"""Prediction orchestration isolates outcomes and delegates numerical deposition."""

from dataclasses import dataclass, replace
import json
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra_validation import (
    Fold,
    ForwardInputs,
    SiteRecord,
    ValidationRefusal,
    grouped_leave_one_out,
    predict_withheld_site,
    score_pollen,
    score_vegetation,
)


@dataclass(frozen=True)
class ReferenceOutput:
    """Hand-calculated response fixture; not an engine or empirical reference."""

    pollen_fraction: tuple[float, ...] = (0.6, 0.4)
    method_profile: str = "synthetic-forward-boundary-test"


class RecordingForward:
    """A callback spy that checks host arguments without duplicating the kernel."""

    def __init__(self, output: ReferenceOutput | None = None) -> None:
        self.output = output if output is not None else ReferenceOutput()
        self.covers: list[tuple[float, ...]] = []

    def __call__(
        self,
        local_cover: tuple[float, ...],
        regional_deposition: tuple[float, ...],
        local_k: tuple[tuple[float, ...], ...],
        terrestrial_fraction: tuple[float, ...],
        ppe: tuple[float, ...],
    ) -> ReferenceOutput:
        self.covers.append(local_cover)
        assert regional_deposition == (0.2, 0.1)
        assert local_k == ((0.3, 0.2),)
        assert terrestrial_fraction == (0.8,)
        assert ppe == (2.0, 1.0)
        return self.output


def context() -> ForwardInputs:
    return ForwardInputs(
        taxa=("tree", "grass"),
        regional_deposition=(0.2, 0.1),
        local_k=((0.3, 0.2),),
        terrestrial_fraction=(0.8,),
        ppe=(2.0, 1.0),
        regional_input_ids=("regional",),
        parameter_input_ids=("parameters",),
        geometry_input_ids=("geometry",),
        temporal_support_id="time-support",
        method_profile="synthetic-forward-boundary-test",
        engine_build_id="synthetic-test-only",
    )


def make_fold() -> Fold:
    return next(
        fold
        for fold in grouped_leave_one_out(
            [SiteRecord("train", "s1"), SiteRecord("test", "s2")]
        )
        if fold.test_record_ids == ("test",)
    )


def graph_for(fold: Fold) -> dict[str, tuple[str, ...]]:
    return {
        **dict.fromkeys(fold.train_record_ids, ()),
        "regional": fold.train_record_ids,
        "parameters": (),
        "geometry": (),
        "time-support": (),
    }


def test_forward_callback_receives_prediction_and_named_ppe_weighted_background() -> (
    None
):
    fold = make_fold()
    model = RecordingForward()
    result = predict_withheld_site(
        fold,
        fold.test_group_ids[0],
        {fold.train_group_ids[0]: {"tree": 0.75, "grass": 0.25}},
        context(),
        model,
        spatial_method="training_mean",
        training_input_ids=fold.train_record_ids,
        dependency_graph=graph_for(fold),
        admitted_external_ids=("regional", "parameters", "geometry", "time-support"),
    )
    assert model.covers == [(0.75, 0.25)]
    assert dict(result.vegetation_fraction) == {"tree": 0.75, "grass": 0.25}
    assert dict(result.pollen_fraction) == {"tree": 0.6, "grass": 0.4}
    assert (
        result.uncertainty_status
        == "deterministic_point_prediction_no_predictive_intervals"
    )
    manifest = json.loads(result.input_manifest_json)
    assert manifest["scientific_acceptance"] == "not_evaluated_by_prediction"
    assert manifest["forward_inputs"]["regional_deposition"] == [0.2, 0.1]


@pytest.mark.parametrize(
    "tainted", ["regional", "parameters", "geometry", "time-support"]
)
def test_test_ancestry_in_any_forward_input_refuses_before_numerical_call(
    tainted: str,
) -> None:
    fold = make_fold()
    graph = graph_for(fold)
    graph[tainted] = fold.test_record_ids
    model = RecordingForward()
    with pytest.raises(ValidationRefusal) as error:
        predict_withheld_site(
            fold,
            fold.test_group_ids[0],
            {fold.train_group_ids[0]: {"tree": 0.75, "grass": 0.25}},
            context(),
            model,
            spatial_method="training_mean",
            training_input_ids=fold.train_record_ids,
            dependency_graph=graph,
            admitted_external_ids=(
                "regional",
                "parameters",
                "geometry",
                "time-support",
            ),
        )
    assert error.value.reason_code == "withheld_input_leakage"
    assert not model.covers


@pytest.mark.parametrize(
    "output",
    [
        ReferenceOutput((1.0,), "synthetic-forward-boundary-test"),
        ReferenceOutput((0.6, 0.4), "wrong-method"),
        ReferenceOutput((-0.2, 1.2)),
        ReferenceOutput((float("nan"), 0.4)),
    ],
)
def test_invalid_numerical_output_or_method_cannot_be_published(
    output: ReferenceOutput,
) -> None:
    fold = make_fold()
    with pytest.raises(ValidationRefusal):
        predict_withheld_site(
            fold,
            fold.test_group_ids[0],
            {fold.train_group_ids[0]: {"tree": 0.75, "grass": 0.25}},
            context(),
            RecordingForward(output),
            spatial_method="training_mean",
            training_input_ids=fold.train_record_ids,
            dependency_graph=graph_for(fold),
            admitted_external_ids=(
                "regional",
                "parameters",
                "geometry",
                "time-support",
            ),
        )


def test_missing_forward_lineage_and_duplicate_taxa_are_not_guessed() -> None:
    with pytest.raises(ValidationRefusal, match="must identify"):
        replace(context(), geometry_input_ids=())
    with pytest.raises(ValidationRefusal, match="unique"):
        replace(context(), taxa=("tree", "tree"))


def test_ten_site_rotations_freeze_both_targets_before_observation_access() -> None:
    folds = grouped_leave_one_out(
        [SiteRecord(f"p{i}", f"site:{i}") for i in range(1, 11)]
    )
    for fold in folds:
        model = RecordingForward()
        training = dict.fromkeys(fold.train_group_ids, {"tree": 0.75, "grass": 0.25})
        prediction = predict_withheld_site(
            fold,
            fold.test_group_ids[0],
            training,
            context(),
            model,
            spatial_method="training_mean",
            training_input_ids=fold.train_record_ids,
            dependency_graph=graph_for(fold),
            admitted_external_ids=(
                "regional",
                "parameters",
                "geometry",
                "time-support",
            ),
        )
        frozen = prediction.prediction_manifest_sha256
        vegetation = score_vegetation(
            dict(prediction.vegetation_fraction), {"tree": 0.8, "grass": 0.2}
        )
        pollen = score_pollen(dict(prediction.pollen_fraction), {"tree": 4, "grass": 6})
        perturbed = score_pollen(
            dict(prediction.pollen_fraction), {"tree": 9, "grass": 1}
        )
        assert pollen != perturbed
        assert prediction.prediction_manifest_sha256 == frozen
        assert vegetation.target == "vegetation_cover"
        assert pollen.target == "pollen_composition"


def test_withheld_inverse_distance_predictions_remain_outcome_independent() -> None:
    fold = Fold("fixed", ("a", "b"), ("test",), ("A", "B"), ("T",))
    model = RecordingForward()
    kwargs: dict[str, Any] = {
        "training_input_ids": fold.train_record_ids,
        "dependency_graph": graph_for(fold),
        "admitted_external_ids": ("regional", "parameters", "geometry", "time-support"),
        "distances_km": {"A": 1.0, "B": 2.0},
    }
    training = {"A": {"tree": 1.0, "grass": 0.0}, "B": {"tree": 0.0, "grass": 1.0}}
    first = predict_withheld_site(
        fold,
        "T",
        training,
        context(),
        model,
        spatial_method="inverse_distance_squared",
        **kwargs,
    )
    assert model.covers == [(0.8, 0.2)]
    assert first.spatial_method == "inverse_distance_squared"
    assert score_vegetation(
        dict(first.vegetation_fraction), {"tree": 1.0, "grass": 0.0}
    ) != score_vegetation(dict(first.vegetation_fraction), {"tree": 0.0, "grass": 1.0})
    assert score_pollen(
        dict(first.pollen_fraction), {"tree": 9, "grass": 1}
    ) != score_pollen(dict(first.pollen_fraction), {"tree": 1, "grass": 9})
    assert (
        predict_withheld_site(
            fold,
            "T",
            training,
            context(),
            model,
            spatial_method="inverse_distance_squared",
            **kwargs,
        )
        == first
    )


def test_predictor_subset_binds_role_without_modifying_outer_fold() -> None:
    fold = Fold("outer", ("anchor", "local"), ("target",), ("ga", "gr"), ("gt",))
    model = RecordingForward()
    result = predict_withheld_site(
        fold,
        "gt",
        {"ga": {"tree": 0.7, "grass": 0.3}},
        context(),
        model,
        spatial_method="training_mean",
        training_input_ids=fold.train_record_ids,
        dependency_graph=graph_for(fold),
        admitted_external_ids=("regional", "parameters", "geometry", "time-support"),
        predictor_group_ids=("ga",),
    )
    manifest = json.loads(result.input_manifest_json)
    assert manifest["fold"]["train_group_ids"] == ["ga", "gr"]
    assert manifest["predictor_group_ids"] == ["ga"]
    assert "anchor" in manifest["allowed_input_closure"]
    assert model.covers == [(0.7, 0.3)]
