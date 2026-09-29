"""Frozen source identity and country completeness for bounded Nordic replay."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.reporting.map_document.static_assets import (
    write_static_atlas_assets,
)
from bijux_pollenomics_dev.ci.atlas_browser.nordic_source_candidate import (
    SOURCE_SELECTION,
    digest,
    generate_nordic_source_candidate,
)


def nordic_repository(root: Path) -> Path:
    retained = root / "docs/report/regions/nordic"
    retained.mkdir(parents=True)
    source_assets = (
        root / "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/assets/map"
    )
    source_assets.mkdir(parents=True)
    (source_assets / "asset.js").write_text("literal asset")
    seed_details: list[dict[str, Any]] = [
        {
            "tabs": {
                "overview": {},
                "chronology": {
                    "fields": ["calibration_status", "comparability_status"],
                    "record_count": 3,
                    "records": [
                        ["calibrated", "comparable"],
                        ["calibrated", "refused"],
                        ["uncalibrated", "context_only"],
                    ],
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
                    "source_snapshot_id": "source-snapshot",
                },
            }
        }
    ]
    layers, details = [], []
    for layer_key in ("neotoma-pollen", "sead-sites"):
        features = []
        for country, selections in SOURCE_SELECTION.items():
            record_id = selections[layer_key]
            features.append(
                {
                    "record_id": record_id,
                    "evidence_row_id": record_id.rsplit(":", 1)[1],
                    "title": record_id,
                    "country": country,
                    "latitude": 57.0,
                    "longitude": 15.0,
                }
            )
            detail = copy.deepcopy(seed_details[0])
            detail["record_id"] = record_id
            detail["tabs"]["overview"]["country"] = country
            details.append(detail)
        layers.append(
            {
                "key": layer_key,
                "label": layer_key,
                "default_enabled": True,
                "group": "environmental-context",
                "features": features,
            }
        )
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
    return retained


def test_nordic_replay_retains_exact_eight_country_source_records(
    tmp_path: Path,
) -> None:
    nordic_repository(tmp_path)
    receipt = generate_nordic_source_candidate(
        tmp_path, tmp_path / "artifacts/candidate"
    )
    assert receipt["selected_source_record_equality"] is True
    assert receipt["countries"] == ["Denmark", "Finland", "Norway", "Sweden"]
    records = receipt["source_records"]
    assert len(records) == 8
    for country, selections in SOURCE_SELECTION.items():
        assert {
            record["record_id"] for record in records if record["country"] == country
        } == set(selections.values())
    for record in records:
        assert record["chronology"]["records"] == [
            ["calibrated", "comparable"],
            ["calibrated", "refused"],
            ["uncalibrated", "context_only"],
        ]
        assert record["classification"]["status"] == "unavailable"
        assert record["source_provenance"]["source_snapshot_id"] == "source-snapshot"


def test_nordic_replay_rejects_tampered_retained_nodes(tmp_path: Path) -> None:
    retained = nordic_repository(tmp_path)
    for path in retained.glob("*.atlas-nodes.*.js"):
        path.write_text("tampered retained source")
    with pytest.raises(ValueError, match="chunk digest mismatch"):
        generate_nordic_source_candidate(tmp_path, tmp_path / "artifacts/candidate")
    assert not (tmp_path / "artifacts/candidate").exists()


def test_nordic_replay_requires_absent_owned_destination(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="repository artifacts"):
        generate_nordic_source_candidate(tmp_path, tmp_path / "outside")
    destination = tmp_path / "artifacts/candidate"
    destination.mkdir(parents=True)
    with pytest.raises(ValueError, match="destination must be absent"):
        generate_nordic_source_candidate(tmp_path, destination)


def test_source_identity_digest_preserves_values_and_ignores_key_order() -> None:
    assert digest({"age": None, "count": 0}) == digest({"count": 0, "age": None})
    assert digest({"age": None}) != digest({"age": 0})
