"""Exact integral population values must survive declared JSON and aggregation."""

from hashlib import sha256
import json
from pathlib import Path
from typing import Any, cast

import pytest

from bijux_pollenomics.collection.sources.hyde import (
    DeclaredGridLayer,
    aggregate_layer,
    load_declared_grid,
)
from bijux_pollenomics.collection.sources.quarantine import IntakeRefusal


def _population(
    tmp_path: Path, payload: dict[str, Any], literal: str
) -> DeclaredGridLayer:
    payload["variable"].update(quantity="population", units="persons")
    payload["values"] = [["REPLACE", 0], [None, 0]]
    content = json.dumps(payload).replace('"REPLACE"', literal).encode()
    path = tmp_path / "population.json"
    path.write_bytes(content)
    return load_declared_grid(
        path.absolute(), expected_sha256=sha256(content).hexdigest()
    )


@pytest.mark.parametrize(
    "literal", ["9007199254740993", "9007199254740993.0", "9.007199254740993e15"]
)
def test_population_rejects_unrepresentable_integral_token(
    tmp_path: Path, declared_payload: dict[str, Any], literal: str
) -> None:
    with pytest.raises(IntakeRefusal, match="population_precision_loss"):
        _population(tmp_path, declared_payload, literal)


@pytest.mark.parametrize(
    "values",
    [[[9007199254740992.0, 1.0], [None, 0.0]], [[9007199254740992, 1.0], [None, 0]]],
)
def test_integral_float_and_mixed_population_mass_refuses_rounding(
    tmp_path: Path, declared_payload: dict[str, Any], values: list[list[object]]
) -> None:
    declared_payload["variable"].update(quantity="population", units="persons")
    declared_payload["values"] = values
    raw = json.dumps(declared_payload).encode()
    path = tmp_path / "mass.json"
    path.write_bytes(raw)
    layer = load_declared_grid(path.absolute(), expected_sha256=sha256(raw).hexdigest())
    with pytest.raises(IntakeRefusal, match="population_precision_loss"):
        aggregate_layer(layer, layer.grid.bounds)


@pytest.mark.parametrize(
    "literal, expected",
    [
        ("1.0", 1.0),
        ("1e0", 1.0),
        ("0.1", 0.1),
        ("1e-1000", 0.0),
        ("1e-999999999999999999999", 0.0),
    ],
)
def test_existing_exact_and_fractional_population_forms_are_retained(
    tmp_path: Path, declared_payload: dict[str, Any], literal: str, expected: float
) -> None:
    layer = _population(tmp_path, declared_payload, literal)
    assert layer.source_values[0] == expected
    assert type(layer.source_values[0]) is float
    assert aggregate_layer(layer, layer.grid.bounds).total == expected


@pytest.mark.parametrize(
    "nodata_literal",
    ["-9007199254740993", "-9007199254740993.0", "-9.007199254740993e15"],
)
def test_population_decimal_nodata_cannot_silently_match_different_integer(
    tmp_path: Path, declared_payload: dict[str, Any], nodata_literal: str
) -> None:
    declared_payload["variable"].update(quantity="population", units="persons")
    declared_payload["nodata_value"] = "NODATA"
    declared_payload["values"] = [[-9007199254740992.0, 0], [None, 0]]
    content = json.dumps(declared_payload).replace('"NODATA"', nodata_literal).encode()
    path = tmp_path / "nodata.json"
    path.write_bytes(content)
    with pytest.raises(IntakeRefusal, match="population_precision_loss"):
        load_declared_grid(path.absolute(), expected_sha256=sha256(content).hexdigest())


def test_fractional_source_rounded_to_integral_float_keeps_fractional_policy(
    tmp_path: Path, declared_payload: dict[str, Any]
) -> None:
    declared_payload["variable"].update(quantity="population", units="persons")
    declared_payload["values"] = [[9007199254740992.0, "FRACTION"], [None, 0.0]]
    content = (
        json.dumps(declared_payload)
        .replace('"FRACTION"', "1.0000000000000001")
        .encode()
    )
    path = tmp_path / "fractional-population.json"
    path.write_bytes(content)
    layer = load_declared_grid(
        path.absolute(), expected_sha256=sha256(content).hexdigest()
    )
    assert layer.source_values[1] == 1.0
    assert aggregate_layer(layer, layer.grid.bounds).total == 9007199254740992.0


def test_legacy_layers_without_lexical_metadata_keep_existing_float_policy(
    tmp_path: Path, declared_payload: dict[str, Any]
) -> None:
    from dataclasses import replace

    declared_payload["variable"].update(quantity="population", units="persons")
    declared_payload["values"] = [[9007199254740992.0, 1.0], [None, 0.0]]
    raw = json.dumps(declared_payload).encode()
    path = tmp_path / "legacy.json"
    path.write_bytes(raw)
    layer = load_declared_grid(path.absolute(), expected_sha256=sha256(raw).hexdigest())
    legacy = replace(layer, population_integral_cells=None)
    assert aggregate_layer(legacy, legacy.grid.bounds).total == 9007199254740992.0


def test_integrality_metadata_must_be_immutable_and_consistent(
    tmp_path: Path, declared_payload: dict[str, Any]
) -> None:
    from dataclasses import replace

    layer = _population(tmp_path, declared_payload, "1.0")
    with pytest.raises(IntakeRefusal, match="population_integrality_invalid"):
        replace(layer, population_integral_cells=cast(Any, [True, True, False, True]))
    with pytest.raises(IntakeRefusal, match="population_integrality_invalid"):
        replace(layer, population_integral_cells=(False, False, False, False))


def test_lexical_integrality_is_part_of_layer_equality_and_asdict(
    tmp_path: Path, declared_payload: dict[str, Any]
) -> None:
    from dataclasses import asdict, replace

    layer = _population(tmp_path, declared_payload, "1.0")
    assert layer.population_integral_cells is not None
    flags = (False, *layer.population_integral_cells[1:])
    different = replace(layer, population_integral_cells=flags)
    assert layer != different
    assert asdict(different)["population_integral_cells"] == flags
