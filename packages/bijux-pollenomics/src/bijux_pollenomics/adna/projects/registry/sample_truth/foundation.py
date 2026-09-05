"""Species and project foundation-truth aggregation."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from .dependencies import SampleTruthDependencies


def build_animal_sample_foundation_truth(
    data_root: Path, *, dependencies: SampleTruthDependencies
) -> dict[str, object]:
    """Count sample-foundation truth classes across species and projects."""
    species_rows: list[dict[str, object]] = []
    project_rows: list[dict[str, object]] = []
    for species_name in dependencies.TRACKED_ADNA_SPECIES:
        species = dependencies.resolve_species_definition(species_name)
        species_root = dependencies._species_root(Path(data_root), species_name)
        sample_rows = dependencies._load_sample_rows(species_root)
        locality_rows = dependencies._load_locality_rows(species_root)
        species_project_rows: list[dict[str, object]] = []
        grouped_samples = dependencies._group_sample_rows_by_project(sample_rows)
        for project_accession, project_sample_rows in sorted(grouped_samples.items()):
            project_row = dependencies._build_project_truth_row(
                species_latin_name=species.latin_name,
                species_common_name=species.common_name,
                project_accession=project_accession,
                sample_rows=project_sample_rows,
                locality_rows=locality_rows,
            )
            project_rows.append(project_row)
            species_project_rows.append(project_row)
        species_rows.append(
            dependencies._build_species_truth_row(
                species_latin_name=species.latin_name,
                species_common_name=species.common_name,
                species_root=species_root,
                sample_rows=sample_rows,
                project_rows=species_project_rows,
            )
        )
    summary = {
        "tracked_species_count": len(species_rows),
        "tracked_project_count": len(project_rows),
        "sample_row_count": sum(
            cast(int, row["sample_row_count"]) for row in species_rows
        ),
        "fully_grounded_count": sum(
            cast(int, row["fully_grounded_count"]) for row in species_rows
        ),
        "partially_grounded_count": sum(
            cast(int, row["partially_grounded_count"]) for row in species_rows
        ),
        "blocked_missing_metadata_count": sum(
            cast(int, row["blocked_missing_metadata_count"]) for row in species_rows
        ),
        "blocked_missing_location_detail_count": sum(
            cast(int, row["blocked_missing_location_detail_count"])
            for row in species_rows
        ),
        "blocked_weak_chronology_count": sum(
            cast(int, row["blocked_weak_chronology_count"]) for row in species_rows
        ),
    }
    return {
        "schema_version": "animal-sample-foundation-truth.v1",
        "summary": summary,
        "species_rows": species_rows,
        "project_rows": project_rows,
    }
