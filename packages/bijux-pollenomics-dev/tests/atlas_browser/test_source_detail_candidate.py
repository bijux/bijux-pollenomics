"""Source integrity and literal chronology preservation for bounded drawer replay."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_pollenomics.reporting.map_document.static_assets import (
    write_static_atlas_assets,
)
from bijux_pollenomics_dev.ci.atlas_browser.source_detail_candidate import (
    SITE_IDS,
    generate_source_detail_candidate,
)


def retained_repository(root: Path) -> tuple[Path, list[dict[str, object]]]:
    retained = root / "docs/report/regions/nordic"
    retained.mkdir(parents=True)
    layers = [
        {
            "key": "neotoma-pollen",
            "label": "Neotoma",
            "default_enabled": True,
            "group": "environmental-context",
            "features": [
                {
                    "record_id": site,
                    "title": f"Source site {index}",
                    "country": "Sweden",
                    "latitude": 57.0 + index,
                    "longitude": 15.0,
                }
                for index, site in enumerate(SITE_IDS)
            ],
        }
    ]
    details: list[dict[str, object]] = [
        {
            "record_id": site,
            "tabs": {
                "overview": {"site_id": site},
                "samples": {
                    "samples": {
                        "record_count": 26,
                        "fields": ["sample_id"],
                        "records": [[f"sample:{index}"] for index in range(26)],
                    }
                },
                "chronology": {
                    "record_count": 3,
                    "fields": ["calibration_status", "comparability_status"],
                    "records": [
                        ["calibrated", "comparable"],
                        ["calibrated", "refused"],
                        ["uncalibrated", "context_only"],
                    ],
                },
                "pollen_composition": {
                    "record_count": 1,
                    "fields": ["sample_id", "source_value", "source_unit"],
                    "records": [["sample:0", 2, "NISP"]],
                },
                "classification": {
                    "status": "unavailable",
                    "reason_code": "review_not_available",
                },
                "relation": {
                    "status": "unavailable",
                    "reason_code": "review_not_available",
                },
                "provenance": {
                    "build_id": "source-build",
                    "record_locator": f"surfaces/sites#site_id={site}",
                    "source_snapshot_id": "source-snapshot",
                },
            },
        }
        for site in SITE_IDS
    ]
    assets = write_static_atlas_assets(
        retained,
        slug="nordic",
        version="source-fixture",
        point_layers=layers,
        polygon_layers=[],
        detail_records=details,
    )
    (retained / "nordic_map.html").write_text(
        '<script id="atlas-static-bootstrap" type="application/json">'
        + json.dumps(assets.manifest)
        + "</script>"
    )
    source_assets = (
        root / "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/assets/map"
    )
    source_assets.mkdir(parents=True)
    (source_assets / "asset.js").write_text("literal asset")
    return retained, details


def test_source_detail_replay_preserves_refused_contextual_and_comparable_claims(
    tmp_path: Path,
) -> None:
    retained_repository(tmp_path)
    destination = tmp_path / "artifacts/candidate"
    receipt = generate_source_detail_candidate(tmp_path, destination)
    assert len(receipt["source_records"]) == 2
    assert receipt["source_records"][0]["chronology_status_counts"] == [
        {"calibration": "calibrated", "comparability": "comparable", "count": 1},
        {"calibration": "calibrated", "comparability": "refused", "count": 1},
        {"calibration": "uncalibrated", "comparability": "context_only", "count": 1},
    ]
    assert (
        receipt["source_records"][0]["source_provenance"]["source_snapshot_id"]
        == "source-snapshot"
    )
    assert receipt["source_records"][0]["sample_count"] == 26
    expected = json.loads((destination / "expectations.json").read_text())
    assert expected["next_detail_status"] == "available"
    assert expected["sample_table_path"] == "samples.samples"
    assert (destination / "_map_assets/asset.js").read_text() == "literal asset"


def test_source_detail_replay_rejects_mutated_chunk_before_writing_candidate(
    tmp_path: Path,
) -> None:
    retained, _details = retained_repository(tmp_path)
    next(retained.glob("*.atlas-nodes.*.js")).write_text("mutated source")
    destination = tmp_path / "artifacts/candidate"
    with pytest.raises(ValueError, match="chunk digest mismatch"):
        generate_source_detail_candidate(tmp_path, destination)
    assert not destination.exists()


def test_source_detail_replay_requires_absent_owned_artifact_destination(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="repository artifacts"):
        generate_source_detail_candidate(tmp_path, tmp_path / "candidate")
    destination = tmp_path / "artifacts/candidate"
    destination.mkdir(parents=True)
    with pytest.raises(ValueError, match="destination must be absent"):
        generate_source_detail_candidate(tmp_path, destination)
