from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pytest

from bijux_pollenomics.adna.workflow.source_artifacts import (
    read_source_artifact_bytes,
)
from bijux_pollenomics.config import DEFAULT_ATLAS_SLUG, DEFAULT_ATLAS_TITLE
from bijux_pollenomics.reporting.models import PublishedReportsReport
from bijux_pollenomics.reporting.service import refresh_animal_adna_foundation
from tests.support.repository import REPOSITORY_ROOT

pytestmark = pytest.mark.generated_artifacts


class AnimalFoundationRefreshUnitTests(unittest.TestCase):
    def test_refresh_animal_adna_foundation_rebuilds_real_sheep_family_surfaces(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            data_root = tmp_root / "data"
            aadr_root = data_root / "aadr"
            report_root = tmp_root / "docs" / "report"
            obishir_supplements = Path(
                "adna/governance/source_library/papers/"
                "10.1038-s41562-021-01083-y/supplementary"
            )
            for filename in (
                "41562_2021_1083_MOESM1_ESM.pdf",
                "41562_2021_1083_MOESM2_ESM.pdf",
            ):
                source = REPOSITORY_ROOT / "data" / obishir_supplements / filename
                destination = data_root / obishir_supplements / filename
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(read_source_artifact_bytes(source))
            camel_bridge = Path(
                "adna/governance/source_library/projects/SRP073444/"
                "paper_table_s1_sample_bridge.csv"
            )
            source = REPOSITORY_ROOT / "data" / camel_bridge
            destination = data_root / camel_bridge
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(read_source_artifact_bytes(source))
            source_library = (
                REPOSITORY_ROOT / "data/adna/governance/source_library"
            )
            archived_sources: dict[str, tuple[Path, str]] = {}
            for metadata_path in source_library.rglob("*.metadata.json"):
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                source_url = metadata.get("source_url")
                content_type = metadata.get("content_type")
                if source_url and content_type:
                    source_path = Path(str(metadata_path).removesuffix(".metadata.json"))
                    archived_sources[source_url] = (
                        source_path,
                        content_type,
                    )

            def fake_downloader(url: str) -> tuple[bytes, str]:
                if "efetch.fcgi" in url:
                    return (b"<PubmedArticleSet/>", "application/xml")
                archived = archived_sources.get(url)
                if archived is not None:
                    path, content_type = archived
                    return (read_source_artifact_bytes(path), content_type)
                if url.endswith("/PMC11162877/fullTextXML"):
                    path = REPOSITORY_ROOT / (
                        "data/adna/governance/source_library/papers/"
                        "10.1093-gbe-evae114/article_full_text.xml"
                    )
                    return (read_source_artifact_bytes(path), "application/xml")
                if url.endswith(".pdf"):
                    return (b"%PDF-1.4\n", "application/pdf")
                if url.endswith(".zip"):
                    return (b"PK\x03\x04", "application/zip")
                if "crossref" in url:
                    return (b'{"message":{"title":["ok"]}}', "application/json")
                return (b"<html><body>ok</body></html>", "text/html")

            fake_report = PublishedReportsReport(
                version="v66",
                generated_on="1970-01-01",
                countries=("Sweden",),
                shared_map_dir=report_root / DEFAULT_ATLAS_SLUG,
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
                (
                    data_root
                    / "adna"
                    / "species"
                    / "ovis_aries"
                    / "normalized"
                    / "sample_records.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    data_root
                    / "adna"
                    / "species"
                    / "ovis_aries"
                    / "normalized"
                    / "site_evidence.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    data_root
                    / "adna"
                    / "species"
                    / "ovis_aries"
                    / "normalized"
                    / "coordinate_provenance.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    data_root
                    / "adna"
                    / "governance"
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
                title=DEFAULT_ATLAS_TITLE,
                slug=DEFAULT_ATLAS_SLUG,
                context_root=data_root,
            )


if __name__ == "__main__":
    unittest.main()
