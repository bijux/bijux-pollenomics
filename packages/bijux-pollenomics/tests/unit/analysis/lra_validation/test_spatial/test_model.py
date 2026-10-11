"""Fitted model mathematics, split isolation and observable refusals."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import json
from math import exp, isclose, log, sqrt
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra_validation.contracts import (
    Fold,
    ValidationRefusal,
    site_group_id,
)
from bijux_pollenomics.analysis.lra_validation.spatial import (
    FittedSpatialModel,
    SiteCoordinate,
    SpatialConfig,
    fit_spatial_model,
)
from bijux_pollenomics.core.geospatial.distance import wgs84_inverse_geodesic


def fit(
    *,
    values: dict[str, dict[str, float]] | None = None,
    coordinates: dict[str, SiteCoordinate] | None = None,
    penalty: float = 0.1,
    scale: float = 100.0,
    **overrides: Any,
) -> FittedSpatialModel:
    fold = Fold("outer", ("r1", "r2"), ("r3",), ("g1", "g2"), ("g3",))
    kwargs: dict[str, Any] = {
        "config": SpatialConfig(scale, penalty, "support:1000m:5500bp"),
        "input_ids": fold.train_record_ids,
        "dependency_graph": {"r1": (), "r2": ()},
    }
    kwargs.update(overrides)
    return fit_spatial_model(
        fold,
        values or {"g1": {"a": 0.75, "b": 0.25}, "g2": {"a": 0.25, "b": 0.75}},
        coordinates or {"g1": SiteCoordinate(0, 0), "g2": SiteCoordinate(0, 1)},
        **kwargs,
    )


def prediction(model: FittedSpatialModel, longitude: float = 0) -> Any:
    return model.predict(
        target_group_id="g3",
        coordinate=SiteCoordinate(0, longitude),
        support_id="support:1000m:5500bp",
    )


def test_two_site_closed_form_ridge_solution() -> None:
    model = fit()
    distance = wgs84_inverse_geodesic(
        latitude_a=0, longitude_a=0, latitude_b=0, longitude_b=1
    ).distance_km_unrounded
    correlation = exp(-0.5 * (distance / 100) ** 2)
    shrinkage = (1 - correlation) ** 2 / ((1 - correlation) ** 2 + 0.1)
    expected = 1 / (1 + exp(-log(3) * shrinkage))
    assert dict(prediction(model).fractions)["a"] == pytest.approx(expected, abs=1e-13)
    assert 0.5 < expected < 0.75
    assert dict(prediction(model, 0.5).fractions) == pytest.approx({"a": 0.5, "b": 0.5})
    manifest = json.loads(model.fit_manifest_json)
    assert manifest["solver"]["rank"] == 2
    assert manifest["solver"]["scaled_stationarity_residual"] < 1e-12


def test_identical_coordinates_give_geometric_composition_centre() -> None:
    model = fit(
        values={"g1": {"a": 0.8, "b": 0.2}, "g2": {"a": 0.4, "b": 0.6}},
        coordinates={"g1": SiteCoordinate(0, 0), "g2": SiteCoordinate(0, 0)},
    )
    expected = sqrt(0.8 * 0.4) / (sqrt(0.8 * 0.4) + sqrt(0.2 * 0.6))
    assert dict(prediction(model).fractions)["a"] == pytest.approx(expected)
    assert not isclose(expected, 0.6)


def test_input_order_and_target_location_do_not_change_fit() -> None:
    original = fit()
    reordered = fit(
        values={"g2": {"b": 0.75, "a": 0.25}, "g1": {"b": 0.25, "a": 0.75}},
        coordinates={"g2": SiteCoordinate(0, 1), "g1": SiteCoordinate(0, 0)},
    )
    assert original == reordered
    before = original.model_sha256
    near, far = prediction(original), prediction(original, 175)
    assert near.model_sha256 == far.model_sha256 == before
    assert near.prediction_sha256 != far.prediction_sha256
    assert sum(dict(far.fractions).values()) == pytest.approx(1)
    attribute = "model_sha256"
    with pytest.raises(FrozenInstanceError):
        setattr(original, attribute, "changed")


def test_no_test_identity_in_training_closure() -> None:
    with pytest.raises(ValidationRefusal):
        fit(
            input_ids=("r1", "r2", "derived"),
            dependency_graph={"r1": (), "r2": (), "derived": ("r3",), "r3": ()},
            admitted_external_ids=("derived",),
        )
    with pytest.raises(ValidationRefusal, match="Full outer training"):
        fit(input_ids=("r1",))


def test_target_group_and_support_must_match() -> None:
    model = fit()
    with pytest.raises(ValidationRefusal, match="g1"):
        model.predict(
            target_group_id="g1",
            coordinate=SiteCoordinate(0, 0),
            support_id=model.config.support_id,
        )
    with pytest.raises(ValidationRefusal, match="different"):
        model.predict(
            target_group_id="g3",
            coordinate=SiteCoordinate(0, 0),
            support_id="different",
        )


@pytest.mark.parametrize(
    "values",
    [
        {"g1": {"a": 0.0, "b": 1.0}, "g2": {"a": 0.5, "b": 0.5}},
        {"g1": {"a": -0.1, "b": 1.1}, "g2": {"a": 0.5, "b": 0.5}},
        {"g1": {"a": 0.4, "b": 0.4}, "g2": {"a": 0.5, "b": 0.5}},
        {"g1": {"a": 0.5, "c": 0.5}, "g2": {"a": 0.5, "b": 0.5}},
        {"g1": {"a": True, "b": 0.0}, "g2": {"a": 0.5, "b": 0.5}},
        {"g1": {"a": float("nan"), "b": 0.5}, "g2": {"a": 0.5, "b": 0.5}},
    ],
)
def test_invalid_compositions_refuse_without_replacement(
    values: dict[str, dict[str, float]],
) -> None:
    with pytest.raises(ValidationRefusal):
        fit(values=values)


@pytest.mark.parametrize(
    "field,value",
    [
        ("penalty", 0),
        ("penalty", -1),
        ("penalty", True),
        ("scale", 0),
        ("scale", float("inf")),
    ],
)
def test_invalid_model_declarations(field: str, value: Any) -> None:
    with pytest.raises(ValidationRefusal):
        fit(**{field: value})


def test_explicit_predictor_subset_preserves_regional_ancestry() -> None:
    fold = Fold(
        "outer", ("r1", "r2", "anchor"), ("r3",), ("g1", "g2", "anchor-group"), ("g3",)
    )
    kwargs: dict[str, Any] = {
        "config": SpatialConfig(100, 0.1, "support"),
        "input_ids": fold.train_record_ids,
        "dependency_graph": dict.fromkeys(fold.train_record_ids, ()),
    }
    compositions = {"g1": {"a": 0.7, "b": 0.3}, "g2": {"a": 0.3, "b": 0.7}}
    coordinates = {"g1": SiteCoordinate(0, 0), "g2": SiteCoordinate(0, 1)}
    with pytest.raises(ValidationRefusal):
        fit_spatial_model(fold, compositions, coordinates, **kwargs)
    model = fit_spatial_model(
        fold, compositions, coordinates, predictor_group_ids=("g2", "g1"), **kwargs
    )
    assert model.groups == ("g1", "g2")
    assert "anchor" in json.loads(model.fit_manifest_json)["allowed_input_closure"]
    assert "anchor-group" in model.fold.train_group_ids


def test_extreme_scale_and_small_ridge_are_accounted_for() -> None:
    tiny_scale = fit(scale=5e-324)
    assert dict(prediction(tiny_scale).fractions)["a"] > 0.5
    with pytest.raises(ValidationRefusal, match="rank deficient"):
        fit(penalty=5e-324)


def test_antimeridian_distances_use_host_wgs84() -> None:
    model = fit(
        coordinates={"g1": SiteCoordinate(0, 179), "g2": SiteCoordinate(0, -179)}
    )
    result = prediction(model, 180)
    assert dict(result.fractions) == pytest.approx({"a": 0.5, "b": 0.5})
    assert 111 < result.nearest_training_distance_km < 112


@pytest.mark.parametrize(
    "change",
    [
        {"coefficients": ((0.0, 0.0), (0.0, 0.0))},
        {"config": SpatialConfig(200, 0.1, "support:1000m:5500bp")},
        {"centres": (SiteCoordinate(1, 1), SiteCoordinate(2, 2))},
        {"model_sha256": "0" * 64},
        {"feature_mean": (0.0, 0.0)},
        {"clr_mean": (1.0, -1.0)},
        {"taxa": ("b", "a")},
        {"groups": ("g2", "g1")},
    ],
)
def test_replaced_fitted_state_cannot_retain_original_identity(
    change: dict[str, Any],
) -> None:
    with pytest.raises(ValidationRefusal, match="Fitted state differs"):
        replace(fit(), **change)


def test_predict_rechecks_identity_even_after_frozen_state_bypass() -> None:
    model = fit()
    object.__setattr__(model, "model_sha256", "0" * 64)
    with pytest.raises(ValidationRefusal):
        prediction(model)


def test_default_model_manifest_and_explicit_none_remain_exact_v1() -> None:
    model = fit()
    explicit = fit(training_admission=None)
    assert model.fit_manifest_json == explicit.fit_manifest_json
    assert model.model_sha256 == explicit.model_sha256
    payload = json.loads(model.fit_manifest_json)
    assert payload["schema_version"] == "lra-fitted-spatial-model.v1"
    assert (
        "training_admission" not in payload and "admitted_external_ids" not in payload
    )


def admitted_model(*, leak: str | None = None) -> FittedSpatialModel:
    from bijux_pollenomics.analysis.lra_validation.contracts import (
        TrainingAdmission,
        canonical_json,
        site_group_id,
    )

    fold = Fold(
        "block",
        ("r1", "r2", "anchor", "excluded"),
        ("t1", "t2"),
        (
            site_group_id(("r1",)),
            site_group_id(("r2",)),
            site_group_id(("anchor",)),
            site_group_id(("excluded",)),
        ),
        (site_group_id(("t1",)), site_group_id(("t2",))),
    )
    admission = TrainingAdmission(
        fold,
        (
            ("r1", site_group_id(("r1",))),
            ("r2", site_group_id(("r2",))),
            ("anchor", site_group_id(("anchor",))),
            ("excluded", site_group_id(("excluded",))),
            ("t1", site_group_id(("t1",))),
            ("t2", site_group_id(("t2",))),
        ),
        (site_group_id(("r1",)), site_group_id(("r2",)), site_group_id(("anchor",))),
        canonical_json({"profile": "synthetic-buffer", "minimum_buffer_m": 1000}),
    )
    graph: dict[str, tuple[str, ...]] = dict.fromkeys(
        (*fold.train_record_ids, *fold.test_record_ids), ()
    )
    graph["fit:r1"] = ("r1", "anchor") if leak is None else ("r1", leak)
    inputs = ("r1", "r2", "anchor", "fit:r1") if leak != "omit_anchor" else ("r1", "r2")
    if leak == "omit_anchor":
        graph["fit:r1"] = ("r1",)
    return fit_spatial_model(
        fold,
        {
            site_group_id(("r1",)): {"a": 0.75, "b": 0.25},
            site_group_id(("r2",)): {"a": 0.25, "b": 0.75},
        },
        {
            site_group_id(("r1",)): SiteCoordinate(0, 0),
            site_group_id(("r2",)): SiteCoordinate(0, 1),
        },
        config=SpatialConfig(100, 0.1, "support"),
        input_ids=inputs,
        dependency_graph=graph,
        admitted_external_ids=("fit:r1", "excluded", "t1", "t2"),
        predictor_group_ids=(site_group_id(("r1",)), site_group_id(("r2",))),
        training_admission=admission,
    )


def test_admitted_model_keeps_multi_target_block_and_regional_ancestry() -> None:
    model = admitted_model()
    payload = json.loads(model.fit_manifest_json)
    assert payload["schema_version"] == "lra-fitted-spatial-model.v2"
    assert payload["fold"]["test_record_ids"] == ["t1", "t2"]
    assert payload["training_admission"]["excluded_training_record_ids"] == ["excluded"]
    assert (
        "anchor" in payload["allowed_input_closure"]
        and "excluded" not in payload["allowed_input_closure"]
    )
    assert site_group_id(("anchor",)) not in model.groups
    left = model.predict(
        target_group_id=site_group_id(("t1",)),
        coordinate=SiteCoordinate(0, 0.2),
        support_id="support",
    )
    right = model.predict(
        target_group_id=site_group_id(("t2",)),
        coordinate=SiteCoordinate(0, 0.8),
        support_id="support",
    )
    assert left.model_sha256 == right.model_sha256 == model.model_sha256
    assert left.fractions != right.fractions


@pytest.mark.parametrize("leak", ["excluded", "t1", "t2", "omit_anchor"])
def test_admitted_model_refuses_excluded_or_missing_regional_ancestry(
    leak: str,
) -> None:
    with pytest.raises(ValidationRefusal):
        admitted_model(leak=leak)


def test_changed_training_admission_cannot_retain_fitted_identity() -> None:
    model = admitted_model()
    assert model.training_admission is not None
    changed = replace(
        model.training_admission,
        admitted_group_ids=(site_group_id(("r1",)), site_group_id(("r2",))),
    )
    with pytest.raises(ValidationRefusal):
        replace(model, training_admission=changed)
    with pytest.raises(ValidationRefusal):
        replace(model, training_admission=None)
