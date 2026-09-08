from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class _CitationAccumulator:
    country: object
    species_latin_name: object
    species_common_name: object
    animal_scope: object
    project_accession: object
    paper_title: object
    paper_doi: object
    publication_year: object
    journal_title: object
    country_assignment_confidence: object
    sample_row_ids: set[str] = field(default_factory=set)
    locality_row_ids: set[str] = field(default_factory=set)
    supplementary_support: set[str] = field(default_factory=set)
    source_posture: set[str] = field(default_factory=set)


def build_citation_rows(
    country: str,
    localities: list[dict[str, object]],
    sample_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], _CitationAccumulator] = {}
    for row in localities:
        key = (str(row["species_latin_name"]), str(row["project_accession"]))
        current = grouped.setdefault(
            key,
            _CitationAccumulator(
                country=country,
                species_latin_name=row["species_latin_name"],
                species_common_name=row["species_common_name"],
                animal_scope=row["animal_scope"],
                project_accession=row["project_accession"],
                paper_title=row["paper_title"],
                paper_doi=row["paper_doi"],
                publication_year=row["publication_year"],
                journal_title=row["journal_title"],
                country_assignment_confidence=row["country_assignment_confidence"],
            ),
        )
        current.locality_row_ids.add(str(row["site_record_id"]))
        supplementary_sources = row.get("supplementary_sources", [])
        if isinstance(supplementary_sources, list):
            for source in supplementary_sources:
                source_text = str(source).strip()
                if source_text:
                    current.supplementary_support.add(source_text)
        source_status = str(row.get("source_support_status", "")).strip()
        if source_status:
            current.source_posture.add(source_status)
    for row in sample_rows:
        key = (str(row["species_latin_name"]), str(row["project_accession"]))
        sample_accumulator = grouped.get(key)
        if sample_accumulator is None:
            continue
        sample_accumulator.sample_row_ids.add(str(row["sample_record_id"]))
        supplementary_source = str(row.get("supplementary_source", "")).strip()
        if supplementary_source:
            sample_accumulator.supplementary_support.add(supplementary_source)
    output_rows = [_as_output_row(row) for row in grouped.values()]
    return sorted(
        output_rows,
        key=lambda row: (str(row["species_latin_name"]), str(row["project_accession"])),
    )


def _as_output_row(row: _CitationAccumulator) -> dict[str, object]:
    return {
        "country": row.country,
        "species_latin_name": row.species_latin_name,
        "species_common_name": row.species_common_name,
        "animal_scope": row.animal_scope,
        "project_accession": row.project_accession,
        "paper_title": row.paper_title,
        "paper_doi": row.paper_doi,
        "publication_year": row.publication_year,
        "journal_title": row.journal_title,
        "country_assignment_confidence": row.country_assignment_confidence,
        "sample_row_ids": sorted(row.sample_row_ids),
        "locality_row_ids": sorted(row.locality_row_ids),
        "sample_row_count": len(row.sample_row_ids),
        "locality_row_count": len(row.locality_row_ids),
        "supplementary_support": "; ".join(sorted(row.supplementary_support)),
        "source_posture": "; ".join(sorted(row.source_posture)),
    }
