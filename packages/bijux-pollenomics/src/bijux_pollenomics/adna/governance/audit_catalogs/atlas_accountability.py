from __future__ import annotations

from pathlib import Path

from .contracts import AtlasAccountability, AtlasAccountabilityRow
from .repository import _load_all_sample_rows_by_id, _nested_string


def build_animal_atlas_candidate_accountability(data_root: Path) -> AtlasAccountability:
    """Require every checked-in final atlas candidate row to keep full evidence anchors."""
    from bijux_pollenomics.adna.governance.atlas_candidates import (
        build_tracked_animal_atlas_evidence_rows,
    )

    sample_lookup = _load_all_sample_rows_by_id(Path(data_root))
    rows: list[AtlasAccountabilityRow] = []
    passed_row_count = 0
    for row in build_tracked_animal_atlas_evidence_rows(Path(data_root)):
        matched_samples = [
            sample_lookup[sample_id]
            for sample_id in row.sample_record_ids
            if sample_id in sample_lookup
        ]
        sample_locality_tokens = sorted(
            {
                _nested_string(sample, "locality_identity", "stable_token")
                for sample in matched_samples
                if _nested_string(sample, "locality_identity", "stable_token")
            }
        )
        chronology_paths = sorted(
            {
                str(sample.get("chronology_provenance_path", "")).strip()
                for sample in matched_samples
                if str(sample.get("chronology_provenance_path", "")).strip()
            }
        )
        sample_lineage_paths = sorted(
            {
                str(sample.get("sample_lineage_path", "")).strip()
                for sample in matched_samples
                if str(sample.get("sample_lineage_path", "")).strip()
            }
        )
        row_payload: AtlasAccountabilityRow = {
            "evidence_row_id": row.evidence_row_id,
            "species_latin_name": row.species_latin_name,
            "project_accession": row.primary_project_accession,
            "site_record_id": row.site_record_id,
            "sample_record_ids": list(row.sample_record_ids),
            "sample_rows_present": bool(matched_samples),
            "sample_lineage_present": bool(sample_lineage_paths),
            "site_evidence_present": bool(
                row.source_artifact_path.strip() and row.source_locator.strip()
            ),
            "chronology_evidence_present": bool(chronology_paths)
            or (
                bool(row.chronology.original_text.strip())
                and str(row.chronology.evidence_class).strip() != "unresolved"
            ),
            "coordinate_provenance_present": bool(
                row.coordinate_source_artifact_path.strip()
                and row.coordinate_source_locator.strip()
            ),
            "sample_locality_matches_site_record": row.site_record_id
            in sample_locality_tokens,
            "sample_lineage_paths": sample_lineage_paths,
            "site_evidence_path": row.source_artifact_path,
            "site_evidence_locator": row.source_locator,
            "chronology_provenance_paths": chronology_paths,
            "coordinate_provenance_path": row.coordinate_source_artifact_path,
            "coordinate_provenance_locator": row.coordinate_source_locator,
            "fully_accountable": False,
        }
        row_payload["fully_accountable"] = all(
            (
                row_payload["sample_rows_present"],
                row_payload["sample_lineage_present"],
                row_payload["site_evidence_present"],
                row_payload["chronology_evidence_present"],
                row_payload["coordinate_provenance_present"],
                row_payload["sample_locality_matches_site_record"],
            )
        )
        if row_payload["fully_accountable"]:
            passed_row_count += 1
        rows.append(row_payload)
    return {
        "schema_version": "animal-atlas-candidate-accountability.v1",
        "candidate_row_count": len(rows),
        "passed_row_count": passed_row_count,
        "overall_ok": passed_row_count == len(rows),
        "rows": rows,
    }
