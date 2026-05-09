from __future__ import annotations

from collections.abc import Mapping
from urllib.parse import quote

from ....core.text import clean_optional_text

__all__ = [
    "SEAD_BROWSER_ROOT",
    "build_sead_site_access_model",
]

SEAD_BROWSER_ROOT = "https://browser.sead.se"


def build_sead_site_access_model(row: Mapping[str, object]) -> dict[str, object]:
    """Describe how one SEAD site can be inspected and what the repository mirrors."""
    site_id = str(row.get("site_id", "")).strip()
    site_name = str(row.get("site_name", "")).strip()
    site_page_url = f"{SEAD_BROWSER_ROOT}/site/{site_id}" if site_id else ""
    search_url = (
        f"{SEAD_BROWSER_ROOT}/sites?search={quote(site_name)}" if site_name else ""
    )

    reference_links: list[dict[str, str]] = []
    bibliography_rows = row.get("bibliography_rows")
    if isinstance(bibliography_rows, list):
        for bibliography_row in bibliography_rows:
            if not isinstance(bibliography_row, dict):
                continue
            url = clean_optional_text(bibliography_row.get("url"))
            doi = clean_optional_text(bibliography_row.get("doi"))
            if not url and doi:
                url = f"https://doi.org/{doi}"
            if not url:
                continue
            label = (
                clean_optional_text(bibliography_row.get("title"))
                or doi
                or f"SEAD reference {clean_optional_text(bibliography_row.get('biblio_id'))}"
            )
            reference_links.append({"label": label, "url": url})

    if site_page_url and reference_links:
        access_visibility = "site_page_with_reference_links"
    elif site_page_url:
        access_visibility = "site_page_only"
    else:
        access_visibility = "no_stable_public_link"

    access_limits = [
        "The repository mirrors site inventory and derived context layers, not the full upstream relational SEAD database."
    ]
    if not reference_links:
        access_limits.append(
            "No stable bibliography or dataset link is currently captured for this row, so readers may need to inspect the SEAD site page directly."
        )
    if not isinstance(row.get("dating_range_rows"), list) and not isinstance(
        row.get("relative_period_rows"), list
    ):
        access_limits.append(
            "This checked-in raw row behaves like a thin site inventory capture rather than a linked temporal dossier."
        )

    return {
        "schema_version": "sead-access-model.v1",
        "site_page_url": site_page_url,
        "search_url": search_url,
        "reference_links": reference_links,
        "access_visibility": access_visibility,
        "repository_posture": "mirrored_site_inventory_and_normalized_context",
        "redistribution_posture": "reference_upstream_pages_and_publish_repository_derived_context_only",
        "reader_action": (
            "Inspect the SEAD site page when the repository view is too thin for chronology or provenance review."
        ),
        "access_limits": access_limits,
    }
