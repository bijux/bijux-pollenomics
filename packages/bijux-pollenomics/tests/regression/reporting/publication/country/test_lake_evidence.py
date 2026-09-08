from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import pytest

from bijux_pollenomics.reporting import (
    generate_country_report,
)

from ..fixtures.aadr import write_anno
from ..fixtures.files import write_json

pytestmark = pytest.mark.generated_artifacts


class CountryReportTests(unittest.TestCase):
    def test_generate_country_report_writes_sweden_lake_evidence_richness_outputs(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            output = Path(tmp) / "docs" / "report" / "sweden"
            context_root = Path(tmp) / "context"
            write_anno(
                root / "ho" / "v62.0_HO_public.anno",
                [
                    "SE1\tSE1\tSweden_Group\tAlpha Lake\tSweden\t57.02\t14.02\tPaperA\t2022\t500 BCE\t2450\tHO\tF",
                ],
            )
            write_json(
                context_root / "neotoma" / "normalized" / "nordic_pollen_sites.geojson",
                {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "geometry": {
                                "type": "Point",
                                "coordinates": [14.0, 57.0],
                            },
                            "properties": {
                                "source": "Neotoma",
                                "layer_key": "neotoma-pollen",
                                "layer_label": "Neotoma pollen sites",
                                "category": "Pollen",
                                "country": "Sweden",
                                "record_id": "alpha",
                                "name": "Lake Alpha",
                                "geometry_type": "Point",
                                "subtitle": "Pollen",
                                "description": "Lake basin with chronology.",
                                "source_url": "https://example.com",
                                "record_count": 1,
                                "time_start_bp": 3000,
                                "time_end_bp": 2000,
                                "time_mean_bp": 2500,
                                "time_label": "2000-3000 BP",
                                "popup_rows": [],
                            },
                        }
                    ],
                },
            )
            write_json(
                context_root
                / "landclim"
                / "normalized"
                / "nordic_pollen_site_sequences.geojson",
                {"type": "FeatureCollection", "features": []},
            )
            write_json(
                context_root
                / "sead"
                / "normalized"
                / "nordic_environmental_sites.geojson",
                {"type": "FeatureCollection", "features": []},
            )
            write_json(
                context_root
                / "raa"
                / "normalized"
                / "sweden_archaeology_density.geojson",
                {"type": "FeatureCollection", "features": []},
            )

            generate_country_report(
                root,
                "Sweden",
                output,
                context_root=context_root,
            )

            self.assertTrue(
                (output / "sweden_lake_evidence_richness_v62.0.json").exists()
            )
            self.assertTrue(
                (output / "sweden_lake_evidence_richness_v62.0_registry.csv").exists()
            )
            self.assertTrue(
                (output / "sweden_lake_evidence_richness_v62.0_scenarios.csv").exists()
            )
            self.assertTrue(
                (output / "sweden_lake_evidence_richness_v62.0_bands.csv").exists()
            )
            self.assertTrue(
                (output / "sweden_lake_evidence_richness_v62.0.geojson").exists()
            )
            self.assertTrue(
                (output / "sweden_lake_evidence_richness_v62.0_map.html").exists()
            )
            self.assertTrue(
                (output / "sweden_lake_evidence_richness_v62.0.md").exists()
            )
            self.assertTrue(
                (output / "_map_assets" / "leaflet" / "leaflet.js").exists()
            )
            readme_text = (output / "README.md").read_text(encoding="utf-8")
            self.assertIn("## Lake Evidence Richness", readme_text)
            self.assertIn(
                "sweden_lake_evidence_richness_v62.0.json",
                readme_text,
            )
            self.assertIn(
                "sweden_lake_evidence_richness_v62.0_map.html",
                readme_text,
            )
            self.assertIn(
                "zero-interval context layers remain spatial evidence only",
                readme_text,
            )
