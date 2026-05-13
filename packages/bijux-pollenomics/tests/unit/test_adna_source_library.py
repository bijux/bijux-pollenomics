from __future__ import annotations

import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from bijux_pollenomics.adna.sources import library as source_library_module
from bijux_pollenomics.adna.sources.inventory import (
    build_reference_stash_doi_integrity_audit,
    build_reference_stash_reconciliation,
    build_supplement_acquisition_checklist,
    build_supplement_file_family_audit,
    build_supplement_recovery_audit,
)
from bijux_pollenomics.adna.sources.library import (
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
    def test_source_artifact_index_cache_can_be_cleared_between_reads(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"
            first_artifact = source_library_module.AdnaSourceArtifact(
                artifact_id="paper:first",
                artifact_kind="article_html",
                label="first",
                source_url="https://example.org/first",
                local_path="adna/governance/source_library/papers/example/article.html",
                fetch_status="archived",
                remote_note="first",
                project_accessions=("PRJEB22390",),
                paper_doi="10.1000/example",
            )
            with patch.object(
                source_library_module,
                "_build_source_artifact_index_uncached",
                side_effect=[(first_artifact,), ()],
            ) as build_uncached:
                source_library_module._clear_source_library_caches()
                first = source_library_module.build_source_artifact_index(output_root)
                second = source_library_module.build_source_artifact_index(output_root)
                source_library_module._clear_source_library_caches()
                third = source_library_module.build_source_artifact_index(output_root)

        self.assertEqual(first, (first_artifact,))
        self.assertEqual(second, first)
        self.assertEqual(third, ())
        self.assertEqual(build_uncached.call_count, 2)

    def test_download_url_rejects_non_http_scheme(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported URL for network fetch"):
            source_library_module._download_url("file:///tmp/source.pdf")

    def test_project_source_bundles_flag_missing_local_sources_before_refresh(
        self,
    ) -> None:
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

    def test_reference_stash_reconciliation_marks_local_staging_ahead_of_repo(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"
            stash_root = Path(tmp) / "stash"
            stash_root.mkdir(parents=True, exist_ok=True)
            (stash_root / "10.1016-j.cell.2019.03.049.pdf").write_bytes(b"%PDF-1.4\n")
            doi_dir = stash_root / "10.1016-j.cell.2019.03.049"
            doi_dir.mkdir(parents=True, exist_ok=True)
            (doi_dir / "table_s1.xlsx").write_bytes(b"sheet")

            with patch.dict(
                "os.environ",
                {"BIJUX_POLLENOMICS_REFERENCE_STASH_ROOT": str(stash_root)},
                clear=False,
            ):
                reconciliation = build_reference_stash_reconciliation(output_root)
                integrity = build_reference_stash_doi_integrity_audit(output_root)
                file_family_audit = build_supplement_file_family_audit(output_root)
                checklist = build_supplement_acquisition_checklist(output_root)
                recovery = build_supplement_recovery_audit(output_root)

        cell_row = next(
            row
            for row in reconciliation["rows"]
            if row["stash_slug"] == "10.1016-j.cell.2019.03.049"
        )
        checklist_row = next(
            row
            for row in checklist["rows"]
            if row["paper_doi"] == "10.1016/j.cell.2019.03.049"
        )
        family_row = next(
            row
            for row in file_family_audit["rows"]
            if row["paper_doi"] == "10.1016/j.cell.2019.03.049"
        )
        recovery_row = next(
            row
            for row in recovery["rows"]
            if row["paper_doi"] == "10.1016/j.cell.2019.03.049"
        )
        self.assertEqual(cell_row["alignment_status"], "local_reference_ahead_of_repo")
        self.assertTrue(integrity["all_stash_dois_tracked"])
        self.assertEqual(integrity["reference_stash_doi_count"], 1)
        self.assertEqual(
            checklist_row["acquisition_check_status"],
            "local_reference_ready_for_ingestion",
        )
        self.assertIn("xlsx_table", family_row["expected_supplementary_file_families"])
        self.assertEqual(
            recovery_row["recovery_status"],
            "local_reference_staged_needs_repo_ingestion",
        )

    def test_materialized_curated_stash_supplements_become_extractable_targets(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"
            stash_root = Path(tmp) / "stash"
            stash_root.mkdir(parents=True, exist_ok=True)
            (stash_root / "10.1111-1755-0998.12551.pdf").write_bytes(b"%PDF-1.4\n")
            doi_dir = stash_root / "10.1111-1755-0998.12551"
            doi_dir.mkdir(parents=True, exist_ok=True)
            (doi_dir / "men12551-sup-0001-supinfo.docx").write_bytes(b"docx")

            with patch.dict(
                "os.environ",
                {"BIJUX_POLLENOMICS_REFERENCE_STASH_ROOT": str(stash_root)},
                clear=False,
            ):
                materialize_source_library(output_root)
                paper_registry = build_paper_registry(output_root)
                recovery = build_supplement_recovery_audit(output_root)

        paper_row = next(
            row for row in paper_registry if row.paper_doi == "10.1111/1755-0998.12551"
        )
        recovery_row = next(
            row
            for row in recovery["rows"]
            if row["paper_doi"] == "10.1111/1755-0998.12551"
        )
        self.assertEqual(paper_row.supplementary_count, 1)
        self.assertEqual(paper_row.sample_extractability, "supplement_extractable")
        self.assertTrue(
            any(
                path.endswith("men12551-sup-0001-supinfo.docx")
                for path in paper_row.expected_supplementary_artifacts
            )
        )
        self.assertEqual(recovery_row["recovery_status"], "archived_and_parseable")

    def test_cross_project_source_audit_and_blockers_stay_reader_visible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"
            audit = build_cross_project_source_audit(output_root)
            blockers = build_missing_source_blockers(output_root)
            intake_audit = build_source_intake_audit(output_root)

        self.assertGreater(audit["paper_dependent_count"], 0)
        self.assertGreater(audit["blocked_count"], 0)
        self.assertGreater(
            intake_audit["blocker_counts"]["missing_paper_capture_count"], 0
        )
        self.assertGreater(
            intake_audit["blocker_counts"]["missing_sample_identifier_count"], 0
        )
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
