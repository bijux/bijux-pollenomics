from __future__ import annotations

import csv
import json
import tempfile
from pathlib import Path

from bijux_pollenomics.analysis import (
    build_lake_archaeology_sensitivity_payload,
    build_sweden_lake_evidence_richness_report,
    write_lake_evidence_richness_geojson,
    write_lake_evidence_richness_registry_csv,
)

from .support import (
    _admit_raa_density_fixture,
    _locality,
    _point_feature,
    _raa_feature,
    _svar_polygon_feature,
    _write_json,
)


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
                        count=12,
                    ),
                    _raa_feature(
                        min_longitude=15.5,
                        min_latitude=59.5,
                        max_longitude=16.5,
                        max_latitude=60.5,
                        count=3,
                    ),
                ],
            },
        )
        _admit_raa_density_fixture(root, heritage_site_count=15)

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
        assert top.band_scores[0].raa_density_site_count == 12
        assert report.methodology["raa_density_authority"] == {
            "admitted": True,
            "reason_codes": [],
            "archived_feature_count": 15,
            "heritage_site_count": 15,
            "density_site_count": 15,
            "density_feature_count": 2,
            "reviewer_id": "test-reviewer",
        }
        assert top.candidate.lake_label == "Alpha"
        assert top.candidate.ambiguity_flags == ()
        assert top.candidate.coordinate_resolution_method == "source_coordinate_medoid"
        assert top.candidate.latitude == 57.0005
        assert top.candidate.longitude == 14.0005
        assert top.candidate.representative_source_record == "landclim-sites:l1"
        sensitivity = build_lake_archaeology_sensitivity_payload(report)
        alpha_baseline = next(
            row
            for row in sensitivity["rows"]
            if row["profile_key"] == "baseline" and row["lake_label"] == "Alpha"
        )
        assert alpha_baseline["sead_temporal_context_window_count"] == 1
        assert alpha_baseline["sead_temporal_context_record_count"] == 2
        assert alpha_baseline["temporal_context_windows"] == "late_holocene"


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
