"""Project review summaries and sample-site ambiguity evidence."""

from __future__ import annotations

from pathlib import Path

from ....sources.archive import build_archive_project_catalog
from .assembly import build_project_sample_site_rows
from .evidence import _counts_by_status


def build_project_sample_site_review_rows(
    output_root: Path,
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for project in build_archive_project_catalog():
        sample_site_rows = build_project_sample_site_rows(
            output_root, project.project_accession
        )
        counts = _counts_by_status(sample_site_rows)
        lacking_count = (
            counts["project_level_site_only"]
            + counts["region_only"]
            + counts["unresolved"]
        )
        missing_reasons = [
            key
            for key in ("project_level_site_only", "region_only", "unresolved")
            if counts[key]
        ]
        rows.append(
            {
                "project_accession": project.project_accession,
                "species_latin_name": project.species_latin_name,
                "recovered_sample_row_count": len(sample_site_rows),
                "direct_sample_site_count": counts["direct_sample_site"],
                "sample_group_site_count": counts["sample_group_site"],
                "project_level_site_only_count": counts["project_level_site_only"],
                "named_place_inferred_count": counts["named_place_inferred"],
                "region_only_count": counts["region_only"],
                "unresolved_count": counts["unresolved"],
                "lacking_defensible_site_assignment_count": lacking_count,
                "missing_reasons": missing_reasons,
            }
        )
    return tuple(rows)


def build_sample_site_ambiguity_ledger(
    output_root: Path,
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    ambiguous_statuses = {
        "sample_group_site",
        "project_level_site_only",
        "region_only",
        "unresolved",
    }
    for project in build_archive_project_catalog():
        for row in build_project_sample_site_rows(
            output_root, project.project_accession
        ):
            if row.locality_resolution_status not in ambiguous_statuses:
                continue
            rows.append(
                {
                    "project_accession": row.project_accession,
                    "species_latin_name": row.species_latin_name,
                    "repo_stable_sample_id": row.repo_stable_sample_id,
                    "preferred_sample_label": row.preferred_sample_label,
                    "locality_resolution_status": row.locality_resolution_status,
                    "locality_text": row.locality_text,
                    "review_note": row.review_note,
                    "location_evidence_artifact_path": row.location_evidence_artifact_path,
                    "location_evidence_locator": row.location_evidence_locator,
                }
            )
    return tuple(rows)
