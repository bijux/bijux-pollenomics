"""Geographic selection uses coordinates, exact metric order and stable IDs."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial.thinning.cohort import (
    select_cohort,
)


def test_medoid_maximin_and_exact_ties_ignore_dictionary_order() -> None:
    geometries = {
        name: {"latitude": 0.0, "longitude": float(index)}
        for index, name in enumerate("abcde")
    }
    before = deepcopy(geometries)
    result = select_cohort(geometries, 3)
    assert result["selection_order"] == ["c", "a", "e"]
    assert result == select_cohort(dict(reversed(list(geometries.items()))), 3)
    assert geometries == before
    assert result["selected"] == ["a", "c", "e"]
    assert result["excluded"] == ["b", "d"]
    matrix = result["distance_matrix_m"]
    assert matrix["a"]["a"] == 0.0
    assert matrix["a"]["e"] == matrix["e"]["a"]
    assert matrix["a"]["b"] == pytest.approx(111319.49079327357)
    assert result["coverage_m"] == matrix["a"]["b"]
    assert result["steps"][0]["criterion"] == "minimum_total_distance"
    assert (
        result["steps"][1]["candidate_values_m"]["a"]
        == result["steps"][1]["candidate_values_m"]["e"]
    )


def test_display_rounding_cannot_create_a_selection_tie() -> None:
    result = select_cohort(
        {
            "a": {"latitude": 0.0, "longitude": -0.000002},
            "middle": {"latitude": 0.0, "longitude": 0.0},
            "z": {"latitude": 0.0, "longitude": 0.0000020000001},
        },
        2,
    )
    assert result["selection_order"] == ["middle", "z"]
    candidates = result["steps"][1]["candidate_values_m"]
    assert round(candidates["a"], 3) == round(candidates["z"], 3)
    assert candidates["z"] > candidates["a"]


def test_coincident_source_centres_do_not_collapse_distinct_named_owners() -> None:
    result = select_cohort({name: {"latitude": 0, "longitude": 0} for name in "cba"}, 3)
    assert result["selection_order"] == ["a", "b", "c"]
    assert result["coverage_m"] == result["min_separation_m"] == 0.0
    single = select_cohort({"a": {"latitude": 0, "longitude": 0}}, 1)
    assert single["min_separation_m"] is None


@pytest.mark.parametrize("size", [0, -1, 3, True, 1.0])
def test_invalid_size_refuses_instead_of_changing_the_requested_population(
    size: Any,
) -> None:
    with pytest.raises(ValueError):
        select_cohort({name: {"latitude": 0, "longitude": 0} for name in "ab"}, size)


@pytest.mark.parametrize(
    "latitude,longitude", [(True, 0), (float("nan"), 0), (91, 0), (0, 181), ("50", 0)]
)
def test_invalid_source_coordinates_refuse(latitude: Any, longitude: Any) -> None:
    with pytest.raises(ValueError):
        select_cohort({"a": {"latitude": latitude, "longitude": longitude}}, 1)


def test_outcome_fields_are_not_consulted_or_projected() -> None:
    sentinel = object()
    result = select_cohort(
        {"a": {"latitude": 50, "longitude": 1, "counts": sentinel}}, 1
    )
    assert result["coordinates"] == {"a": {"latitude": 50, "longitude": 1}}
    assert "counts" not in str(result)
