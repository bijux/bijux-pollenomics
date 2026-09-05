"""Materialized source-library registry publication behavior."""

from __future__ import annotations

import io
import json
from pathlib import Path
import tempfile
from typing import cast
import unittest
import zipfile

from bijux_pollenomics.adna.sources.library import (
    build_paper_registry,
    build_project_registry,
    build_source_artifact_index,
    build_source_intake_audit,
    build_source_intake_release_guard,
    build_source_storage_audit,
    build_supplement_registry,
    build_supplement_zip_member_registry,
    materialize_source_library,
    refresh_source_library,
)
from bijux_pollenomics.adna.workflow.source_artifacts import read_source_artifact_text


class SourceRegistryMaterializationTests(unittest.TestCase):
    def test_refresh_and_materialize_source_library_publish_master_registries(
        self,
    ) -> None:
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

            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "project_registry.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "paper_registry.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "supplement_registry.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "supplement_zip_member_registry.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "source_artifact_index.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "source_intake_audit.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "source_intake_release_guard.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "source_storage_audit.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "source_storage_audit.md"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "tracked_project_and_paper_inventory.md"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "project_sample_site_review.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "sample_site_ambiguity_ledger.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "sample_site_manual_curation_queue.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "sample_locality_conflict_ledger.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "sample_locality_manual_curation_workflow.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "project_locality_substitution_ledger.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "site_name_normalization_dictionary.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "species_locality_completeness.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "project_locality_completeness.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "project_sample_chronology_review.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "sample_chronology_normalization_audit.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "sample_chronology_ambiguity_ledger.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "sample_chronology_conflict_ledger.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "sample_chronology_precision_audit.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "species_chronology_completeness.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "project_chronology_completeness.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "sample_chronology_review.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "date_evidence_gap_queue.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "tracked_project_scope_audit.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "project_source_evidence_matrix.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "reference_stash_reconciliation.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "reference_stash_doi_integrity_audit.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "supplement_file_family_audit.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "supplement_acquisition_checklist.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "supplement_recovery_audit.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "source_blocker_review.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "cross_project_source_intake_dossier.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "project_recovery_stage_review.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "project_expected_sample_yield_review.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "paper_expected_sample_yield_review.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "species_project_deficit_ledger.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "manual_curation_worklist.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "source_recovery_progress.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "missing_source_queue.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "source_recovery_release_guard.json"
                ).is_file()
            )

            sheep_project = next(
                item
                for item in project_registry
                if item.project_accession == "PRJEB36540"
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
            self.assertEqual(
                sheep_paper.sample_extractability, "supplement_extractable"
            )
            self.assertEqual(
                sheep_paper.sample_table_extraction_status,
                "published_empty",
            )
            self.assertTrue(
                any(
                    path.endswith("42003_2021_2794_MOESM4_ESM.zip")
                    for path in sheep_paper.expected_supplementary_artifacts
                )
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
            source_artifact_index = build_source_artifact_index(output_root)
            storage_audit = build_source_storage_audit(output_root)
            article_path = (
                output_root
                / "adna"
                / "governance"
                / "source_library"
                / "papers"
                / "10.1038-s41562-021-01083-y"
                / "article.html"
            )
            archive_path = (
                output_root
                / "adna"
                / "governance"
                / "source_library"
                / "projects"
                / "PRJEB36540"
                / "archive_metadata.html"
            )
            article_metadata_path = article_path.with_suffix(
                article_path.suffix + ".metadata.json"
            )
            archive_metadata_path = archive_path.with_suffix(
                archive_path.suffix + ".metadata.json"
            )
            self.assertFalse(article_path.is_file())
            self.assertTrue(article_path.with_name("article.html.gz").is_file())
            self.assertFalse(archive_path.is_file())
            self.assertTrue(
                archive_path.with_name("archive_metadata.html.gz").is_file()
            )
            self.assertEqual(
                read_source_artifact_text(article_path),
                "<html><body>ok</body></html>",
            )
            self.assertEqual(
                read_source_artifact_text(archive_path),
                "<html><body>ok</body></html>",
            )
            article_metadata = json.loads(article_metadata_path.read_text("utf-8"))
            archive_metadata = json.loads(archive_metadata_path.read_text("utf-8"))
            self.assertEqual(article_metadata["content_encoding"], "gzip")
            self.assertTrue(article_metadata["storage_path"].endswith(".html.gz"))
            self.assertEqual(archive_metadata["content_encoding"], "gzip")
            self.assertTrue(archive_metadata["storage_path"].endswith(".html.gz"))
            article_artifact = next(
                item
                for item in source_artifact_index
                if item.local_path.endswith("10.1038-s41562-021-01083-y/article.html")
            )
            self.assertEqual(article_artifact.content_encoding, "gzip")
            self.assertTrue(str(article_artifact.storage_path).endswith(".html.gz"))
            self.assertGreater(
                cast(int, storage_audit["compressed_html_artifact_count"]), 0
            )
            self.assertEqual(storage_audit["uncompressed_html_artifact_count"], 0)

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
            intake_dossier_payload = json.loads(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "projects"
                    / "PRJEB36540"
                    / "intake_dossier.json"
                ).read_text(encoding="utf-8")
            )
            self.assertIn("stage_statuses", intake_dossier_payload)
            self.assertIn("publication_readiness_status", intake_dossier_payload)
            self.assertIn("manual_curation_work_units", intake_dossier_payload)
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
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "projects"
                    / "PRJEB36540"
                    / "locality_worksheet.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "projects"
                    / "PRJEB36540"
                    / "sample_locality_evidence.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "projects"
                    / "PRJEB36540"
                    / "sample_sites.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "projects"
                    / "PRJEB36540"
                    / "sample_chronology.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "projects"
                    / "PRJEB36540"
                    / "sample_chronology_evidence.json"
                ).is_file()
            )
