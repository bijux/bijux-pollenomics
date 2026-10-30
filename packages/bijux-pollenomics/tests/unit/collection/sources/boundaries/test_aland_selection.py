"""Explicit source-unit selection and lossless Finland/Åland composition."""

from __future__ import annotations

from copy import deepcopy
from datetime import date
import hashlib
import json
from pathlib import Path
from typing import Any, cast
from unittest.mock import patch

import pytest

from bijux_pollenomics.collection.sources.boundaries.archive import (
    build_combined_country_boundaries,
    write_boundary_archive,
)
from bijux_pollenomics.collection.sources.boundaries.collection import (
    BOUNDARY_CODES,
    NATURAL_EARTH_ADMIN0_URL,
    NATURAL_EARTH_TERMS_URL,
    NATURAL_EARTH_VERSION,
    build_country_boundary_collection,
    collect_boundaries_data,
    fetch_natural_earth_admin0_payload,
    load_country_boundaries,
)
from bijux_pollenomics.collection.sources.boundaries.store import (
    NORDIC_ADMIN0_MEMBERS,
    NORDIC_WITH_ALAND_PROFILE,
    boundary_selection_profile,
    load_repository_country_boundaries,
    validate_boundary_collection,
)
from bijux_pollenomics.collection.spatial import classify_country


def _polygon(
    west: float, south: float = 60.0, span: float = 0.1
) -> list[list[list[float]]]:
    return [
        [
            [west, south],
            [west + span, south],
            [west + span, south + span],
            [west, south + span],
            [west, south],
        ]
    ]


def _source() -> dict[str, Any]:
    features = []
    for code, sovereign, sovereignty, west in (
        ("SWE", "Sweden", "SWE", 15.0),
        ("NOR", "Norway", "NOR", 10.0),
        ("ALD", "Finland", "FI1", 19.5),
        ("FIN", "Finland", "FI1", 25.0),
        ("DNK", "Denmark", "DN1", 12.0),
        ("FRO", "Denmark", "DN1", -7.0),
        ("GRL", "Denmark", "DN1", -40.0),
    ):
        geometry: dict[str, Any] = {"type": "Polygon", "coordinates": _polygon(west)}
        if code == "FIN":
            first = _polygon(west)
            first.append(_polygon(west + 0.02, 60.02, 0.02)[0])
            geometry = {
                "type": "MultiPolygon",
                "coordinates": [first, _polygon(west + 1.0)],
            }
        if code == "NOR":
            geometry = {
                "type": "MultiPolygon",
                "coordinates": [_polygon(west), _polygon(3.4, -54.4)],
            }
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "ADM0_A3": code,
                    "SOVEREIGNT": sovereign,
                    "SOV_A3": sovereignty,
                    "source_note": code + " preserved",
                },
                "geometry": geometry,
            }
        )
    return {"type": "FeatureCollection", "features": features}


def _manifest() -> dict[str, Any]:
    return {
        "schema_version": "natural-earth-boundary-receipt.v2",
        "generated_on": "2026-10-27",
        "source": "Natural Earth",
        "version": NATURAL_EARTH_VERSION,
        "asset_url": NATURAL_EARTH_ADMIN0_URL,
        "sha256": "a" * 64,
        "license": "public_domain",
        "license_url": NATURAL_EARTH_TERMS_URL,
        "source_crs": "EPSG:4326",
        "coordinate_transformation": "none",
        "country_selection_field": "ADM0_A3",
        "geometry_inclusion_policy": "retain_all_geometry_parts_from_each_selected_admin0_feature",
        "country_codes": dict(BOUNDARY_CODES),
        "country_selection_profile": NORDIC_WITH_ALAND_PROFILE,
        "country_admin0_members": {
            country: list(members) for country, members in NORDIC_ADMIN0_MEMBERS.items()
        },
    }


def _selected(source: dict[str, Any]) -> dict[str, Any]:
    return {
        country: build_country_boundary_collection(
            source, code, selection_profile=NORDIC_WITH_ALAND_PROFILE
        )
        for country, code in BOUNDARY_CODES.items()
    }


def test_fetch_receipt_declares_exact_members_without_extra_public_countries() -> None:
    text = json.dumps(_source())
    with patch(
        "bijux_pollenomics.collection.sources.boundaries.collection.fetch_text",
        return_value=text,
    ):
        source, manifest = fetch_natural_earth_admin0_payload()
    assert source == _source()
    assert manifest["sha256"] == hashlib.sha256(text.encode()).hexdigest()
    assert manifest["schema_version"] == "natural-earth-boundary-receipt.v2"
    assert boundary_selection_profile(manifest) == NORDIC_WITH_ALAND_PROFILE
    assert manifest["country_admin0_members"] == {
        "Sweden": ["SWE"],
        "Norway": ["NOR"],
        "Finland": ["FIN", "ALD"],
        "Denmark": ["DNK"],
    }


def test_legacy_receipt_cannot_silently_claim_a_new_member_profile() -> None:
    manifest = _manifest()
    manifest["schema_version"] = "natural-earth-boundary-receipt.v1"
    with pytest.raises(ValueError, match="Legacy"):
        boundary_selection_profile(manifest)


def test_profile_preserves_raw_units_and_exact_geometry_parts() -> None:
    source = _source()
    before = deepcopy(source)
    selected = _selected(source)
    finland = selected["Finland"]["features"]
    assert isinstance(finland, list)
    assert [f["properties"]["ADM0_A3"] for f in finland] == ["FIN", "ALD"]
    assert finland == [source["features"][3], source["features"][2]]
    combined = cast(dict[str, Any], build_combined_country_boundaries(selected))
    rows = combined["features"]
    assert isinstance(rows, list)
    assert len(rows) == 4
    expected = source["features"][3]["geometry"]["coordinates"] + [
        source["features"][2]["geometry"]["coordinates"]
    ]
    assert rows[2]["geometry"] == {"type": "MultiPolygon", "coordinates": expected}
    for position, source_position in ((0, 0), (1, 1), (3, 4)):
        assert (
            rows[position]["geometry"]
            == source["features"][source_position]["geometry"]
        )
    assert selected["Denmark"]["features"] == [source["features"][4]]
    assert source == before


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "duplicate",
        "malformed_duplicate",
        "wrong_sovereign",
        "wrong_sovereign_code",
        "wrong_type",
    ],
)
def test_missing_duplicate_or_misbound_aland_refuses(mutation: str) -> None:
    source = _source()
    aland = source["features"][2]
    if mutation == "missing":
        source["features"].remove(aland)
    elif mutation == "duplicate":
        source["features"].append(deepcopy(aland))
    elif mutation == "malformed_duplicate":
        duplicate = deepcopy(aland)
        del duplicate["geometry"]
        source["features"].append(duplicate)
    elif mutation == "wrong_sovereign":
        aland["properties"]["SOVEREIGNT"] = "Denmark"
    elif mutation == "wrong_sovereign_code":
        aland["properties"]["SOV_A3"] = "DN1"
    else:
        aland["type"] = "NotFeature"
    with pytest.raises(ValueError):
        _selected(source)


@pytest.mark.parametrize(
    "mutation",
    [
        "unknown_profile",
        "null_profile",
        "missing_member",
        "duplicate_member",
        "foreign_member",
        "extra_country",
        "wrong_primary",
    ],
)
def test_receipt_profile_is_closed_and_explicit(mutation: str) -> None:
    manifest = _manifest()
    if mutation == "unknown_profile":
        manifest["country_selection_profile"] = "all_sovereignty"
    elif mutation == "null_profile":
        manifest["country_selection_profile"] = None
    elif mutation == "missing_member":
        manifest["country_admin0_members"]["Finland"] = ["FIN"]
    elif mutation == "duplicate_member":
        manifest["country_admin0_members"]["Finland"] = ["FIN", "ALD", "ALD"]
    elif mutation == "foreign_member":
        manifest["country_admin0_members"]["Denmark"].append("GRL")
    elif mutation == "extra_country":
        manifest["country_admin0_members"]["Åland"] = ["ALD"]
    else:
        manifest["country_codes"]["Finland"] = "ALD"
    with pytest.raises(ValueError):
        boundary_selection_profile(manifest)


def test_collector_writes_and_repository_loader_reopens_the_same_profile(
    tmp_path: Path,
) -> None:
    source = _source()
    output = tmp_path / "data" / "boundaries"
    with patch(
        "bijux_pollenomics.collection.sources.boundaries.collection.fetch_natural_earth_admin0_payload",
        return_value=(source, _manifest()),
    ):
        selected, report = collect_boundaries_data(output)
    loaded = load_repository_country_boundaries(tmp_path / "data")
    assert loaded == selected
    assert classify_country(19.55, 60.05, loaded) == "Finland"
    assert classify_country(-6.95, 60.05, loaded) == ""
    assert classify_country(3.45, -54.35, loaded) == "Norway"
    saved = json.loads(report.manifest_path.read_text())
    assert saved["country_artifacts"]["Finland"]["feature_count"] == 2
    assert saved["normalized_artifact"]["feature_count"] == 4
    assert len(json.loads(report.combined_path.read_text())["features"]) == 4
    saved["country_artifacts"]["Finland"]["feature_count"] = True
    report.manifest_path.write_text(json.dumps(saved))
    with pytest.raises(ValueError, match="member count"):
        load_country_boundaries(output)


def test_retained_source_mode_hashes_exact_bytes_without_fetching(
    tmp_path: Path,
) -> None:
    source = _source()
    source["features"][2]["properties"]["NAME"] = "Åland"
    raw = (json.dumps(source, ensure_ascii=False) + "\n").encode("utf-8")
    asset = tmp_path / "source.geojson"
    asset.write_bytes(raw)
    with patch(
        "bijux_pollenomics.collection.sources.boundaries.collection.fetch_natural_earth_admin0_payload",
        side_effect=AssertionError("Retained assets must not be downloaded again"),
    ):
        selected, report = collect_boundaries_data(
            tmp_path / "boundaries", source_path=asset
        )
    receipt = json.loads(report.manifest_path.read_text())
    assert receipt["acquisition_mode"] == "retained_asset"
    assert receipt["source_captured_at_utc"] is None
    assert receipt["sha256"] == hashlib.sha256(raw).hexdigest()
    assert str(asset) not in report.manifest_path.read_text()
    assert asset.read_bytes() == raw
    assert selected["Finland"]["features"] == [
        source["features"][3],
        source["features"][2],
    ]


def test_retained_capture_timestamp_is_distinct_from_artifact_build_date(
    tmp_path: Path,
) -> None:
    asset = tmp_path / "source.geojson"
    asset.write_text(json.dumps(_source()))
    prefix = "bijux_pollenomics.collection.sources.boundaries.collection"
    captured = "2026-10-27T22:49:00+00:00"
    with patch(prefix + ".date") as build_date:
        build_date.today.return_value = date(2026, 10, 28)
        _, report = collect_boundaries_data(
            tmp_path / "dated", source_path=asset, source_captured_at_utc=captured
        )
    receipt = json.loads(report.manifest_path.read_text())
    assert receipt["generated_on"] == "2026-10-28"
    assert receipt["source_captured_at_utc"] == captured
    for timestamp in (
        "not-an-instant",
        "2026-10-27T22:49:00",
        "2026-10-27T22:49:00+02:00",
    ):
        with pytest.raises(ValueError, match="timestamp"):
            collect_boundaries_data(
                tmp_path / "invalid",
                source_path=asset,
                source_captured_at_utc=timestamp,
            )
    assert not (tmp_path / "invalid").exists()
    with (
        patch(
            prefix + ".fetch_natural_earth_admin0_payload",
            side_effect=AssertionError("No overridden network timestamp"),
        ),
        pytest.raises(ValueError, match="retained"),
    ):
        collect_boundaries_data(tmp_path / "network", source_captured_at_utc=captured)


def test_legacy_single_feature_path_and_receipt_remain_unchanged(
    tmp_path: Path,
) -> None:
    source = _source()
    malformed = deepcopy(source["features"][3])
    malformed["geometry"] = None
    source["features"].append(malformed)
    legacy = {
        country: build_country_boundary_collection(source, code)
        for country, code in BOUNDARY_CODES.items()
    }
    assert legacy["Finland"]["features"] == [source["features"][3]]
    manifest = _manifest()
    manifest["schema_version"] = "natural-earth-boundary-receipt.v1"
    del manifest["country_selection_profile"]
    del manifest["country_admin0_members"]
    assert boundary_selection_profile(manifest) is None
    output = tmp_path / "legacy"
    write_boundary_archive(output, country_boundaries=legacy, source_manifest=manifest)
    assert load_country_boundaries(output) == legacy
    normalized = cast(dict[str, Any], build_combined_country_boundaries(legacy))
    for combined, original in zip(
        normalized["features"],
        [source["features"][i] for i in (0, 1, 3, 4)],
        strict=True,
    ):
        assert combined["geometry"] == original["geometry"]


def test_raw_profile_cannot_hide_missing_or_duplicate_members(tmp_path: Path) -> None:
    finland = _selected(_source())["Finland"]
    for members in (
        finland["features"][:1],
        finland["features"] + finland["features"][:1],
    ):
        with pytest.raises(ValueError, match="unique complete ordered"):
            validate_boundary_collection(
                {"type": "FeatureCollection", "features": members},
                path=tmp_path / "finland.geojson",
                country="Finland",
                country_code="FIN",
                selection_profile=NORDIC_WITH_ALAND_PROFILE,
            )
