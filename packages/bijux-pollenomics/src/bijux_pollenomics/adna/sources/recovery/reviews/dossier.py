"""Authoritative per-project recovery dossier assembly."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def build_dossier(
    output_root: Path,
    project_accession: str,
    *,
    surface: Any,
) -> dict[str, Any]:
    rows = {
        str(row["project_accession"]): row
        for row in surface._project_recovery_rows(output_root)
    }
    row = rows[project_accession]
    manual_rows = [
        item
        for item in surface.build_manual_curation_worklist(output_root)["rows"]
        if str(item["project_accession"]) == project_accession
    ]
    contradictory_evidence = []
    if surface._int_value(row["chronology_conflict_count"]) > 0:
        contradictory_evidence.append(
            f"{row['chronology_conflict_count']} chronology row(s) still disagree between sample-owned and context-level evidence."
        )
    if bool(row["publication_blocked_by_locality_substitution"]):
        contradictory_evidence.append(
            "Locality substitution review still blocks publication because project-level geography would flatten distinct sample evidence."
        )
    inferred_claims = []
    if surface._int_value(row["named_place_inferred_count"]) > 0:
        inferred_claims.append(
            f"{row['named_place_inferred_count']} site row(s) still depend on named-place inference."
        )
    if surface._int_value(row["sample_group_site_count"]) > 0:
        inferred_claims.append(
            f"{row['sample_group_site_count']} site row(s) still resolve only at a sample-group level."
        )
    return {
        "schema_version": "animal-project-recovery-dossier.v1",
        "project_accession": row["project_accession"],
        "species_latin_name": row["species_latin_name"],
        "paper_doi": row["paper_doi"],
        "archive_status": row["archive_status"],
        "evidence_strength": row["evidence_strength"],
        "inventory_disposition": row["inventory_disposition"],
        "stage_statuses": row["stage_statuses"],
        "blocking_stages": row["blocking_stages"],
        "next_required_stage": row["next_required_stage"],
        "publication_readiness_status": row["publication_readiness_status"],
        "expected_sample_count": row["expected_sample_count"],
        "expected_sample_count_status": row["expected_sample_count_status"],
        "expected_sample_count_provenance": row["expected_sample_count_provenance"],
        "expected_sample_count_artifact_path": row[
            "expected_sample_count_artifact_path"
        ],
        "minimum_expected_sample_count": row["minimum_expected_sample_count"],
        "recovered_sample_count": row["recovered_sample_count"],
        "final_sample_count": row["final_sample_count"],
        "unresolved_sample_count": row["unresolved_sample_count"],
        "minimum_gap_count": row["minimum_gap_count"],
        "recovery_gap_status": row["recovery_gap_status"],
        "implausibly_low_recovery": row["implausibly_low_recovery"],
        "implausibly_low_recovery_reason": row["implausibly_low_recovery_reason"],
        "known_assets": row["known_assets"],
        "missing_assets": row["missing_assets"],
        "expected_contributions": row["expected_contributions"],
        "expected_contribution_surfaces": row["expected_contribution_surfaces"],
        "contradictory_evidence": contradictory_evidence,
        "inferred_claims": inferred_claims,
        "manual_curation_work_units": manual_rows,
        "major_deficit_reasons": row["major_deficit_reasons"],
    }
