from __future__ import annotations

import json
from pathlib import Path

from bijux_pollenomics.adna import (
    AdnaChronology,
    AdnaCoordinate,
    AdnaLocalityIdentity,
    AdnaLocalitySummary,
)


def _locality(
    name: str,
    latitude: float,
    longitude: float,
    *,
    sample_count: int,
) -> AdnaLocalitySummary:
    return AdnaLocalitySummary(
        identity=AdnaLocalityIdentity(
            namespace="shared_locality",
            stable_token=f"{name.casefold().replace(' ', '-')}-{latitude}-{longitude}",
            locality_text=name,
            political_entity="Sweden",
            source_anchor_tokens=("shared", str(latitude), str(longitude)),
        ),
        species_latin_name="Homo sapiens",
        species_common_name="human",
        source_family="AADR",
        source_releases=("v66",),
        record_modalities=("metadata_only",),
        review_strengths=("primary_paper_pinned",),
        provenance_qualities=("release_manifest_pinned",),
        locality=name,
        coordinates=AdnaCoordinate(
            latitude=latitude,
            longitude=longitude,
            latitude_text=str(latitude),
            longitude_text=str(longitude),
            confidence="unknown",
        ),
        sample_count=sample_count,
        sample_ids=tuple(f"S{index}" for index in range(sample_count)),
        datasets=("dataset",),
        chronology=AdnaChronology(
            original_text="3000 BP",
            time_start_bp=2500,
            time_end_bp=3500,
            time_mean_bp=3000,
            dating_basis="bp_window",
        ),
        sample_namespace="shared:sample",
    )


def _point_feature(
    *,
    source: str,
    layer_key: str,
    layer_label: str,
    category: str,
    country: str,
    record_id: str,
    name: str,
    latitude: float,
    longitude: float,
    description: str,
    time_start_bp: int | None = 2400,
    time_end_bp: int | None = 3600,
) -> dict[str, object]:
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [longitude, latitude]},
        "properties": {
            "source": source,
            "layer_key": layer_key,
            "layer_label": layer_label,
            "category": category,
            "country": country,
            "record_id": record_id,
            "name": name,
            "geometry_type": "Point",
            "subtitle": category,
            "description": description,
            "source_url": "https://example.test",
            "record_count": 1,
            "time_start_bp": time_start_bp,
            "time_end_bp": time_end_bp,
            "time_mean_bp": 3000 if time_start_bp is not None else None,
            "time_label": "3000 BP" if time_start_bp is not None else "",
            "popup_rows": [],
        },
    }


def _raa_feature(
    *,
    min_longitude: float,
    min_latitude: float,
    max_longitude: float,
    max_latitude: float,
    count: int,
) -> dict[str, object]:
    return {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [min_longitude, min_latitude],
                    [max_longitude, min_latitude],
                    [max_longitude, max_latitude],
                    [min_longitude, max_latitude],
                    [min_longitude, min_latitude],
                ]
            ],
        },
        "properties": {
            "layer_key": "raa-archaeology",
            "layer_label": "RAÄ archaeology density",
            "country": "Sweden",
            "count": count,
            "count_label": str(count),
        },
    }


def _admit_raa_density_fixture(root: Path, *, heritage_site_count: int) -> None:
    raw_features = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [14.0, 57.0]},
            "properties": {"antikvariskbedomningtyp_namn": "Fornlämning"},
        }
        for _ in range(heritage_site_count)
    ]
    _write_json(
        root / "raa" / "raw" / "publicerade_lamningar_centrumpunkt.geojson",
        {"type": "FeatureCollection", "features": raw_features},
    )
    _write_json(
        root / "raa" / "raw" / "publicerade_lamningar_centrumpunkt_summary.json",
        {
            "archived_feature_count": heritage_site_count,
            "heritage_site_count": heritage_site_count,
        },
    )
    _write_json(
        root / "raa" / "normalized" / "sweden_archaeology_layer.json",
        {
            "counts": {"fornlamning": heritage_site_count},
            "density_feature_count": 2,
        },
    )
    _write_json(
        root / "raa" / "review" / "spatiotemporal_review.json",
        {"release_status": "accepted", "reviewer_id": "test-reviewer"},
    )


def _svar_polygon_feature(
    *,
    record_id: str,
    name: str,
    latitude: float,
    longitude: float,
    lake_name_status: str = "official_register_name",
    area_km2: float = 1.5,
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
            "layer_key": "svar-lakes",
            "layer_label": "SMHI SVAR lake registry",
            "category": "Lake registry",
            "country": "SE",
            "record_id": record_id,
            "name": name,
            "register_name": name,
            "water_name": "",
            "fallback_name": "",
            "sjoid": record_id,
            "sj_uuid": f"uuid-{record_id}",
            "sj_vatten_id": f"water-{record_id}",
            "district": "test-district",
            "area_km2": area_km2,
            "lake_name_status": lake_name_status,
            "source_url": f"https://example.test/svar/{record_id}",
            "geometry_type": "Polygon",
        },
    }


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
