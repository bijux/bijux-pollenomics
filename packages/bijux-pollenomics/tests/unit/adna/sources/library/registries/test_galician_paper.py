"""Use retained primary captures without assigning sample context or new custody."""

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics.adna.sources.archive import build_archive_project_catalog
from bijux_pollenomics.adna.sources.library import build_paper_registry
from bijux_pollenomics.adna.sources.library.specifications import (
    _expand_remote_assets,
    _paper_source_spec,
)
from bijux_pollenomics.adna.sources.library.storage import (
    _retained_galician_paper_artifacts,
)
from tests.support.repository import REPOSITORY_ROOT

DOI = "10.1371/journal.pone.0249537"
pytestmark = pytest.mark.generated_artifacts


def test_primary_paper_and_supplements_bind_existing_paths_without_acquisition() -> (
    None
):
    spec = _paper_source_spec(DOI)
    assert not _expand_remote_assets(spec, build_archive_project_catalog())
    artifacts = _retained_galician_paper_artifacts(
        REPOSITORY_ROOT / "data", spec, ("PRJNA705960",)
    )
    assert len(artifacts) == 4
    assert all(item.fetch_status == "archived" for item in artifacts)
    assert all(
        item.project_accessions == ("PRJNA705960",)
        and item.storage_path == item.local_path
        and (REPOSITORY_ROOT / "data" / item.local_path).is_file()
        for item in artifacts
    )
    paper = next(
        item
        for item in build_paper_registry(REPOSITORY_ROOT / "data")
        if item.paper_doi == DOI
    )
    assert paper.article_readability_status == "readable_html"
    assert paper.supplementary_count == 2
    assert paper.supplementary_download_status == "archived"


@pytest.mark.parametrize("source", ["article.html", "biosamples/SAMN18106827.xml"])
def test_changed_primary_or_biosample_bytes_refuse_retained_binding(
    monkeypatch: pytest.MonkeyPatch, source: str
) -> None:
    target = REPOSITORY_ROOT / "data/adna/review/galician_cattle" / source
    original = Path.read_bytes

    def read_bytes(path: Path) -> bytes:
        raw = original(path)
        return raw + b" " if path == target else raw

    monkeypatch.setattr(Path, "read_bytes", read_bytes)
    with pytest.raises(ValueError, match="retained source differs"):
        _retained_galician_paper_artifacts(
            REPOSITORY_ROOT / "data", _paper_source_spec(DOI), ("PRJNA705960",)
        )


def test_absent_retained_review_does_not_claim_archived_sources(tmp_path: Path) -> None:
    artifacts = _retained_galician_paper_artifacts(
        tmp_path / "data", _paper_source_spec(DOI), ("PRJNA705960",)
    )
    assert len(artifacts) == 4
    assert all(
        item.fetch_status == "missing" and item.byte_size is None for item in artifacts
    )
