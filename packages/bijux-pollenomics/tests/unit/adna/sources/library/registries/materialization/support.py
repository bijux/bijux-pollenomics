"""Shared source-library materialization fixture support."""

from __future__ import annotations

import io
from pathlib import Path
import zipfile

from bijux_pollenomics.adna.sources.library import (
    materialize_source_library,
    refresh_source_library,
)
from tests.support.repository import REPOSITORY_ROOT


def materialize_test_library(output_root: Path) -> Path:
    """Build one deterministic source library for all materialization assertions."""
    refresh_source_library(output_root, downloader=_fixture_downloader)
    materialize_source_library(output_root)
    return output_root


def source_library_root(output_root: Path) -> Path:
    """Return the governed source-library publication root."""
    return output_root / "adna" / "governance" / "source_library"


def _fixture_downloader(url: str) -> tuple[bytes, str]:
    if "/ena/browser/api/xml/SAMEA11296029" in url:
        accession = url.rsplit("/", maxsplit=1)[-1]
        source_path = (
            REPOSITORY_ROOT
            / "data/adna/governance/source_library/projects/PRJEB59481/ena_samples"
            / f"{accession}.xml"
        )
        return (source_path.read_bytes(), "application/xml")
    if url.endswith("PMC11162877/fullTextXML"):
        source_path = (
            REPOSITORY_ROOT
            / "data/adna/governance/source_library/papers/10.1093-gbe-evae114/"
            "article_full_text.xml"
        )
        return (source_path.read_bytes(), "application/xml")
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
