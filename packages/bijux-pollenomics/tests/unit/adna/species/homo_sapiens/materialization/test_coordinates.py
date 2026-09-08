"""AADR coordinate-evidence parsing tests."""

import pytest

from bijux_pollenomics.adna.species.homo_sapiens.materialization import (
    parse_aadr_coordinates,
)


def test_zero_coordinates_remain_admitted_zero_values() -> None:
    evidence = parse_aadr_coordinates("0", " 0.0 ")

    assert evidence.status == "admitted"
    assert evidence.latitude == 0.0
    assert evidence.longitude == 0.0
    assert evidence.latitude_raw == "0"
    assert evidence.longitude_raw == " 0.0 "


@pytest.mark.parametrize(
    ("latitude_raw", "longitude_raw", "status"),
    [
        ("", "  ", "missing"),
        ("..", "..", "missing"),
        ("..", "18", "partial"),
        ("59", "", "partial"),
        ("unknown", "18", "invalid_numeric"),
        ("nan", "18", "non_finite"),
        ("91", "18", "out_of_range"),
        ("59", "181", "out_of_range"),
    ],
)
def test_unusable_coordinate_tokens_are_preserved_without_fabricated_points(
    latitude_raw: str,
    longitude_raw: str,
    status: str,
) -> None:
    evidence = parse_aadr_coordinates(latitude_raw, longitude_raw)

    assert evidence.status == status
    assert evidence.latitude is None
    assert evidence.longitude is None
    assert evidence.latitude_raw == latitude_raw
    assert evidence.longitude_raw == longitude_raw
    assert not evidence.admitted
