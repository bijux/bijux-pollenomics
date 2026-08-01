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
        "The repository mirrors the scoped site inventory, linked chronology and bibliography relations, and derived context layers, not the full upstream relational SEAD database."
    ]
    if not reference_links:
        access_limits.append(
            "Captured bibliography for this row exposes no directly followable DOI or URL, so readers may need to inspect the SEAD site page directly."
        )
    chronology_keys = (
        "dating_range_rows",
        "relative_period_rows",
        "analysis_entity_age_rows",
        "geochronology_rows",
        "dendro_date_rows",
    )
    if not any(
        isinstance(row.get(key), list) and row.get(key) for key in chronology_keys
    ):
        access_limits.append(
            "No linked upstream chronology is captured for this site, so it remains spatial context rather than a dated map observation."
        )

    return {
        "schema_version": "sead-access-model.v1",
        "site_page_url": site_page_url,
        "search_url": search_url,
        "reference_links": reference_links,
        "access_visibility": access_visibility,
        "repository_posture": "mirrored_relational_inventory_and_temporal_context",
        "redistribution_posture": "reference_upstream_pages_and_publish_repository_derived_context_only",
        "reader_action": (
            "Inspect the SEAD site page when captured chronology or bibliography does not answer the research question."
        ),
        "access_limits": access_limits,
    }
