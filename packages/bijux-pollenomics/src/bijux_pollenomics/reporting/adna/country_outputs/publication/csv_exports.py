from __future__ import annotations

import csv
from pathlib import Path

from ..models import CountryAnimalOutputBundle


def write_country_animal_samples_csv(
    path: Path, bundle: CountryAnimalOutputBundle
) -> None:
    """Write one CSV table of country-resolved animal sample rows."""
    fieldnames = (
        "country",
        "species_latin_name",
        "species_common_name",
        "source_native_tax_id",
        "source_native_scientific_name",
        "taxon_alignment_status",
        "sample_record_id",
        "sample_group_id",
        "sample_namespace",
        "feature_id",
        "evidence_row_id",
        "site_record_id",
        "project_accession",
        "paper_title",
        "paper_doi",
        "supplementary_source",
        "locality",
        "country_assignment_confidence",
        "country_assignment_reason",
        "coordinate_basis",
        "coordinate_confidence",
        "latitude_text",
        "longitude_text",
        "source_locator",
        "source_support_status",
        "sample_evidence_status",
        "sample_lineage_path",
        "sample_lineage_locator",
        "sample_lineage_excerpt",
        "chronology_provenance_path",
        "chronology_provenance_kind",
        "chronology_provenance_locator",
        "chronology_provenance_text",
        "chronology_normalization_status",
        "site_evidence_path",
        "site_evidence_kind",
        "site_evidence_locator",
        "site_evidence_text",
        "coordinate_provenance_path",
        "coordinate_provenance_locator",
        "coordinate_provenance_note",
        "time_label",
        "chronology_evidence_class",
        "chronology_precision_posture",
        "inclusion_status",
        "inclusion_note",
        "sample_basis",
    )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in bundle.sample_rows:
            writer.writerow(row)


def write_country_animal_species_csv(
    path: Path, bundle: CountryAnimalOutputBundle
) -> None:
    """Write one CSV table of country-resolved animal species rows."""
    fieldnames = (
        "country",
        "species_latin_name",
        "species_common_name",
        "animal_scope",
        "curated_project_count",
        "mapped_locality_count",
        "mapped_sample_count",
        "sample_row_count",
        "assignment_confidence",
        "coordinate_posture",
        "oldest_signal_bp",
        "youngest_signal_bp",
        "project_accessions",
        "sample_lineage_backed_sample_count",
        "site_evidence_backed_sample_count",
        "chronology_provenance_backed_sample_count",
        "coordinate_provenance_backed_sample_count",
        "exact_coordinate_sample_count",
        "approximate_coordinate_sample_count",
        "caution_note",
    )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in bundle.species_rows:
            project_accessions = row.get("project_accessions", [])
            writer.writerow(
                {
                    **row,
                    "project_accessions": ";".join(
                        str(item)
                        for item in (
                            project_accessions
                            if isinstance(project_accessions, list)
                            else []
                        )
                    ),
                }
            )
