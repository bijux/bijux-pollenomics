from __future__ import annotations

import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from bijux_pollenomics.adna.source_library import (
    build_cross_project_source_audit,
    build_missing_source_blockers,
    build_paper_registry,
    build_project_registry,
    build_project_source_bundles,
    build_source_intake_audit,
    build_source_intake_release_guard,
    build_supplement_registry,
    build_supplement_zip_member_registry,
    materialize_source_library,
    refresh_source_library,
)


class AdnaSourceLibraryUnitTests(unittest.TestCase):
    def test_project_source_bundles_flag_missing_local_sources_before_refresh(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"
            bundles = build_project_source_bundles(output_root)

        horse_bundle = next(
            item for item in bundles if item.project_accession == "PRJEB22390"
        )
        self.assertTrue(horse_bundle.paper_required)
        self.assertFalse(horse_bundle.supplement_required)
        self.assertIn("missing_local_paper_evidence", horse_bundle.blockers)
        self.assertNotIn("missing_local_supplementary_material", horse_bundle.blockers)

    def test_refresh_and_materialize_source_library_publish_master_registries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"

            def fake_downloader(url: str) -> tuple[bytes, str]:
                if url.endswith(".zip"):
                    payload = io.BytesIO()
                    with zipfile.ZipFile(payload, "w") as archive:
                        archive.writestr("TableS1.csv", "sample_id,site\ns1,Anatolia\n")
                        archive.writestr("README.txt", "supplementary bundle")
                    return (payload.getvalue(), "application/zip")
                if url.endswith(".pdf"):
                    return (b"%PDF-1.4\n", "application/pdf")
                if "crossref" in url:
                    return (b'{"message":{"title":["ok"]}}', "application/json")
                if "efetch.fcgi" in url:
                    return (b"<PubmedArticleSet/>", "application/xml")
                return (b"<html><body>ok</body></html>", "text/html")

            refresh_source_library(output_root, downloader=fake_downloader)
            materialize_source_library(output_root)

            project_registry = build_project_registry(output_root)
            paper_registry = build_paper_registry(output_root)
            supplement_registry = build_supplement_registry(output_root)
            member_registry = build_supplement_zip_member_registry(output_root)
            intake_audit = build_source_intake_audit(output_root)
            release_guard = build_source_intake_release_guard(output_root)

            self.assertTrue((output_root / "adna" / "governance" / "source_library" / "project_registry.json").is_file())
            self.assertTrue((output_root / "adna" / "governance" / "source_library" / "paper_registry.json").is_file())
            self.assertTrue((output_root / "adna" / "governance" / "source_library" / "supplement_registry.json").is_file())
            self.assertTrue((output_root / "adna" / "governance" / "source_library" / "supplement_zip_member_registry.json").is_file())
            self.assertTrue((output_root / "adna" / "governance" / "source_library" / "source_intake_audit.json").is_file())
            self.assertTrue((output_root / "adna" / "governance" / "source_library" / "source_intake_release_guard.json").is_file())
            self.assertTrue((output_root / "adna" / "governance" / "source_library" / "tracked_project_and_paper_inventory.md").is_file())

            sheep_project = next(
                item for item in project_registry if item.project_accession == "PRJEB36540"
            )
            self.assertEqual(sheep_project.paper_download_status, "archived")
            self.assertEqual(sheep_project.supplement_download_status, "archived")
            self.assertEqual(
                sheep_project.expected_sample_count_status,
                "not_yet_curated",
            )
            self.assertEqual(
                sheep_project.sample_identifier_status,
                "paper_or_supplement_targets_curated",
            )

            sheep_paper = next(
                item
                for item in paper_registry
                if item.paper_doi == "10.1038/s42003-021-02794-8"
            )
            self.assertEqual(sheep_paper.supplementary_count, 5)
            self.assertEqual(sheep_paper.article_download_status, "archived")
            self.assertEqual(sheep_paper.sample_extractability, "supplement_extractable")
            self.assertTrue(
                any(path.endswith("42003_2021_2794_MOESM4_ESM.zip") for path in sheep_paper.expected_supplementary_artifacts)
            )

            self.assertTrue(
                any(
                    item.paper_doi == "10.1038/s42003-021-02794-8"
                    and item.artifact_kind == "supplementary_zip"
                    for item in supplement_registry
                )
            )
            self.assertTrue(
                any(
                    item["paper_doi"] == "10.1038/s42003-021-02794-8"
                    and item["member_name"] == "TableS1.csv"
                    for item in member_registry
                )
            )
            self.assertEqual(intake_audit["sample_extractable_violations"], [])
            self.assertTrue(release_guard["passing"])

            bundle_path = (
                output_root
                / "adna"
                / "governance"
                / "source_library"
                / "projects"
                / "PRJEB36540"
                / "bundle_manifest.json"
            )
            self.assertTrue(bundle_path.is_file())
            payload = json.loads(bundle_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["paper_download_status"], "archived")
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "projects"
                    / "PRJEB36540"
                    / "intake_dossier.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "papers"
                    / "10.1038-s42003-021-02794-8"
                    / "supplementary_manifest.json"
                ).is_file()
            )

    def test_cross_project_source_audit_and_blockers_stay_reader_visible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"
            audit = build_cross_project_source_audit(output_root)
            blockers = build_missing_source_blockers(output_root)
            intake_audit = build_source_intake_audit(output_root)

        self.assertGreater(audit["paper_dependent_count"], 0)
        self.assertGreater(audit["blocked_count"], 0)
        self.assertGreater(intake_audit["blocker_counts"]["missing_paper_capture_count"], 0)
        self.assertGreater(intake_audit["blocker_counts"]["missing_sample_identifier_count"], 0)
        self.assertTrue(
            any(
                row["project_accession"] == "PRJEB22390"
                and "missing_local_paper_evidence" in row["blockers"]
                and "missing_paper_capture" in row["blocker_categories"]
                for row in blockers["rows"]
            )
        )


if __name__ == "__main__":
    unittest.main()
