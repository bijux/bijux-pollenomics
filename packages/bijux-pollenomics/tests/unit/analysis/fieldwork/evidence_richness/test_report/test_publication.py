from __future__ import annotations

import csv
from dataclasses import replace
import json
from pathlib import Path
import tempfile

from bijux_pollenomics.analysis import (
    build_lake_archaeology_sensitivity_payload,
    build_lake_evidence_richness_geojson,
    build_sweden_lake_evidence_richness_report,
    render_lake_archaeology_sensitivity_markdown,
    render_lake_evidence_richness_markdown,
    write_lake_evidence_richness_band_csv,
    write_lake_evidence_richness_geojson,
    write_lake_evidence_richness_json,
    write_lake_evidence_richness_registry_csv,
    write_lake_evidence_richness_scenario_csv,
)

from .support import (
    _locality,
    _point_feature,
    _write_json,
)


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
            root / "neotoma" / "review" / "temporal_review.json",
            {
                "coverage_summary": {
                    "chronology_capture_posture": "bp_site_spans_without_chronology_rows"
                }
            },
        )
        _write_json(
            root / "sead" / "normalized" / "nordic_environmental_sites.geojson",
            {"type": "FeatureCollection", "features": []},
        )
        _write_json(
            root / "sead" / "review" / "temporal_review.json",
            {"inventory_summary": {"temporal_capture_posture": "site_inventory_only"}},
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
        report_without_identity_thresholds = replace(
            report,
            methodology={**report.methodology, "identity_diagnostics": {}},
        )
        fallback_markdown = render_lake_evidence_richness_markdown(
            report_without_identity_thresholds
        )
        archaeology_sensitivity = build_lake_archaeology_sensitivity_payload(report)
        archaeology_markdown = render_lake_archaeology_sensitivity_markdown(
            archaeology_sensitivity
        )
        empty_archaeology_markdown = render_lake_archaeology_sensitivity_markdown(
            {**archaeology_sensitivity, "rows": []}
        )
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
        assert "cleaned-name matching within not recorded km" in fallback_markdown
        assert len(band_rows) == len(report.radii_km)
        assert len(registry_rows) == 1
        assert len(scenario_rows) == len(report.radii_km) + 2
        assert any(
            row["scenario_key"] == "fieldwork_shortlist" for row in scenario_rows
        )
        assert geojson["type"] == "FeatureCollection"
        assert geojson["features"][0]["properties"]["name"] == "Alpha"
        assert geojson["features"][0]["properties"]["time_start_bp"] == 1001
        assert geojson["features"][0]["properties"]["time_end_bp"] == 3000
        assert (
            geojson["features"][0]["properties"]["temporal_semantics"]["evidence_class"]
            == "nearby_lake_context_summary"
        )
        assert markdown.startswith("# Sweden lake evidence richness")
        assert len(archaeology_sensitivity["profiles"]) == 3
        assert all(
            abs(sum(profile["weights"].values()) - 1.0) < 0.000001
            for profile in archaeology_sensitivity["profiles"]
        )
        assert "Why The Baseline Is 0.07" in archaeology_markdown
        assert "RAÄ density alone" in archaeology_markdown
        assert empty_archaeology_markdown.endswith("\n")
        assert not empty_archaeology_markdown.endswith("\n\n")
        assert "## Interpretation guardrails" in markdown
        assert "1/1 ranked lakes have numeric navigation context" in markdown
        assert "Nearby time context is not lake chronology" in markdown
        assert "## 10 km Ranking" in markdown
        assert "Lake registry id" in markdown
        assert "not_available" in markdown
        assert "no checked-in records" in markdown
        assert "chronology rows absent in checked-in raw capture" in markdown
        assert "- Sampling note:" not in markdown
        assert (
            "https://www.google.com/maps/search/?api=1&query=57.000000,14.000000"
            in markdown
        )
        assert registry_rows[0]["google_maps_url"].startswith(
            "https://www.google.com/maps/search/"
        )
        assert registry_rows[0]["lake_registry_id"] == ""
        assert registry_rows[0]["representative_source_record"] == "neotoma-pollen:n1"
        registry_temporal_evidence = json.loads(
            registry_rows[0]["direct_pollen_temporal_evidence"]
        )
        assert registry_temporal_evidence[0]["source_record"] == "neotoma-pollen:n1"
        assert registry_temporal_evidence[0]["time_start_bp"] == 2400
        assert registry_temporal_evidence[0]["time_end_bp"] == 3600
        scenario_temporal_evidence = json.loads(
            scenario_rows[0]["direct_pollen_temporal_evidence"]
        )
        assert scenario_temporal_evidence == registry_temporal_evidence
        context_evidence = json.loads(registry_rows[0]["temporal_context_evidence"])
        assert {row["source_layer_key"] for row in context_evidence} == {
            "human-adna",
            "neotoma-pollen",
        }
        assert all(
            row["evidence_role"] == "nearby_temporal_context"
            for row in context_evidence
        )
        assert payload["methodology"]["temporal_navigation"] == {
            "candidate_count": 1,
            "candidate_with_numeric_context_count": 1,
            "candidate_with_direct_numeric_pollen_count": 1,
            "context_summary_count": 2,
            "context_source_layer_counts": {
                "human-adna": 1,
                "neotoma-pollen": 1,
            },
            "context_window_counts": {"late_holocene": 2},
            "context_radius_km": 50,
            "interpretation_rule": (
                "Temporal context summaries support time navigation for the ranked "
                "lake set. They remain explicitly separate from direct lake pollen "
                "chronology."
            ),
        }


def test_source_spatiotemporal_registry_does_not_override_scoped_counts() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_json(
            root / "landclim" / "normalized" / "nordic_pollen_site_sequences.geojson",
            {
                "type": "FeatureCollection",
                "features": [
                    _point_feature(
                        source="LandClim",
                        layer_key="landclim-sites",
                        layer_label="LandClim pollen sites",
                        category="Pollen",
                        country="Sweden",
                        record_id="l1",
                        name="Lake Beta",
                        latitude=58.0,
                        longitude=15.0,
                        description="Sequence-backed lake context.",
                    ),
                ],
            },
        )
        _write_json(
            root / "neotoma" / "normalized" / "nordic_pollen_sites.geojson",
            {"type": "FeatureCollection", "features": []},
        )
        _write_json(
            root / "sead" / "normalized" / "nordic_environmental_sites.geojson",
            {"type": "FeatureCollection", "features": []},
        )
        _write_json(
            root / "source_spatiotemporal_posture_registry.json",
            {
                "rows": [
                    {
                        "source_key": "landclim",
                        "temporal_support_note": (
                            "Checked-in LandClim sequence points carry numeric BP "
                            "windows in the normalized repository layer."
                        ),
                        "distance_scoring_note": (
                            "Use LandClim to strengthen pollen context around lakes."
                        ),
                        "record_count": 99,
                        "numeric_interval_record_count": 88,
                    }
                ]
            },
        )

        report = build_sweden_lake_evidence_richness_report(
            context_root=root,
            human_localities=(),
            animal_localities=(),
        )

        landclim_summary = report.methodology["source_temporal_coverage"][
            "landclim_pollen"
        ]
        assert landclim_summary["record_count"] == 1
        assert landclim_summary["numeric_interval_record_count"] == 1


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
