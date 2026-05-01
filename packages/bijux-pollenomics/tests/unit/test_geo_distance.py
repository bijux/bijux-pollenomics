from __future__ import annotations

from bijux_pollenomics.core.geo_distance import haversine_km


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
