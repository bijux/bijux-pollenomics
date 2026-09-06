from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from bijux_pollenomics.analysis import build_sweden_land_use_synthesis


def test_sweden_land_use_synthesis_keeps_time_and_target_decisions(
    tmp_path: Path,
) -> None:
    landclim_path = (
        tmp_path
        / "landclim"
        / "normalized"
        / "nordic_reveals_temporal_grid_cells.geojson"
    )
    sead_path = tmp_path / "sead" / "normalized" / "nordic_temporal_evidence.geojson"
    landclim_path.parent.mkdir(parents=True)
    sead_path.parent.mkdir(parents=True)
    landclim_path.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [13.0, 55.0],
                                    [14.0, 55.0],
                                    [14.0, 57.0],
                                    [13.0, 57.0],
                                    [13.0, 55.0],
                                ]
                            ],
                        },
                        "properties": {
                            "dataset_id": "937075",
                            "record_id": "937075:test:1000-2000-bp",
                            "parent_grid_record_id": "test",
                            "time_start_bp": 1000,
                            "time_end_bp": 2000,
                            "time_mean_bp": 1500,
                            "time_label": "1000-2000 BP",
                            "quality_class": "high",
                            "reconstruction_values": {
                                "ET": 20.0,
                                "ST": 30.0,
                                "OL": 50.0,
                                "AL": 10.0,
                                "GL": 40.0,
                                "Cerealia.t": 3.0,
                                "Secale": 1.0,
                            },
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    sead_path.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [13.703841, 56.133926],
                        },
                        "properties": {
                            "source_url": "https://browser.sead.se/site/1",
                            "time_start_bp": 1200,
                            "time_end_bp": 1300,
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    candidates = []
    candidate_rows = (
        ("Finjasjön", 56.133926, 13.703841),
        ("Östra Ringsjön", 55.872216, 13.536269),
        ("Havgårdssjön", 55.485801, 13.354724),
        ("Bjäresjö", 55.45927, 13.751909),
        ("Registry Lake", 56.2, 13.8),
        ("Outside Grid Lake", 58.0, 17.0),
    )
    for rank, (name, latitude, longitude) in enumerate(candidate_rows, start=1):
        candidates.append(
            SimpleNamespace(
                aggregate_rank=rank,
                candidate=SimpleNamespace(
                    lake_name=name,
                    latitude=latitude,
                    longitude=longitude,
                    lake_registry_id=f"registry-{rank}",
                    lake_area_km2=float(rank),
                    lake_sampling_readiness_posture="site_review_required",
                    representative_source_url=f"https://example.test/lake/{rank}",
                ),
            )
        )
    human = SimpleNamespace(
        coordinates=SimpleNamespace(latitude=56.133926, longitude=13.703841),
        chronology=SimpleNamespace(time_start_bp=1100, time_end_bp=1400),
        sample_count=2,
    )
    animal = {
        "latitude": 56.133926,
        "longitude": 13.703841,
        "sample_count": 1,
        "chronology": {"time_start_bp": 1150, "time_end_bp": 1350},
    }

    payload = build_sweden_land_use_synthesis(
        context_root=tmp_path,
        lake_report=SimpleNamespace(assessments=tuple(candidates)),
        human_localities=(human,),
        animal_localities=(animal,),
    )

    assert payload["target_count"] == 8
    assert payload["schema_version"] == "sweden-land-use-synthesis.v2"
    assert payload["time_row_count"] == 7
    assert payload["landclim_covered_target_count"] == 7
    assert payload["landclim_uncovered_target_count"] == 1
    finja = next(row for row in payload["rows"] if row["target_name"] == "Finjasjön")
    assert finja["forest_cover"] == 50.0
    assert finja["quality_class"] == "high"
    assert finja["open_land_cover"] == 50.0
    assert finja["agricultural_land_cover"] == 10.0
    assert finja["cereal_type_pollen_cover"] == 3.0
    assert finja["rye_pollen_cover"] == 1.0
    assert finja["sead_site_count_20km"] == 1
    assert finja["human_adna_sample_count_20km"] == 2
    assert finja["animal_adna_sample_count_20km"] == 1
    gullakra = next(
        row
        for row in payload["target_decisions"]
        if row["requested_name"] == "Gullåkra"
    )
    assert gullakra["lake_decision"] == "exclude_lake_ranking_include_context"
    assert gullakra["registry_id"] == ""
    registry_lake = next(
        row
        for row in payload["target_decisions"]
        if row["requested_name"] == "Registry Lake"
    )
    assert registry_lake["landclim_coverage_posture"] == "covered_by_governed_grid"
    assert registry_lake["landclim_window_count"] == 1
    outside_grid = next(
        row
        for row in payload["target_decisions"]
        if row["requested_name"] == "Outside Grid Lake"
    )
    assert outside_grid["landclim_coverage_posture"] == "outside_governed_grid"
    assert outside_grid["landclim_window_count"] == 0
    assert not any(row["target_name"] == "Outside Grid Lake" for row in payload["rows"])
