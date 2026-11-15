"""Basin alternatives retain explicit units and the existing local support."""

from copy import deepcopy
from importlib import import_module
from typing import Any

import pytest


def implementation() -> Any:
    try:
        return import_module(
            "bijux_pollenomics_dev.source_completion.pollen_reconstruction."
            "bokesjon_pilot.basin_sensitivity.protocol"
        )
    except ModuleNotFoundError:
        pytest.fail("The bounded basin geometry implementation is missing")


def test_hectares_become_radius_without_rescaling_outer_support() -> None:
    module = implementation()
    profiles = module.profiles()
    assert [row.radius_m for row in profiles] == pytest.approx(
        [69.0988298942671, 71.36496464611085, 80.0], abs=1e-12
    )
    original = {"basin": {"diameter_m": 160.0, "site_type": "lake"}, "marker": 7}
    before = deepcopy(original)
    geometry = module.static_geometry(original, profiles[0].radius_m)
    assert original == before
    assert geometry["basin"]["diameter_m"] == pytest.approx(138.1976597885342)
    assert geometry["inversion_rings"][0]["inner_m"] == pytest.approx(70.0988298942671)
    assert [row["outer_m"] for row in geometry["inversion_rings"]] == [500, 1000]
    assert [row["outer_m"] for row in geometry["forward_rings"]] == [
        500,
        1000,
        10000,
        100000,
    ]
    assert geometry["marker"] == 7


def test_baseline_geometry_preserves_original_first_ring() -> None:
    geometry = implementation().static_geometry(
        {"basin": {"diameter_m": 160.0, "site_type": "lake"}}, 80.0
    )
    assert geometry["inversion_rings"][0] == {
        "inner_m": 81.0,
        "outer_m": 500,
        "mean_m": 290.5,
        "ring_area_m2": 764786.1739972456,
        "terrestrial_area_m2": 764786.1739972456,
    }


@pytest.mark.parametrize("radius", [True, 0, -1, 499, 500, float("nan"), float("inf")])
def test_invalid_radius_cannot_make_empty_or_inverted_land_ring(radius: float) -> None:
    with pytest.raises(ValueError, match="radius"):
        implementation().static_geometry({"basin": {"site_type": "lake"}}, radius)
