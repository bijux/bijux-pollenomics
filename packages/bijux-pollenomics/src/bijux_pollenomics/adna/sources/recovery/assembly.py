from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from bijux_pollenomics.adna.projects.evidence.chronology import (
    build_date_evidence_gap_queue,
    build_project_sample_chronology_review_rows,
    build_sample_chronology_ambiguity_ledger,
    build_sample_chronology_conflict_ledger,
)
from bijux_pollenomics.adna.projects.evidence.localities import (
    build_project_locality_substitution_ledger,
)
from bijux_pollenomics.adna.projects.sample_master import (
    build_cross_project_sample_master_completeness,
)
from bijux_pollenomics.adna.projects.sample_master.tables.baltic_sheep import (
    build_baltic_sheep_material_conflicts,
)
from bijux_pollenomics.adna.projects.registry.sites import (
    build_project_sample_site_review_rows,
)
from bijux_pollenomics.adna.sources.library.registries import (
    build_paper_registry,
    build_project_registry,
    build_project_source_bundles,
)

from .metrics import (
    _cache_key,
    _coordinate_counts_by_project,
    _count_rows,
    _dynamic_row,
    _int_value,
)
from .policy import (
    _expected_contribution_surfaces,
    _expected_contributions,
    _implausibly_low_recovery,
    _known_assets,
    _major_deficit_reasons,
    _minimum_expected_sample_count,
    _missing_assets,
    _next_required_stage,
    _overall_recovery_status,
    _project_stage_statuses,
    _recovery_depth_score,
    _recovery_gap_status,
)


def _project_recovery_rows(output_root: Path) -> list[dict[str, Any]]:
    return list(_project_recovery_rows_cached(_cache_key(output_root)))


@lru_cache(maxsize=8)
def _project_recovery_rows_cached(
    output_root_key: str,
) -> tuple[dict[str, Any], ...]:
    output_root = Path(output_root_key)
    project_rows = list(build_project_registry(output_root))
    bundles = {
        bundle.project_accession: bundle
        for bundle in build_project_source_bundles(output_root)
    }
    paper_rows = {row.paper_doi: row for row in build_paper_registry(output_root)}
    sample_master_rows = {
        row["project_accession"]: _dynamic_row(row)
        for row in build_cross_project_sample_master_completeness(output_root)
    }
    site_review_rows = {
        row["project_accession"]: _dynamic_row(row)
        for row in build_project_sample_site_review_rows(output_root)
    }
    chronology_review_rows = {
        row["project_accession"]: _dynamic_row(row)
        for row in build_project_sample_chronology_review_rows(output_root)
    }
    chronology_gap_rows = {
        row["project_accession"]: _dynamic_row(row)
        for row in build_date_evidence_gap_queue(output_root)
    }
    chronology_ambiguity_counts = _count_rows(
        build_sample_chronology_ambiguity_ledger(output_root),
        key="project_accession",
    )
    chronology_conflict_counts = _count_rows(
        build_sample_chronology_conflict_ledger(output_root),
        key="project_accession",
    )
    locality_substitution_rows = {
        row["project_accession"]: _dynamic_row(row)
        for row in build_project_locality_substitution_ledger(output_root)
    }
    coordinate_counts = _coordinate_counts_by_project(output_root)
    baltic_material_conflicts = build_baltic_sheep_material_conflicts(output_root)

    rows: list[dict[str, Any]] = []
    for project_row in project_rows:
        bundle = bundles[project_row.project_accession]
        paper_row = (
            None
            if project_row.primary_paper_doi is None
            else paper_rows.get(project_row.primary_paper_doi)
        )
        sample_master_row = sample_master_rows.get(project_row.project_accession, {})
        site_row = site_review_rows.get(project_row.project_accession, {})
        chronology_row = chronology_review_rows.get(project_row.project_accession, {})
        gap_row = chronology_gap_rows.get(project_row.project_accession, {})
        substitution_row = locality_substitution_rows.get(
            project_row.project_accession, {}
        )
        coord_counts = coordinate_counts.get(project_row.project_accession, {})
        stage_statuses = _project_stage_statuses(
            project_row=project_row,
            bundle=bundle,
            paper_row=paper_row,
            sample_master_row=sample_master_row,
            site_row=site_row,
            chronology_row=chronology_row,
            coord_counts=coord_counts,
        )
        minimum_expected = _minimum_expected_sample_count(
            project_row, sample_master_row
        )
        final_sample_count = _int_value(
            sample_master_row.get("final_sample_count") or 0
        )
        minimum_gap_count = (
            None
            if minimum_expected is None
            else max(_int_value(minimum_expected) - final_sample_count, 0)
        )
        implausibly_low, implausibly_low_reason = _implausibly_low_recovery(
            project_row=project_row,
            sample_master_row=sample_master_row,
            minimum_gap_count=minimum_gap_count,
        )
        rows.append(
            {
                "project_accession": project_row.project_accession,
                "species_latin_name": project_row.species_latin_name,
                "paper_doi": project_row.primary_paper_doi or "",
                "archive_status": project_row.archive_status,
                "evidence_strength": project_row.evidence_strength,
                "inventory_disposition": project_row.inventory_disposition,
                "evidence_acquisition_state": project_row.evidence_acquisition_state,
                "expected_sample_count": project_row.expected_sample_count,
                "expected_sample_count_status": project_row.expected_sample_count_status,
                "expected_sample_count_provenance": project_row.expected_sample_count_provenance,
                "expected_sample_count_artifact_path": project_row.expected_sample_count_artifact_path,
                "minimum_expected_sample_count": minimum_expected,
                "recovered_sample_count": _int_value(
                    sample_master_row.get("recovered_sample_count") or 0
                ),
                "final_sample_count": final_sample_count,
                "unresolved_sample_count": sample_master_row.get(
                    "unresolved_sample_count"
                ),
                "minimum_gap_count": minimum_gap_count,
                "sample_identifier_status": project_row.sample_identifier_status,
                "sample_table_extraction_status": project_row.sample_table_extraction_status,
                "paper_download_status": project_row.paper_download_status,
                "supplement_download_status": project_row.supplement_download_status,
                "lacking_defensible_site_assignment_count": _int_value(
                    site_row.get("lacking_defensible_site_assignment_count") or 0
                ),
                "named_place_inferred_count": _int_value(
                    site_row.get("named_place_inferred_count") or 0
                ),
                "sample_group_site_count": _int_value(
                    site_row.get("sample_group_site_count") or 0
                ),
                "missing_chronology_count": _int_value(
                    gap_row.get("missing_date_count") or 0
                ),
                "chronology_conflict_count": _int_value(
                    chronology_conflict_counts.get(project_row.project_accession, 0)
                ),
                "chronology_ambiguity_count": _int_value(
                    chronology_ambiguity_counts.get(project_row.project_accession, 0)
                ),
                "material_evidence_expected_count": (
                    5 if project_row.project_accession == "PRJEB59481" else 0
                ),
                "material_evidence_conflict_count": (
                    len(baltic_material_conflicts)
                    if project_row.project_accession == "PRJEB59481"
                    else 0
                ),
                "mappable_coordinate_count": _int_value(
                    coord_counts.get("mappable_point", 0)
                ),
                "coordinate_blocked_count": _int_value(
                    coord_counts.get("refused_region_only", 0)
                )
                + _int_value(site_row.get("region_only_count") or 0)
                + _int_value(site_row.get("project_level_site_only_count") or 0),
                "publication_blocked_by_locality_substitution": bool(
                    substitution_row.get("publication_blocked")
                ),
                "expected_contributions": _expected_contributions(
                    project_row=project_row,
                    paper_row=paper_row,
                    site_row=site_row,
                    chronology_row=chronology_row,
                ),
                "expected_contribution_surfaces": _expected_contribution_surfaces(
                    project_row=project_row,
                    paper_row=paper_row,
                ),
                "stage_statuses": stage_statuses,
                "blocking_stages": [
                    stage
                    for stage, status in stage_statuses.items()
                    if status == "blocked"
                ],
                "next_required_stage": _next_required_stage(stage_statuses),
                "publication_readiness_status": stage_statuses["publication_readiness"],
                "overall_recovery_status": _overall_recovery_status(stage_statuses),
                "completed_stage_count": sum(
                    1 for status in stage_statuses.values() if status == "complete"
                ),
                "required_stage_count": sum(
                    1 for status in stage_statuses.values() if status != "not_required"
                ),
                "recovery_depth_score": _recovery_depth_score(stage_statuses),
                "recovery_gap_status": _recovery_gap_status(
                    project_row=project_row,
                    sample_master_row=sample_master_row,
                    minimum_gap_count=minimum_gap_count,
                ),
                "implausibly_low_recovery": implausibly_low,
                "implausibly_low_recovery_reason": implausibly_low_reason,
                "known_assets": _known_assets(project_row, bundle),
                "missing_assets": _missing_assets(
                    project_row=project_row,
                    bundle=bundle,
                    sample_master_row=sample_master_row,
                    site_row=site_row,
                    gap_row=gap_row,
                ),
                "major_deficit_reasons": _major_deficit_reasons(
                    project_row=project_row,
                    minimum_gap_count=minimum_gap_count,
                    site_row=site_row,
                    gap_row=gap_row,
                    coord_counts=coord_counts,
                    implausibly_low=implausibly_low,
                ),
            }
        )
    rows.sort(
        key=lambda item: (
            str(item["species_latin_name"]),
            str(item["project_accession"]),
        )
    )
    return tuple(rows)
