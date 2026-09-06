from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pytest
from bijux_pollenomics.reporting import (
    generate_multi_country_map,
)

from ..fixtures.aadr import write_anno
from ..fixtures.files import write_csv
from ..fixtures.lake_evidence import lake_scenario_row
from ..static_assets import read_static_atlas_payload_text

pytestmark = pytest.mark.generated_artifacts


class CountryReportTests(unittest.TestCase):
    def test_generate_multi_country_map_can_publish_optional_sweden_lake_layers(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            output = Path(tmp) / "docs" / "report" / "regions" / "nordic"
            scenario_csv = (
                Path(tmp)
                / "docs"
                / "report"
                / "countries"
                / "sweden"
                / "sweden_lake_evidence_richness_v62.0_scenarios.csv"
            )
            lake_markdown = (
                Path(tmp)
                / "docs"
                / "report"
                / "countries"
                / "sweden"
                / "sweden_lake_evidence_richness_v62.0.md"
            )
            write_anno(
                root / "ho" / "v62.0_HO_public.anno",
                [
                    "SE1\tSE1\tSweden_Group\tLake Alpha\tSweden\t57.02\t14.02\tPaperA\t2022\t500 BCE\t2450\tHO\tF",
                ],
            )
            write_csv(
                scenario_csv,
                fieldnames=[
                    "scenario_key",
                    "scenario_label",
                    "radius_km",
                    "rank",
                    "score",
                    "lake_name",
                    "lake_label",
                    "lake_token",
                    "latitude",
                    "longitude",
                    "google_maps_url",
                    "aggregate_rank",
                    "aggregate_score",
                    "scenario_top20_presence_count",
                    "scenario_top20_labels",
                    "lake_registry_id",
                    "lake_name_status",
                    "lake_area_km2",
                    "lake_sampling_posture",
                    "lake_sampling_fit",
                    "lake_sampling_notes",
                    "duplicate_name_count",
                    "coordinate_spread_km",
                    "ambiguity_flags",
                    "ambiguity_note",
                    "direct_pollen_temporal_evidence",
                ],
                rows=[
                    lake_scenario_row("aggregate", "Aggregate", "1"),
                    lake_scenario_row("consensus", "Consensus", "1"),
                    lake_scenario_row(
                        "fieldwork_shortlist", "Fieldwork shortlist", "1"
                    ),
                    lake_scenario_row("radius_10km", "10 km", "1"),
                    lake_scenario_row("radius_20km", "20 km", "1"),
                    lake_scenario_row("radius_30km", "30 km", "1"),
                    lake_scenario_row("radius_40km", "40 km", "1"),
                    lake_scenario_row("radius_50km", "50 km", "1"),
                ],
            )
            lake_markdown.parent.mkdir(parents=True, exist_ok=True)
            lake_markdown.write_text(
                "# Sweden lake evidence richness\n",
                encoding="utf-8",
            )

            generate_multi_country_map(
                version_dir=root,
                countries=["Sweden"],
                output_dir=output,
                title="Nordic Evidence Atlas",
                slug="nordic-atlas",
            )

            atlas_payload_text = read_static_atlas_payload_text(output, "nordic-atlas")
            for label in (
                "Sweden lake aggregate top 40",
                "Sweden lake consensus top 40",
                "Sweden lake fieldwork shortlist",
                "Sweden lake 10 km top 40",
                "Sweden lake 20 km top 40",
                "Sweden lake 30 km top 40",
                "Sweden lake 40 km top 40",
                "Sweden lake 50 km top 40",
            ):
                self.assertIn(label, atlas_payload_text)
            self.assertIn('"default_enabled":false', atlas_payload_text)
            self.assertIn('"applies_time_filter":true', atlas_payload_text)
            self.assertIn('"time_start_bp":3600', atlas_payload_text)
            self.assertIn("neotoma-pollen:alpha", atlas_payload_text)
            self.assertIn("Optional Sweden lake ranking overlay", atlas_payload_text)
            self.assertIn(
                "sweden_lake_evidence_richness_v62.0_scenarios.csv",
                atlas_payload_text,
            )
