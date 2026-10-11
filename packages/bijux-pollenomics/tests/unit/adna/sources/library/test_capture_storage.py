"""Stored aDNA source migration and cache behavior."""

from __future__ import annotations

import gzip
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from bijux_pollenomics.adna.sources import library as source_library_module
from bijux_pollenomics.adna.sources.library import storage as source_library_storage
from bijux_pollenomics.adna.workflow.source_artifacts import (
    migrate_html_source_artifact,
    read_source_artifact_text,
)


class OfficialSourceStorageTests(unittest.TestCase):
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
