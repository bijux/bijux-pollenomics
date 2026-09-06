from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pytest
from bijux_pollenomics.reporting import (
    generate_country_report,
)

from ..fixtures.aadr import write_anno
from ..fixtures.animal_adna import write_tracked_animal_species

pytestmark = pytest.mark.generated_artifacts


class CountryReportTests(unittest.TestCase):
    def test_generate_country_report_can_publish_country_animal_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            output = Path(tmp) / "docs" / "report" / "sweden"
            context_root = Path(tmp) / "data"
            write_anno(
                root / "ho" / "v62.0_HO_public.anno",
                [
                    "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tHO\tF",
                ],
            )
            write_tracked_animal_species(
                context_root / "adna" / "species" / "ovis_aries",
                latin_name="Ovis aries",
                common_name="sheep",
                locality="Uppland sheep lead",
                political_entity="Sweden",
                project_accession="PRJEB59481",
                support_class="accepted",
                product_role="domesticated_core",
                nordic_inclusion=True,
                chronology_bucket="1001-3000 BP",
                paper_title="Baltic short-tailed sheep aDNA",
                paper_doi="10.1000/sheep",
            )

            generate_country_report(root, "Sweden", output, context_root=context_root)

            self.assertTrue((output / "sweden_animal_adna_v62.0_summary.json").exists())
            self.assertTrue((output / "sweden_animal_adna_v62.0_samples.csv").exists())
            self.assertTrue((output / "sweden_animal_adna_v62.0_samples.md").exists())
            self.assertTrue((output / "sweden_animal_adna_v62.0_species.csv").exists())
            self.assertTrue(
                (output / "sweden_animal_adna_v62.0_localities.geojson").exists()
            )
            self.assertTrue((output / "sweden_animal_adna_v62.0_citations.md").exists())
            self.assertTrue((output / "sweden_animal_adna_v62.0_warnings.md").exists())
            summary = json.loads(
                (output / "sweden_aadr_v62.0_summary.json").read_text(encoding="utf-8")
            )
            animal_summary = json.loads(
                (output / "sweden_animal_adna_v62.0_summary.json").read_text(
                    encoding="utf-8"
                )
            )
            sample_rows_markdown = (
                output / "sweden_animal_adna_v62.0_samples.md"
            ).read_text(encoding="utf-8")
            citations_markdown = (
                output / "sweden_animal_adna_v62.0_citations.md"
            ).read_text(encoding="utf-8")
            warnings_markdown = (
                output / "sweden_animal_adna_v62.0_warnings.md"
            ).read_text(encoding="utf-8")
            readme_text = (output / "README.md").read_text(encoding="utf-8")

            self.assertEqual(summary["animal_adna"]["total_species"], 1)
            self.assertEqual(summary["animal_adna"]["total_localities"], 1)
            self.assertEqual(summary["animal_adna"]["total_sample_rows"], 1)
            self.assertEqual(
                summary["animal_adna"]["artifacts"]["samples_csv"],
                "sweden_animal_adna_v62.0_samples.csv",
            )
            self.assertEqual(
                summary["animal_adna"]["artifacts"]["samples_markdown"],
                "sweden_animal_adna_v62.0_samples.md",
            )
            self.assertEqual(animal_summary["total_localities"], 1)
            self.assertEqual(animal_summary["total_sample_rows"], 1)
            self.assertEqual(
                animal_summary["species_rows"][0]["assignment_confidence"],
                "exact_country",
            )
            self.assertEqual(
                animal_summary["species_rows"][0]["sample_row_count"],
                1,
            )
            self.assertEqual(
                animal_summary["sample_rows"][0]["sample_record_id"],
                "ovis_aries:sample:prjeb59481",
            )
            self.assertIn("Country-resolved animal sample rows", readme_text)
            self.assertIn("## Animal aDNA Country Outputs", readme_text)
            self.assertIn("sweden_animal_adna_v62.0_samples.csv", readme_text)
            self.assertIn("sweden_animal_adna_v62.0_samples.md", readme_text)
            self.assertIn("sweden_animal_adna_v62.0_species.csv", readme_text)
            self.assertIn("Country-Resolved Animal Species", readme_text)
            self.assertIn("ovis_aries:sample:prjeb59481", sample_rows_markdown)
            self.assertIn("10.1000/sheep", sample_rows_markdown)
            self.assertIn("Sample rows", citations_markdown)
            self.assertIn("named_site_geocoding_only", warnings_markdown)

    def test_generate_country_report_marks_regional_animal_projection_in_warnings(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            output = Path(tmp) / "docs" / "report" / "sweden"
            context_root = Path(tmp) / "data"
            write_anno(
                root / "ho" / "v62.0_HO_public.anno",
                [
                    "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tHO\tF",
                ],
            )
            write_tracked_animal_species(
                context_root / "adna" / "species" / "ovis_aries",
                latin_name="Ovis aries",
                common_name="sheep",
                locality="Baltic sheep lead",
                political_entity="Baltic Sea Region",
                project_accession="PRJEB59481",
                support_class="accepted",
                product_role="domesticated_core",
                nordic_inclusion=True,
                chronology_bucket="1001-3000 BP",
                paper_title="Baltic short-tailed sheep aDNA",
                paper_doi="10.1000/sheep",
            )

            generate_country_report(root, "Sweden", output, context_root=context_root)

            animal_summary = json.loads(
                (output / "sweden_animal_adna_v62.0_summary.json").read_text(
                    encoding="utf-8"
                )
            )
            warnings_text = (output / "sweden_animal_adna_v62.0_warnings.md").read_text(
                encoding="utf-8"
            )

            self.assertEqual(
                animal_summary["localities"][0]["country_assignment_confidence"],
                "regional_projection",
            )
            self.assertIn("regional_projection", warnings_text)
            self.assertIn("not one country-exact excavation label", warnings_text)
