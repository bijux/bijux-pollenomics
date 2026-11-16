"""LandClim I source IDs, physical cells and uncertainty stay separately bound."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.landclim.grid import feature_key_from_geometry
from bijux_pollenomics.collection.sources.landclim.time_windows.landclim_i import (
    _merge_landclim_i_time_windows,
)
from bijux_pollenomics.reporting.context.polygons.external import (
    build_external_polygon_layer,
)
from tests.support.workbooks import write_xlsx

HEADER = ["LCGRID_", "LCGRID_ID", "Cell", "Cell label", "fixture-a", "fixture-b"]
NORTH = ["source-owner-a", "522", "6°E 53°N", "synthetic north", "0.1", "0.9"]
SOUTH = ["source-owner-b", "522", "6°E 51°N", "synthetic south", "0.7", "0.3"]
BOUNDARIES = {
    name: {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [[5, south], [8, south], [8, north], [5, north], [5, south]]
                    ],
                },
            }
        ],
    }
    for name, south, north in [("Netherlands", 52, 54), ("Germany", 49, 52)]
}


def _merge(
    path: Path,
    means: list[list[str]],
    *,
    errors: list[list[str]] | None = None,
    features: dict | None = None,
    group: str = "land_cover_types",
) -> dict:
    if errors is None:
        errors = [[*row[:4], "0.01", "0.02"] for row in means]
    write_xlsx(
        path,
        {
            "2700-3200BPmeanLC": [["Synthetic means"], HEADER, *means],
            "2700-3200BPSE": [["Synthetic errors"], HEADER, *errors],
        },
    )
    result = {} if features is None else features
    _merge_landclim_i_time_windows(
        result,
        path,
        value_group=group,
        bbox=(5, 49, 8, 55),
        country_boundaries=BOUNDARIES,
    )
    return result


def _by_geometry(features: dict) -> dict[str, dict[str, Any]]:
    return {
        feature_key_from_geometry(feature["geometry"]): feature["properties"]
        for feature in features.values()
    }


@pytest.mark.parametrize("reverse", [False, True])
def test_same_native_id_at_distinct_centers_retains_each_geometry_mean_and_error(
    tmp_path: Path, reverse: bool
) -> None:
    means = [NORTH, SOUTH]
    errors = [[*NORTH[:4], "0.03", "0.04"], [*SOUTH[:4], "0.05", "0.06"]]
    features = _merge(
        tmp_path / "cells.xlsx",
        list(reversed(means)) if reverse else means,
        errors=list(reversed(errors)),
    )
    assert len(features) == 2
    by_geometry = _by_geometry(features)
    for geometry, values, uncertainty in [
        ("6.000000,52.000000,7.000000,53.000000", [0.1, 0.9], [0.03, 0.04]),
        ("6.000000,50.000000,7.000000,51.000000", [0.7, 0.3], [0.05, 0.06]),
    ]:
        properties = by_geometry[geometry]
        assert properties["source_grid_record_id"] == "522"
        assert properties["physical_grid_record_id"] == geometry
        assert properties["reconstruction_values"]["land_cover_types"] == dict(
            zip(["fixture-a", "fixture-b"], values, strict=True)
        )
        assert properties["standard_errors"]["land_cover_types"] == dict(
            zip(["fixture-a", "fixture-b"], uncertainty, strict=True)
        )
    assert len({f["properties"]["record_id"] for f in features.values()}) == 2
    assert (
        len({f["properties"]["parent_grid_record_id"] for f in features.values()}) == 2
    )
    layer = build_external_polygon_layer(
        {"type": "FeatureCollection", "features": list(features.values())}
    )
    assert layer["count"] == 2


def test_source_order_and_subset_do_not_change_physical_identities(
    tmp_path: Path,
) -> None:
    complete = _by_geometry(_merge(tmp_path / "complete.xlsx", [NORTH, SOUTH]))
    reverse = _by_geometry(_merge(tmp_path / "reverse.xlsx", [SOUTH, NORTH]))
    subset = _by_geometry(_merge(tmp_path / "subset.xlsx", [SOUTH]))
    assert {key: value["record_id"] for key, value in complete.items()} == {
        key: value["record_id"] for key, value in reverse.items()
    }
    assert (
        next(iter(subset.values()))["record_id"]
        == complete[next(iter(subset))]["record_id"]
    )


@pytest.mark.parametrize("second_values", [["0.6", "0.4"], ["0.1", "0.9"]])
def test_repeated_same_physical_mean_is_refused_without_mutating_caller(
    tmp_path: Path, second_values: list[str]
) -> None:
    features = _merge(tmp_path / "existing.xlsx", [SOUTH])
    before = deepcopy(features)
    with pytest.raises(ValueError, match="repeat physical cell"):
        _merge(
            tmp_path / "duplicate.xlsx",
            [NORTH, [*NORTH[:4], *second_values]],
            errors=[[*NORTH[:4], "0.01", "0.02"]],
            features=features,
        )
    assert features == before


def test_matched_groups_join_only_the_same_physical_source_identity(
    tmp_path: Path,
) -> None:
    features = _merge(tmp_path / "lct.xlsx", [NORTH, SOUTH])
    _merge(
        tmp_path / "pft.xlsx",
        [SOUTH, NORTH],
        features=features,
        group="plant_functional_types",
    )
    assert len(features) == 2
    assert all(
        set(f["properties"]["reconstruction_values"])
        == {"land_cover_types", "plant_functional_types"}
        for f in features.values()
    )
    before = deepcopy(features)
    with pytest.raises(ValueError, match="source grid identity"):
        _merge(
            tmp_path / "conflicting-source.xlsx",
            [[NORTH[0], "other", *NORTH[2:]]],
            features=features,
            group="another-panel",
        )
    assert features == before


@pytest.mark.parametrize(
    "errors,reason",
    [
        ([], "standard-error"),
        (
            [[*NORTH[:4], "0.01", "0.02"], [*NORTH[:4], "0.03", "0.04"]],
            "repeat source cell",
        ),
        ([[NORTH[0], "other", *NORTH[2:4], "0.01", "0.02"]], "source grid identity"),
    ],
)
def test_missing_duplicate_or_mismatched_error_owner_is_explicit(
    tmp_path: Path, errors: list[list[str]], reason: str
) -> None:
    with pytest.raises(ValueError, match=reason):
        _merge(tmp_path / "error-owner.xlsx", [NORTH], errors=errors)


def test_geometry_aliases_cannot_hide_repeated_uncertainty(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="repeat source cell"):
        _merge(
            tmp_path / "alias-error.xlsx",
            [NORTH],
            errors=[
                [*NORTH[:4], "0.01", "0.02"],
                [NORTH[0], NORTH[1], "6.0°E 53.0°N", NORTH[3], "0.03", "0.04"],
            ],
        )


def test_distinct_close_centers_are_never_rounded_into_one_cell(tmp_path: Path) -> None:
    first = [*NORTH[:2], "6.0000001°E 53°N", *NORTH[3:]]
    second = [*NORTH[:2], "6.0000002°E 53°N", *SOUTH[3:]]
    features = _merge(tmp_path / "close-centers.xlsx", [first, second])
    assert len(features) == 2
    assert (
        len({f["properties"]["physical_grid_record_id"] for f in features.values()})
        == 2
    )


def test_mean_error_geometry_aliases_join_the_same_physical_cell(
    tmp_path: Path,
) -> None:
    errors = [[NORTH[0], NORTH[1], "6.0°E 53.0°N", NORTH[3], "0.03", "0.04"]]
    features = _merge(tmp_path / "alias-join.xlsx", [NORTH], errors=errors)
    assert next(iter(features.values()))["properties"]["standard_errors"][
        "land_cover_types"
    ] == {"fixture-a": 0.03, "fixture-b": 0.04}


@pytest.mark.parametrize(
    "reverse,rotation", [(False, 0), (True, 0), (False, 2), (True, 1)]
)
def test_closed_rectangles_have_orientation_independent_exact_identity(
    reverse: bool, rotation: int
) -> None:
    from bijux_pollenomics.collection.sources.landclim.time_windows.landclim_i_cells import (
        physical_cell_key,
    )

    vertices = [[6.0, 52.0], [7.0, 52.0], [7.0, 53.0], [6.0, 53.0]]
    if reverse:
        vertices.reverse()
    vertices = vertices[rotation:] + vertices[:rotation]
    assert (
        physical_cell_key(
            {"type": "Polygon", "coordinates": [[*vertices, vertices[0]]]}
        )
        == "6.000000,52.000000,7.000000,53.000000"
    )


@pytest.mark.parametrize(
    "geometry",
    [
        None,
        {},
        {"type": "MultiPolygon", "coordinates": []},
        {
            "type": "Polygon",
            "coordinates": [[[6, 52], [7, 53], [7, 52], [6, 53], [6, 52]]],
        },
        {
            "type": "Polygon",
            "coordinates": [[[6, 52], [8, 52], [8, 53], [6, 53], [6, 52]]],
        },
        {
            "type": "Polygon",
            "coordinates": [[[180, 52], [181, 52], [181, 53], [180, 53], [180, 52]]],
        },
        {
            "type": "Polygon",
            "coordinates": [[[6, 90], [7, 90], [7, 91], [6, 91], [6, 90]]],
        },
        {
            "type": "Polygon",
            "coordinates": [[[6, 52], [7, 52], [7, float("nan")], [6, 53], [6, 52]]],
        },
        {
            "type": "Polygon",
            "coordinates": [[[6, 52], [7, 52], [7, float("inf")], [6, 53], [6, 52]]],
        },
        {
            "type": "Polygon",
            "coordinates": [[[True, 52], [7, 52], [7, 53], [6, 53], [True, 52]]],
        },
    ],
)
def test_invalid_geometry_is_refused_before_identity_can_collapse(
    geometry: object,
) -> None:
    from bijux_pollenomics.collection.sources.landclim.time_windows.landclim_i_cells import (
        physical_cell_key,
    )

    with pytest.raises(ValueError, match="geometry is invalid"):
        physical_cell_key(geometry)


def test_source_coordinate_precision_loss_is_explicit(tmp_path: Path) -> None:
    source = [*NORTH[:2], "6.0000000000000001°E 53°N", *NORTH[3:]]
    with pytest.raises(ValueError, match="coordinate precision"):
        _merge(tmp_path / "precision.xlsx", [source])


def test_public_builder_has_order_independent_landclim_i_geometry_and_values(
    tmp_path: Path,
) -> None:
    from unittest.mock import patch

    from bijux_pollenomics.collection.sources.landclim import time_windows

    results = []
    for directory, rows in [("forward", [NORTH, SOUTH]), ("reverse", [SOUTH, NORTH])]:
        root = tmp_path / directory
        paths = {}
        for filename in [
            "landclim_i_land_cover_types.xlsx",
            "landclim_i_plant_functional_types.xlsx",
        ]:
            path = root / filename
            write_xlsx(
                path,
                {
                    "2700-3200BPmeanLC": [["Synthetic means"], HEADER, *rows],
                    "2700-3200BPSE": [
                        ["Synthetic errors"],
                        HEADER,
                        *[[*row[:4], "0.01", "0.02"] for row in rows],
                    ],
                },
            )
            paths[filename] = path
        paths["landclim_ii_reveals_results.zip"] = root / "not-opened.zip"
        paths["landclim_ii_grid_cell_quality.xlsx"] = root / "not-opened.xlsx"
        with (
            patch.object(time_windows, "_merge_landclim_ii_time_windows"),
            patch.object(time_windows, "landclim_ii_quality_lookup", return_value={}),
        ):
            results.append(
                time_windows.build_landclim_temporal_grid_geojson(
                    paths, (5, 49, 8, 55), BOUNDARIES
                )
            )
    assert results[0] == results[1]
    assert len(results[0]["features"]) == 2


def test_source_label_cannot_claim_a_different_physical_geometry() -> None:
    from bijux_pollenomics.collection.sources.landclim.time_windows.landclim_i_cells import (
        physical_cell_key,
    )

    geometry = {
        "type": "Polygon",
        "coordinates": [[[6, 52], [7, 52], [7, 53], [6, 53], [6, 52]]],
    }
    with pytest.raises(ValueError, match="source label disagrees"):
        physical_cell_key(geometry, source_label="8°E 55°N")


def test_fractional_northwest_constructor_roundtrip_has_no_inverse_roundoff_refusal() -> (
    None
):
    from bijux_pollenomics.collection.sources.landclim.grid import (
        grid_geometry_from_nw_cell_label,
    )
    from bijux_pollenomics.collection.sources.landclim.time_windows.landclim_i_cells import (
        physical_cell_key,
    )

    label = "0.1°E 0.1°N"
    assert (
        physical_cell_key(grid_geometry_from_nw_cell_label(label), source_label=label)
        == "0.100000,-0.900000,1.100000,0.100000"
    )


def test_later_group_identity_refusal_cannot_mutate_an_earlier_existing_cell(
    tmp_path: Path,
) -> None:
    features = _merge(tmp_path / "existing-panels.xlsx", [NORTH, SOUTH])
    before = deepcopy(features)
    conflicting_south = [SOUTH[0], "other-source-id", *SOUTH[2:]]
    with pytest.raises(ValueError, match="source grid identity"):
        _merge(
            tmp_path / "partial-panel.xlsx",
            [NORTH, conflicting_south],
            features=features,
            group="plant_functional_types",
        )
    assert features == before
