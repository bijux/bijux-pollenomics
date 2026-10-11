"""Shared source-library materialization fixture support."""

from __future__ import annotations

import io
from pathlib import Path
import shutil
import zipfile

from bijux_pollenomics.adna.sources.library import (
    materialize_source_library,
    refresh_source_library,
)
from bijux_pollenomics.adna.workflow.source_artifacts import read_source_artifact_bytes
from tests.support.repository import REPOSITORY_ROOT


def materialize_test_library(output_root: Path) -> Path:
    """Build one deterministic source library for all materialization assertions."""
    refresh_source_library(output_root, downloader=_fixture_downloader)
    source_dir = (
        "adna/governance/source_library/papers/10.1038-s41562-021-01083-y/supplementary"
    )
    for name in ("41562_2021_1083_MOESM1_ESM.pdf", "41562_2021_1083_MOESM2_ESM.pdf"):
        destination = output_root / source_dir / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPOSITORY_ROOT / "data" / source_dir / name, destination)
    camel_source_dir = "adna/governance/source_library/projects/SRP073444"
    for name in (
        "paper_table_s1_sample_bridge.csv",
        "paper_table_s1_sample_bridge.csv.metadata.json",
    ):
        destination = output_root / camel_source_dir / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPOSITORY_ROOT / "data" / camel_source_dir / name, destination)
    materialize_source_library(output_root)
    return output_root


def source_library_root(output_root: Path) -> Path:
    """Return the governed source-library publication root."""
    return output_root / "adna" / "governance" / "source_library"


def _fixture_downloader(url: str) -> tuple[bytes, str]:
    if url.endswith("/sra?term=SRP073444"):
        source_path = (
            REPOSITORY_ROOT
            / "data/adna/governance/source_library/projects/SRP073444/archive_metadata.html"
        )
        return (read_source_artifact_bytes(source_path), "text/html")
    if "accession=SRP073444&result=read_run" in url:
        source_path = (
            REPOSITORY_ROOT
            / "data/adna/governance/source_library/projects/SRP073444/ena_run_samples.tsv"
        )
        return (source_path.read_bytes(), "text/tab-separated-values")
    if any(
        f"accession={accession}" in url
        for accession in ("PRJEB41594", "PRJEB60484", "PRJNA705960")
    ):
        accession = next(
            accession
            for accession in ("PRJEB41594", "PRJEB60484", "PRJNA705960")
            if f"accession={accession}" in url
        )
        source_path = (
            REPOSITORY_ROOT
            / "data/adna/governance/source_library/projects"
            / accession
            / "archive_metadata.html"
        )
        return (read_source_artifact_bytes(source_path), "text/plain")
    if "/ena/browser/api/xml/SAMEA" in url:
        accession = url.rsplit("/", maxsplit=1)[-1]
        for project in ("PRJEB41594", "PRJEB59481", "PRJEB60484"):
            source_path = (
                REPOSITORY_ROOT
                / "data/adna/governance/source_library/projects"
                / project
                / "ena_samples"
                / f"{accession}.xml"
            )
            if source_path.is_file():
                return (source_path.read_bytes(), "application/xml")
        raise ValueError(f"Unrecognized official ENA fixture accession: {accession}")
    if "41598_2024_54296_MOESM2_ESM.xlsx" in url:
        source_path = (
            REPOSITORY_ROOT
            / "data/adna/governance/source_library/papers/10.1038-s41598-024-54296-2/"
            "supplementary/41598_2024_54296_MOESM2_ESM.xlsx"
        )
        return (
            source_path.read_bytes(),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    if url.endswith("2023.09.21.558762v1.full.pdf"):
        source_path = (
            REPOSITORY_ROOT
            / "data/adna/governance/source_library/papers/10.1111-mec.17274/author_preprint.pdf"
        )
        return (source_path.read_bytes(), "application/pdf")
    if "2023.09.21.558762/DC2/embed/media-2.xlsx" in url:
        source_path = (
            REPOSITORY_ROOT
            / "data/adna/governance/source_library/papers/10.1111-mec.17274/"
            "supplementary/author-preprint-table-s3.xlsx"
        )
        return (
            source_path.read_bytes(),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
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
