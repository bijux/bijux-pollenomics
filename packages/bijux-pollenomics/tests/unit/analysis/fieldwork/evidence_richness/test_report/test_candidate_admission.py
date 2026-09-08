from __future__ import annotations

from pathlib import Path
import tempfile

from bijux_pollenomics.analysis import (
    build_sweden_lake_evidence_richness_report,
    render_lake_evidence_richness_markdown,
)

from .support import (
    _locality,
    _point_feature,
    _svar_polygon_feature,
    _write_json,
)


def test_lake_evidence_refuses_orphaned_svar_review_subset() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_json(
            root / "svar" / "review" / "sweden_lake_candidate_registry.geojson",
            {
                "type": "FeatureCollection",
                "features": [
                    _svar_polygon_feature(
                        record_id="orphan-1001",
                        name="Lake Orphan",
                        latitude=57.0,
                        longitude=14.0,
                        area_km2=2.3,
                    )
                ],
            },
        )

        report = build_sweden_lake_evidence_richness_report(
            context_root=root,
            human_localities=(),
            animal_localities=(),
        )
        markdown = render_lake_evidence_richness_markdown(report)

        assert report.candidate_count == 0
        assert report.assessments == ()
        assert report.methodology["availability_status"] == "blocked"
        assert report.methodology["refusal_reason"] == "governing_svar_registry_missing"
        assert report.methodology["derived_subset_admitted"] is False
        assert "contains `0` admitted candidates" in markdown
        assert "`governing_svar_registry_missing`" in markdown
        assert "No derived review subset is promoted" in markdown


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
        assert [
            assessment.candidate.lake_name for assessment in report.assessments
        ] == ["Hornsjön"]


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
