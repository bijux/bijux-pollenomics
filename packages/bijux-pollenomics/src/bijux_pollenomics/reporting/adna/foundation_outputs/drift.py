"""Animal foundation drift responsibilities."""

from __future__ import annotations
from typing import Any, cast
from pathlib import Path
from ..atlas_evidence_rows import build_tracked_animal_atlas_evidence_rows
from .repository import (
    _group_coordinate_rows_by_species,
    _group_sample_rows_by_species,
    _group_site_rows_by_species,
    _load_country_payloads,
)


def build_animal_cross_surface_drift_report(
    *,
    data_root: Path,
    report_root: Path,
) -> dict[str, Any]:
    """Compare counts and traceability across normalized, atlas, and country outputs."""
    atlas_rows: list[dict[str, Any]] = [
        cast(dict[str, Any], row.as_dict())
        for row in build_tracked_animal_atlas_evidence_rows(data_root)
    ]
    atlas_by_species: dict[str, list[dict[str, Any]]] = {}
    for row in atlas_rows:
        atlas_by_species.setdefault(str(row.get("species_latin_name", "")), []).append(
            row
        )
    country_payloads = _load_country_payloads(report_root)
    rows: list[dict[str, Any]] = []
    for species_name, sample_rows in _group_sample_rows_by_species(data_root).items():
        site_rows = _group_site_rows_by_species(data_root).get(species_name, [])
        provenance_rows = _group_coordinate_rows_by_species(data_root).get(
            species_name, []
        )
        atlas_species_rows = atlas_by_species.get(species_name, [])
        country_sample_count = 0
        country_locality_count = 0
        for payload in country_payloads:
            for row in payload.get("sample_rows", []):
                if str(row.get("species_latin_name", "")) == species_name:
                    country_sample_count += 1
            for row in payload.get("localities", []):
                if str(row.get("species_latin_name", "")) == species_name:
                    country_locality_count += 1
        sample_ids = {
            str(row.get("identity", {}).get("stable_token", "")).strip()
            for row in sample_rows
            if str(row.get("identity", {}).get("stable_token", "")).strip()
        }
        provenance_projects = {
            str(row.get("project_accession", "")).strip()
            for row in provenance_rows
            if str(row.get("project_accession", "")).strip()
        }
        site_projects = {
            str(row.get("project_accession", "")).strip()
            for row in site_rows
            if str(row.get("project_accession", "")).strip()
        }
        findings: list[str] = []
        for row in atlas_species_rows:
            row_sample_ids = {
                str(item) for item in row.get("sample_record_ids", []) if str(item)
            }
            if not row_sample_ids.issubset(sample_ids):
                findings.append("atlas_rows_reference_unknown_sample_ids")
                break
        for row in atlas_species_rows:
            project = str(row.get("primary_project_accession", "")).strip()
            if project and (
                project not in provenance_projects or project not in site_projects
            ):
                findings.append("atlas_rows_reference_unlinked_project_evidence")
                break
        if country_locality_count > len(atlas_species_rows):
            findings.append("country_locality_rows_exceed_shared_atlas_rows")
        atlas_sample_count = sum(
            int(row.get("sample_count", 0) or 0) for row in atlas_species_rows
        )
        if country_sample_count > atlas_sample_count:
            findings.append("country_sample_rows_exceed_shared_atlas_sample_counts")
        rows.append(
            {
                "species_latin_name": species_name,
                "normalized_sample_row_count": len(sample_rows),
                "normalized_site_evidence_count": len(site_rows),
                "normalized_coordinate_row_count": len(provenance_rows),
                "mappable_coordinate_row_count": sum(
                    1
                    for row in provenance_rows
                    if str(row.get("mapping_posture", "")) == "mappable_point"
                ),
                "atlas_evidence_row_count": len(atlas_species_rows),
                "atlas_evidence_sample_count": atlas_sample_count,
                "published_country_sample_count": country_sample_count,
                "published_country_locality_count": country_locality_count,
                "drift_detected": bool(findings),
                "findings": findings,
            }
        )
    rows.sort(key=lambda row: str(row["species_latin_name"]))
    return {
        "schema_version": "animal-cross-surface-drift.v1",
        "rows": rows,
        "drift_detected": any(bool(row["drift_detected"]) for row in rows),
    }
