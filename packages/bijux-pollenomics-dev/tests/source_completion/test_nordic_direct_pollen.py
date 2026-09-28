"""Tests for source-coordinate handling in the Nordic pollen study."""

import json

import pytest

from bijux_pollenomics_dev.source_completion.nordic_direct_pollen import (
    _is_direct_pollen_count,
    _select_comparable_age,
    _site_coordinate,
)


def test_point_geometry_preserves_source_coordinate() -> None:
    coordinate = _site_coordinate(
        json.dumps({"type": "Point", "coordinates": [24.5, 64.25]})
    )

    assert coordinate.longitude == pytest.approx(24.5)
    assert coordinate.latitude == pytest.approx(64.25)


def test_polygon_geometry_uses_area_centroid() -> None:
    coordinate = _site_coordinate(
        json.dumps(
            {
                "type": "Polygon",
                "coordinates": [
                    [
                        [10.0, 60.0],
                        [12.0, 60.0],
                        [12.0, 62.0],
                        [10.0, 62.0],
                        [10.0, 60.0],
                    ]
                ],
            }
        )
    )

    assert coordinate.longitude == pytest.approx(11.0)
    assert coordinate.latitude == pytest.approx(61.0)


@pytest.mark.parametrize(
    ("changes", "expected"),
    [
        ({}, True),
        ({"source_value": 1.0}, False),
        ({"source_unit": "percent"}, False),
        ({"source_element_type": "spore"}, False),
    ],
)
def test_direct_count_requires_literal_pollen_nisp_integer(
    changes: dict[str, object], expected: bool
) -> None:
    row: dict[str, object] = {
        "source_element": "pollen",
        "source_element_type": "pollen",
        "source_unit": "NISP",
        "unit_family": "count",
        "detection_status": "reported_value",
        "source_value": 1,
        "source_reported_name": "Alnus",
    }
    row.update(changes)

    assert _is_direct_pollen_count(row) is expected


def test_comparable_age_prefers_one_source_default_and_refuses_ambiguity() -> None:
    first = {"chronology_id": "source-default", "source_age_value": 200}
    second = {"chronology_id": "alternative", "source_age_value": 260}
    chronologies = {
        "source-default": {"source_is_default_assertion": True},
        "alternative": {"source_is_default_assertion": False},
    }
    assert _select_comparable_age([second, first], chronologies) == first
    assert _select_comparable_age([second], chronologies) == second
    chronologies["alternative"]["source_is_default_assertion"] = True
    assert _select_comparable_age([second, first], chronologies) is None
