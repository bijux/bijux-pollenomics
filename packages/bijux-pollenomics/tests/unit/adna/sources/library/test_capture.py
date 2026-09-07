"""aDNA source capture, storage, and drift-refusal tests."""

from __future__ import annotations

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
from bijux_pollenomics.adna.workflow.source_artifacts import (
    SourceArtifactContentDriftError,
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
