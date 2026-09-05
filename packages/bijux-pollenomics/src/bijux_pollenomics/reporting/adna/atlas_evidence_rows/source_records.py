"""Load source-native animal evidence records and review metadata."""

from __future__ import annotations

import csv
import json
from pathlib import Path


def _load_locality_rows(species_root: Path) -> list[dict[str, object]]:
    path = species_root / "normalized" / "locality_summaries.json"
    if not path.is_file():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("localities", [])
    return [row for row in rows if isinstance(row, dict)]


def _load_sample_rows(species_root: Path) -> list[dict[str, object]]:
    path = species_root / "normalized" / "sample_records.json"
    if not path.is_file():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("samples", [])
    return [row for row in rows if isinstance(row, dict)]


def _load_coordinate_provenance_lookup(
    species_root: Path,
) -> dict[tuple[str, str], dict[str, object]]:
    path = species_root / "normalized" / "coordinate_provenance.json"
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("coordinate_provenance", [])
    lookup: dict[tuple[str, str], dict[str, object]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        project_accession = str(row.get("project_accession", "")).strip()
        if not project_accession:
            continue
        site_label = str(row.get("site_label", "")).strip()
        lookup[(project_accession, site_label)] = row
    return lookup


def _load_site_evidence_lookup(
    species_root: Path,
) -> dict[tuple[str, str], dict[str, object]]:
    path = species_root / "normalized" / "site_evidence.json"
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("site_evidence", [])
    lookup: dict[tuple[str, str], dict[str, object]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        project_accession = str(row.get("project_accession", "")).strip()
        if not project_accession:
            continue
        site_label = str(row.get("site_label", "")).strip()
        lookup[(project_accession, site_label)] = row
    return lookup


def _lookup_project_locality_row(
    lookup: dict[tuple[str, str], dict[str, object]],
    *,
    project_accession: str,
    locality_text: str,
) -> dict[str, object] | None:
    return lookup.get((project_accession, locality_text))


def _load_citation_lookup(species_root: Path) -> dict[str, dict[str, str]]:
    path = species_root / "manifests" / "citation_manifest.csv"
    if not path.is_file():
        return {}
    lookup: dict[str, dict[str, str]] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            accession = str(row.get("project_accession", "")).strip()
            if not accession:
                continue
            lookup[accession] = {
                "paper_title": str(row.get("paper_title", "")).strip(),
                "paper_doi": str(row.get("paper_doi", "")).strip(),
                "publication_year": str(row.get("publication_year", "")).strip(),
                "journal_title": str(row.get("journal_title", "")).strip(),
            }
    return lookup


def _load_review_lookup(species_root: Path) -> dict[str, dict[str, str]]:
    path = species_root / "review" / "species_review.json"
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    lookup: dict[str, dict[str, str]] = {}
    for key in (
        "accepted_projects",
        "rejected_projects",
        "too_weak_projects",
        "comparator_projects",
        "nordic_unmapped_leads",
    ):
        rows = payload.get(key, [])
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            accession = str(row.get("project_accession", "")).strip()
            if accession:
                lookup[accession] = {
                    "support_class": str(row.get("support_class", "")),
                    "reason": str(row.get("reason", "")),
                    "paper_title": str(row.get("paper_title", "")),
                    "paper_doi": str(row.get("paper_doi", "")),
                }
    return lookup


def _animal_scope_for(species_root: Path) -> str:
    payload = json.loads(
        (species_root / "reports" / "support_summary.json").read_text(encoding="utf-8")
    )
    dataset_review = payload.get("dataset_review", {})
    return (
        "comparator"
        if isinstance(dataset_review, dict)
        and str(dataset_review.get("product_role", "")).strip() == "comparator"
        else "domesticated_core"
    )
