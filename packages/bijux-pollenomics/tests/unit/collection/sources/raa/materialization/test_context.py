"""Native-context rights/identity controls independent of historical WFS admission."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sqlite3
from typing import cast

from pyproj import CRS
import pytest

from bijux_pollenomics.collection.sources.raa.authority import (
    assess_raa_density_authority,
)
from bijux_pollenomics.collection.sources.raa.materialization.context import (
    open_raa_source_context,
)

from .support import A, blob, identity

ROOT = Path(__file__).resolve().parents[8]


def descriptor(path: Path) -> dict[str, object]:
    raw = json.loads(
        (ROOT / "data/raa/raw/national_geopackage_source.json").read_bytes()
    )
    digest, size = identity(path)
    raw.update(sha256=digest, byte_count=size)
    return cast(dict[str, object], raw)


def valid_crs(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute(
            "UPDATE gpkg_spatial_ref_sys SET definition=?",
            (CRS.from_epsg(3006).to_wkt(),),
        )


def test_lazy_context_preserves_native_fields_and_keeps_legacy_refusal(
    database: Path,
) -> None:
    valid_crs(database)
    source = descriptor(database)
    with open_raa_source_context(database, source) as context:
        rows = list(context.rows("lamning"))
        assert [row["lamningsnamn"] for row in rows] == ["Å", "", "same-readable"]
        assert rows[0]["inspire_ruin"] == 0
        assert rows[0]["publiceringsdatum"] is None
        assert rows[0]["uuid"] == A
        attributes = list(context.rows("egenskap"))
        assert [row["varde"] for row in attributes] == ["", "Rund", None, "0", None]
        assert attributes[1]["lamning_uuid"] is None
        assert attributes[1]["ingaendelamning_id"] == 10
        profile = context.profile
        assert profile["status"] == "admitted_source_context"
        assert profile["source_record_count"] == 3
        assert profile["geometry_occurrence_counts_by_role"] == {
            "native_remains_geometry": 4,
            "positional_uncertainty": 2,
        }
        for key in (
            "scientific_admission",
            "chronology_admission",
            "event_admission",
            "publication_admission",
            "legacy_density_admission",
        ):
            assert profile[key] is False
        profile["status"] = "forged"
        assert context.profile["status"] == "admitted_source_context"
        with pytest.raises(sqlite3.DatabaseError):
            context.connection.execute("DELETE FROM lamning")
        with pytest.raises(ValueError, match="owned base table"):
            list(context.rows("sqlite_schema"))
    decision = assess_raa_density_authority(database.parent.parent)
    assert decision.admitted is False
    assert "missing_raw_inventory" in decision.reason_codes


def test_geometry_roles_preserve_invalid_and_null_payloads(database: Path) -> None:
    valid_crs(database)
    with open_raa_source_context(database, descriptor(database)) as context:
        raw = list(context.rows("point"))
        assert raw[0]["geometri"] == blob()
        points = list(context.geometry_rows("point"))
        assert points[0]["geometry_role"] == "native_remains_geometry"
        assert (
            cast(dict[str, object], points[0]["geometry"])["status"]
            == "structurally_valid_nonempty"
        )
        assert cast(dict[str, object], points[1]["geometry"])["reason_codes"] == [
            "declared_crs_mismatch"
        ]
        uncertain = list(context.geometry_rows("lämningar_sverige_lägesosäkerhet"))
        assert uncertain[0]["geometry_role"] == "positional_uncertainty"
        assert (
            cast(dict[str, object], uncertain[1]["geometry"])["status"] == "source_null"
        )
        assert all(row["scientific_admission"] is False for row in points + uncertain)


@pytest.mark.parametrize(
    "field,value",
    [
        ("rights_status", "not established"),
        ("rights_authority_version", "unknown"),
        ("rights_authority_url", "https://example.org"),
        ("download_url", "https://example.org/source.gpkg"),
        ("private_source_root_relative_path", "raa/another-source.gpkg"),
        ("scientific_admission", True),
        ("canonical_adoption", True),
    ],
)
def test_unbound_rights_source_or_rewritten_history_refuses(
    database: Path, field: str, value: object
) -> None:
    source = descriptor(database)
    source[field] = value
    with pytest.raises(ValueError), open_raa_source_context(database, source):
        pytest.fail("unbound source/rights context was admitted")


def test_raw_byte_identity_and_source_crs_refuse(database: Path) -> None:
    source = descriptor(database)
    wrong = deepcopy(source)
    wrong["sha256"] = "0" * 64
    with (
        pytest.raises(ValueError, match="SHA256"),
        open_raa_source_context(database, wrong),
    ):
        pytest.fail("mismatched source bytes admitted")
    with (
        pytest.raises(ValueError, match="declared CRS refused"),
        open_raa_source_context(database, source),
    ):
        pytest.fail("unreadable source WKT admitted")
