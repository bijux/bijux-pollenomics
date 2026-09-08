"""Reference-stash reconciliation and DOI-integrity evidence."""

from __future__ import annotations

from collections.abc import Sized
from pathlib import Path
from typing import cast

from ..library.registries import build_paper_registry
from ..library.specifications import _doi_slug
from ..library.storage import _reference_stash_records, _resolve_reference_stash_root
from .model import SOURCE_INVENTORY_SCHEMA_VERSION, _count_by


def build_reference_stash_reconciliation(output_root: Path) -> dict[str, object]:
    """Compare tracked repo capture against the local reference stash without overstating repo completeness."""
    paper_rows = {row.paper_doi: row for row in build_paper_registry(output_root)}
    stash_records = _reference_stash_records(output_root)
    rows: list[dict[str, object]] = []
    all_slugs = sorted({_doi_slug(doi) for doi in paper_rows} | set(stash_records))
    for slug in all_slugs:
        paper_row = next(
            (row for doi, row in paper_rows.items() if _doi_slug(doi) == slug),
            None,
        )
        stash_record = cast(dict[str, object], stash_records.get(slug, {}))
        rows.append(
            {
                "stash_slug": slug,
                "paper_doi": "" if paper_row is None else paper_row.paper_doi,
                "paper_registry_present": paper_row is not None,
                "repository_article_capture_status": (
                    "missing"
                    if paper_row is None
                    else paper_row.article_download_status
                ),
                "repository_supplement_capture_status": (
                    "missing"
                    if paper_row is None
                    else paper_row.supplementary_download_status
                ),
                "local_reference_article_status": (
                    "local_reference_staged"
                    if stash_record.get("article_formats")
                    else "missing"
                ),
                "local_reference_supplement_status": (
                    "local_reference_staged"
                    if stash_record.get("supplementary_assets")
                    else "missing"
                ),
                "repository_supplementary_count": (
                    0 if paper_row is None else int(paper_row.supplementary_count)
                ),
                "local_reference_supplementary_asset_count": len(
                    cast(Sized, stash_record.get("supplementary_assets", ()))
                ),
                "alignment_status": _reconciliation_alignment_status(
                    paper_row, stash_record
                ),
            }
        )
    return {
        "schema_version": SOURCE_INVENTORY_SCHEMA_VERSION,
        "reference_stash_visible": _resolve_reference_stash_root(output_root)
        is not None,
        "row_count": len(rows),
        "counts": _count_by(rows, "alignment_status"),
        "rows": rows,
    }


def build_reference_stash_doi_integrity_audit(output_root: Path) -> dict[str, object]:
    """Verify that every DOI visible in the local reference stash is represented in the tracked paper registry."""
    paper_rows = {row.paper_doi: row for row in build_paper_registry(output_root)}
    tracked_slugs = {_doi_slug(doi): doi for doi in paper_rows}
    stash_records = _reference_stash_records(output_root)
    rows = []
    for slug in sorted(set(tracked_slugs) | set(stash_records)):
        paper_doi = tracked_slugs.get(slug, "")
        rows.append(
            {
                "stash_slug": slug,
                "paper_doi": paper_doi,
                "represented_in_paper_registry": bool(paper_doi),
                "representation_status": (
                    "matched"
                    if slug in tracked_slugs and slug in stash_records
                    else (
                        "tracked_without_local_reference"
                        if slug in tracked_slugs
                        else "local_reference_not_tracked"
                    )
                ),
            }
        )
    missing_in_registry = [
        row["stash_slug"] for row in rows if not row["represented_in_paper_registry"]
    ]
    missing_in_stash = [
        row["paper_doi"]
        for row in rows
        if row["paper_doi"]
        and row["representation_status"] == "tracked_without_local_reference"
    ]
    return {
        "schema_version": SOURCE_INVENTORY_SCHEMA_VERSION,
        "reference_stash_visible": _resolve_reference_stash_root(output_root)
        is not None,
        "paper_registry_doi_count": len(paper_rows),
        "reference_stash_doi_count": len(stash_records),
        "all_stash_dois_tracked": len(missing_in_registry) == 0,
        "missing_in_paper_registry": missing_in_registry,
        "tracked_without_local_reference": missing_in_stash,
        "rows": rows,
    }


def _reconciliation_alignment_status(
    paper_row: object | None, stash_record: dict[str, object]
) -> str:
    repo_supplements = (
        0 if paper_row is None else int(getattr(paper_row, "supplementary_count", 0))
    )
    stash_supplements = len(cast(Sized, stash_record.get("supplementary_assets", ())))
    if paper_row is not None and stash_supplements == repo_supplements:
        return "aligned"
    if paper_row is not None and stash_supplements > repo_supplements:
        return "local_reference_ahead_of_repo"
    if paper_row is not None:
        return "repo_ahead_of_local_reference"
    return "local_reference_not_tracked"
