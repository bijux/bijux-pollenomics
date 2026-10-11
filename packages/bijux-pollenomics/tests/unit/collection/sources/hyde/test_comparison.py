from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.hyde import (
    Bounds,
    aggregate_layer,
    compare_layers,
)
from bijux_pollenomics.collection.sources.quarantine import IntakeRefusal

from .fixtures import write_layer


def test_fraction_weights_use_land_area_and_keep_missing_denominator(
    tmp_path: Path, declared_payload: dict[str, Any]
) -> None:
    layer = write_layer(tmp_path, declared_payload)
    result = aggregate_layer(layer, layer.grid.bounds)
    north_area = layer.grid.cell_bounds(0, 0).area_km2
    south_area = layer.grid.cell_bounds(1, 0).area_km2
    assert result.observed_cell_count == 3
    assert result.full_land_area_km2 == pytest.approx(1.5 * north_area + 2 * south_area)
    assert result.missing_land_area_km2 == pytest.approx(south_area)
    assert result.observed_land_area_km2 == pytest.approx(1.5 * north_area + south_area)
    assert result.total == pytest.approx(0.25 * north_area + south_area)
    assert result.value == pytest.approx(
        (0.25 * north_area + south_area) / (1.5 * north_area + south_area)
    )
    assert result.value_units == "1"
    assert result.total_units == "km2"


def test_sum_of_exact_population_cells_cannot_silently_lose_integer_mass(
    tmp_path: Path, declared_payload: dict[str, Any]
) -> None:
    declared_payload["variable"].update(quantity="population", units="persons")
    declared_payload["values"] = [[9007199254740992, 1], [None, 0]]
    layer = write_layer(tmp_path, declared_payload)
    with pytest.raises(IntakeRefusal, match="population_precision_loss"):
        aggregate_layer(layer, layer.grid.bounds)


@pytest.mark.parametrize(
    "quantity,units", [("area_km2", "km2"), ("population", "persons")]
)
def test_extensive_values_are_summed_not_area_weighted(
    tmp_path: Path, declared_payload: dict[str, Any], quantity: str, units: str
) -> None:
    declared_payload["variable"].update(quantity=quantity, units=units)
    declared_payload["values"] = [[10, 20], [None, 30]]
    layer = write_layer(tmp_path, declared_payload)
    result = aggregate_layer(layer, layer.grid.bounds)
    assert result.total == 60
    assert result.value == 60
    assert result.total_units == units


def test_common_mask_scores_same_cells_and_reports_available_support(
    tmp_path: Path, declared_payload: dict[str, Any]
) -> None:
    left = write_layer(tmp_path, declared_payload)
    other = deepcopy(declared_payload)
    other["values"] = [[0, None], [1, 1]]
    right = write_layer(tmp_path, other, "right.json")
    result = compare_layers(
        left, right, left.grid.bounds, class_match_reference="fixture:class-match-v1"
    )
    assert (
        result.left_common.observed_cell_count
        == result.right_common.observed_cell_count
        == 2
    )
    assert (
        result.left_available.observed_cell_count
        == result.right_available.observed_cell_count
        == 3
    )
    assert result.value_difference == 0
    assert result.total_difference == 0
    assert result.independent_observation_truth is False
    assert result.public_release_allowed is False


def test_empty_data_remains_missing_and_empty_common_mask_refuses(
    tmp_path: Path, declared_payload: dict[str, Any]
) -> None:
    layer = write_layer(tmp_path, declared_payload)
    declared_payload["values"] = [[None, None], [None, None]]
    empty = write_layer(tmp_path, declared_payload, "empty.json")
    result = aggregate_layer(empty, empty.grid.bounds)
    assert result.value is None and result.total is None
    assert result.missing_land_area_km2 == result.full_land_area_km2
    with pytest.raises(IntakeRefusal, match="no_common_observed_land_support"):
        compare_layers(
            layer, empty, layer.grid.bounds, class_match_reference="fixture:match"
        )


def test_partial_coastal_cell_and_unsupported_region_refuse(
    tmp_path: Path, declared_payload: dict[str, Any]
) -> None:
    layer = write_layer(tmp_path, declared_payload)
    with pytest.raises(
        IntakeRefusal, match="partial_cell_transfer_requires_land_overlay"
    ):
        aggregate_layer(layer, Bounds(10.5, 60, 12, 62))
    with pytest.raises(IntakeRefusal, match="target_outside_grid"):
        aggregate_layer(layer, Bounds(9, 60, 12, 62))


@pytest.mark.parametrize(
    "section,field,value,reason",
    [
        ("variable", "category_key", "fixture:forest", "class_or_quantity_mismatch"),
        ("grid", "row_order", "south_to_north", "grid_or_land_mask_mismatch"),
    ],
)
def test_comparison_requires_explicit_compatible_support(
    tmp_path: Path,
    declared_payload: dict[str, Any],
    section: str,
    field: str,
    value: Any,
    reason: str,
) -> None:
    left = write_layer(tmp_path, declared_payload)
    declared_payload[section][field] = value
    right = write_layer(tmp_path, declared_payload, "right.json")
    with pytest.raises(IntakeRefusal, match=reason):
        compare_layers(
            left, right, left.grid.bounds, class_match_reference="fixture:match"
        )


def test_time_matching_does_not_interpolate_and_mapping_is_not_implicit(
    tmp_path: Path, declared_payload: dict[str, Any]
) -> None:
    left = write_layer(tmp_path, declared_payload)
    declared_payload["time"]["start"]["year"] = 2020
    declared_payload["time"]["end"]["year"] = 2020
    right = write_layer(tmp_path, declared_payload, "right.json")
    with pytest.raises(IntakeRefusal, match="time_support_mismatch"):
        compare_layers(
            left, right, left.grid.bounds, class_match_reference="fixture:match"
        )
    with pytest.raises(IntakeRefusal, match="class_match_reference_required"):
        compare_layers(left, left, left.grid.bounds, class_match_reference="")
