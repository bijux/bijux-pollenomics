"""Tests for project-specific sample recovery from governed sources."""

from __future__ import annotations

import pytest

from bijux_pollenomics.adna.projects.sample_master import (
    build_project_sample_master_rows,
)

from .support import SampleMasterRecoveryTestCase

pytestmark = pytest.mark.generated_artifacts


class SourceRecoveryTests(SampleMasterRecoveryTestCase):
    def test_archive_native_sample_master_expands_accession_ranges(self) -> None:
        rows = build_project_sample_master_rows(self.data_root, "KU605068-KU605080")

        self.assertEqual(len(rows), 13)
        self.assertEqual(rows[0].archive_native_sample_id, "KU605068")
        self.assertEqual(rows[-1].archive_native_sample_id, "KU605080")
        self.assertTrue(
            all(row.sample_evidence_status == "article_text_extracted" for row in rows)
        )
        self.assertTrue(all(row.sample_identity_resolution == "final" for row in rows))

        palm = next(row for row in rows if row.archive_native_sample_id == "KU605068")
        self.assertEqual(palm.preferred_sample_label, "Palm152")
        self.assertEqual(palm.locality_text, "Palmyra")
        self.assertEqual(palm.political_entity, "Syria")
        self.assertEqual(palm.chronology_text, "1650-2050 BP")

        modern = next(row for row in rows if row.archive_native_sample_id == "KU605080")
        self.assertEqual(modern.preferred_sample_label, "Drom820")
        self.assertEqual(modern.locality_text, "Pakistan")
        self.assertEqual(modern.chronology_text, "0 BP (modern comparator)")

    def test_dog_accessions_recover_article_owned_sites_and_dates(self) -> None:
        hx = build_project_sample_master_rows(self.data_root, "SRS1407453")
        mitogenomes = build_project_sample_master_rows(
            self.data_root, "KX379528-KX379529"
        )

        self.assertEqual(len(hx), 1)
        self.assertEqual(hx[0].preferred_sample_label, "HXH")
        self.assertEqual(hx[0].locality_text, "Herxheim")
        self.assertEqual(hx[0].chronology_text, "5223-5040 BCE")

        self.assertEqual(len(mitogenomes), 2)
        ctc = next(
            row for row in mitogenomes if row.archive_native_sample_id == "KX379528"
        )
        self.assertEqual(ctc.preferred_sample_label, "CTC")
        self.assertEqual(ctc.locality_text, "Cherry Tree Cave")
        self.assertEqual(ctc.chronology_text, "2900-2632 BCE")

    def test_sheep_project_sample_master_extracts_rows_from_supplementary_tables(
        self,
    ) -> None:
        rows = build_project_sample_master_rows(self.data_root, "PRJEB36540")

        self.assertGreater(len(rows), 10)
        first = rows[0]
        self.assertEqual(first.sample_evidence_status, "direct_table_extracted")
        self.assertEqual(first.sample_basis, "supplementary_table_sample_label_anchor")
        self.assertIn("42003_2021_2794_MOESM4_ESM.zip", first.sample_lineage_path)
        self.assertIn("Sheet1!row", first.sample_lineage_locator)
        self.assertEqual(first.sample_identity_resolution, "final")

    def test_horse_project_sample_master_merges_lab_and_panel_tables(self) -> None:
        rows = build_project_sample_master_rows(self.data_root, "PRJEB22390")

        self.assertEqual(len(rows), 42)
        botai = next(
            row for row in rows if row.archive_native_sample_id == "CGG_1_018173"
        )
        self.assertEqual(botai.preferred_sample_label, "Botai 1 5500")
        self.assertEqual(botai.locality_text, "Botai")
        self.assertEqual(botai.chronology_text, "5500 BP")
        self.assertIn("aao3297_tables11.xlsx", botai.sample_lineage_path)
        self.assertIn("aao3297_tables15.xlsx", botai.sample_lineage_path)
        self.assertEqual(botai.sample_identity_resolution, "final")

    def test_horse_time_series_and_dom2_projects_publish_recovered_sample_rows(
        self,
    ) -> None:
        time_series_rows = build_project_sample_master_rows(
            self.data_root, "PRJEB31613"
        )
        dom2_rows = build_project_sample_master_rows(self.data_root, "PRJEB44430")
        domestication_rows = build_project_sample_master_rows(
            self.data_root, "PRJEB19970"
        )

        self.assertEqual(len(time_series_rows), 244)
        self.assertEqual(len(dom2_rows), 248)
        self.assertEqual(len(domestication_rows), 14)

        uppsala = next(
            row
            for row in time_series_rows
            if row.preferred_sample_label == "Uppsala_Upps02_1317"
        )
        self.assertEqual(uppsala.locality_text, "Uppsala")
        self.assertEqual(uppsala.political_entity, "Sweden")
        self.assertEqual(uppsala.latitude_text, "59.860999999999997")
        self.assertEqual(uppsala.longitude_text, "17.638999999999999")
        self.assertEqual(uppsala.chronology_text, "1217-1417 BP")

        ginnerup = next(
            row
            for row in dom2_rows
            if row.preferred_sample_label == "DJM130x6_Dan_m3011"
        )
        self.assertEqual(ginnerup.locality_text, "Ginnerup")
        self.assertEqual(ginnerup.political_entity, "Denmark")
        self.assertEqual(ginnerup.latitude_text, "56.41134")
        self.assertEqual(ginnerup.longitude_text, "10.74481")
        self.assertEqual(ginnerup.chronology_text, "4961 BP")
        self.assertEqual(ginnerup.archive_native_sample_id, "SAMEA9533224")

        berel = next(
            row
            for row in domestication_rows
            if row.preferred_sample_label == "Berel_BER01_A_2300"
        )
        self.assertEqual(berel.locality_text, "Berel'")
        self.assertEqual(berel.political_entity, "Kazakhstan")
        self.assertEqual(berel.chronology_text, "2300 BP")

    def test_goat_cattle_and_reindeer_projects_publish_source_backed_sample_rows(
        self,
    ) -> None:
        goat_rows = build_project_sample_master_rows(self.data_root, "PRJNA1328209")
        cattle_rows = build_project_sample_master_rows(self.data_root, "PRJNA705960")
        reindeer_rows = build_project_sample_master_rows(self.data_root, "PRJEB60484")

        self.assertEqual(len(goat_rows), 5)
        self.assertEqual(len(cattle_rows), 11)
        self.assertEqual(len(reindeer_rows), 20)

        qinghai = next(row for row in goat_rows if row.preferred_sample_label == "DC23")
        self.assertEqual(qinghai.locality_text, "Lake Qinghai basin")
        self.assertEqual(qinghai.chronology_text, "3480-3580 BP")
        self.assertIn("Supplementary_tables.xlsx", qinghai.sample_lineage_path)

        cattle_anchor = cattle_rows[0]
        self.assertEqual(
            cattle_anchor.sample_basis, "archive_project_sample_accession_anchor"
        )
        self.assertEqual(cattle_anchor.sample_evidence_status, "archive_native")
        self.assertTrue(cattle_anchor.archive_native_sample_id.startswith("SAMN"))

        reindeer_anchor = reindeer_rows[0]
        self.assertEqual(
            reindeer_anchor.sample_basis, "archive_project_sample_accession_anchor"
        )
        self.assertEqual(reindeer_anchor.sample_evidence_status, "archive_native")
        self.assertTrue(reindeer_anchor.archive_native_sample_id.startswith("SAMEA"))

    def test_locally_captured_archive_projects_publish_native_sample_rows(
        self,
    ) -> None:
        expected_counts = {
            "PRJEB30282": 343,
            "PRJEB31621": 77,
            "PRJEB41594": 5,
            "PRJEB59481": 5,
            "PRJEB75467": 44,
            "PRJEB81815": 87,
        }

        for project_accession, expected_count in expected_counts.items():
            with self.subTest(project_accession=project_accession):
                rows = build_project_sample_master_rows(
                    self.data_root, project_accession
                )
                self.assertEqual(len(rows), expected_count)
                self.assertTrue(
                    all(row.sample_identity_resolution == "final" for row in rows)
                )
                self.assertTrue(all(row.sample_lineage_path for row in rows))
                self.assertTrue(all(row.sample_lineage_locator for row in rows))
