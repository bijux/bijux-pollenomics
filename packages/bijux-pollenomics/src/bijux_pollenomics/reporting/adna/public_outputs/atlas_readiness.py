from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from ....adna.governance.audit_catalogs import (
    build_cross_species_map_readiness,
    build_public_animal_output_honesty,
)
from ....adna.workflow.paths import adna_species_dir
from ..atlas_evidence_rows import build_tracked_animal_atlas_evidence_rows


def _build_animal_atlas_readiness(
    data_root: Path,
    country_payloads: list[dict[str, object]],
) -> dict[str, object]:
    readiness_payload = build_cross_species_map_readiness(Path(data_root))
    honesty_payload = build_public_animal_output_honesty(
        Path(data_root), Path(data_root) / "__no_report_root__"
    )
    mapped_sample_ids_by_species = _mapped_sample_ids_by_species(Path(data_root))
    candidate_rows_by_species = _candidate_rows_by_species(Path(data_root))
    rows = []
    country_counts: dict[str, dict[str, int]] = {}
    for payload in country_payloads:
        country = str(payload.get("country", ""))
        for row in cast(list[object], payload.get("species_rows", [])):
            if not isinstance(row, dict):
                continue
            species_name = str(row.get("species_latin_name", ""))
            if not species_name:
                continue
            species_counts = country_counts.setdefault(species_name, {})
            species_counts[country] = int(row.get("mapped_locality_count", 0) or 0)
    for row in cast(list[object], readiness_payload.get("rows", [])):
        if not isinstance(row, dict):
            continue
        species_name = str(row.get("species_latin_name", ""))
        direct_count = int(row.get("direct_coordinate_backed", 0) or 0)
        geocoded_count = int(row.get("indirectly_geocoded", 0) or 0)
        unresolved_count = int(row.get("unresolved", 0) or 0)
        refused_count = int(row.get("refused_from_mapping", 0) or 0)
        map_ready_count = direct_count + geocoded_count
        total_curated = map_ready_count + unresolved_count + refused_count
        honesty_row: dict[str, object] = next(
            (
                item
                for item in cast(list[object], honesty_payload.get("rows", []))
                if isinstance(item, dict)
                and str(item.get("species_latin_name", "")) == species_name
            ),
            {},
        )
        candidate_point_count = len(candidate_rows_by_species.get(species_name, []))
        mapped_sample_count = len(mapped_sample_ids_by_species.get(species_name, set()))
        blocked_sample_count = int(
            cast(str, honesty_row.get("blocked_sample_count", 0)) or 0
        )
        readiness_status, status_reason = _atlas_readiness_status(
            candidate_point_count=candidate_point_count,
            mapped_sample_count=mapped_sample_count,
            blocked_sample_count=blocked_sample_count,
            unresolved_count=unresolved_count,
            refused_count=refused_count,
        )
        rows.append(
            {
                **row,
                "candidate_point_count": candidate_point_count,
                "mapped_sample_count": mapped_sample_count,
                "blocked_sample_count": blocked_sample_count,
                "map_ready_count": map_ready_count,
                "total_curated_rows": total_curated,
                "map_ready_share": (
                    round(map_ready_count / total_curated, 4) if total_curated else 0.0
                ),
                "readiness_status": readiness_status,
                "status_reason": status_reason,
                "country_mapped_locality_counts": country_counts.get(
                    species_name,
                    {},
                ),
            }
        )
    status_counts: dict[str, int] = {}
    for row in rows:
        status = str(row.get("readiness_status", ""))
        status_counts[status] = status_counts.get(status, 0) + 1
    return {
        "schema_version": "animal-atlas-readiness.v1",
        "status_counts": status_counts,
        "rows": rows,
    }


def _build_animal_atlas_exclusion_report(data_root: Path) -> dict[str, object]:
    mapped_sample_ids_by_species = _mapped_sample_ids_by_species(Path(data_root))
    rows = []
    species_dir = adna_species_dir(Path(data_root))
    if not species_dir.is_dir():
        return {
            "schema_version": "animal-atlas-exclusion-report.v1",
            "row_count": 0,
            "rows": [],
        }
    for species_root in sorted(path for path in species_dir.iterdir() if path.is_dir()):
        if species_root.name == "homo_sapiens":
            continue
        provenance_lookup = _coordinate_provenance_by_project_and_locality(species_root)
        for sample_row in _load_species_sample_rows(species_root):
            species_name = str(sample_row.get("species_latin_name", "")).strip()
            sample_id = str(
                cast(dict[str, object], sample_row.get("identity", {})).get(
                    "stable_token", ""
                )
            ).strip()
            if not species_name or not sample_id:
                continue
            if sample_id in mapped_sample_ids_by_species.get(species_name, set()):
                continue
            locality_identity = cast(
                dict[str, object], sample_row.get("locality_identity", {})
            )
            project_accession = str(sample_row.get("project_accession", "")).strip()
            locality_text = str(locality_identity.get("locality_text", "")).strip()
            provenance = provenance_lookup.get((project_accession, locality_text), {})
            chronology = cast(dict[str, object], sample_row.get("chronology", {}))
            exclusion_reason = _atlas_exclusion_reason(
                sample_row=sample_row,
                provenance=provenance,
            )
            rows.append(
                {
                    "species_latin_name": species_name,
                    "species_common_name": str(
                        sample_row.get("species_common_name", "")
                    ),
                    "project_accession": project_accession,
                    "sample_record_id": sample_id,
                    "locality": str(sample_row.get("locality") or locality_text),
                    "political_entity": str(
                        locality_identity.get("political_entity", "")
                    ),
                    "inclusion_status": str(sample_row.get("inclusion_status", "")),
                    "inclusion_note": str(sample_row.get("inclusion_note", "")),
                    "chronology_normalization_status": str(
                        sample_row.get("chronology_normalization_status", "")
                    ),
                    "chronology_precision_posture": str(
                        chronology.get("precision_posture", "")
                    ),
                    "coordinate_basis": str(provenance.get("coordinate_basis", "")),
                    "mapping_posture": str(provenance.get("mapping_posture", "")),
                    "coordinate_confidence": str(
                        provenance.get("coordinate_confidence", "")
                    ),
                    "sample_lineage_path": str(
                        sample_row.get("sample_lineage_path", "")
                    ),
                    "chronology_provenance_path": str(
                        sample_row.get("chronology_provenance_path", "")
                    ),
                    "coordinate_provenance_path": str(
                        provenance.get("source_artifact_path", "")
                    ),
                    "coordinate_provenance_locator": str(
                        provenance.get("source_locator", "")
                    ),
                    "exclusion_reason": exclusion_reason,
                }
            )
    rows.sort(
        key=lambda row: (
            str(row["species_latin_name"]),
            str(row["project_accession"]),
            str(row["sample_record_id"]),
        )
    )
    return {
        "schema_version": "animal-atlas-exclusion-report.v1",
        "row_count": len(rows),
        "rows": rows,
    }


def _mapped_sample_ids_by_species(data_root: Path) -> dict[str, set[str]]:
    mapped: dict[str, set[str]] = {}
    for row in build_tracked_animal_atlas_evidence_rows(Path(data_root)):
        mapped.setdefault(row.species_latin_name, set()).update(row.sample_record_ids)
    return mapped


def _candidate_rows_by_species(data_root: Path) -> dict[str, list[object]]:
    rows: dict[str, list[object]] = {}
    for row in build_tracked_animal_atlas_evidence_rows(Path(data_root)):
        rows.setdefault(row.species_latin_name, []).append(row)
    return rows


def _load_species_sample_rows(species_root: Path) -> list[dict[str, object]]:
    path = species_root / "normalized" / "sample_records.json"
    if not path.is_file():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("samples", [])
    return [row for row in rows if isinstance(row, dict)]


def _coordinate_provenance_by_project_and_locality(
    species_root: Path,
) -> dict[tuple[str, str], dict[str, object]]:
    path = species_root / "normalized" / "coordinate_provenance.json"
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("coordinate_provenance", [])
    lookup: dict[tuple[str, str], dict[str, object]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        project_accession = str(row.get("project_accession", "")).strip()
        locality_text = str(row.get("site_label", "")).strip()
        if project_accession:
            lookup[(project_accession, locality_text)] = row
    return lookup


def _atlas_readiness_status(
    *,
    candidate_point_count: int,
    mapped_sample_count: int,
    blocked_sample_count: int,
    unresolved_count: int,
    refused_count: int,
) -> tuple[str, str]:
    if candidate_point_count == 0 and (unresolved_count > 0 or refused_count > 0):
        return (
            "blocked",
            f"{blocked_sample_count} blocked sample rows still fail atlas publication.",
        )
    if candidate_point_count == 0:
        return (
            "absent",
            "No candidate point rows are currently published for this species.",
        )
    if candidate_point_count < 5 or mapped_sample_count < 5:
        return (
            "thin",
            f"{candidate_point_count} candidate point rows remain too thin for broad atlas claims.",
        )
    return (
        "publishable",
        f"{candidate_point_count} candidate point rows now survive the current atlas contract.",
    )


def _atlas_exclusion_reason(
    *,
    sample_row: dict[str, object],
    provenance: dict[str, object],
) -> str:
    inclusion_status = str(sample_row.get("inclusion_status", "")).strip()
    mapping_posture = str(provenance.get("mapping_posture", "")).strip()
    chronology_status = str(
        sample_row.get("chronology_normalization_status", "")
    ).strip()
    if inclusion_status == "sample_context_blocked":
        return "sample locality remains unresolved and cannot be mapped honestly"
    if mapping_posture == "refused_region_only":
        return "geography remains region-only and the atlas refuses a false point"
    if chronology_status in {"unresolved", "conflict"}:
        return "chronology remains unresolved enough that the sample stays out of the public map"
    if not provenance:
        return "no coordinate provenance row currently supports point publication"
    return "sample is tracked but does not yet satisfy the full atlas point contract"
