"""Density membership follows native representative points, including islands."""

from __future__ import annotations

from typing import cast

import pytest

from bijux_pollenomics.collection.sources.raa.outputs import (
    build_raa_density_geojson,
    count_raa_features,
)


def _polygon(west: float, south: float, east: float, north: float) -> dict[str, object]:
    return {
        "type": "Polygon",
        "coordinates": [
            [[west, south], [east, south], [east, north], [west, north], [west, south]]
        ],
    }


def _boundary(*geometries: dict[str, object]) -> dict[str, object]:
    return {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "geometry": geometry, "properties": {}}
            for geometry in geometries
        ],
    }


def _inventory(*geometries: object) -> dict[str, object]:
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": geometry,
                "properties": {
                    "lamningsnummer": str(index),
                    "antikvariskbedomningtyp_namn": "Fornlämning",
                },
            }
            for index, geometry in enumerate(geometries)
        ],
    }


def _cells(density: dict[str, object]) -> list[dict[str, object]]:
    return cast(list[dict[str, object]], density["features"])


def test_occupied_island_cell_survives_without_country_corners_or_center() -> None:
    density = build_raa_density_geojson(
        feature_inventory=_inventory({"type": "Point", "coordinates": [18.15, 57.15]}),
        sweden_boundary=_boundary(_polygon(18.1, 57.1, 18.2, 57.2)),
    )

    assert _cells(density) == [
        {
            "type": "Feature",
            "geometry": _polygon(18.0, 57.0, 19.0, 58.0),
            "properties": {
                "layer_key": "raa-archaeology",
                "layer_label": "RAÄ archaeology density",
                "country": "Sweden",
                "count": 1,
                "count_label": "1",
            },
        }
    ]


def test_all_boundary_features_contribute_without_duplicate_membership() -> None:
    density = build_raa_density_geojson(
        feature_inventory=_inventory(
            {"type": "Point", "coordinates": [18.15, 57.15]},
            {"type": "Point", "coordinates": [20.15, 59.15]},
        ),
        sweden_boundary=_boundary(
            _polygon(18.1, 57.1, 18.2, 57.2),
            _polygon(20.1, 59.1, 20.2, 59.2),
            _polygon(18.1, 57.1, 18.2, 57.2),
        ),
    )

    assert [
        cast(dict[str, object], cell["properties"])["count"] for cell in _cells(density)
    ] == [1, 1]
    assert [cell["geometry"] for cell in _cells(density)] == [
        _polygon(18.0, 57.0, 19.0, 58.0),
        _polygon(20.0, 59.0, 21.0, 60.0),
    ]


def test_holes_and_foreign_points_do_not_enter_an_occupied_country_cell() -> None:
    geometry: dict[str, object] = {
        "type": "Polygon",
        "coordinates": [
            [[18.0, 57.0], [18.9, 57.0], [18.9, 57.9], [18.0, 57.9], [18.0, 57.0]],
            [[18.1, 57.1], [18.3, 57.1], [18.3, 57.3], [18.1, 57.3], [18.1, 57.1]],
        ],
    }
    inventory = _inventory(
        {"type": "Point", "coordinates": [18.6, 57.6]},
        {"type": "Point", "coordinates": [18.7, 57.7]},
        {"type": "Point", "coordinates": [18.2, 57.2]},
        {"type": "Point", "coordinates": [18.95, 57.2]},
        None,
        {"type": "Point", "coordinates": []},
    )
    density = build_raa_density_geojson(
        feature_inventory=inventory, sweden_boundary=_boundary(geometry)
    )

    assert count_raa_features(inventory, heritage_statuses={"Fornlämning"}) == 6
    assert len(_cells(density)) == 1
    assert cast(dict[str, object], _cells(density)[0]["properties"])["count"] == 2


@pytest.mark.parametrize(
    "geometry",
    [
        _polygon(18.12, 57.12, 18.18, 57.18),
        {"type": "LineString", "coordinates": [[18.12, 57.12], [18.18, 57.18]]},
    ],
)
def test_existing_nonpoint_representative_geometry_semantics_are_preserved(
    geometry: dict[str, object],
) -> None:
    density = build_raa_density_geojson(
        feature_inventory=_inventory(geometry),
        sweden_boundary=_boundary(_polygon(18.1, 57.1, 18.2, 57.2)),
    )

    assert len(_cells(density)) == 1
    assert cast(dict[str, object], _cells(density)[0]["properties"])["count"] == 1
