from __future__ import annotations

import csv
import json
from pathlib import Path
import tempfile

from bijux_pollenomics.adna import (
    AdnaChronology,
    AdnaCoordinate,
    AdnaLocalityIdentity,
    AdnaLocalitySummary,
)
from bijux_pollenomics.analysis import (
    build_lake_evidence_richness_geojson,
    build_sweden_lake_evidence_richness_report,
    render_lake_evidence_richness_markdown,
    write_lake_evidence_richness_band_csv,
    write_lake_evidence_richness_geojson,
    write_lake_evidence_richness_json,
    write_lake_evidence_richness_registry_csv,
    write_lake_evidence_richness_scenario_csv,
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
            time_start_bp=3500,
            time_end_bp=2500,
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
    time_start_bp: int | None = 3600,
    time_end_bp: int | None = 2400,
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


def test_build_sweden_lake_evidence_richness_report_ranks_multi_signal_lakes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_json(
            root / "neotoma" / "normalized" / "nordic_pollen_sites.geojson",
            {
                "type": "FeatureCollection",
                "features": [
                    _point_feature(
                        source="Neotoma",
                        layer_key="neotoma-pollen",
                        layer_label="Neotoma pollen sites",
                        category="Pollen",
                        country="Sweden",
                        record_id="n1",
                        name="Lake Alpha",
                        latitude=57.0,
                        longitude=14.0,
                        description="Lake basin with deep sequence.",
                    ),
                    _point_feature(
                        source="Neotoma",
                        layer_key="neotoma-pollen",
                        layer_label="Neotoma pollen sites",
                        category="Pollen",
                        country="Sweden",
                        record_id="n2",
                        name="Lake Gamma",
                        latitude=60.0,
                        longitude=16.0,
                        description="Small lake in upland valley.",
                    ),
                    _point_feature(
                        source="Neotoma",
                        layer_key="neotoma-pollen",
                        layer_label="Neotoma pollen sites",
                        category="Pollen",
                        country="Sweden",
                        record_id="n3",
                        name="Bog Beta",
                        latitude=58.0,
                        longitude=15.0,
                        description="Raised bog with peat accumulation.",
                    ),
                ],
            },
        )
        _write_json(
            root / "landclim" / "normalized" / "nordic_pollen_site_sequences.geojson",
            {
                "type": "FeatureCollection",
                "features": [
                    _point_feature(
                        source="LandClim",
                        layer_key="landclim-sites",
                        layer_label="LandClim pollen sites",
                        category="Pollen sequence",
                        country="Sweden",
                        record_id="l1",
                        name="Lake Alpha",
                        latitude=57.0005,
                        longitude=14.0005,
                        description="LandClim site metadata.",
                    ),
                    _point_feature(
                        source="LandClim",
                        layer_key="landclim-sites",
                        layer_label="LandClim pollen sites",
                        category="Pollen sequence",
                        country="Sweden",
                        record_id="l2",
                        name="Lake Gamma",
                        latitude=60.0,
                        longitude=16.0,
                        description="LandClim site metadata.",
                    ),
                ],
            },
        )
        _write_json(
            root / "sead" / "normalized" / "nordic_environmental_sites.geojson",
            {
                "type": "FeatureCollection",
                "features": [
                    _point_feature(
                        source="SEAD",
                        layer_key="sead-sites",
                        layer_label="SEAD sites",
                        category="Environmental archaeology",
                        country="Sweden",
                        record_id="s1",
                        name="Alpha archaeology 1",
                        latitude=57.03,
                        longitude=14.01,
                        description="Nearby archaeology.",
                    ),
                    _point_feature(
                        source="SEAD",
                        layer_key="sead-sites",
                        layer_label="SEAD sites",
                        category="Environmental archaeology",
                        country="Sweden",
                        record_id="s2",
                        name="Alpha archaeology 2",
                        latitude=57.04,
                        longitude=14.02,
                        description="Nearby archaeology.",
                    ),
                    _point_feature(
                        source="SEAD",
                        layer_key="sead-sites",
                        layer_label="SEAD sites",
                        category="Environmental archaeology",
                        country="Sweden",
                        record_id="s3",
                        name="Gamma archaeology",
                        latitude=60.12,
                        longitude=16.08,
                        description="More distant archaeology.",
                    ),
                ],
            },
        )
        _write_json(
            root / "raa" / "normalized" / "sweden_archaeology_density.geojson",
            {
                "type": "FeatureCollection",
                "features": [
                    _raa_feature(
                        min_longitude=13.5,
                        min_latitude=56.5,
                        max_longitude=14.5,
                        max_latitude=57.5,
                        count=1200,
                    ),
                    _raa_feature(
                        min_longitude=15.5,
                        min_latitude=59.5,
                        max_longitude=16.5,
                        max_latitude=60.5,
                        count=300,
                    ),
                ],
            },
        )

        report = build_sweden_lake_evidence_richness_report(
            context_root=root,
            human_localities=(
                _locality("Alpha human cluster", 57.02, 14.02, sample_count=8),
                _locality("Gamma human cluster", 60.12, 16.04, sample_count=2),
            ),
            animal_localities=(
                {
                    "locality": "Alpha horse",
                    "latitude": 57.05,
                    "longitude": 14.04,
                    "sample_count": 1,
                },
            ),
        )

        assert report.schema_version == "sweden-lake-evidence-richness.v2"
        assert report.candidate_count == 2
        assert [
            assessment.candidate.lake_name for assessment in report.assessments
        ] == [
            "Alpha",
            "Gamma",
        ]
        top = report.assessments[0]
        assert top.candidate.direct_pollen_source_count == 2
        assert top.aggregate_score > report.assessments[1].aggregate_score
        assert top.band_scores[0].human_adna_locality_count == 1
        assert top.band_scores[0].domesticated_animal_locality_count == 1
        assert top.band_scores[0].sead_site_count == 2
        assert top.band_scores[0].raa_density_site_count == 1200
        assert top.candidate.lake_label == "Alpha"
        assert top.candidate.ambiguity_flags == ()
        assert top.candidate.coordinate_resolution_method == "source_coordinate_medoid"
        assert top.candidate.latitude == 57.0005
        assert top.candidate.longitude == 14.0005
        assert top.candidate.representative_source_record == "landclim-sites:l1"


def test_build_sweden_lake_evidence_richness_report_prefers_svar_lakes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_json(
            root / "svar" / "normalized" / "sweden_lake_registry.geojson",
            {
                "type": "FeatureCollection",
                "features": [
                    _svar_polygon_feature(
                        record_id="1001",
                        name="Lake Alpha",
                        latitude=57.0,
                        longitude=14.0,
                        area_km2=2.3,
                    ),
                    _svar_polygon_feature(
                        record_id="1002",
                        name="Lake Gamma",
                        latitude=60.0,
                        longitude=16.0,
                        area_km2=1.1,
                    ),
                    _svar_polygon_feature(
                        record_id="1003",
                        name="Lake Delta",
                        latitude=63.0,
                        longitude=19.0,
                        area_km2=0.8,
                    ),
                ],
            },
        )
        _write_json(
            root / "neotoma" / "normalized" / "nordic_pollen_sites.geojson",
            {
                "type": "FeatureCollection",
                "features": [
                    _point_feature(
                        source="Neotoma",
                        layer_key="neotoma-pollen",
                        layer_label="Neotoma pollen sites",
                        category="Pollen",
                        country="Sweden",
                        record_id="n1",
                        name="Lake Alpha",
                        latitude=57.0005,
                        longitude=14.0005,
                        description="Lake basin with deep sequence.",
                    ),
                    _point_feature(
                        source="Neotoma",
                        layer_key="neotoma-pollen",
                        layer_label="Neotoma pollen sites",
                        category="Pollen",
                        country="Sweden",
                        record_id="n2",
                        name="Lake Gamma",
                        latitude=60.0005,
                        longitude=16.0004,
                        description="Lake basin with chronology.",
                    ),
                    _point_feature(
                        source="Neotoma",
                        layer_key="neotoma-pollen",
                        layer_label="Neotoma pollen sites",
                        category="Pollen",
                        country="Sweden",
                        record_id="n3",
                        name="Lake Delta",
                        latitude=63.0003,
                        longitude=19.0002,
                        description="Lake basin with chronology.",
                    ),
                ],
            },
        )
        _write_json(
            root / "landclim" / "normalized" / "nordic_pollen_site_sequences.geojson",
            {"type": "FeatureCollection", "features": []},
        )
        _write_json(
            root / "sead" / "normalized" / "nordic_environmental_sites.geojson",
            {
                "type": "FeatureCollection",
                "features": [
                    _point_feature(
                        source="SEAD",
                        layer_key="sead-sites",
                        layer_label="SEAD sites",
                        category="Environmental archaeology",
                        country="Sweden",
                        record_id="s1",
                        name="Alpha archaeology",
                        latitude=57.03,
                        longitude=14.01,
                        description="Nearby archaeology.",
                    ),
                    _point_feature(
                        source="SEAD",
                        layer_key="sead-sites",
                        layer_label="SEAD sites",
                        category="Environmental archaeology",
                        country="Sweden",
                        record_id="s2",
                        name="Gamma archaeology",
                        latitude=60.12,
                        longitude=16.08,
                        description="More distant archaeology.",
                    ),
                ],
            },
        )
        _write_json(
            root / "raa" / "normalized" / "sweden_archaeology_density.geojson",
            {
                "type": "FeatureCollection",
                "features": [
                    _raa_feature(
                        min_longitude=13.5,
                        min_latitude=56.5,
                        max_longitude=14.5,
                        max_latitude=57.5,
                        count=1200,
                    ),
                    _raa_feature(
                        min_longitude=15.5,
                        min_latitude=59.5,
                        max_longitude=16.5,
                        max_latitude=60.5,
                        count=300,
                    ),
                ],
            },
        )

        report = build_sweden_lake_evidence_richness_report(
            context_root=root,
            human_localities=(
                _locality("Alpha human cluster", 57.02, 14.02, sample_count=8),
                _locality("Gamma human cluster", 60.12, 16.04, sample_count=2),
            ),
            animal_localities=(
                {
                    "locality": "Alpha horse",
                    "latitude": 57.05,
                    "longitude": 14.04,
                    "sample_count": 1,
                },
            ),
        )

        assert report.candidate_count == 2
        assert [
            assessment.candidate.lake_name for assessment in report.assessments
        ] == [
            "Alpha",
            "Gamma",
        ]
        top = report.assessments[0]
        assert top.candidate.representative_source_record == "svar-lakes:1001"
        assert (
            top.candidate.coordinate_resolution_method
            == "svar_polygon_representative_point"
        )
        assert top.candidate.latitude == 57.0
        assert top.candidate.longitude == 14.0
        assert top.candidate.lake_registry_id == "1001"
        assert top.candidate.lake_registry_uuid == "uuid-1001"
        assert top.candidate.lake_water_identity == "water-1001"
        assert top.candidate.lake_name_status == "official_register_name"
        assert top.candidate.lake_area_km2 == 2.3
        assert top.candidate.lake_sampling_posture == "sampling_lake_candidate"
        assert top.candidate.lake_sampling_fit == 1.0
        assert top.aggregate_score > report.assessments[1].aggregate_score
        assert report.methodology["score_components"]["human_adna_signal"] == 0.59
        assert "ranking_decision_rule" in report.methodology

        registry_csv_path = root / "sweden_lake_evidence_registry.csv"
        geojson_path = root / "sweden_lake_evidence.geojson"
        write_lake_evidence_richness_registry_csv(registry_csv_path, report)
        write_lake_evidence_richness_geojson(geojson_path, report)

        with registry_csv_path.open(encoding="utf-8", newline="") as handle:
            registry_rows = list(csv.DictReader(handle))
        geojson = json.loads(geojson_path.read_text(encoding="utf-8"))

        assert registry_rows[0]["lake_registry_id"] == "1001"
        assert registry_rows[0]["lake_name_status"] == "official_register_name"
        assert registry_rows[0]["lake_sampling_posture"] == "sampling_lake_candidate"
        assert registry_rows[0]["lake_sampling_fit"] == "1.0"
        popup_rows = {
            row["label"]: row["value"]
            for row in geojson["features"][0]["properties"]["popup_rows"]
        }
        assert popup_rows["Lake registry id"] == "1001"
        assert popup_rows["Lake name status"] == "official_register_name"
        assert popup_rows["Sampling posture"] == "sampling_lake_candidate"


def test_svar_lake_candidates_prefer_direct_pollen_when_human_context_is_similar() -> (
    None
):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_json(
            root / "svar" / "normalized" / "sweden_lake_registry.geojson",
            {
                "type": "FeatureCollection",
                "features": [
                    _svar_polygon_feature(
                        record_id="2101",
                        name="Lake Alpha",
                        latitude=57.0000,
                        longitude=14.0000,
                        area_km2=1.4,
                    ),
                    _svar_polygon_feature(
                        record_id="2102",
                        name="Lake Beta",
                        latitude=57.0400,
                        longitude=14.0400,
                        area_km2=1.4,
                    ),
                ],
            },
        )
        _write_json(
            root / "neotoma" / "normalized" / "nordic_pollen_sites.geojson",
            {
                "type": "FeatureCollection",
                "features": [
                    _point_feature(
                        source="Neotoma",
                        layer_key="neotoma-pollen",
                        layer_label="Neotoma pollen sites",
                        category="Pollen",
                        country="Sweden",
                        record_id="n1",
                        name="Lake Alpha",
                        latitude=57.0003,
                        longitude=14.0002,
                        description="Direct lake-basin pollen support.",
                    ),
                    _point_feature(
                        source="Neotoma",
                        layer_key="neotoma-pollen",
                        layer_label="Neotoma pollen sites",
                        category="Pollen",
                        country="Sweden",
                        record_id="n2",
                        name="Lake Alpha",
                        latitude=57.0004,
                        longitude=14.0001,
                        description="Second direct pollen record.",
                    ),
                ],
            },
        )
        _write_json(
            root / "landclim" / "normalized" / "nordic_pollen_site_sequences.geojson",
            {"type": "FeatureCollection", "features": []},
        )
        _write_json(
            root / "sead" / "normalized" / "nordic_environmental_sites.geojson",
            {
                "type": "FeatureCollection",
                "features": [
                    _point_feature(
                        source="SEAD",
                        layer_key="sead-sites",
                        layer_label="SEAD sites",
                        category="Environmental archaeology",
                        country="Sweden",
                        record_id="s1",
                        name="Shared archaeology 1",
                        latitude=57.0200,
                        longitude=14.0200,
                        description="Shared archaeology support.",
                    ),
                    _point_feature(
                        source="SEAD",
                        layer_key="sead-sites",
                        layer_label="SEAD sites",
                        category="Environmental archaeology",
                        country="Sweden",
                        record_id="s2",
                        name="Shared archaeology 2",
                        latitude=57.0250,
                        longitude=14.0250,
                        description="Shared archaeology support.",
                    ),
                ],
            },
        )
        _write_json(
            root / "raa" / "normalized" / "sweden_archaeology_density.geojson",
            {
                "type": "FeatureCollection",
                "features": [
                    _raa_feature(
                        min_longitude=13.5,
                        min_latitude=56.5,
                        max_longitude=14.5,
                        max_latitude=57.5,
                        count=900,
                    ),
                ],
            },
        )

        report = build_sweden_lake_evidence_richness_report(
            context_root=root,
            human_localities=(
                _locality("Shared human cluster", 57.0200, 14.0200, sample_count=6),
            ),
            animal_localities=(),
        )

        assert report.candidate_count == 2
        assert report.assessments[0].candidate.lake_name == "Alpha"
        assert report.assessments[0].candidate.direct_pollen_source_count >= 1
        assert report.assessments[1].candidate.lake_name == "Beta"
        assert report.assessments[1].candidate.direct_pollen_source_count == 0


def test_svar_lake_candidates_prefer_direct_pollen_with_human_chronology_overlap() -> (
    None
):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_json(
            root / "svar" / "normalized" / "sweden_lake_registry.geojson",
            {
                "type": "FeatureCollection",
                "features": [
                    _svar_polygon_feature(
                        record_id="2201",
                        name="Lake Alpha",
                        latitude=57.0000,
                        longitude=14.0000,
                        area_km2=1.4,
                    ),
                    _svar_polygon_feature(
                        record_id="2202",
                        name="Lake Beta",
                        latitude=57.0400,
                        longitude=14.0400,
                        area_km2=1.4,
                    ),
                ],
            },
        )
        _write_json(
            root / "neotoma" / "normalized" / "nordic_pollen_sites.geojson",
            {
                "type": "FeatureCollection",
                "features": [
                    _point_feature(
                        source="Neotoma",
                        layer_key="neotoma-pollen",
                        layer_label="Neotoma pollen sites",
                        category="Pollen",
                        country="Sweden",
                        record_id="n1",
                        name="Lake Alpha",
                        latitude=57.0003,
                        longitude=14.0002,
                        description="Direct lake-basin pollen support.",
                        time_start_bp=3600,
                        time_end_bp=2400,
                    ),
                    _point_feature(
                        source="Neotoma",
                        layer_key="neotoma-pollen",
                        layer_label="Neotoma pollen sites",
                        category="Pollen",
                        country="Sweden",
                        record_id="n2",
                        name="Lake Beta",
                        latitude=57.0403,
                        longitude=14.0402,
                        description="Direct lake-basin pollen support.",
                        time_start_bp=900,
                        time_end_bp=100,
                    ),
                ],
            },
        )
        for relative_path in (
            root / "landclim" / "normalized" / "nordic_pollen_site_sequences.geojson",
            root / "sead" / "normalized" / "nordic_environmental_sites.geojson",
            root / "raa" / "normalized" / "sweden_archaeology_density.geojson",
        ):
            _write_json(relative_path, {"type": "FeatureCollection", "features": []})

        report = build_sweden_lake_evidence_richness_report(
            context_root=root,
            human_localities=(
                _locality("Shared human cluster", 57.0200, 14.0200, sample_count=6),
            ),
            animal_localities=(),
        )

        assert report.candidate_count == 2
        assert report.assessments[0].candidate.lake_name == "Alpha"
        assert report.assessments[0].candidate.direct_pollen_source_count == 1
        assert report.assessments[1].candidate.lake_name == "Beta"
        assert (
            report.assessments[0].candidate.direct_pollen_signal
            > report.assessments[1].candidate.direct_pollen_signal
        )


def test_svar_lake_candidates_prefer_sead_sites_with_human_chronology_overlap() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_json(
            root / "svar" / "normalized" / "sweden_lake_registry.geojson",
            {
                "type": "FeatureCollection",
                "features": [
                    _svar_polygon_feature(
                        record_id="2301",
                        name="Lake Alpha",
                        latitude=57.0000,
                        longitude=14.0000,
                        area_km2=1.4,
                    ),
                    _svar_polygon_feature(
                        record_id="2302",
                        name="Lake Beta",
                        latitude=58.0000,
                        longitude=15.0000,
                        area_km2=1.4,
                    ),
                ],
            },
        )
        _write_json(
            root / "neotoma" / "normalized" / "nordic_pollen_sites.geojson",
            {
                "type": "FeatureCollection",
                "features": [
                    _point_feature(
                        source="Neotoma",
                        layer_key="neotoma-pollen",
                        layer_label="Neotoma pollen sites",
                        category="Pollen",
                        country="Sweden",
                        record_id="n1",
                        name="Lake Alpha",
                        latitude=57.0002,
                        longitude=14.0001,
                        description="Direct lake-basin pollen support.",
                    ),
                    _point_feature(
                        source="Neotoma",
                        layer_key="neotoma-pollen",
                        layer_label="Neotoma pollen sites",
                        category="Pollen",
                        country="Sweden",
                        record_id="n2",
                        name="Lake Beta",
                        latitude=58.0002,
                        longitude=15.0001,
                        description="Direct lake-basin pollen support.",
                    ),
                ],
            },
        )
        _write_json(
            root / "landclim" / "normalized" / "nordic_pollen_site_sequences.geojson",
            {"type": "FeatureCollection", "features": []},
        )
        _write_json(
            root / "sead" / "normalized" / "nordic_environmental_sites.geojson",
            {
                "type": "FeatureCollection",
                "features": [
                    _point_feature(
                        source="SEAD",
                        layer_key="sead-sites",
                        layer_label="SEAD sites",
                        category="Environmental archaeology",
                        country="Sweden",
                        record_id="s1",
                        name="Alpha archaeology",
                        latitude=57.0100,
                        longitude=14.0100,
                        description="Nearby archaeology with overlapping chronology.",
                        time_start_bp=3400,
                        time_end_bp=2600,
                    ),
                    _point_feature(
                        source="SEAD",
                        layer_key="sead-sites",
                        layer_label="SEAD sites",
                        category="Environmental archaeology",
                        country="Sweden",
                        record_id="s2",
                        name="Beta archaeology",
                        latitude=58.0100,
                        longitude=15.0100,
                        description="Nearby archaeology without chronology overlap.",
                        time_start_bp=700,
                        time_end_bp=100,
                    ),
                ],
            },
        )
        _write_json(
            root / "raa" / "normalized" / "sweden_archaeology_density.geojson",
            {
                "type": "FeatureCollection",
                "features": [
                    _raa_feature(
                        min_longitude=13.5,
                        min_latitude=56.5,
                        max_longitude=14.5,
                        max_latitude=57.5,
                        count=400,
                    ),
                    _raa_feature(
                        min_longitude=14.5,
                        min_latitude=57.5,
                        max_longitude=15.5,
                        max_latitude=58.5,
                        count=400,
                    ),
                ],
            },
        )

        report = build_sweden_lake_evidence_richness_report(
            context_root=root,
            human_localities=(
                _locality("Alpha human cluster", 57.0200, 14.0200, sample_count=4),
                _locality("Beta human cluster", 58.0200, 15.0200, sample_count=4),
            ),
            animal_localities=(),
        )

        assert report.candidate_count == 2
        assert report.assessments[0].candidate.lake_name == "Alpha"
        alpha_band_20 = next(
            score
            for score in report.assessments[0].band_scores
            if score.radius_km == 20
        )
        beta_band_20 = next(
            score
            for score in report.assessments[1].band_scores
            if score.radius_km == 20
        )
        assert alpha_band_20.human_overlap_sead_site_count == 1
        assert beta_band_20.human_overlap_sead_site_count == 0


def test_svar_lake_candidates_exclude_engineered_and_wetland_names() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_json(
            root / "svar" / "normalized" / "sweden_lake_registry.geojson",
            {
                "type": "FeatureCollection",
                "features": [
                    _svar_polygon_feature(
                        record_id="3001",
                        name="Hornsjön",
                        latitude=57.0,
                        longitude=14.0,
                        area_km2=1.4,
                    ),
                    _svar_polygon_feature(
                        record_id="3002",
                        name="Kvarndammen",
                        latitude=57.02,
                        longitude=14.02,
                        area_km2=0.08,
                    ),
                    _svar_polygon_feature(
                        record_id="3003",
                        name="Frösslundamossen",
                        latitude=57.04,
                        longitude=14.04,
                        area_km2=0.12,
                    ),
                ],
            },
        )
        for relative_path in (
            root / "neotoma" / "normalized" / "nordic_pollen_sites.geojson",
            root / "landclim" / "normalized" / "nordic_pollen_site_sequences.geojson",
            root / "sead" / "normalized" / "nordic_environmental_sites.geojson",
            root / "raa" / "normalized" / "sweden_archaeology_density.geojson",
        ):
            _write_json(relative_path, {"type": "FeatureCollection", "features": []})

        report = build_sweden_lake_evidence_richness_report(
            context_root=root,
            human_localities=(
                _locality("Hornsjön cluster", 57.01, 14.01, sample_count=4),
            ),
            animal_localities=(),
        )

        assert report.candidate_count == 1
        assert [assessment.candidate.lake_name for assessment in report.assessments] == [
            "Hornsjön"
        ]


def test_svar_lake_candidates_flag_duplicate_registry_names() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_json(
            root / "svar" / "normalized" / "sweden_lake_registry.geojson",
            {
                "type": "FeatureCollection",
                "features": [
                    _svar_polygon_feature(
                        record_id="2001",
                        name="Lillsjön",
                        latitude=57.93223,
                        longitude=16.38903,
                    ),
                    _svar_polygon_feature(
                        record_id="2002",
                        name="Lillsjön",
                        latitude=57.08333,
                        longitude=12.53333,
                        lake_name_status="water_surface_name",
                    ),
                ],
            },
        )
        _write_json(
            root / "neotoma" / "normalized" / "nordic_pollen_sites.geojson",
            {"type": "FeatureCollection", "features": []},
        )
        _write_json(
            root / "landclim" / "normalized" / "nordic_pollen_site_sequences.geojson",
            {"type": "FeatureCollection", "features": []},
        )
        _write_json(
            root / "sead" / "normalized" / "nordic_environmental_sites.geojson",
            {"type": "FeatureCollection", "features": []},
        )
        _write_json(
            root / "raa" / "normalized" / "sweden_archaeology_density.geojson",
            {"type": "FeatureCollection", "features": []},
        )

        report = build_sweden_lake_evidence_richness_report(
            context_root=root,
            human_localities=(
                _locality("Lillsjön east cluster", 57.94, 16.39, sample_count=2),
                _locality("Lillsjön west cluster", 57.09, 12.54, sample_count=1),
            ),
            animal_localities=(),
        )

        assert report.candidate_count == 2
        labels = [assessment.candidate.lake_label for assessment in report.assessments]
        assert all(label.startswith("Lillsjön (") for label in labels)
        duplicate_named = next(
            assessment.candidate
            for assessment in report.assessments
            if assessment.candidate.lake_registry_id == "2002"
        )
        assert "duplicate_sweden_name" in duplicate_named.ambiguity_flags
        assert "non_official_registry_name" not in duplicate_named.ambiguity_flags


def test_lake_candidates_do_not_merge_different_nearby_lakes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_json(
            root / "neotoma" / "normalized" / "nordic_pollen_sites.geojson",
            {
                "type": "FeatureCollection",
                "features": [
                    _point_feature(
                        source="Neotoma",
                        layer_key="neotoma-pollen",
                        layer_label="Neotoma pollen sites",
                        category="Pollen",
                        country="Sweden",
                        record_id="n1",
                        name="Bjäresjösjön",
                        latitude=55.4560,
                        longitude=13.7560,
                        description="Lake basin with chronology.",
                    ),
                    _point_feature(
                        source="Neotoma",
                        layer_key="neotoma-pollen",
                        layer_label="Neotoma pollen sites",
                        category="Pollen",
                        country="Sweden",
                        record_id="n2",
                        name="Bjärsjöholmssjön",
                        latitude=55.4520,
                        longitude=13.7818,
                        description="Nearby but distinct lake basin.",
                    ),
                ],
            },
        )
        _write_json(
            root / "landclim" / "normalized" / "nordic_pollen_site_sequences.geojson",
            {"type": "FeatureCollection", "features": []},
        )
        _write_json(
            root / "sead" / "normalized" / "nordic_environmental_sites.geojson",
            {"type": "FeatureCollection", "features": []},
        )
        _write_json(
            root / "raa" / "normalized" / "sweden_archaeology_density.geojson",
            {"type": "FeatureCollection", "features": []},
        )

        report = build_sweden_lake_evidence_richness_report(
            context_root=root,
            human_localities=(),
            animal_localities=(),
        )

        assert report.candidate_count == 2
        assert {
            assessment.candidate.lake_name for assessment in report.assessments
        } == {
            "Bjäresjösjön",
            "Bjärsjöholmssjön",
        }


def test_lake_candidates_flag_duplicate_names_and_source_position_notes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_json(
            root / "neotoma" / "normalized" / "nordic_pollen_sites.geojson",
            {
                "type": "FeatureCollection",
                "features": [
                    _point_feature(
                        source="Neotoma",
                        layer_key="neotoma-pollen",
                        layer_label="Neotoma pollen sites",
                        category="Pollen",
                        country="Sweden",
                        record_id="3288",
                        name="M. Lommesjön",
                        latitude=56.2000,
                        longitude=13.1000,
                        description="Lake basin with uncertain publication position.",
                    ),
                    _point_feature(
                        source="Neotoma",
                        layer_key="neotoma-pollen",
                        layer_label="Neotoma pollen sites",
                        category="Pollen",
                        country="Sweden",
                        record_id="31818",
                        name="Lillsjön",
                        latitude=57.93223,
                        longitude=16.38903,
                        description="Lake basin in Småland.",
                    ),
                    _point_feature(
                        source="Neotoma",
                        layer_key="neotoma-pollen",
                        layer_label="Neotoma pollen sites",
                        category="Pollen",
                        country="Sweden",
                        record_id="3238",
                        name="Lillsjön",
                        latitude=57.08333,
                        longitude=12.53333,
                        description="Lake basin in Halland.",
                    ),
                ],
            },
        )
        _write_json(
            root / "neotoma" / "raw" / "neotoma_pollen_sites.json",
            {
                "generated_on": "2026-06-22",
                "source": "Neotoma",
                "datasettype": "pollen",
                "site_count": 1,
                "dataset_count": 1,
                "rows": [
                    {
                        "siteid": 3288,
                        "sitename": "M. Lommesjön",
                        "notes": (
                            "We assume that the site is Lake Lommesjön. "
                            "However, another lake also called Lommesjön is found "
                            "approx. 1 km NE and the position is not clear in the publication."
                        ),
                    }
                ],
            },
        )
        _write_json(
            root / "landclim" / "normalized" / "nordic_pollen_site_sequences.geojson",
            {"type": "FeatureCollection", "features": []},
        )
        _write_json(
            root / "sead" / "normalized" / "nordic_environmental_sites.geojson",
            {"type": "FeatureCollection", "features": []},
        )
        _write_json(
            root / "raa" / "normalized" / "sweden_archaeology_density.geojson",
            {"type": "FeatureCollection", "features": []},
        )

        report = build_sweden_lake_evidence_richness_report(
            context_root=root,
            human_localities=(),
            animal_localities=(),
        )

        labels = {assessment.candidate.lake_label for assessment in report.assessments}
        assert any(label.startswith("Lillsjön (") for label in labels)
        lommesjon = next(
            assessment.candidate
            for assessment in report.assessments
            if assessment.candidate.lake_name == "Lommesjön"
        )
        assert "source_position_note" in lommesjon.ambiguity_flags
        assert "position is not clear" in lommesjon.ambiguity_note


def test_lake_evidence_richness_packets_write_reviewable_outputs() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_json(
            root / "neotoma" / "normalized" / "nordic_pollen_sites.geojson",
            {
                "type": "FeatureCollection",
                "features": [
                    _point_feature(
                        source="Neotoma",
                        layer_key="neotoma-pollen",
                        layer_label="Neotoma pollen sites",
                        category="Pollen",
                        country="Sweden",
                        record_id="n1",
                        name="Lake Alpha",
                        latitude=57.0,
                        longitude=14.0,
                        description="Lake basin with deep sequence.",
                    ),
                ],
            },
        )
        _write_json(
            root / "landclim" / "normalized" / "nordic_pollen_site_sequences.geojson",
            {"type": "FeatureCollection", "features": []},
        )
        _write_json(
            root / "sead" / "normalized" / "nordic_environmental_sites.geojson",
            {"type": "FeatureCollection", "features": []},
        )
        _write_json(
            root / "raa" / "normalized" / "sweden_archaeology_density.geojson",
            {"type": "FeatureCollection", "features": []},
        )

        report = build_sweden_lake_evidence_richness_report(
            context_root=root,
            human_localities=(
                _locality("Alpha human cluster", 57.02, 14.02, sample_count=3),
            ),
            animal_localities=(),
        )
        json_path = root / "lake_evidence.json"
        band_csv_path = root / "lake_evidence_bands.csv"
        registry_csv_path = root / "lake_evidence_registry.csv"
        scenario_csv_path = root / "lake_evidence_scenarios.csv"
        geojson_path = root / "lake_evidence.geojson"
        markdown = render_lake_evidence_richness_markdown(report)
        write_lake_evidence_richness_json(json_path, report)
        write_lake_evidence_richness_band_csv(band_csv_path, report)
        write_lake_evidence_richness_registry_csv(registry_csv_path, report)
        write_lake_evidence_richness_scenario_csv(scenario_csv_path, report)
        write_lake_evidence_richness_geojson(geojson_path, report)

        payload = json.loads(json_path.read_text(encoding="utf-8"))
        with band_csv_path.open(encoding="utf-8", newline="") as handle:
            band_rows = list(csv.DictReader(handle))
        with registry_csv_path.open(encoding="utf-8", newline="") as handle:
            registry_rows = list(csv.DictReader(handle))
        with scenario_csv_path.open(encoding="utf-8", newline="") as handle:
            scenario_rows = list(csv.DictReader(handle))
        geojson = json.loads(geojson_path.read_text(encoding="utf-8"))

        assert payload["candidate_count"] == 1
        assert len(band_rows) == len(report.radii_km)
        assert len(registry_rows) == 1
        assert len(scenario_rows) == len(report.radii_km) + 2
        assert any(
            row["scenario_key"] == "fieldwork_shortlist" for row in scenario_rows
        )
        assert geojson["type"] == "FeatureCollection"
        assert geojson["features"][0]["properties"]["name"] == "Alpha"
        assert markdown.startswith("# Sweden lake evidence richness")
        assert "## Interpretation guardrails" in markdown
        assert "## 10 km Ranking" in markdown
        assert "Lake registry id" in markdown
        assert "not_available" in markdown
        assert "spatial inventory only" in markdown
        assert (
            "https://www.google.com/maps/search/?api=1&query=57.000000,14.000000"
            in markdown
        )
        assert registry_rows[0]["google_maps_url"].startswith(
            "https://www.google.com/maps/search/"
        )
        assert registry_rows[0]["lake_registry_id"] == ""
        assert registry_rows[0]["representative_source_record"] == "neotoma-pollen:n1"


def test_lake_evidence_geojson_matches_report_candidate_count() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_json(
            root / "neotoma" / "normalized" / "nordic_pollen_sites.geojson",
            {
                "type": "FeatureCollection",
                "features": [
                    _point_feature(
                        source="Neotoma",
                        layer_key="neotoma-pollen",
                        layer_label="Neotoma pollen sites",
                        category="Pollen",
                        country="Sweden",
                        record_id="n1",
                        name="Lake Alpha",
                        latitude=57.0,
                        longitude=14.0,
                        description="Lake basin with deep sequence.",
                    ),
                    _point_feature(
                        source="Neotoma",
                        layer_key="neotoma-pollen",
                        layer_label="Neotoma pollen sites",
                        category="Pollen",
                        country="Sweden",
                        record_id="n2",
                        name="Lake Beta",
                        latitude=58.0,
                        longitude=15.0,
                        description="Lake basin with deep sequence.",
                    ),
                ],
            },
        )
        _write_json(
            root / "landclim" / "normalized" / "nordic_pollen_site_sequences.geojson",
            {"type": "FeatureCollection", "features": []},
        )
        _write_json(
            root / "sead" / "normalized" / "nordic_environmental_sites.geojson",
            {"type": "FeatureCollection", "features": []},
        )
        _write_json(
            root / "raa" / "normalized" / "sweden_archaeology_density.geojson",
            {"type": "FeatureCollection", "features": []},
        )

        report = build_sweden_lake_evidence_richness_report(
            context_root=root,
            human_localities=(),
            animal_localities=(),
        )
        geojson = build_lake_evidence_richness_geojson(report)

        assert len(geojson["features"]) == report.candidate_count
