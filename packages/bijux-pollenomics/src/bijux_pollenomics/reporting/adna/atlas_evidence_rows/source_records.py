"""Load source-native animal evidence records and review metadata."""

from __future__ import annotations

import csv
import json
from pathlib import Path

_PROJECT_SCOPE_RULES = {
    (
        "domesticated_core_curated",
        "domesticated_core",
        False,
    ): "domesticated_core",
    (
        "archive_pending_paper_linkage",
        "domesticated_core",
        False,
    ): "domesticated_core",
    (
        "wild_or_progenitor_context",
        "wild_or_progenitor_context",
        False,
    ): "wild_or_progenitor_context",
    ("comparator_only", "domesticated_core", True): "comparator",
    ("comparator_only", "ancient_comparator", True): "comparator",
}


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


def _load_project_animal_scope_lookup(species_root: Path) -> dict[str, str] | None:
    path = species_root / "normalized" / "project_summaries.json"
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return {}
    rows = payload.get("projects", [])
    if not isinstance(rows, list):
        return {}
    lookup: dict[str, str] = {}
    seen_accessions: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        accession = str(row.get("project_accession", "")).strip()
        if not accession:
            continue
        if accession in seen_accessions:
            lookup.pop(accession, None)
            continue
        seen_accessions.add(accession)
        comparator_status = row.get("comparator_status")
        if not isinstance(comparator_status, bool):
            continue
        rule = (
            str(row.get("support_class", "")).strip(),
            str(row.get("domestication_scope", "")).strip(),
            comparator_status,
        )
        scope = _PROJECT_SCOPE_RULES.get(rule)
        if scope is not None:
            lookup[accession] = scope
    return lookup


def _project_sample_animal_scope_for(
    species_root: Path,
    project_scope_lookup: dict[str, str] | None,
    *,
    project_accessions: tuple[str, ...],
    sample_rows: tuple[dict[str, object], ...],
) -> str | None:
    declared_projects = tuple(accession.strip() for accession in project_accessions)
    sample_projects = tuple(
        str(row.get("project_accession", "")).strip() for row in sample_rows
    )
    if (
        len(declared_projects) != 1
        or any(not accession for accession in declared_projects)
        or not sample_projects
        or any(not accession for accession in sample_projects)
        or set(sample_projects) != set(declared_projects)
    ):
        return None
    if project_scope_lookup is None:
        return _animal_scope_for(species_root)
    return project_scope_lookup.get(declared_projects[0])


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
