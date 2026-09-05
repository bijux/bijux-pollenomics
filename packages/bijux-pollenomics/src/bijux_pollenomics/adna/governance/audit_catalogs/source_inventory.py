from __future__ import annotations

from typing import TypedDict

from bijux_pollenomics.adna.projects.registry.context import (
    build_species_freshness_rows,
)
from bijux_pollenomics.adna.sources.ena import build_archive_project_catalog
from bijux_pollenomics.adna.species.tracked_species import TRACKED_ADNA_SPECIES
from .contracts import ArchiveInventoryRow, BibliographyRow


class _BibliographyGroup(TypedDict):
    paper_title: str
    paper_doi: str | None
    journal_title: str | None
    publication_year: int | None
    reference_kind: str
    species_latin_names: set[str]
    project_accessions: set[str]


class _ArchiveGroup(TypedDict):
    source_family: str
    project_accession: str
    metadata_url: str
    result_kind: str
    archive_status: str
    evidence_strength: object
    access_policy: str
    species_latin_names: set[str]


def build_cross_species_bibliography() -> tuple[BibliographyRow, ...]:
    """Deduplicate cited animal aDNA literature across all tracked species."""
    grouped: dict[str, _BibliographyGroup] = {}
    for project in build_archive_project_catalog():
        linkage = project.paper_linkage
        if linkage is None:
            continue
        key = linkage.doi or linkage.paper_title.casefold()
        current = grouped.setdefault(
            key,
            {
                "paper_title": linkage.paper_title,
                "paper_doi": linkage.doi,
                "journal_title": linkage.journal_title,
                "publication_year": linkage.publication_year,
                "reference_kind": linkage.reference_kind,
                "species_latin_names": set(),
                "project_accessions": set(),
            },
        )
        current["species_latin_names"].add(project.species_latin_name)
        current["project_accessions"].add(project.project_accession)
    rows: list[BibliographyRow] = []
    for row in grouped.values():
        rows.append(
            {
                "paper_title": row["paper_title"],
                "paper_doi": row["paper_doi"],
                "journal_title": row["journal_title"],
                "publication_year": row["publication_year"],
                "reference_kind": row["reference_kind"],
                "species_latin_names": sorted(row["species_latin_names"]),
                "project_accessions": sorted(row["project_accessions"]),
                "species_count": len(row["species_latin_names"]),
                "project_count": len(row["project_accessions"]),
            }
        )
    return tuple(
        sorted(
            rows,
            key=lambda item: (
                item["publication_year"] or 0,
                item["paper_title"].casefold(),
            ),
            reverse=True,
        )
    )


def build_cross_species_archive_inventory() -> tuple[ArchiveInventoryRow, ...]:
    """Deduplicate the tracked cross-species archive inventory."""
    grouped: dict[tuple[str, str], _ArchiveGroup] = {}
    for project in build_archive_project_catalog():
        key = (project.source_family, project.project_accession)
        current = grouped.setdefault(
            key,
            {
                "source_family": project.source_family,
                "project_accession": project.project_accession,
                "metadata_url": project.metadata_url,
                "result_kind": project.result_kind,
                "archive_status": project.archive_status,
                "evidence_strength": project.as_dict()["evidence_strength"],
                "access_policy": project.access_policy,
                "species_latin_names": set(),
            },
        )
        current["species_latin_names"].add(project.species_latin_name)
    rows: list[ArchiveInventoryRow] = []
    for row in grouped.values():
        rows.append(
            {
                "source_family": row["source_family"],
                "project_accession": row["project_accession"],
                "metadata_url": row["metadata_url"],
                "result_kind": row["result_kind"],
                "archive_status": row["archive_status"],
                "evidence_strength": row["evidence_strength"],
                "access_policy": row["access_policy"],
                "species_latin_names": sorted(row["species_latin_names"]),
                "species_count": len(row["species_latin_names"]),
            }
        )
    return tuple(
        sorted(
            rows, key=lambda item: (item["source_family"], item["project_accession"])
        )
    )


def build_species_freshness_table() -> tuple[dict[str, object], ...]:
    """Return one freshness row per tracked animal species."""
    rows = build_species_freshness_rows(build_archive_project_catalog())
    tracked = set(TRACKED_ADNA_SPECIES)
    return tuple(row for row in rows if row["species_latin_name"] in tracked)
