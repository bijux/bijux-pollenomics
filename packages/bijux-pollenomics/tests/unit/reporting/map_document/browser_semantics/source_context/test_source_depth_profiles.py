"""Depth labels use the bound, exact native source profile rather than global units."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, cast

import pytest

from tests.support.neotoma import download_row
from tests.support.neotoma.relational_shapes import nested, rows

from ...evidence_projection.neotoma_metadata.test_chronology_models import materialized
from ..pollen.test_pollen_small_multiples import script
from ..support import run_node_json


def observe(tabs: dict[str, Any]) -> dict[str, Any]:
    """Render all three actual optional plot owners, without replacing decoders."""
    return cast(
        dict[str, Any],
        run_node_json(
            script()
            + "const tabs="
            + json.dumps(tabs)
            + """;const original=JSON.stringify(tabs);
const native=pollenObservationDiagramData(tabs),key=native.groups[0]?.key;
console.log(JSON.stringify({age:renderAgeDepthDiagram(tabs),
 native:renderPollenDepthDiagram(tabs),
 panels:renderPollenSmallMultiples(tabs,key),
 unchanged:original===JSON.stringify(tabs)}));"""
        ),
    )


def profiles(tabs: dict[str, Any]) -> list[dict[str, Any]]:
    table = tabs["chronology"]["source_quality"]["profiles"]
    return [dict(zip(table["fields"], row, strict=True)) for row in table["records"]]


def replace_profiles(tabs: dict[str, Any], values: list[dict[str, Any]]) -> None:
    table = tabs["chronology"]["source_quality"]["profiles"]
    table["records"] = [[row[field] for field in table["fields"]] for row in values]
    table["record_count"] = len(values)


def test_actual_quality_producer_qualifies_each_depth_axis_with_cited_cm(
    tmp_path: Path,
) -> None:
    tabs, _ = materialized(tmp_path, download_row())
    original = deepcopy(tabs)
    output = observe(tabs)
    for axis in ("age", "native", "panels"):
        assert "Source depth (cm)" in output[axis]
        assert "documented source cm midpoints" in output[axis]
        assert (
            "https://open.neotomadb.org/dbschema/tables/analysisunits.html"
            in output[axis]
        )
        assert "physical core base" in output[axis]
    assert output["unchanged"] is True and tabs == original


def test_explicit_mm_contradiction_never_receives_cm_from_another_model(
    tmp_path: Path,
) -> None:
    source = download_row()
    model = nested(
        rows(nested(source, "site", "collectionunit")["chronologies"])[0], "chronology"
    )
    rows(model["chroncontrols"])[0]["depthunits"] = "mm"
    tabs, _ = materialized(tmp_path, source)
    output = observe(tabs)
    # Each source age group keeps its own qualification. Native value panels
    # cannot pick the other model's unit when source profiles disagree.
    assert "explicit depth unit contradiction" in output["age"]
    assert "Source depth (cm)" in output["age"]
    for axis in ("native", "panels"):
        assert "Source depth (cm)" not in output[axis]
        assert "explicit depth unit contradiction" in output[axis]
        assert "<svg" not in output[axis]
        assert "coordinate comparison refused" in output[axis]
    assert output["unchanged"] is True


@pytest.mark.parametrize(
    "field", ["dataset_id", "collection_unit_id", "site_id", "country_code"]
)
def test_foreign_profile_cannot_qualify_native_depth(
    tmp_path: Path, field: str
) -> None:
    tabs, _ = materialized(tmp_path, download_row())
    values = profiles(tabs)
    for row in values:
        row[field] = "foreign"
    replace_profiles(tabs, values)
    output = observe(tabs)
    for axis in ("age", "native", "panels"):
        assert "Source depth (cm)" not in output[axis]
        assert "matching source depth profile unavailable" in output[axis]


@pytest.mark.parametrize(
    "field", ["chronology_id", "source_age_type", "source_age_unit"]
)
def test_foreign_age_identity_cannot_qualify_chronology_axis(
    tmp_path: Path, field: str
) -> None:
    tabs, _ = materialized(tmp_path, download_row())
    values = profiles(tabs)
    for row in values:
        row[field] = "foreign"
    replace_profiles(tabs, values)
    output = observe(tabs)
    assert "Source depth (cm)" not in output["age"]
    assert "matching source depth profile unavailable" in output["age"]


@pytest.mark.parametrize(
    "damage", ["missing", "duplicate", "count", "schema", "unit", "citations"]
)
def test_unavailable_or_ambiguous_qualification_does_not_promote_depth_units(
    tmp_path: Path, damage: str
) -> None:
    tabs, _ = materialized(tmp_path, download_row())
    quality = tabs["chronology"]["source_quality"]
    values = profiles(tabs)
    if damage == "missing":
        del tabs["chronology"]["source_quality"]
    elif damage == "duplicate":
        replace_profiles(tabs, values + [deepcopy(values[0])])
    elif damage == "count":
        quality["profiles"]["record_count"] += 1
    elif damage == "schema":
        quality["schema_version"] = "unknown"
    else:
        for row in values:
            row["depth_unit" if damage == "unit" else "depth_contract_sources"] = (
                "mm" if damage == "unit" else []
            )
        replace_profiles(tabs, values)
    output = observe(tabs)
    for axis in ("age", "native", "panels"):
        assert "Source depth (cm)" not in output[axis]
        assert "unit not supplied" in output[axis]
    assert output["unchanged"] is True


def test_non_neotoma_source_cannot_borrow_neotoma_profile(tmp_path: Path) -> None:
    tabs, _ = materialized(tmp_path, download_row())
    tabs["overview"]["source_family"] = "sead"
    output = observe(tabs)
    assert all(
        "Source depth (cm)" not in output[axis] for axis in ("age", "native", "panels")
    )


@pytest.mark.parametrize(
    "field",
    [
        "source_snapshot_id",
        "build_id",
        "materialization_sha256",
        "site_id",
        "country_code",
        "source_family",
    ],
)
def test_profile_from_another_bound_source_cannot_qualify_axes(
    tmp_path: Path, field: str
) -> None:
    tabs, _ = materialized(tmp_path, download_row())
    tabs["chronology"]["source_quality"]["source_scope"][field] = "foreign"
    output = observe(tabs)
    for axis in ("age", "native", "panels"):
        assert "Source depth (cm)" not in output[axis]
        assert "source depth profile scope mismatch" in output[axis]


def test_untrusted_citation_text_is_escaped_without_altering_raw_profile(
    tmp_path: Path,
) -> None:
    tabs, _ = materialized(tmp_path, download_row())
    values = profiles(tabs)
    for row in values:
        row["depth_contract_sources"].append("<img src=x onerror=bad>")
    replace_profiles(tabs, values)
    output = observe(tabs)
    for axis in ("age", "native", "panels"):
        assert "<img" not in output[axis]
        assert "&lt;img src=x onerror=bad&gt;" in output[axis]
    assert output["unchanged"] is True


def test_unaged_sample_cannot_borrow_other_members_cm_depth_contract(
    tmp_path: Path,
) -> None:
    source = download_row()
    dataset = nested(source, "site", "collectionunit", "dataset")
    sample_rows = rows(dataset["samples"])
    unaged = deepcopy(sample_rows[0])
    unaged.update(
        sampleid=9300, analysisunitid=9400, depth=200, depthunits="mm", ages=[]
    )
    dataset["samples"] = [*sample_rows, unaged]
    tabs, _ = materialized(tmp_path, source)
    output = observe(tabs)
    assert "Source depth (cm)" in output["age"]
    for axis in ("native", "panels"):
        assert "Source depth (cm)" not in output[axis]
        assert "coordinate comparison refused" in output[axis]
        assert "<svg" not in output[axis]
    assert output["unchanged"] is True


@pytest.mark.parametrize(
    "damage", ["missing", "foreign_sample", "foreign_profile", "duplicate"]
)
def test_missing_or_ambiguous_sample_profile_linkage_does_not_qualify_cm(
    tmp_path: Path, damage: str
) -> None:
    tabs, _ = materialized(tmp_path, download_row())
    table = tabs["chronology"]["source_quality"]["claim_diagnostics"]
    if damage == "missing":
        table["records"] = []
        table["record_count"] = 0
    elif damage == "duplicate":
        table["records"].append(deepcopy(table["records"][0]))
        table["record_count"] += 1
    else:
        field = "sample_id" if damage == "foreign_sample" else "profile_id"
        for row in table["records"]:
            row[table["fields"].index(field)] = "foreign"
    output = observe(tabs)
    for axis in ("age", "native", "panels"):
        assert "Source depth (cm)" not in output[axis]
    assert output["unchanged"] is True
