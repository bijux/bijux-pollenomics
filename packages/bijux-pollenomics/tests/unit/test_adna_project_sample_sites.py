from __future__ import annotations

from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import pytest

from bijux_pollenomics.adna import project_sample_sites as project_sample_sites_module
from bijux_pollenomics.adna.project_sample_sites import (
    build_project_sample_site_review_rows,
    build_project_sample_site_rows,
    build_sample_site_ambiguity_ledger,
    build_sample_site_manual_curation_queue,
)

pytestmark = pytest.mark.generated_artifacts


class AdnaProjectSampleSitesUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data_root = Path(__file__).resolve().parents[4] / "data"

    def test_sheep_project_sample_sites_keep_direct_rows_and_hierarchy(self) -> None:
        rows = build_project_sample_site_rows(self.data_root, "PRJEB36540")

        self.assertGreater(len(rows), 10)
        first = next(row for row in rows if row.locality_text == "Barcın Höyük")
        self.assertEqual(first.locality_resolution_status, "direct_sample_site")
        self.assertEqual(
            first.location_evidence_artifact_kind, "supplementary_spreadsheet_row"
        )
        self.assertEqual(first.country_name, "Turkey")
        self.assertEqual(first.region_name, "Bursa Province")

    def test_region_scale_projects_stay_visible_as_weak_sample_site_rows(self) -> None:
        rows = build_project_sample_site_rows(self.data_root, "SRS1407451")

        self.assertTrue(rows)
        self.assertTrue(
            all(row.locality_resolution_status == "region_only" for row in rows)
        )
        self.assertTrue(
            all(
                "broad contextual centroid" in row.review_note.lower()
                or "region" in row.review_note.lower()
                for row in rows
            )
        )

    def test_horse_project_sample_sites_publish_direct_botai_rows(self) -> None:
        rows = build_project_sample_site_rows(self.data_root, "PRJEB22390")

        botai = next(
            row for row in rows if row.preferred_sample_label == "Botai 1 5500"
        )
        self.assertEqual(botai.locality_text, "Botai")
        self.assertEqual(botai.locality_resolution_status, "direct_sample_site")
        self.assertEqual(
            botai.location_evidence_artifact_kind, "supplementary_spreadsheet_row"
        )
        self.assertEqual(botai.chronology_text, "5500 BP")

    def test_horse_nordic_project_sample_sites_keep_country_and_direct_coordinate_posture(
        self,
    ) -> None:
        rows = build_project_sample_site_rows(self.data_root, "PRJEB31613")

        uppsala = next(
            row for row in rows if row.preferred_sample_label == "Uppsala_Upps02_1317"
        )
        self.assertEqual(uppsala.locality_text, "Uppsala")
        self.assertEqual(uppsala.country_name, "Sweden")
        self.assertEqual(uppsala.coordinate_basis, "supplementary_table_coordinates")
        self.assertEqual(uppsala.coordinate_confidence, "exact")
        self.assertEqual(uppsala.chronology_text, "1217-1417 BP")

    def test_review_rows_ambiguity_ledger_and_manual_queue_stay_reader_visible(
        self,
    ) -> None:
        review_rows = build_project_sample_site_review_rows(self.data_root)
        ambiguity_rows = build_sample_site_ambiguity_ledger(self.data_root)
        queue_rows = build_sample_site_manual_curation_queue(self.data_root)

        self.assertEqual(len(review_rows), 40)
        sheep_review = next(
            row for row in review_rows if row["project_accession"] == "PRJEB36540"
        )
        self.assertGreater(sheep_review["direct_sample_site_count"], 10)
        self.assertEqual(sheep_review["lacking_defensible_site_assignment_count"], 0)

        self.assertTrue(
            any(
                row["project_accession"] == "SRS1407451"
                and row["locality_resolution_status"] == "region_only"
                for row in ambiguity_rows
            )
        )
        self.assertTrue(
            any(
                row["project_accession"] == "SRS1407451"
                and row["queued_sample_count"] > 0
                for row in queue_rows
            )
        )

    def test_ghostscript_text_uses_resolved_local_pdf_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "atlas.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n")
            with (
                patch.object(
                    project_sample_sites_module.shutil,
                    "which",
                    return_value="/usr/bin/gs",
                ),
                patch.object(
                    project_sample_sites_module.subprocess,
                    "run",
                    return_value=SimpleNamespace(returncode=0, stdout="atlas text"),
                ) as mock_run,
            ):
                text = project_sample_sites_module._ghostscript_text(pdf_path)

        self.assertEqual(text, "atlas text")
        args = mock_run.call_args.args[0]
        self.assertEqual(args[0], "/usr/bin/gs")
        self.assertEqual(args[-1], str(pdf_path.resolve()))


if __name__ == "__main__":
    unittest.main()
