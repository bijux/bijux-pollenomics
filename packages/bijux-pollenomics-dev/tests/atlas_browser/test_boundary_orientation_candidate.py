"""Controlled geometry must remain schematic and source-free."""

from __future__ import annotations

from bijux_pollenomics_dev.ci.atlas_browser.boundary_orientation_candidate import (
    COUNTRIES,
    RECTANGLES,
    boundary_layers,
)


def test_controlled_boundaries_are_closed_and_country_specific() -> None:
    layers = boundary_layers()
    assert len(layers) == 1
    layer = layers[0]
    assert layer["key"] == layer["kind"] == "country-boundaries"
    assert layer["group"] == "orientation"
    assert "Schematic rectangles only" in layer["coverage_label"]

    features = layer["geojson"]["features"]
    assert len(features) == len(COUNTRIES) == 4
    assert [row["properties"]["country"] for row in features] == list(COUNTRIES)
    for row in features:
        assert row["properties"]["controlled_geometry"] is True
        country = row["properties"]["country"]
        west, south, east, north = RECTANGLES[country]
        ring = row["geometry"]["coordinates"][0]
        assert ring == [
            [west, south],
            [east, south],
            [east, north],
            [west, north],
            [west, south],
        ]
