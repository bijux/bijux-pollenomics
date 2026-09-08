from __future__ import annotations

from bijux_pollenomics.adna.domain.models.vocabularies import (
    ADNA_APPROXIMATE_COORDINATE_CONFIDENCE,
)


def build_evidence_quality_summary(
    *,
    sample_rows: list[dict[str, object]],
    species_rows: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "sample_row_count": len(sample_rows),
        "species_row_count": len(species_rows),
        "sample_lineage_backed_sample_count": sum(
            1 for row in sample_rows if str(row.get("sample_lineage_path", "")).strip()
        ),
        "site_evidence_backed_sample_count": sum(
            1 for row in sample_rows if str(row.get("site_evidence_path", "")).strip()
        ),
        "chronology_provenance_backed_sample_count": sum(
            1
            for row in sample_rows
            if str(row.get("chronology_provenance_path", "")).strip()
        ),
        "coordinate_provenance_backed_sample_count": sum(
            1
            for row in sample_rows
            if str(row.get("coordinate_provenance_path", "")).strip()
        ),
        "exact_coordinate_sample_count": sum(
            1
            for row in sample_rows
            if str(row.get("coordinate_confidence", "")).strip() == "exact"
        ),
        "approximate_coordinate_sample_count": sum(
            1
            for row in sample_rows
            if str(row.get("coordinate_confidence", "")).strip()
            in ADNA_APPROXIMATE_COORDINATE_CONFIDENCE
        ),
    }


def build_traceability_summary(
    *,
    sample_rows: list[dict[str, object]],
    locality_rows: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "sample_record_ids": sorted(
            {
                str(row.get("sample_record_id", "")).strip()
                for row in sample_rows
                if str(row.get("sample_record_id", "")).strip()
            }
        ),
        "site_record_ids": sorted(
            {
                str(row.get("site_record_id", "")).strip()
                for row in locality_rows
                if str(row.get("site_record_id", "")).strip()
            }
        ),
        "sample_lineage_paths": sorted(
            {
                str(row.get("sample_lineage_path", "")).strip()
                for row in sample_rows
                if str(row.get("sample_lineage_path", "")).strip()
            }
        ),
        "site_evidence_paths": sorted(
            {
                str(row.get("source_artifact_path", "")).strip()
                for row in locality_rows
                if str(row.get("source_artifact_path", "")).strip()
            }
        ),
        "chronology_provenance_paths": sorted(
            {
                str(row.get("chronology_provenance_path", "")).strip()
                for row in sample_rows
                if str(row.get("chronology_provenance_path", "")).strip()
            }
        ),
        "coordinate_provenance_paths": sorted(
            {
                str(row.get("coordinate_provenance_path", "")).strip()
                for row in sample_rows
                if str(row.get("coordinate_provenance_path", "")).strip()
            }
        ),
    }


def published_chronology_value(
    value: int | None,
    precision_posture: str,
) -> int | None:
    """Publish admitted numeric chronology without hiding its caveat posture."""
    if precision_posture not in {
        "sample_precise_point",
        "sample_precise_interval",
        "sample_approximate_or_modeled",
        "contextual_interval",
    }:
        return None
    return value
