"""Square-root simplex geometry, exact zeros and stable distance weighting."""

from __future__ import annotations

from math import fsum, sqrt

import pytest

from bijux_pollenomics.analysis.lra_validation.contracts import ValidationRefusal
from bijux_pollenomics.analysis.lra_validation.metrics import hellinger_distance
from bijux_pollenomics.analysis.lra_validation.spatial.hellinger import (
    gaussian_distance_weights,
    hellinger_barycentre,
)


def test_weighted_mean_matches_independent_one_dimensional_optimum() -> None:
    sources = {"left": {"a": 1.0, "b": 0.0}, "right": {"a": 0.0, "b": 1.0}}
    result = hellinger_barycentre(sources, {"left": 3.0, "right": 1.0})
    assert result == pytest.approx({"a": 0.9, "b": 0.1})
    # On the positive unit circle the first-order condition is tan(theta)=1/3.
    assert sqrt(result["b"] / result["a"]) == pytest.approx(1 / 3)

    def objective(p: dict[str, float]) -> float:
        return fsum(
            weight * hellinger_distance(p, sources[group]) ** 2
            for group, weight in {"left": 0.75, "right": 0.25}.items()
        )

    for index in range(101):
        candidate = {"a": index / 100, "b": 1 - index / 100}
        assert objective(result) <= objective(candidate) + 1e-15


def test_shared_zeros_survive_and_result_can_leave_ordinary_convex_hull() -> None:
    sources = {
        "left": {"a": 0.5, "b": 0.5, "c": 0.0, "absent": 0.0},
        "right": {"a": 0.5, "b": 0.0, "c": 0.5, "absent": 0.0},
    }
    result = hellinger_barycentre(sources, {"left": 1.0, "right": 1.0})
    assert result == pytest.approx({"a": 2 / 3, "b": 1 / 6, "c": 1 / 6, "absent": 0})
    assert result["absent"] == 0
    assert result["a"] > max(source["a"] for source in sources.values())
    reversed_sources = {
        group: dict(reversed(tuple(values.items())))
        for group, values in reversed(tuple(sources.items()))
    }
    assert hellinger_barycentre(reversed_sources, {"right": 1, "left": 1}) == result


def test_single_identical_and_zero_weight_sources() -> None:
    source = {"a": 0.25, "b": 0.75, "absent": 0.0}
    assert hellinger_barycentre({"one": source}, {"one": 1}) == pytest.approx(source)
    assert hellinger_barycentre(
        {"one": source, "two": source}, {"one": 1e308, "two": 1e308}
    ) == pytest.approx(source)
    assert hellinger_barycentre(
        {"one": source, "two": {"a": 1, "b": 0, "absent": 0}},
        {"one": 1, "two": 0},
    ) == pytest.approx(source)


@pytest.mark.parametrize("scale", [20.0, 100.0])
def test_gaussian_weights_keep_nearest_support_when_all_raw_weights_underflow(
    scale: float,
) -> None:
    weights = gaussian_distance_weights(
        {"a": 15000.0, "tie": 15000.0, "far": 15000.01}, length_scale_km=scale
    )
    assert fsum(weights.values()) == pytest.approx(1)
    assert weights["a"] == weights["tie"]
    assert 0 <= weights["far"] <= weights["a"]
    assert weights["a"] > 0


def test_gaussian_weights_match_distance_ratio_and_coincident_ties() -> None:
    weights = gaussian_distance_weights({"a": 0, "b": 2}, length_scale_km=2)
    assert weights["b"] / weights["a"] == pytest.approx(0.6065306597126334)
    assert gaussian_distance_weights({"a": 0, "b": 0}, length_scale_km=20) == {
        "a": 0.5,
        "b": 0.5,
    }


@pytest.mark.parametrize(
    ("sources", "weights"),
    [
        ({}, {}),
        ({"a": {"x": 1}}, {"b": 1}),
        ({"a": {"x": 1}}, {"a": 0}),
        ({"a": {"x": 1}}, {"a": -1}),
        ({"a": {"x": 1}}, {"a": float("nan")}),
        ({"a": {"x": 1}, "b": {"y": 1}}, {"a": 1, "b": 1}),
        ({"a": {"x": 1.1, "y": -0.1}}, {"a": 1}),
        ({"a": {"x": 0.2, "y": 0.3}}, {"a": 1}),
    ],
)
def test_invalid_compositions_or_weights_refuse(
    sources: dict[str, dict[str, float]], weights: dict[str, float]
) -> None:
    with pytest.raises(ValidationRefusal):
        hellinger_barycentre(sources, weights)


@pytest.mark.parametrize("distances,scale", [({}, 1), ({"a": -1}, 1), ({"a": 1}, 0)])
def test_invalid_distance_configuration_refuses(
    distances: dict[str, float], scale: float
) -> None:
    with pytest.raises(ValidationRefusal):
        gaussian_distance_weights(distances, length_scale_km=scale)


def test_relative_weight_and_supported_composition_underflow_refuse() -> None:
    with pytest.raises(ValidationRefusal) as refusal:
        gaussian_distance_weights({"near": 0, "far": 20000}, length_scale_km=20)
    assert refusal.value.reason_code == "hellinger_weight_underflow"
    with pytest.raises(ValidationRefusal) as refusal:
        hellinger_barycentre({"a": {"x": 1}, "b": {"x": 1}}, {"a": 1e308, "b": 1e-300})
    assert refusal.value.reason_code == "hellinger_weight_underflow"
    with pytest.raises(ValidationRefusal) as refusal:
        hellinger_barycentre(
            {"a": {"x": 1, "y": 0}, "b": {"x": 0, "y": 1}},
            {"a": 1.0, "b": 1e-200},
        )
    assert refusal.value.reason_code == "hellinger_composition_underflow"


def test_normalization_cannot_silently_remove_positive_gaussian_support() -> None:
    with pytest.raises(ValidationRefusal) as refusal:
        gaussian_distance_weights(
            {"near": 0, "tie": 0, "small": sqrt(1490)}, length_scale_km=1
        )
    assert refusal.value.reason_code == "hellinger_weight_underflow"
