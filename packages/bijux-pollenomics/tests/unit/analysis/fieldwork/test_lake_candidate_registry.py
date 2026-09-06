from __future__ import annotations

import json
import tempfile
from pathlib import Path

from bijux_pollenomics.analysis import (
    build_sweden_lake_candidate_registry,
    write_sweden_lake_candidate_registry,
)


def _lake_feature(
    *, lake_id: str, name: str, longitude: float, latitude: float, area_km2: float
) -> dict[str, object]:
    offset = 0.01
    return {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [longitude - offset, latitude - offset],
                    [longitude + offset, latitude - offset],
                    [longitude + offset, latitude + offset],
                    [longitude - offset, latitude + offset],
                    [longitude - offset, latitude - offset],
                ]
            ],
        },
        "properties": {
            "source": "SMHI SVAR",
            "country": "SE",
            "record_id": lake_id,
            "sjoid": lake_id,
            "name": name,
            "area_km2": area_km2,
            "source_url": f"https://example.test/svar/{lake_id}",
        },
    }


def test_candidate_registry_resolves_pollen_lakes_and_named_targets() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        svar_path = root / "sweden_lake_registry.geojson"
        pollen_path = root / "pollen.geojson"
        svar_path.write_text(
            json.dumps(
                {
                    "type": "FeatureCollection",
                    "features": [
                        _lake_feature(
                            lake_id="alpha",
                            name="Lake Alpha",
                            longitude=14.0,
                            latitude=57.0,
                            area_km2=0.12,
                        ),
                        _lake_feature(
                            lake_id="beta",
                            name="Lake Beta",
                            longitude=15.0,
                            latitude=58.0,
                            area_km2=2.4,
                        ),
                    ],
                }
            ),
            encoding="utf-8",
        )
        pollen_path.write_text(
            json.dumps(
                {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "geometry": {
                                "type": "Point",
                                "coordinates": [14.001, 57.001],
                            },
                            "properties": {
                                "country": "Sweden",
                                "layer_key": "neotoma-pollen",
                                "record_id": "pollen-alpha",
                            },
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

        registry, review = build_sweden_lake_candidate_registry(
            svar_geojson_path=svar_path,
            pollen_geojson_paths=(pollen_path,),
            generated_on="2026-08-01",
            named_targets=("Lake Beta", "Missing marsh"),
        )

        assert registry["selection"]["candidate_count"] == 2
        alpha, beta = registry["features"]
        assert alpha["properties"]["matched_pollen_records"] == [
            "neotoma-pollen:pollen-alpha"
        ]
        assert alpha["properties"]["sampling_area_screen"] == "compact_lake_review"
        assert beta["properties"]["candidate_selection_reasons"] == [
            "named_target_review"
        ]
        assert (
            beta["properties"]["sampling_readiness_posture"] == "site_review_required"
        )
        assert len(beta["properties"]["sampling_missing_inputs"]) == 5
        assert review["named_targets"][0]["registry_status"] == "matched"
        assert review["named_targets"][1]["registry_status"] == (
            "not_present_in_svar_lakes"
        )

        registry_path = root / "review" / "candidate_registry.geojson"
        review_path = root / "review" / "candidate_registry_review.json"
        write_sweden_lake_candidate_registry(
            registry_path=registry_path,
            review_path=review_path,
            registry=registry,
            review=review,
        )
        assert registry_path.is_file()
        assert review_path.is_file()
