"""Compressed source-artifact storage behavior."""

import json
from pathlib import Path
from typing import cast

from bijux_pollenomics.adna.sources.library import (
    build_source_artifact_index,
    build_source_storage_audit,
)
from bijux_pollenomics.adna.workflow.source_artifacts import read_source_artifact_text

from .support import source_library_root


def test_html_artifacts_are_compressed_without_changing_read_semantics(
    materialized_output_root: Path,
) -> None:
    root = source_library_root(materialized_output_root)
    article_path = root / "papers/10.1038-s41562-021-01083-y/article.html"
    archive_path = root / "projects/PRJEB36540/archive_metadata.html"

    assert not article_path.is_file()
    assert article_path.with_name("article.html.gz").is_file()
    assert not archive_path.is_file()
    assert archive_path.with_name("archive_metadata.html.gz").is_file()
    assert read_source_artifact_text(article_path) == "<html><body>ok</body></html>"
    assert read_source_artifact_text(archive_path) == "<html><body>ok</body></html>"

    for logical_path in (article_path, archive_path):
        metadata_path = logical_path.with_suffix(logical_path.suffix + ".metadata.json")
        metadata = json.loads(metadata_path.read_text("utf-8"))
        assert metadata["content_encoding"] == "gzip"
        assert metadata["storage_path"].endswith(".html.gz")


def test_storage_registry_and_audit_describe_compressed_html(
    materialized_output_root: Path,
) -> None:
    article_artifact = next(
        item
        for item in build_source_artifact_index(materialized_output_root)
        if item.local_path.endswith("10.1038-s41562-021-01083-y/article.html")
    )
    assert article_artifact.content_encoding == "gzip"
    assert str(article_artifact.storage_path).endswith(".html.gz")

    audit = build_source_storage_audit(materialized_output_root)
    assert cast(int, audit["compressed_html_artifact_count"]) > 0
    assert audit["uncompressed_html_artifact_count"] == 0
