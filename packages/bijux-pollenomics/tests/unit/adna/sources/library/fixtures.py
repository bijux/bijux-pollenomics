"""Reusable aDNA source-library test specifications."""

from __future__ import annotations

from __future__ import annotations
from bijux_pollenomics.adna.sources import library as source_library_module


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
