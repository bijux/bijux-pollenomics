"""Governed manual-curation work-unit construction."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def build_curation_worklist(output_root_key: str, *, surface: Any) -> dict[str, Any]:
    output_root = Path(output_root_key)
    chronology_gap_rows = {
        str(row["project_accession"]): surface._dynamic_row(row)
        for row in surface.build_date_evidence_gap_queue(output_root)
    }
    chronology_ambiguity_counts = surface._count_rows(
        surface.build_sample_chronology_ambiguity_ledger(output_root),
        key="project_accession",
    )
    chronology_conflict_counts = surface._count_rows(
        surface.build_sample_chronology_conflict_ledger(output_root),
        key="project_accession",
    )
    identity_ambiguity_counts = surface._count_rows(
        surface.build_sample_identity_ambiguity_ledger(output_root),
        key="project_accession",
    )

    rows: list[dict[str, Any]] = []
    for source_row in surface.build_sample_site_manual_curation_queue(output_root):
        row = surface._dynamic_row(source_row)
        rows.append(
            {
                "project_accession": row["project_accession"],
                "species_latin_name": row["species_latin_name"],
                "work_unit_type": "site_resolution",
                "work_unit_state": "pending_manual_curation",
                "open_item_count": row["queued_sample_count"],
                "rationale": "; ".join(row["queue_reasons"]),
                "downstream_impact": "blocks exact site, coordinate, and publication recovery",
                "recommended_source_surfaces": surface._nonempty_paths(
                    list(row["sample_site_targets"])
                    + list(row["expected_supplementary_artifacts"])
                    + list(row["local_artifact_paths"])
                ),
            }
        )
    for source_row in surface.build_sample_locality_manual_curation_workflow_rows(
        output_root
    ):
        row = surface._dynamic_row(source_row)
        rows.append(
            {
                "project_accession": row["project_accession"],
                "species_latin_name": row["species_latin_name"],
                "work_unit_type": "locality_string_resolution",
                "work_unit_state": row["decision_status"],
                "open_item_count": row["queued_sample_count"],
                "rationale": row["locality_resolution_status"]
                if not str(row["decision_rationale"]).strip()
                else row["decision_rationale"],
                "downstream_impact": "blocks coordinate derivation and exact locality publication",
                "recommended_source_surfaces": surface._nonempty_paths(
                    list(row["recommended_source_surfaces"])
                ),
            }
        )
    for project_accession, gap_row in chronology_gap_rows.items():
        open_item_count = (
            surface._int_value(gap_row["missing_date_count"])
            + surface._int_value(chronology_ambiguity_counts.get(project_accession, 0))
            + surface._int_value(chronology_conflict_counts.get(project_accession, 0))
        )
        if open_item_count <= 0:
            continue
        rows.append(
            {
                "project_accession": project_accession,
                "species_latin_name": gap_row["species_latin_name"],
                "work_unit_type": "chronology_recovery",
                "work_unit_state": "pending_source_recovery",
                "open_item_count": open_item_count,
                "rationale": "; ".join(gap_row["gap_reasons"]),
                "downstream_impact": "blocks chronology honesty and publication precision",
                "recommended_source_surfaces": [
                    f"{surface.ADNA_SOURCE_LIBRARY_DIR}/projects/{project_accession}/sample_chronology.json",
                    f"{surface.ADNA_SOURCE_LIBRARY_DIR}/projects/{project_accession}/intake_dossier.json",
                ],
            }
        )
    for project_accession, ambiguity_count in identity_ambiguity_counts.items():
        if surface._int_value(ambiguity_count) <= 0:
            continue
        rows.append(
            {
                "project_accession": project_accession,
                "species_latin_name": surface._project_species(project_accession),
                "work_unit_type": "sample_identity_resolution",
                "work_unit_state": "pending_manual_curation",
                "open_item_count": surface._int_value(ambiguity_count),
                "rationale": "Stable sample identity rows still carry unresolved ambiguity.",
                "downstream_impact": "blocks trustworthy project-level sample recovery counts",
                "recommended_source_surfaces": [
                    f"{surface.ADNA_SOURCE_LIBRARY_DIR}/projects/{project_accession}/sample_master.json"
                ],
            }
        )
    rows.sort(
        key=lambda item: (
            str(item["species_latin_name"]),
            str(item["project_accession"]),
            str(item["work_unit_type"]),
        )
    )
    return {
        "schema_version": "animal-manual-curation-worklist.v1",
        "row_count": len(rows),
        "counts": surface._count_rows(rows, key="work_unit_type"),
        "rows": rows,
    }
