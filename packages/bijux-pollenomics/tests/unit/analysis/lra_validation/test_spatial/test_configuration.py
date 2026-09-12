"""Coordinate validation stays with the existing geodesic authority."""

from typing import Any

import pytest

from bijux_pollenomics.analysis.lra_validation.spatial import (
    SiteCoordinate,
    SpatialConfig,
)


@pytest.mark.parametrize(
    "latitude,longitude",
    [(91, 0), (-91, 0), (0, 181), (0, -181), (True, 0), (0, float("nan"))],
)
def test_invalid_coordinates(latitude: Any, longitude: Any) -> None:
    with pytest.raises(ValueError):
        SiteCoordinate(latitude, longitude)


def test_metadata_is_explicit_and_frozen() -> None:
    config = SpatialConfig(10, 1, "declared-support")
    assert config.as_dict()["zero_policy"] == "strictly_positive_no_replacement"
    assert config.as_dict()["parameter_selection"] == "caller_declared_not_verified"
    assert SiteCoordinate(0, 0).as_dict() == {"latitude": 0.0, "longitude": 0.0}
