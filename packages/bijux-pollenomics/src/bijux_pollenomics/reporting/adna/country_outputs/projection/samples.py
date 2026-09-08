from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path

from .....adna.workflow.paths import adna_species_dir


def build_sample_rows(
    country: str,
    localities: list[dict[str, object]],
    sample_lookup: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    sample_rows: list[dict[str, object]] = []
    for locality in localities:
        project_accession = str(locality.get("project_accession", "")).strip()
        locality_sample_record_ids = locality.get("sample_record_ids", [])
        if not isinstance(locality_sample_record_ids, list):
            continue
        for sample_record_id in locality_sample_record_ids:
            sample_id = str(sample_record_id).strip()
            sample = sample_lookup.get(sample_id, {})
            chronology = _as_mapping(sample.get("chronology"))
            coordinates = _as_mapping(sample.get("coordinates"))
            identity = _as_mapping(sample.get("identity"))
            sample_rows.append(
                {
                    "country": country,
                    "species_latin_name": str(locality.get("species_latin_name", "")),
                    "species_common_name": str(locality.get("species_common_name", "")),
                    "animal_scope": str(locality.get("animal_scope", "")),
                    "source_native_tax_id": str(sample.get("source_native_tax_id", "")),
                    "source_native_scientific_name": str(
                        sample.get("source_native_scientific_name", "")
                    ),
                    "taxon_alignment_status": str(
                        sample.get("taxon_alignment_status", "")
                    ),
                    "sample_record_id": sample_id,
                    "sample_group_id": str(
                        sample.get("group_id")
                        or sample.get("master_id")
                        or project_accession
                    ),
                    "sample_namespace": str(identity.get("namespace", "")),
                    "feature_id": str(locality.get("feature_id", "")),
                    "evidence_row_id": str(locality.get("evidence_row_id", "")),
                    "site_record_id": str(locality.get("site_record_id", "")),
                    "project_accession": project_accession,
                    "paper_title": str(
                        sample.get("publication") or locality.get("paper_title", "")
                    ),
                    "paper_doi": str(
                        sample.get("paper_doi") or locality.get("paper_doi", "")
                    ),
                    "supplementary_source": str(sample.get("supplementary_source", "")),
                    "locality": str(
                        sample.get("locality") or locality.get("locality", "")
                    ),
                    "country_assignment_confidence": str(
                        locality.get("country_assignment_confidence", "")
                    ),
                    "country_assignment_reason": str(
                        locality.get("country_assignment_reason", "")
                    ),
                    "coordinate_basis": str(locality.get("coordinate_basis", "")),
                    "coordinate_confidence": str(
                        locality.get("coordinate_confidence", "")
                    ),
                    "source_locator": str(locality.get("source_locator", "")),
                    "source_support_status": str(
                        locality.get("source_support_status", "")
                    ),
                    "sample_evidence_status": str(
                        sample.get("sample_evidence_status", "")
                    ),
                    "sample_lineage_path": str(sample.get("sample_lineage_path", "")),
                    "sample_lineage_locator": str(
                        sample.get("sample_lineage_locator", "")
                    ),
                    "sample_lineage_excerpt": str(
                        sample.get("sample_lineage_excerpt", "")
                    ),
                    "site_evidence_path": str(locality.get("source_artifact_path", "")),
                    "site_evidence_kind": str(locality.get("source_artifact_kind", "")),
                    "site_evidence_locator": str(locality.get("source_locator", "")),
                    "site_evidence_text": str(locality.get("exact_source_text", "")),
                    "time_label": str(
                        chronology.get("original_text")
                        or locality.get("time_label", "")
                    ),
                    "chronology_evidence_class": str(
                        chronology.get("evidence_class")
                        or locality.get("chronology_evidence_class", "")
                    ),
                    "chronology_precision_posture": str(
                        chronology.get("precision_posture")
                        or locality.get("chronology_precision_posture", "")
                    ),
                    "chronology_normalization_status": str(
                        sample.get("chronology_normalization_status", "")
                    ),
                    "chronology_provenance_path": str(
                        sample.get("chronology_provenance_path", "")
                    ),
                    "chronology_provenance_kind": str(
                        sample.get("chronology_provenance_kind", "")
                    ),
                    "chronology_provenance_locator": str(
                        sample.get("chronology_provenance_locator", "")
                    ),
                    "chronology_provenance_text": str(
                        sample.get("chronology_provenance_text", "")
                    ),
                    "inclusion_status": str(sample.get("inclusion_status", "")),
                    "inclusion_note": str(sample.get("inclusion_note", "")),
                    "sample_basis": str(sample.get("sample_basis", "")),
                    "latitude_text": str(
                        coordinates.get("latitude_text")
                        or locality.get("latitude_text", "")
                    ),
                    "longitude_text": str(
                        coordinates.get("longitude_text")
                        or locality.get("longitude_text", "")
                    ),
                    "coordinate_provenance_path": str(
                        locality.get("coordinate_source_artifact_path", "")
                    ),
                    "coordinate_provenance_locator": str(
                        locality.get("coordinate_source_locator", "")
                    ),
                    "coordinate_provenance_note": str(
                        locality.get("coordinate_support_gap_note", "")
                    ),
                }
            )
    sample_rows.sort(
        key=lambda row: (
            str(row["species_latin_name"]),
            str(row["project_accession"]),
            str(row["sample_record_id"]),
        )
    )
    return sample_rows


def load_country_sample_lookup(data_root: Path) -> dict[str, dict[str, object]]:
    lookup: dict[str, dict[str, object]] = {}
    species_root = adna_species_dir(Path(data_root))
    for sample_path in species_root.glob("*/normalized/sample_records.json"):
        payload = json.loads(sample_path.read_text(encoding="utf-8"))
        rows = payload.get("samples", [])
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            identity = _as_mapping(row.get("identity"))
            stable_token = str(identity.get("stable_token", "")).strip()
            if stable_token:
                lookup[stable_token] = row
    return lookup


def _as_mapping(value: object) -> Mapping[str, object]:
    if isinstance(value, dict):
        return value
    return {}
