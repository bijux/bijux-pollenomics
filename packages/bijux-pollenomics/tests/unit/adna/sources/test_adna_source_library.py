from __future__ import annotations

import gzip
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from bijux_pollenomics.adna.source_artifact_storage import (
    SourceArtifactContentDriftError,
    migrate_html_source_artifact,
    read_source_artifact_text,
    write_source_artifact_bytes,
)
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
    build_source_artifact_index,
    build_source_intake_audit,
    build_source_intake_release_guard,
    build_source_storage_audit,
    build_supplement_registry,
    build_supplement_zip_member_registry,
    materialize_source_library,
    refresh_source_library,
)


class AdnaSourceLibraryUnitTests(unittest.TestCase):
    def test_gzip_storage_is_deterministic_and_refuses_logical_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first_logical = root / "first.html"
            second_logical = root / "second.html"
            payload = b"<html><body>stable evidence</body></html>"

            first_stored = write_source_artifact_bytes(first_logical, payload)
            second_stored = write_source_artifact_bytes(second_logical, payload)
            first_storage_bytes = first_stored.read_bytes()

            self.assertEqual(first_storage_bytes, second_stored.read_bytes())
            self.assertEqual(first_storage_bytes[4:8], b"\x00\x00\x00\x00")
            first_inode = first_stored.stat().st_ino
            repeated_path = write_source_artifact_bytes(first_logical, payload)
            self.assertEqual(repeated_path.stat().st_ino, first_inode)
            self.assertEqual(repeated_path.read_bytes(), first_storage_bytes)
            with self.assertRaises(SourceArtifactContentDriftError) as raised:
                write_source_artifact_bytes(first_logical, b"different evidence")

            self.assertEqual(read_source_artifact_text(first_logical), payload.decode())
            self.assertEqual(first_stored.read_bytes(), first_storage_bytes)
            self.assertNotEqual(
                raised.exception.existing_sha256,
                raised.exception.candidate_sha256,
            )

    def test_refresh_records_content_drift_without_replacing_capture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"
            spec = _bounded_paper_spec()

            def initial_downloader(url: str) -> tuple[bytes, str]:
                if "crossref" in url:
                    return b'{"message":{"title":["stable"]}}', "application/json"
                return b"<html><body>historical evidence</body></html>", "text/html"

            def changed_downloader(url: str) -> tuple[bytes, str]:
                if "crossref" in url:
                    return b'{"message":{"title":["stable"]}}', "application/json"
                return b"<html><body>changed evidence</body></html>", "text/html"

            with (
                patch.object(
                    source_library_module,
                    "build_archive_project_catalog",
                    return_value=(),
                ),
                patch.object(
                    source_library_module,
                    "_paper_source_specs",
                    return_value={spec.doi: spec},
                ),
            ):
                refresh_source_library(output_root, downloader=initial_downloader)
                with self.assertRaisesRegex(ValueError, "refused capture"):
                    refresh_source_library(output_root, downloader=changed_downloader)

            article_path = (
                source_library_module.adna_source_library_root(output_root)
                / "papers"
                / "10.1000-source-capture"
                / "article.html"
            )
            self.assertEqual(
                read_source_artifact_text(article_path),
                "<html><body>historical evidence</body></html>",
            )
            refusals = tuple(
                article_path.parent.glob("article.html.capture-refusal-*.json")
            )
            self.assertEqual(len(refusals), 1)
            refusal = json.loads(refusals[0].read_text(encoding="utf-8"))
            self.assertEqual(refusal["status"], "refused")
            self.assertEqual(refusal["reason_code"], "content_drift")
            self.assertNotEqual(refusal["existing_sha256"], refusal["candidate_sha256"])

    def test_identical_refresh_preserves_capture_and_metadata_inodes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"
            spec = _bounded_paper_spec()

            def downloader(url: str) -> tuple[bytes, str]:
                if "crossref" in url:
                    return b'{"message":{"title":["stable"]}}', "application/json"
                return b"<html><body>stable evidence</body></html>", "text/html"

            with (
                patch.object(
                    source_library_module,
                    "build_archive_project_catalog",
                    return_value=(),
                ),
                patch.object(
                    source_library_module,
                    "_paper_source_specs",
                    return_value={spec.doi: spec},
                ),
            ):
                refresh_source_library(output_root, downloader=downloader)
                article_path = (
                    source_library_module.adna_source_library_root(output_root)
                    / "papers"
                    / "10.1000-source-capture"
                    / "article.html"
                )
                stored_path = article_path.with_name("article.html.gz")
                metadata_path = article_path.with_suffix(".html.metadata.json")
                stored_identity = (stored_path.stat().st_ino, stored_path.read_bytes())
                metadata_identity = (
                    metadata_path.stat().st_ino,
                    metadata_path.read_bytes(),
                )

                refresh_source_library(output_root, downloader=downloader)

            self.assertEqual(
                (stored_path.stat().st_ino, stored_path.read_bytes()), stored_identity
            )
            self.assertEqual(
                (metadata_path.stat().st_ino, metadata_path.read_bytes()),
                metadata_identity,
            )

    def test_observed_http_success_challenge_pages_are_refused(self) -> None:
        challenge_pages = {
            "google_recaptcha": (
                b'<html><script src="https://google.com/recaptcha/challengepage">'
                b'</script><div class="RecaptchaChallengePageUi"></div></html>'
            ),
            "pubmed_cookie_challenge": (
                b"<html><body>Cookies must be enabled to continue. "
                b"This is a browser challenge page.</body></html>"
            ),
        }
        for label, payload in challenge_pages.items():
            with self.subTest(label=label):
                self.assertEqual(
                    source_library_module._http_success_refusal_reason(
                        payload, "text/html; charset=utf-8"
                    ),
                    "http_success_block_or_error_page",
                )

    def test_refresh_refuses_http_success_access_denied_page(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"
            spec = _bounded_paper_spec()
            article_path = (
                source_library_module.adna_source_library_root(output_root)
                / "papers"
                / "10.1000-source-capture"
                / "article.html"
            )
            article_path.parent.mkdir(parents=True, exist_ok=True)
            article_path.write_bytes(b"<html><body>historical evidence</body></html>")

            def blocked_downloader(url: str) -> tuple[bytes, str]:
                if "crossref" in url:
                    return (
                        b"<html><head><title>Access Denied</title></head></html>",
                        "text/html",
                    )
                return b"<html><body>historical evidence</body></html>", "text/html"

            with (
                patch.object(
                    source_library_module,
                    "build_archive_project_catalog",
                    return_value=(),
                ),
                patch.object(
                    source_library_module,
                    "_paper_source_specs",
                    return_value={spec.doi: spec},
                ),
                self.assertRaisesRegex(ValueError, "refused capture"),
            ):
                refresh_source_library(output_root, downloader=blocked_downloader)

            self.assertEqual(
                article_path.read_bytes(),
                b"<html><body>historical evidence</body></html>",
            )
            self.assertFalse(article_path.with_name("article.html.gz").is_file())
            crossref_path = article_path.parent / "crossref.json"
            self.assertFalse(crossref_path.is_file())
            refusal_paths = tuple(
                article_path.parent.glob("crossref.json.capture-refusal-*.json")
            )
            self.assertEqual(len(refusal_paths), 1)
            refusal = json.loads(refusal_paths[0].read_text(encoding="utf-8"))
            self.assertEqual(refusal["reason_code"], "http_success_block_or_error_page")
            refusal_inode = refusal_paths[0].stat().st_ino
            with (
                patch.object(
                    source_library_module,
                    "build_archive_project_catalog",
                    return_value=(),
                ),
                patch.object(
                    source_library_module,
                    "_paper_source_specs",
                    return_value={spec.doi: spec},
                ),
                self.assertRaisesRegex(ValueError, "refused capture"),
            ):
                refresh_source_library(output_root, downloader=blocked_downloader)
            self.assertEqual(refusal_paths[0].stat().st_ino, refusal_inode)

    def test_migrate_html_source_artifact_compresses_existing_capture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"
            article_path = (
                output_root
                / "adna"
                / "governance"
                / "source_library"
                / "papers"
                / "10.1000-example"
                / "article.html"
            )
            metadata_path = article_path.with_suffix(
                article_path.suffix + ".metadata.json"
            )
            article_path.parent.mkdir(parents=True, exist_ok=True)
            article_path.write_text("<html><body>ok</body></html>", encoding="utf-8")
            metadata_path.write_text(
                json.dumps(
                    {
                        "schema_version": "adna-source-library.v1",
                        "source_url": "https://example.test/article",
                        "artifact_kind": "article_html",
                        "content_type": "text/html; charset=utf-8",
                        "byte_size": 0,
                        "paper_doi": "10.1000/example",
                    }
                ),
                encoding="utf-8",
            )

            stored_path = migrate_html_source_artifact(
                article_path,
                output_root=output_root,
            )
            self.assertFalse(article_path.is_file())
            self.assertEqual(stored_path.name, "article.html.gz")
            self.assertTrue(stored_path.is_file())
            self.assertEqual(
                read_source_artifact_text(article_path),
                "<html><body>ok</body></html>",
            )
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            self.assertEqual(
                metadata["byte_size"], len(b"<html><body>ok</body></html>")
            )
            self.assertEqual(metadata["content_encoding"], "gzip")
            self.assertEqual(
                metadata["storage_path"],
                "adna/governance/source_library/papers/10.1000-example/article.html.gz",
            )
            self.assertEqual(metadata["storage_byte_size"], stored_path.stat().st_size)

    def test_migration_canonicalizes_equivalent_legacy_gzip_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"
            article_path = (
                output_root
                / "adna"
                / "governance"
                / "source_library"
                / "papers"
                / "10.1000-example"
                / "article.html"
            )
            compressed_path = article_path.with_name("article.html.gz")
            payload = b"<html><body>historical evidence</body></html>"
            article_path.parent.mkdir(parents=True, exist_ok=True)
            article_path.write_bytes(payload)

            legacy_buffer = io.BytesIO()
            with gzip.GzipFile(
                filename="",
                mode="wb",
                fileobj=legacy_buffer,
                mtime=1_782_099_554,
            ) as handle:
                handle.write(payload)
            compressed_path.write_bytes(legacy_buffer.getvalue())

            canonical_buffer = io.BytesIO()
            with gzip.GzipFile(
                filename="",
                mode="wb",
                fileobj=canonical_buffer,
                mtime=0,
            ) as handle:
                handle.write(payload)
            canonical_bytes = canonical_buffer.getvalue()
            self.assertNotEqual(compressed_path.read_bytes(), canonical_bytes)

            stored_path = migrate_html_source_artifact(
                article_path,
                output_root=output_root,
            )

            self.assertEqual(stored_path, compressed_path)
            self.assertFalse(article_path.exists())
            self.assertEqual(stored_path.read_bytes(), canonical_bytes)
            self.assertEqual(read_source_artifact_text(article_path).encode(), payload)
            canonical_identity = (stored_path.stat().st_ino, stored_path.read_bytes())

            repeated_path = migrate_html_source_artifact(
                article_path,
                output_root=output_root,
            )

            self.assertEqual(repeated_path, stored_path)
            self.assertEqual(
                (repeated_path.stat().st_ino, repeated_path.read_bytes()),
                canonical_identity,
            )

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
            self.assertGreater(storage_audit["compressed_html_artifact_count"], 0)
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


def _bounded_paper_spec() -> source_library_module._PaperSourceSpec:
    doi = "10.1000/source-capture"
    return source_library_module._PaperSourceSpec(
        doi=doi,
        article_source_url="https://example.test/article",
        article_local_path=(
            f"{source_library_module.ADNA_SOURCE_LIBRARY_DIR}/papers/"
            "10.1000-source-capture/article.html"
        ),
        article_kind="article_html",
        article_note="bounded source-capture fixture",
    )


if __name__ == "__main__":
    unittest.main()
