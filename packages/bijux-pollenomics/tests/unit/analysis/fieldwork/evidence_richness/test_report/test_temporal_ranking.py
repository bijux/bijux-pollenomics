from __future__ import annotations

import tempfile
from pathlib import Path

from bijux_pollenomics.analysis import (
    build_sweden_lake_evidence_richness_report,
)

from .support import (
    _locality,
    _point_feature,
    _raa_feature,
    _svar_polygon_feature,
    _write_json,
)


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
                        time_start_bp=2400,
                        time_end_bp=3600,
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
                        time_start_bp=100,
                        time_end_bp=900,
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
                        time_start_bp=2600,
                        time_end_bp=3400,
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
                        time_start_bp=100,
                        time_end_bp=700,
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
