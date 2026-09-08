from __future__ import annotations

import pytest

from bijux_pollenomics.core.geospatial.distance import (
    InvalidCoordinateError,
    haversine_km,
    wgs84_inverse_geodesic,
)


def test_haversine_km_is_zero_for_identical_points() -> None:
    assert (
        haversine_km(
            latitude_a=59.3293,
            longitude_a=18.0686,
            latitude_b=59.3293,
            longitude_b=18.0686,
        )
        == 0.0
    )


def test_haversine_km_is_symmetric() -> None:
    stockholm_to_uppsala = haversine_km(
        latitude_a=59.3293,
        longitude_a=18.0686,
        latitude_b=59.8586,
        longitude_b=17.6389,
    )
    uppsala_to_stockholm = haversine_km(
        latitude_a=59.8586,
        longitude_a=17.6389,
        latitude_b=59.3293,
        longitude_b=18.0686,
    )

    assert round(stockholm_to_uppsala, 6) == round(uppsala_to_stockholm, 6)


def test_haversine_km_tracks_known_order_of_magnitude() -> None:
    distance = haversine_km(
        latitude_a=59.3293,
        longitude_a=18.0686,
        latitude_b=55.6761,
        longitude_b=12.5683,
    )

    assert 500.0 < distance < 550.0


@pytest.mark.parametrize("_fixture_id", [pytest.param("SPACE-001", id="SPACE-001")])
def test_malmo_to_lund_uses_wgs84_inverse_geodesic(_fixture_id: str) -> None:
    distance = wgs84_inverse_geodesic(
        latitude_a=55.6050,
        longitude_a=13.0038,
        latitude_b=55.7047,
        longitude_b=13.1910,
    )

    assert 15.0 < distance.distance_km_unrounded < 17.0
    assert distance.distance_km_display == round(distance.distance_km_unrounded, 3)
    assert distance.distance_algorithm == "WGS84 inverse geodesic"
    assert distance.distance_library == "pyproj"
    assert distance.distance_library_version


@pytest.mark.parametrize("_fixture_id", [pytest.param("SPACE-009", id="SPACE-009")])
def test_eligibility_distance_retains_library_and_full_precision(
    _fixture_id: str,
) -> None:
    distance = wgs84_inverse_geodesic(
        latitude_a=55.6050,
        longitude_a=13.0038,
        latitude_b=55.7047,
        longitude_b=13.1910,
    )

    assert distance.distance_km_unrounded != distance.distance_km_display
    assert distance.distance_library == "pyproj"
    assert distance.distance_library_version


@pytest.mark.parametrize("_fixture_id", [pytest.param("SPACE-004", id="SPACE-004")])
def test_identical_coordinates_keep_zero_distance(_fixture_id: str) -> None:
    distance = wgs84_inverse_geodesic(
        latitude_a=59.3293,
        longitude_a=18.0686,
        latitude_b=59.3293,
        longitude_b=18.0686,
    )

    assert distance.distance_km_unrounded == 0.0


@pytest.mark.parametrize(
    ("fixture_id", "latitude", "longitude"),
    (
        pytest.param("SPACE-005", 91.0, 18.0, id="SPACE-005-latitude"),
        pytest.param("SPACE-005", 59.0, 181.0, id="SPACE-005-longitude"),
        pytest.param("SPACE-005", float("nan"), 18.0, id="SPACE-005-non-finite"),
        pytest.param("SPACE-006", None, 18.0, id="SPACE-006-missing"),
    ),
)
def test_invalid_coordinates_are_refused(
    fixture_id: str,
    latitude: float | None,
    longitude: float,
) -> None:
    del fixture_id
    with pytest.raises(InvalidCoordinateError):
        wgs84_inverse_geodesic(
            latitude_a=latitude,  # type: ignore[arg-type]
            longitude_a=longitude,
            latitude_b=59.0,
            longitude_b=18.0,
        )
