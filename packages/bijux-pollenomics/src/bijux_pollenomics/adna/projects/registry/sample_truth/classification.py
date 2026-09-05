"""Grounding classification and count derivation for animal samples."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import cast

StatusCounter = Callable[[list[dict[str, object]]], dict[str, int]]
SiteCounter = Callable[[list[dict[str, object]]], int]
ReadmeCounter = Callable[[Path], int | None]


def build_project_truth_row(
    *,
    species_latin_name: str,
    species_common_name: str,
    project_accession: str,
    sample_rows: list[dict[str, object]],
    locality_rows: list[dict[str, object]],
    status_counter: StatusCounter,
    site_counter: SiteCounter,
) -> dict[str, object]:
    status_counts = status_counter(sample_rows)
    sample_basis_values = {
        str(row.get("sample_basis", "")).strip()
        for row in sample_rows
        if str(row.get("sample_basis", "")).strip()
    }
    locality_summary_count = sum(
        1
        for row in locality_rows
        if project_accession
        in {
            str(item).strip()
            for item in cast(list[object], row.get("project_accessions", []))
            if str(item).strip()
        }
    )
    return {
        "species_latin_name": species_latin_name,
        "species_common_name": species_common_name,
        "project_accession": project_accession,
        "sample_row_count": len(sample_rows),
        "fully_grounded_count": status_counts["fully_grounded"],
        "partially_grounded_count": status_counts["partially_grounded"],
        "blocked_missing_metadata_count": status_counts["blocked_missing_metadata"],
        "blocked_missing_location_detail_count": status_counts[
            "blocked_missing_location_detail"
        ],
        "blocked_weak_chronology_count": status_counts["blocked_weak_chronology"],
        "sample_backed_site_count": site_counter(sample_rows),
        "project_locality_summary_count": locality_summary_count,
        "uses_project_level_sample_anchor": any(
            value in {"project_accession_anchor", "accession_range_anchor"}
            for value in sample_basis_values
        ),
        "sample_basis_values": sorted(sample_basis_values),
    }


def build_species_truth_row(
    *,
    species_latin_name: str,
    species_common_name: str,
    species_root: Path,
    sample_rows: list[dict[str, object]],
    project_rows: list[dict[str, object]],
    status_counter: StatusCounter,
    readme_counter: ReadmeCounter,
) -> dict[str, object]:
    status_counts = status_counter(sample_rows)
    readme_count = readme_counter(species_root / "README.md")
    return {
        "species_latin_name": species_latin_name,
        "species_common_name": species_common_name,
        "sample_row_count": len(sample_rows),
        "fully_grounded_count": status_counts["fully_grounded"],
        "partially_grounded_count": status_counts["partially_grounded"],
        "blocked_missing_metadata_count": status_counts["blocked_missing_metadata"],
        "blocked_missing_location_detail_count": status_counts[
            "blocked_missing_location_detail"
        ],
        "blocked_weak_chronology_count": status_counts["blocked_weak_chronology"],
        "project_count": len(project_rows),
        "reported_curated_sample_count": readme_count,
        "uses_project_level_sample_anchor": any(
            bool(row["uses_project_level_sample_anchor"]) for row in project_rows
        ),
    }


def status_counts(
    sample_rows: list[dict[str, object]],
    status_classifier: Callable[[dict[str, object]], str],
) -> dict[str, int]:
    counts = {
        "fully_grounded": 0,
        "partially_grounded": 0,
        "blocked_missing_metadata": 0,
        "blocked_missing_location_detail": 0,
        "blocked_weak_chronology": 0,
    }
    for row in sample_rows:
        counts[status_classifier(row)] += 1
    return counts


def sample_truth_status(sample_row: dict[str, object]) -> str:
    if not has_any_linkage(sample_row):
        return "blocked_missing_metadata"
    if str(sample_row.get("inclusion_status", "")) == "sample_context_blocked":
        return "blocked_missing_location_detail"
    chronology = sample_row.get("chronology", {})
    if not isinstance(chronology, dict):
        return "blocked_weak_chronology"
    if chronology.get("time_start_bp") is None or chronology.get("time_end_bp") is None:
        return "blocked_weak_chronology"
    coordinates = sample_row.get("coordinates", {})
    if not isinstance(coordinates, dict):
        return "partially_grounded"
    has_coordinates = bool(
        str(coordinates.get("latitude_text", "")).strip()
        and str(coordinates.get("longitude_text", "")).strip()
    )
    if has_coordinates and str(coordinates.get("confidence", "")).strip() != "withheld":
        return "fully_grounded"
    return "partially_grounded"


def has_any_linkage(sample_row: dict[str, object]) -> bool:
    return bool(
        str(sample_row.get("paper_doi", "")).strip()
        or str(sample_row.get("paper_url", "")).strip()
        or str(sample_row.get("supplementary_source", "")).strip()
    )


def sample_backed_site_count(sample_rows: list[dict[str, object]]) -> int:
    site_tokens: set[str] = set()
    for row in sample_rows:
        if str(row.get("inclusion_status", "")) == "archive_identity_only":
            # Archive-only identities preserve the project denominator but do not
            # assert a sample-owned locality. Their placeholder token therefore
            # cannot contribute to locality-summary reconciliation.
            continue
        locality_identity = row.get("locality_identity")
        if not isinstance(locality_identity, dict):
            continue
        if str(row.get("inclusion_status", "")) == "sample_context_blocked":
            continue
        token = str(locality_identity.get("stable_token", "")).strip()
        if token:
            site_tokens.add(token)
    return len(site_tokens)
