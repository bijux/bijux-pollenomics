"""Repository boundary admission and country-selection fidelity."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.boundaries.store import (
    load_repository_country_boundaries,
)
from bijux_pollenomics.collection.spatial import classify_country
from tests.support.context_data.boundaries import write_synthetic_boundary_manifest


def _repository_boundary_fixture(
    tmp_path: Path,
) -> tuple[Path, dict[str, dict[str, object]]]:
    data_root = tmp_path / "data"
    raw_root = data_root / "boundaries" / "raw"
    raw_root.mkdir(parents=True)
    payloads: dict[str, dict[str, object]] = {}
    for country, code, west, south in (
        ("Denmark", "DNK", 9.0, 54.0),
        ("Finland", "FIN", 24.0, 60.0),
        ("Norway", "NOR", 4.0, 58.0),
        ("Sweden", "SWE", 14.0, 55.0),
    ):
        payload: dict[str, object] = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"ADM0_A3": code},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [west, south],
                                [west + 1, south],
                                [west + 1, south + 1],
                                [west, south + 1],
                                [west, south],
                            ]
                        ],
                    },
                }
            ],
        }
        (raw_root / f"{country.casefold()}.geojson").write_text(json.dumps(payload))
        payloads[country] = payload
    write_synthetic_boundary_manifest(raw_root)
    return data_root, payloads


def test_repository_loader_preserves_valid_country_geometry_and_order(
    tmp_path: Path,
) -> None:
    data_root, payloads = _repository_boundary_fixture(tmp_path)
    before = {
        path.name: path.read_bytes()
        for path in (data_root / "boundaries/raw").iterdir()
    }
    loaded = load_repository_country_boundaries(data_root)
    assert loaded == payloads
    assert list(loaded) == ["Denmark", "Finland", "Norway", "Sweden"]
    for longitude, latitude, country in (
        (9.5, 54.5, "Denmark"),
        (24.5, 60.5, "Finland"),
        (4.5, 58.5, "Norway"),
        (14.5, 55.5, "Sweden"),
    ):
        assert classify_country(longitude, latitude, loaded) == country
    assert classify_country(35, 72, loaded) == ""
    assert before == {
        path.name: path.read_bytes()
        for path in (data_root / "boundaries/raw").iterdir()
    }


def test_repository_loader_refuses_coordinate_drift_before_country_selection(
    tmp_path: Path,
) -> None:
    data_root, payloads = _repository_boundary_fixture(tmp_path)
    raw_root = data_root / "boundaries" / "raw"
    original_manifest = (raw_root / "source_manifest.json").read_bytes()
    assert classify_country(14.5, 55.5, payloads) == "Sweden"
    replacement: dict[str, object] = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"ADM0_A3": "SWE"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [20, 55],
                            [21, 55],
                            [21, 56],
                            [20, 56],
                            [20, 55],
                        ]
                    ],
                },
            }
        ],
    }
    changed: dict[str, dict[str, object]] = {**payloads, "Sweden": replacement}
    assert classify_country(14.5, 55.5, changed) == ""
    (raw_root / "sweden.geojson").write_text(json.dumps(replacement))
    with pytest.raises(ValueError, match="digest mismatch"):
        load_repository_country_boundaries(data_root)
    assert (raw_root / "source_manifest.json").read_bytes() == original_manifest


@pytest.mark.parametrize(
    "field,value",
    [
        ("version", "5.0.0"),
        ("asset_url", "https://example.invalid/other.geojson"),
        ("source_crs", "EPSG:3857"),
        ("geometry_inclusion_policy", "mainland_only"),
    ],
)
def test_repository_loader_refuses_changed_source_authority(
    tmp_path: Path, field: str, value: str
) -> None:
    data_root, _ = _repository_boundary_fixture(tmp_path)
    manifest_path = data_root / "boundaries/raw/source_manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest[field] = value
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        load_repository_country_boundaries(data_root)


@pytest.mark.parametrize("missing", ["source_manifest.json", "finland.geojson"])
def test_repository_loader_refuses_incomplete_authority_instead_of_inference(
    tmp_path: Path, missing: str
) -> None:
    data_root, _ = _repository_boundary_fixture(tmp_path)
    (data_root / "boundaries/raw" / missing).unlink()
    with pytest.raises((ValueError, FileNotFoundError)):
        load_repository_country_boundaries(data_root)
