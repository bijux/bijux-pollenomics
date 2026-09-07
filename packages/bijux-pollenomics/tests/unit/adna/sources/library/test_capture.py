"""aDNA source capture, storage, and drift-refusal tests."""

from __future__ import annotations

import gzip
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from bijux_pollenomics.adna.sources import library as source_library_module
from bijux_pollenomics.adna.sources.library import (
    acquisition as source_library_acquisition,
)
from bijux_pollenomics.adna.sources.library import (
    refresh_source_library,
)
from bijux_pollenomics.adna.sources.library import storage as source_library_storage
from bijux_pollenomics.adna.workflow.source_artifacts import (
    SourceArtifactContentDriftError,
    migrate_html_source_artifact,
    read_source_artifact_text,
    write_source_artifact_bytes,
)
from tests.support.repository import REPOSITORY_ROOT

from .fixtures import _bounded_paper_spec

DATA_ROOT = REPOSITORY_ROOT / "data"


class SourceCaptureTests(unittest.TestCase):
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
                    source_library_acquisition,
                    "build_archive_project_catalog",
                    return_value=(),
                ),
                patch.object(
                    source_library_acquisition,
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
                    source_library_acquisition,
                    "build_archive_project_catalog",
                    return_value=(),
                ),
                patch.object(
                    source_library_acquisition,
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

    def test_xml_capture_rejects_html_and_wrong_official_roots(self) -> None:
        ena_path = Path(
            "adna/governance/source_library/projects/PRJEB59481/ena_samples/"
            "SAMEA112960291.xml"
        )
        article_path = Path(
            "adna/governance/source_library/papers/10.1093-gbe-evae114/"
            "article_full_text.xml"
        )

        self.assertEqual(
            source_library_acquisition._xml_capture_refusal_reason(
                logical_path=ena_path,
                payload=b"<html/>",
                content_type="text/html",
            ),
            "xml_source_returned_non_xml_media_type",
        )
        self.assertEqual(
            source_library_acquisition._xml_capture_refusal_reason(
                logical_path=ena_path,
                payload=b"<article/>",
                content_type="application/xml",
            ),
            "ena_sample_source_root_mismatch",
        )
        self.assertEqual(
            source_library_acquisition._xml_capture_refusal_reason(
                logical_path=article_path,
                payload=b"<SAMPLE_SET/>",
                content_type="application/xml",
            ),
            "article_full_text_source_root_mismatch",
        )
        self.assertEqual(
            source_library_acquisition._xml_capture_refusal_reason(
                logical_path=ena_path,
                payload=b"<SAMPLE_SET/>",
                content_type="application/xml",
            ),
            "ena_sample_source_semantic_mismatch",
        )
        self.assertEqual(
            source_library_acquisition._xml_capture_refusal_reason(
                logical_path=article_path,
                payload=b"<article/>",
                content_type="application/xml",
            ),
            "article_full_text_source_semantic_mismatch",
        )

    def test_xml_capture_refuses_entity_declarations(self) -> None:
        ena_path = Path(
            "adna/governance/source_library/projects/PRJEB59481/ena_samples/"
            "SAMEA112960291.xml"
        )
        payload = (
            b'<!DOCTYPE SAMPLE_SET [<!ENTITY source SYSTEM "file:///etc/passwd">]>'
            b"<SAMPLE_SET>&source;</SAMPLE_SET>"
        )

        self.assertEqual(
            source_library_acquisition._xml_capture_refusal_reason(
                logical_path=ena_path,
                payload=payload,
                content_type="application/xml",
            ),
            "unsafe_xml_source_payload",
        )

    def test_xml_capture_refuses_dtd_attribute_defaults(self) -> None:
        ena_path = Path(
            "adna/governance/source_library/projects/PRJEB59481/ena_samples/"
            "SAMEA112960291.xml"
        )
        payload = (
            b"<!DOCTYPE SAMPLE_SET [<!ATTLIST SAMPLE accession CDATA "
            b'"SAMEA112960291" alias CDATA "AKAS001">]>'
            b"<SAMPLE_SET><SAMPLE/></SAMPLE_SET>"
        )

        self.assertEqual(
            source_library_acquisition._xml_capture_refusal_reason(
                logical_path=ena_path,
                payload=payload,
                content_type="application/xml",
            ),
            "unsafe_xml_source_payload",
        )

    def test_xml_capture_accepts_a_declaration_only_doctype(self) -> None:
        payload = (
            b'<!DOCTYPE article PUBLIC "-//NLM//DTD JATS (Z39.96) Journal '
            b'Archiving and Interchange DTD with MathML3 v1.4 20241031//EN" '
            b'"JATS-archivearticle1-4-mathml3.dtd">'
            b"<article><title>Safe</title></article>"
        )

        self.assertIsNone(
            source_library_acquisition._xml_capture_refusal_reason(
                logical_path=Path("papers/article_full_text.xml"),
                payload=payload,
                content_type="application/xml",
            )
        )

    def test_official_xml_capture_uses_full_artifact_semantics(self) -> None:
        ena_path = Path(
            "adna/governance/source_library/projects/PRJEB59481/ena_samples/"
            "SAMEA112960291.xml"
        )
        article_path = Path(
            "adna/governance/source_library/papers/10.1093-gbe-evae114/"
            "article_full_text.xml"
        )
        ena_payload = (DATA_ROOT / ena_path).read_bytes()
        article_payload = (DATA_ROOT / article_path).read_bytes()

        self.assertIsNone(
            source_library_acquisition._xml_capture_refusal_reason(
                logical_path=ena_path,
                payload=ena_payload,
                content_type="application/xml",
            )
        )
        self.assertIsNone(
            source_library_acquisition._xml_capture_refusal_reason(
                logical_path=article_path,
                payload=article_payload,
                content_type="application/xml",
            )
        )
        self.assertEqual(
            source_library_acquisition._xml_capture_refusal_reason(
                logical_path=ena_path,
                payload=ena_payload.replace(b"60.23", b"60.24"),
                content_type="application/xml",
            ),
            "ena_sample_source_semantic_mismatch",
        )
        self.assertEqual(
            source_library_acquisition._xml_capture_refusal_reason(
                logical_path=article_path,
                payload=article_payload.replace(b"PMC11162877", b"PMC00000000", 1),
                content_type="application/xml",
            ),
            "article_full_text_source_semantic_mismatch",
        )

    def test_identical_official_xml_refuses_missing_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"
            logical_path = (
                output_root
                / "adna/governance/source_library/projects/PRJEB59481/ena_samples/"
                "SAMEA112960291.xml"
            )
            payload = (
                DATA_ROOT
                / "adna/governance/source_library/projects/PRJEB59481/ena_samples/"
                "SAMEA112960291.xml"
            ).read_bytes()
            logical_path.parent.mkdir(parents=True, exist_ok=True)
            logical_path.write_bytes(payload)

            assessment = source_library_acquisition._assess_downloaded_source_capture(
                output_root=output_root,
                logical_path=logical_path,
                source_url=("https://www.ebi.ac.uk/ena/browser/api/xml/SAMEA112960291"),
                payload=payload,
                content_type="application/xml",
            )

            self.assertEqual(assessment.disposition.value, "refused")
            self.assertIsNotNone(assessment.refusal_path)
            assert assessment.refusal_path is not None
            refusal = json.loads(assessment.refusal_path.read_text(encoding="utf-8"))
            self.assertEqual(refusal["reason_code"], "official_source_receipt_mismatch")

    def test_identical_official_xml_refuses_stale_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"
            relative_path = Path(
                "adna/governance/source_library/projects/PRJEB59481/ena_samples/"
                "SAMEA112960291.xml"
            )
            logical_path = output_root / relative_path
            source_path = DATA_ROOT / relative_path
            receipt_path = logical_path.with_suffix(".xml.metadata.json")
            logical_path.parent.mkdir(parents=True, exist_ok=True)
            payload = source_path.read_bytes()
            logical_path.write_bytes(payload)
            receipt = json.loads(
                source_path.with_suffix(".xml.metadata.json").read_text(
                    encoding="utf-8"
                )
            )
            receipt["content_sha256"] = "0" * 64
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

            assessment = source_library_acquisition._assess_downloaded_source_capture(
                output_root=output_root,
                logical_path=logical_path,
                source_url=("https://www.ebi.ac.uk/ena/browser/api/xml/SAMEA112960291"),
                payload=payload,
                content_type="application/xml",
            )

            self.assertEqual(assessment.disposition.value, "refused")
            self.assertIsNotNone(assessment.refusal_path)

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
                    source_library_acquisition,
                    "build_archive_project_catalog",
                    return_value=(),
                ),
                patch.object(
                    source_library_acquisition,
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
                    source_library_acquisition,
                    "build_archive_project_catalog",
                    return_value=(),
                ),
                patch.object(
                    source_library_acquisition,
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
                source_library_storage,
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
