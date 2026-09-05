from __future__ import annotations

import json

def lake_scenario_row(
    scenario_key: str,
    scenario_label: str,
    rank: str,
) -> dict[str, str]:
    radius = ""
    if scenario_key.startswith("radius_"):
        radius = scenario_key.removeprefix("radius_").removesuffix("km")
    return {
        "scenario_key": scenario_key,
        "scenario_label": scenario_label,
        "radius_km": radius,
        "rank": rank,
        "score": "0.8123",
        "lake_name": "Lake Alpha",
        "lake_label": "Lake Alpha",
        "lake_token": f"lake-alpha-{scenario_key}",
        "latitude": "57.020000",
        "longitude": "14.020000",
        "google_maps_url": "https://www.google.com/maps/search/?api=1&query=57.020000,14.020000",
        "aggregate_rank": "3",
        "aggregate_score": "0.7441",
        "scenario_top20_presence_count": "6",
        "scenario_top20_labels": "aggregate; consensus; fieldwork shortlist",
        "lake_registry_id": "lake-registry-1",
        "lake_name_status": "water_surface_name",
        "lake_area_km2": "2.750",
        "lake_sampling_posture": "sampling_lake_candidate",
        "lake_sampling_fit": "0.9100",
        "lake_sampling_notes": "Prefer bathymetry and access checks before fieldwork.",
        "duplicate_name_count": "0",
        "coordinate_spread_km": "0.0000",
        "ambiguity_flags": "",
        "ambiguity_note": "",
        "direct_pollen_temporal_evidence": json.dumps(
            [
                {
                    "source_record": "neotoma-pollen:alpha",
                    "source_name": "Lake Alpha",
                    "source_layer_key": "neotoma-pollen",
                    "latitude": 57.02,
                    "longitude": 14.02,
                    "source_url": "https://example.test/neotoma/alpha",
                    "time_start_bp": 3600,
                    "time_end_bp": 2400,
                    "time_mean_bp": 3000,
                    "time_label": "3600–2400 BP",
                    "temporal_semantics": {},
                }
            ]
        ),
    }
