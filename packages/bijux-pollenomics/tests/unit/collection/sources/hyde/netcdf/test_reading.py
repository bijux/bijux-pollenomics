from __future__ import annotations

from collections.abc import Callable
import inspect
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.hyde.netcdf import (
    HydeNetcdfDeclarationInventory,
    read_hyde_netcdf_declaration_inventory,
    reopen_hyde_netcdf_declaration_inventory,
)
from bijux_pollenomics.collection.sources.hyde.netcdf.reading import (
    _read_hyde_netcdf_declaration_inventory,
    _reopen_hyde_netcdf_declaration_inventory,
)
from bijux_pollenomics.collection.sources.quarantine import IntakeRefusal

from .support import rewrite_headers, rewrite_json, write_inputs


def _read(inputs: dict[str, object]) -> object:
    return _read_hyde_netcdf_declaration_inventory(**inputs)  # type: ignore[arg-type]


def test_retains_exact_declaration_closure_without_admission(tmp_path: Path) -> None:
    product = _read_hyde_netcdf_declaration_inventory(
        **write_inputs(tmp_path)  # type: ignore[arg-type]
    )
    assert len(product.files) == 48
    assert product.scenario_counts == (("base", 16), ("lower", 16), ("upper", 16))
    assert [axis.name for axis in product.axes] == ["time", "lat", "lon"]
    assert product.axes[0].coordinate_values == (-365.0, 0.0, 365.0)
    assert product.axes[0].spacing == (365.0, 365.0)
    assert product.axes[1].orientation == "descending"
    assert product.axes[2].orientation == "ascending"
    assert product.files[0].dimensions == ("time", "lat", "lon")
    assert product.files[0].fill_value == -9999.0
    assert product.native_release_admitted is False
    assert product.rights_cleared is False
    assert product.crs_assigned is False
    assert product.canonical_bp_conversion_allowed is False
    assert product.scenario_confidence_bounds is False
    assert product.publication_allowed is False
    assert product.independent_measured_vegetation_truth is False
    assert product.scientific_acceptance == "not_evaluated"
    assert len(product.sha256) == 64
    assert product.payload()["schema_version"] == "hyde-netcdf-declaration-inventory.v1"


def test_public_reader_embeds_the_shipped_parent_identities() -> None:
    assert tuple(
        inspect.signature(read_hyde_netcdf_declaration_inventory).parameters
    ) == (
        "file_inventory_path",
        "inventory_report_path",
        "header_inventory_path",
        "conflict_report_path",
    )
    assert tuple(
        inspect.signature(reopen_hyde_netcdf_declaration_inventory).parameters
    ) == (
        "canonical_bytes",
        "file_inventory_path",
        "inventory_report_path",
        "header_inventory_path",
        "conflict_report_path",
    )


def test_typed_reopen_is_bound_to_the_same_authenticated_parents(
    tmp_path: Path,
) -> None:
    class BytesSubclass(bytes):
        pass

    inputs = write_inputs(tmp_path)
    product = _read_hyde_netcdf_declaration_inventory(
        **inputs  # type: ignore[arg-type]
    )
    reopened = _reopen_hyde_netcdf_declaration_inventory(
        product.canonical_bytes,
        **inputs,  # type: ignore[arg-type]
    )
    assert reopened == product
    with pytest.raises(IntakeRefusal, match="hyde_netcdf_canonical_identity_invalid"):
        _reopen_hyde_netcdf_declaration_inventory(
            product.canonical_bytes + b"\n",
            **inputs,  # type: ignore[arg-type]
        )
    with pytest.raises(IntakeRefusal, match="hyde_netcdf_canonical_identity_invalid"):
        _reopen_hyde_netcdf_declaration_inventory(
            BytesSubclass(product.canonical_bytes),
            **inputs,  # type: ignore[arg-type]
        )


def _wrong_file_identity(rows: list[dict[str, Any]]) -> None:
    rows[0]["bytes"] += 1


def _wrong_dimension(rows: list[dict[str, Any]]) -> None:
    rows[0]["dimensions"]["lat"]["size"] += 1


def _wrong_data_order(rows: list[dict[str, Any]]) -> None:
    variable = Path(rows[0]["path"]).stem
    rows[0]["variables"][variable]["dimensions"] = ["time", "lon", "lat"]


def _wrong_axis_order(rows: list[dict[str, Any]]) -> None:
    rows[0]["variables"]["lat"]["coordinate_values"].reverse()


def _wrong_unit(rows: list[dict[str, Any]]) -> None:
    variable = Path(rows[0]["path"]).stem
    rows[0]["variables"][variable]["attributes"]["units"] = "fraction"


def _wrong_fill(rows: list[dict[str, Any]]) -> None:
    variable = Path(rows[0]["path"]).stem
    rows[0]["variables"][variable]["attributes"]["_FillValue"] = 0.0


def _wrong_calendar(rows: list[dict[str, Any]]) -> None:
    rows[0]["variables"]["time"]["attributes"]["calendar"] = "proleptic_gregorian"


def _wrong_release(rows: list[dict[str, Any]]) -> None:
    rows[0]["attributes"]["version"] = "HYDE3.5"


def _wrong_scenario(rows: list[dict[str, Any]]) -> None:
    rows[0]["path"] = rows[0]["path"].replace("_base/", "_upper/")


@pytest.mark.parametrize(
    "mutation",
    [
        _wrong_file_identity,
        _wrong_dimension,
        _wrong_data_order,
        _wrong_axis_order,
        _wrong_unit,
        _wrong_fill,
        _wrong_calendar,
        _wrong_release,
        _wrong_scenario,
    ],
    ids=[
        "identity",
        "dimension",
        "data-order",
        "axis-order",
        "unit",
        "fill",
        "calendar",
        "release",
        "scenario",
    ],
)
def test_rehashed_semantic_mutations_are_refused(
    tmp_path: Path, mutation: Callable[[list[dict[str, Any]]], None]
) -> None:
    inputs = write_inputs(tmp_path)
    rewrite_headers(inputs, mutation)
    with pytest.raises(IntakeRefusal):
        _read(inputs)


def test_rehashed_scenario_confidence_relabelling_is_refused(tmp_path: Path) -> None:
    inputs = write_inputs(tmp_path)

    def mutate(value: dict[str, Any]) -> None:
        value["scenario_semantics"]["confidence_bounds_status"] = "declared"

    rewrite_json(inputs, "conflict_report", mutate)
    with pytest.raises(IntakeRefusal):
        _read(inputs)


def test_digest_mismatch_refuses_before_parsing(tmp_path: Path) -> None:
    inputs = write_inputs(tmp_path)
    inputs["expected_header_inventory_sha256"] = "f" * 64
    with pytest.raises(IntakeRefusal):
        _read(inputs)


def test_direct_product_forgery_is_refused() -> None:
    with pytest.raises(IntakeRefusal):
        HydeNetcdfDeclarationInventory(
            input_sha256=(),
            custody_manifest_sha256="a" * 64,
            dataset_inventory_sha256="b" * 64,
            dataset_file_count=0,
            dataset_byte_count=0,
            axes=(),
            files=(),
            conflicts=(),
        )
