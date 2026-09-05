"""Drift checks between sample truth and summary surfaces."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from .dependencies import SampleTruthDependencies


def build_project_locality_count_drift(
    data_root: Path,
    *,
    dependencies: SampleTruthDependencies,
) -> tuple[dict[str, object], ...]:
    """Compare project locality summaries against sample-backed site counts."""
    rows: list[dict[str, object]] = []
    for species_name in dependencies.TRACKED_ADNA_SPECIES:
        species = dependencies.resolve_species_definition(species_name)
        species_root = dependencies._species_root(Path(data_root), species_name)
        sample_rows = dependencies._load_sample_rows(species_root)
        locality_rows = dependencies._load_locality_rows(species_root)
        grouped_samples = dependencies._group_sample_rows_by_project(sample_rows)
        for project_accession, project_sample_rows in sorted(grouped_samples.items()):
            sample_site_count = dependencies._sample_backed_site_count(
                project_sample_rows
            )
            locality_summary_count = sum(
                1
                for row in locality_rows
                if str(row.get("locality", "")).strip()
                and project_accession
                in {
                    str(item).strip()
                    for item in cast(list[object], row.get("project_accessions", []))
                    if str(item).strip()
                }
            )
            drift_detected = (
                sample_site_count > 0 and locality_summary_count != sample_site_count
            )
            rows.append(
                {
                    "species_latin_name": species.latin_name,
                    "project_accession": project_accession,
                    "sample_row_count": len(project_sample_rows),
                    "sample_backed_site_count": sample_site_count,
                    "project_locality_summary_count": locality_summary_count,
                    "drift_detected": drift_detected,
                }
            )
    return tuple(row for row in rows if bool(row["drift_detected"]))


def build_species_sample_count_drift(
    data_root: Path, *, dependencies: SampleTruthDependencies
) -> tuple[dict[str, object], ...]:
    """Compare species README sample claims against current sample-master counts."""
    rows: list[dict[str, object]] = []
    for species_name in dependencies.TRACKED_ADNA_SPECIES:
        species = dependencies.resolve_species_definition(species_name)
        species_root = dependencies._species_root(Path(data_root), species_name)
        sample_rows = dependencies._load_sample_rows(species_root)
        readme_count = dependencies._readme_curated_sample_count(
            species_root / "README.md"
        )
        if readme_count is None:
            continue
        drift_detected = readme_count != len(sample_rows)
        if not drift_detected:
            continue
        rows.append(
            {
                "species_latin_name": species.latin_name,
                "species_common_name": species.common_name,
                "readme_curated_sample_count": readme_count,
                "actual_sample_row_count": len(sample_rows),
                "drift_detected": drift_detected,
            }
        )
    return tuple(rows)
