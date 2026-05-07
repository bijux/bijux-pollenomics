from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from bijux_pollenomics.reporting.models import PublishedReportsReport
from bijux_pollenomics.reporting.service import refresh_animal_adna_foundation


class AnimalFoundationRefreshUnitTests(unittest.TestCase):
    def test_refresh_animal_adna_foundation_rebuilds_real_sheep_family_surfaces(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            data_root = tmp_root / "data"
            aadr_root = data_root / "aadr"
            report_root = tmp_root / "docs" / "report"

            def fake_downloader(url: str) -> tuple[bytes, str]:
                if url.endswith(".pdf"):
                    return (b"%PDF-1.4\n", "application/pdf")
                if url.endswith(".zip"):
                    return (b"PK\x03\x04", "application/zip")
                if "crossref" in url:
                    return (b'{"message":{"title":["ok"]}}', "application/json")
                if "efetch.fcgi" in url:
                    return (b"<PubmedArticleSet/>", "application/xml")
                return (b"<html><body>ok</body></html>", "text/html")

            fake_report = PublishedReportsReport(
                version="v66",
                generated_on="1970-01-01",
                countries=("Sweden",),
                shared_map_dir=report_root / "nordic-atlas",
                country_output_dirs=(report_root / "sweden",),
                summary_path=report_root / "published_reports_summary.json",
            )

            with patch(
                "bijux_pollenomics.reporting.service.generate_published_reports",
                return_value=fake_report,
            ) as generate_reports:
                report = refresh_animal_adna_foundation(
                    data_root=data_root,
                    aadr_root=aadr_root,
                    report_root=report_root,
                    countries=("Sweden",),
                    version="v66",
                    species_names=("sheep",),
                    source_downloader=fake_downloader,
                )

            self.assertEqual(report.schema_version, "animal-foundation-refresh.v1")
            self.assertEqual(report.refreshed_species_latin_names, ("Ovis aries",))
            self.assertIn("PRJEB36540", report.refreshed_project_accessions)
            self.assertGreater(report.source_library_project_count, 0)
            self.assertGreaterEqual(report.atlas_evidence_row_count, 0)
            self.assertTrue(
                (data_root / "adna" / "ovis_aries" / "normalized" / "sample_records.json").is_file()
            )
            self.assertTrue(
                (data_root / "adna" / "ovis_aries" / "normalized" / "site_evidence.json").is_file()
            )
            self.assertTrue(
                (
                    data_root
                    / "adna"
                    / "ovis_aries"
                    / "normalized"
                    / "coordinate_provenance.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    data_root
                    / "adna"
                    / "source_library"
                    / "projects"
                    / "PRJEB36540"
                    / "bundle_manifest.json"
                ).is_file()
            )
            generate_reports.assert_called_once_with(
                version_dir=aadr_root / "v66",
                countries=("Sweden",),
                output_root=report_root,
                title="Nordic Evidence Atlas",
                slug="nordic-atlas",
                context_root=data_root,
            )


if __name__ == "__main__":
    unittest.main()
