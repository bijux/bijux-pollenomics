"""Current chronology diagnostics retain group identity and per-profile depth basis."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.reporting.map_document.evidence_projection.neotoma_chronology import (
    chronology_quality_tables,
)
from tests.support.neotoma import download_row
from tests.support.neotoma.relational_shapes import nested, rows

from .test_neotoma_chronology_models import materialized


def decode(table: dict[str, Any]) -> list[dict[str, Any]]:
    return [dict(zip(table["fields"], row, strict=True)) for row in table["records"]]


def test_current_quality_tables_expose_exact_model_dataset_and_cited_cm_profile(
    tmp_path: Path,
) -> None:
    tabs, _ = materialized(tmp_path, download_row())
    quality = tabs["chronology"]["source_quality"]
    assert quality["schema_version"] == "neotoma-source-chronology-quality.v1"
    profiles = decode(quality["profiles"])
    assert len(profiles) == 2
    calibrated = next(
        row for row in profiles if row["chronology_id"] == "neotoma:chronology:301:7001"
    )
    assert calibrated["dataset_id"] == "neotoma:dataset:201"
    assert calibrated["collection_unit_id"] == "neotoma:collection-unit:301"
    assert calibrated["source_age_type"] == "Calibrated radiocarbon years BP"
    assert calibrated["source_age_unit"] == "year"
    assert calibrated["depth_unit"] == "cm"
    assert calibrated["depth_coordinate_status"] == "documented_source_cm_midpoints"
    assert (
        "https://open.neotomadb.org/dbschema/tables/analysisunits.html"
        in calibrated["depth_contract_sources"]
    )
    claims = decode(quality["claim_diagnostics"])
    assert {row["sample_id"] for row in claims} == {"neotoma:sample:9202"}
    assert len(claims) == 2
    assert all(
        row["profile_id"] in {profile["profile_id"] for profile in profiles}
        for row in claims
    )
    assert quality["source_profile"]["eligibility_changed"] is False
    assert quality["source_scope"] == {
        "source_family": "neotoma",
        "source_snapshot_id": tabs["provenance"]["source_snapshot_id"],
        "build_id": tabs["provenance"]["build_id"],
        "materialization_sha256": tabs["provenance"]["materialization_sha256"],
        "site_id": "neotoma:site:20",
        "country_code": "SE",
    }
    assert tabs["chronology"]["source_issues"]["conflicts"]["record_count"] == 0


def test_explicit_mm_remains_unqualified_in_current_profile_transport(
    tmp_path: Path,
) -> None:
    source = download_row()
    model = nested(
        rows(nested(source, "site", "collectionunit")["chronologies"])[0], "chronology"
    )
    rows(model["chroncontrols"])[0]["depthunits"] = "mm"
    tabs, _ = materialized(tmp_path, source)
    profiles = decode(tabs["chronology"]["source_quality"]["profiles"])
    selected = next(
        row for row in profiles if row["chronology_id"] == "neotoma:chronology:301:7001"
    )
    assert selected["depth_unit"] is None
    assert (
        selected["depth_coordinate_status"]
        == "refused_explicit_depth_unit_contradiction"
    )
    assert selected["sample_ids_outside_control_midpoint_envelope"] == []


def test_legacy_missing_quality_surfaces_remain_unavailable() -> None:
    result = chronology_quality_tables({}, {"neotoma:site:20"})
    assert result["neotoma:site:20"] == {
        "status": "unavailable",
        "reason_code": "neotoma_chronology_quality_metadata_unavailable",
    }


def test_quality_transport_cannot_drop_source_rows_with_unknown_site_owner() -> None:
    loaded: dict[str, Any] = {
        "samples": ([{"sample_id": "sample:unknown", "site_id": "site:unknown"}], (1,)),
        "age_claims": ([], ()),
        "chronologies": ([], ()),
        "chronology_controls": ([], ()),
        "conflicts": ([], ()),
    }
    with pytest.raises(ValueError, match="owner"):
        chronology_quality_tables(loaded, {"neotoma:site:20"})
