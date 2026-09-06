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
        country = str(payload.get("country", "")).strip()
        if not country:
            raise ValueError("Animal country readiness requires a country identity")
        for row in _required_rows(payload, "species_rows"):
            species_name = str(row.get("species_latin_name", ""))
            if not species_name:
                raise ValueError("Animal country readiness row requires a species name")
            species_counts = country_counts.setdefault(species_name, {})
            if country in species_counts:
                raise ValueError(
                    f"Animal country readiness repeats {species_name} for {country}"
                )
            species_counts[country] = _required_count(row, "mapped_locality_count")
    honesty_rows = _required_rows(honesty_payload, "rows")
    honesty_by_species = _rows_by_species(honesty_rows, context="sample accounting")
    readiness_rows = _required_rows(readiness_payload, "rows")
    readiness_by_species = _rows_by_species(
        readiness_rows, context="coordinate readiness"
    )
    if not honesty_by_species.keys() <= readiness_by_species.keys():
        raise ValueError(
            "Animal sample accounting contains an unknown coordinate-readiness species"
        )
    for row in readiness_rows:
        species_name = str(row.get("species_latin_name", "")).strip()
        unresolved_count = _required_count(row, "unresolved_sample_count")
        direct_coordinate_count = _required_count(row, "direct_coordinate_backed")
        indirect_coordinate_count = _required_count(row, "indirectly_geocoded")
        refused_count = _required_count(row, "refused_coordinate_provenance_count")
        region_only_refusal_count = _required_count(
            row, "region_only_coordinate_refusal_count"
        )
        unresolved_location_refusal_count = _required_count(
            row, "unresolved_location_coordinate_refusal_count"
        )
        map_ready_count = _required_count(row, "coordinate_provenance_mappable_count")
        if direct_coordinate_count + indirect_coordinate_count != map_ready_count:
            raise ValueError(
                f"Animal mappable coordinate postures do not reconcile for {species_name}"
            )
        if (
            region_only_refusal_count + unresolved_location_refusal_count
            != refused_count
        ):
            raise ValueError(
                f"Animal coordinate refusal postures do not reconcile for {species_name}"
            )
        coordinate_provenance_denominator = map_ready_count + refused_count
        publication_candidate_count = _required_count(
            row, "publication_candidate_count"
        )
        candidate_point_count = len(candidate_rows_by_species.get(species_name, []))
        if candidate_point_count != publication_candidate_count:
            raise ValueError(
                f"Animal publication candidates do not reconcile for {species_name}"
            )
        not_materialized_count = _required_count(row, "not_materialized_count")
        if publication_candidate_count + not_materialized_count != map_ready_count:
            raise ValueError(
                f"Animal mappable coordinate provenance does not reconcile for {species_name}"
            )
        mapped_sample_count = len(mapped_sample_ids_by_species.get(species_name, set()))
        honesty_row = honesty_by_species.get(species_name)
        if honesty_row is None:
            if any(
                (
                    unresolved_count,
                    map_ready_count,
                    publication_candidate_count,
                    not_materialized_count,
                    candidate_point_count,
                    mapped_sample_count,
                )
            ):
                raise ValueError(
                    f"Animal atlas readiness has evidence but no sample accounting for {species_name}"
                )
            honesty_row = {
                "mapped_sample_count": 0,
                "blocked_sample_count": 0,
                "tracked_sample_count": 0,
                "unresolved_sample_count": 0,
            }
        honesty_mapped_sample_count = _required_count(
            honesty_row, "mapped_sample_count"
        )
        blocked_sample_count = _required_count(honesty_row, "blocked_sample_count")
        tracked_sample_count = _required_count(honesty_row, "tracked_sample_count")
        honesty_unresolved_count = _required_count(
            honesty_row, "unresolved_sample_count"
        )
        if mapped_sample_count != honesty_mapped_sample_count:
            raise ValueError(
                f"Animal mapped sample accounting does not reconcile for {species_name}"
            )
        if unresolved_count != honesty_unresolved_count:
            raise ValueError(
                f"Animal unresolved sample accounting does not reconcile for {species_name}"
            )
        if mapped_sample_count + blocked_sample_count != tracked_sample_count:
            raise ValueError(
                f"Animal sample readiness does not reconcile for {species_name}"
            )
        if unresolved_count > blocked_sample_count:
            raise ValueError(
                f"Unresolved samples exceed blocked samples for {species_name}"
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
                "tracked_sample_count": tracked_sample_count,
                "unresolved_sample_count": unresolved_count,
                "coordinate_mappable_provenance_count": map_ready_count,
                "coordinate_refused_provenance_count": refused_count,
                "coordinate_provenance_denominator": (
                    coordinate_provenance_denominator
                ),
                "coordinate_mappable_share": _share(
                    map_ready_count, coordinate_provenance_denominator
                ),
                "publication_share_of_mappable_coordinates": _share(
                    publication_candidate_count, map_ready_count
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
    readiness_totals = cast(dict[str, object], readiness_payload.get("totals", {}))
    honesty_totals = cast(dict[str, object], honesty_payload.get("totals", {}))
    tracked_total = _required_count(honesty_totals, "tracked_sample_count")
    mapped_total = _required_count(honesty_totals, "mapped_sample_count")
    blocked_total = _required_count(honesty_totals, "blocked_sample_count")
    unresolved_total = _required_count(honesty_totals, "unresolved_sample_count")
    readiness_unresolved_total = _required_count(
        readiness_totals, "unresolved_sample_count"
    )
    if mapped_total + blocked_total != tracked_total:
        raise ValueError("Animal sample readiness totals do not reconcile")
    if unresolved_total > blocked_total:
        raise ValueError("Unresolved animal samples exceed blocked sample totals")
    if readiness_unresolved_total != unresolved_total:
        raise ValueError("Animal unresolved sample totals do not reconcile")
    sample_row_totals = (
        sum(_required_count(row, "tracked_sample_count") for row in honesty_rows),
        sum(_required_count(row, "mapped_sample_count") for row in honesty_rows),
        sum(_required_count(row, "blocked_sample_count") for row in honesty_rows),
        sum(_required_count(row, "unresolved_sample_count") for row in honesty_rows),
    )
    if sample_row_totals != (
        tracked_total,
        mapped_total,
        blocked_total,
        unresolved_total,
    ):
        raise ValueError("Animal sample accounting rows do not match totals")
    coordinate_total = _required_count(
        readiness_totals, "coordinate_provenance_row_count"
    )
    mappable_total = _required_count(
        readiness_totals, "coordinate_provenance_mappable_count"
    )
    direct_total = _required_count(readiness_totals, "direct_coordinate_backed")
    indirect_total = _required_count(readiness_totals, "indirectly_geocoded")
    refused_total = _required_count(
        readiness_totals, "refused_coordinate_provenance_count"
    )
    region_only_refusal_total = _required_count(
        readiness_totals, "region_only_coordinate_refusal_count"
    )
    unresolved_location_refusal_total = _required_count(
        readiness_totals, "unresolved_location_coordinate_refusal_count"
    )
    published_total = _required_count(readiness_totals, "publication_candidate_count")
    not_materialized_total = _required_count(readiness_totals, "not_materialized_count")
    if mappable_total + refused_total != coordinate_total:
        raise ValueError("Animal coordinate-provenance totals do not reconcile")
    if direct_total + indirect_total != mappable_total:
        raise ValueError("Animal mappable coordinate posture totals do not reconcile")
    if region_only_refusal_total + unresolved_location_refusal_total != refused_total:
        raise ValueError("Animal coordinate refusal posture totals do not reconcile")
    if published_total + not_materialized_total != mappable_total:
        raise ValueError("Animal coordinate publication totals do not reconcile")
    row_mappable_total = sum(
        _required_count(row, "coordinate_provenance_mappable_count")
        for row in readiness_rows
    )
    row_direct_total = sum(
        _required_count(row, "direct_coordinate_backed") for row in readiness_rows
    )
    row_indirect_total = sum(
        _required_count(row, "indirectly_geocoded") for row in readiness_rows
    )
    row_refused_total = sum(
        _required_count(row, "refused_coordinate_provenance_count")
        for row in readiness_rows
    )
    row_region_only_refusal_total = sum(
        _required_count(row, "region_only_coordinate_refusal_count")
        for row in readiness_rows
    )
    row_unresolved_location_refusal_total = sum(
        _required_count(row, "unresolved_location_coordinate_refusal_count")
        for row in readiness_rows
    )
    row_unresolved_total = sum(
        _required_count(row, "unresolved_sample_count") for row in readiness_rows
    )
    row_published_total = sum(
        _required_count(row, "publication_candidate_count") for row in readiness_rows
    )
    row_not_materialized_total = sum(
        _required_count(row, "not_materialized_count") for row in readiness_rows
    )
    row_coordinate_total = row_mappable_total + row_refused_total
    if (
        row_coordinate_total,
        row_mappable_total,
        row_direct_total,
        row_indirect_total,
        row_refused_total,
        row_region_only_refusal_total,
        row_unresolved_location_refusal_total,
        row_published_total,
        row_not_materialized_total,
        row_unresolved_total,
    ) != (
        coordinate_total,
        mappable_total,
        direct_total,
        indirect_total,
        refused_total,
        region_only_refusal_total,
        unresolved_location_refusal_total,
        published_total,
        not_materialized_total,
        readiness_unresolved_total,
    ):
        raise ValueError("Animal coordinate readiness rows do not match totals")
    return {
        "schema_version": "animal-atlas-readiness.v2",
        "status_counts": status_counts,
        "reconciled_denominators": {
            "coordinate_provenance": {
                "denominator": coordinate_total,
                "mappable": mappable_total,
                "refused": refused_total,
            },
            "publication": {
                "denominator": mappable_total,
                "published": published_total,
                "not_materialized": not_materialized_total,
            },
            "samples": {
                "denominator": tracked_total,
                "mapped": mapped_total,
                "blocked": blocked_total,
                "unresolved_subset_of_blocked": unresolved_total,
            },
        },
        "rows": rows,
    }


def _share(numerator: int, denominator: int) -> float | None:
    if numerator < 0 or denominator < 0 or numerator > denominator:
        raise ValueError("Animal atlas readiness share must use a valid denominator")
    if denominator == 0:
        return None
    return round(numerator / denominator, 4)


def _required_count(payload: dict[str, object], field: str) -> int:
    value = payload.get(field)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(
            f"Animal atlas readiness {field} must be a nonnegative integer"
        )
    return value


def _required_rows(
    payload: dict[str, object],
    field: str,
) -> list[dict[str, object]]:
    value = payload.get(field)
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise ValueError(f"Animal atlas readiness {field} must be a list of rows")
    return cast(list[dict[str, object]], value)


def _rows_by_species(
    rows: list[dict[str, object]],
    *,
    context: str,
) -> dict[str, dict[str, object]]:
    indexed: dict[str, dict[str, object]] = {}
    for row in rows:
        species_name = str(row.get("species_latin_name", "")).strip()
        if not species_name:
            raise ValueError(f"Animal {context} row requires a species name")
        if species_name in indexed:
            raise ValueError(f"Animal {context} repeats {species_name}")
        indexed[species_name] = row
    return indexed


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
            political_entity = locality_identity.get("political_entity")
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
                    "political_entity": (
                        str(political_entity).strip()
                        if political_entity is not None
                        else None
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
    if candidate_point_count == 0 and (
        blocked_sample_count > 0 or unresolved_count > 0 or refused_count > 0
    ):
        return (
            "blocked",
            (
                f"{blocked_sample_count} blocked sample rows and {refused_count} refused "
                "coordinate-provenance rows still prevent atlas publication."
            ),
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
