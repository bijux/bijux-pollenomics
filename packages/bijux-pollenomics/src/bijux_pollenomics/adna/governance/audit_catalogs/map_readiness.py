from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

from bijux_pollenomics.adna.species.tracked_species import TRACKED_ADNA_SPECIES

from .contracts import (
    MapReadinessAudit,
    MapReadinessPostureRow,
    MapReadinessRow,
    MapReadinessTotals,
)
from .repository import (
    _load_coordinate_provenance_rows,
    _load_sample_rows,
    _species_root,
)


def build_cross_species_map_readiness(data_root: Path) -> MapReadinessAudit:
    """Report coordinate posture and publication admission across tracked animals."""
    publication_counts, not_materialized_rows = _map_publication_accounting(
        Path(data_root)
    )
    not_materialized_counts = Counter(
        str(row["species_latin_name"]) for row in not_materialized_rows
    )
    rows: list[MapReadinessRow] = []
    totals: MapReadinessTotals = {
        "direct_coordinate_backed": 0,
        "indirectly_geocoded": 0,
        "unresolved_sample_count": 0,
        "refused_coordinate_provenance_count": 0,
        "region_only_coordinate_refusal_count": 0,
        "unresolved_location_coordinate_refusal_count": 0,
        "coordinate_provenance_mappable_count": 0,
        "coordinate_provenance_row_count": 0,
        "publication_candidate_count": 0,
        "not_materialized_count": 0,
    }
    for species_name in TRACKED_ADNA_SPECIES:
        posture = _build_species_map_readiness_row(Path(data_root), species_name)
        species_latin_name = posture["species_latin_name"]
        coordinate_mappable_count = (
            posture["direct_coordinate_backed"] + posture["indirectly_geocoded"]
        )
        publication_candidate_count = publication_counts[species_latin_name]
        not_materialized_count = not_materialized_counts[species_latin_name]
        if (
            publication_candidate_count + not_materialized_count
            != coordinate_mappable_count
        ):
            raise ValueError(
                f"Animal map-readiness counts do not reconcile for {species_latin_name}"
            )
        row: MapReadinessRow = {
            **posture,
            "coordinate_provenance_mappable_count": coordinate_mappable_count,
            "publication_candidate_count": publication_candidate_count,
            "not_materialized_count": not_materialized_count,
        }
        rows.append(row)
        totals["direct_coordinate_backed"] += row["direct_coordinate_backed"]
        totals["indirectly_geocoded"] += row["indirectly_geocoded"]
        totals["unresolved_sample_count"] += row["unresolved_sample_count"]
        totals["refused_coordinate_provenance_count"] += row[
            "refused_coordinate_provenance_count"
        ]
        totals["region_only_coordinate_refusal_count"] += row[
            "region_only_coordinate_refusal_count"
        ]
        totals["unresolved_location_coordinate_refusal_count"] += row[
            "unresolved_location_coordinate_refusal_count"
        ]
        totals["coordinate_provenance_mappable_count"] += row[
            "coordinate_provenance_mappable_count"
        ]
        totals["coordinate_provenance_row_count"] += (
            row["coordinate_provenance_mappable_count"]
            + row["refused_coordinate_provenance_count"]
        )
        totals["publication_candidate_count"] += row["publication_candidate_count"]
        totals["not_materialized_count"] += row["not_materialized_count"]
    return {
        "schema_version": "adna-cross-species-map-readiness.v3",
        "rows": rows,
        "totals": totals,
        "not_materialized_rows": not_materialized_rows,
        "publication_accounting": {
            "overall_ok": (
                totals["coordinate_provenance_mappable_count"]
                == totals["publication_candidate_count"]
                + totals["not_materialized_count"]
                and totals["not_materialized_count"] == len(not_materialized_rows)
            ),
            "coordinate_posture_definition": (
                "Coordinate provenance rows whose mapping posture is mappable_point."
            ),
            "publication_candidate_definition": (
                "Atlas rows backed by an admitted sample and a joined locality."
            ),
            "not_materialized_reason_definition": (
                "A coordinate-ready provenance row did not satisfy every atlas "
                "publication admission requirement, including sample, locality, and "
                "chronology support, and remains excluded from point publication."
            ),
            "unresolved_sample_definition": (
                "Sample rows whose inclusion status is sample_context_blocked; this "
                "sample denominator is never added to coordinate-provenance rows."
            ),
            "coordinate_refusal_definition": (
                "Coordinate provenance rows with a refused_* mapping posture, "
                "partitioned into region-only and unresolved-location refusals."
            ),
        },
    }


def _build_species_map_readiness_row(
    data_root: Path, species_name: str
) -> MapReadinessPostureRow:
    from bijux_pollenomics.adna.species.definitions import resolve_species_definition

    species = resolve_species_definition(species_name)
    species_root = _species_root(data_root, species_name)
    provenance_rows = _load_coordinate_provenance_rows(species_root)
    allowed_mapping_postures = {
        "mappable_point",
        "refused_region_only",
        "refused_unresolved_location",
    }
    unknown_mapping_postures = sorted(
        {
            str(row.get("mapping_posture", "")).strip() or "<empty>"
            for row in provenance_rows
            if str(row.get("mapping_posture", "")).strip()
            not in allowed_mapping_postures
        }
    )
    if unknown_mapping_postures:
        raise ValueError(
            "Animal map-readiness found unsupported mapping postures: "
            + ", ".join(unknown_mapping_postures)
        )
    allowed_mappable_bases = {
        "archive_coordinates",
        "direct_published_coordinates",
        "named_site_geocoding",
        "supplementary_proximal_site_coordinates",
        "supplementary_table_coordinates",
    }
    unknown_mappable_bases = sorted(
        {
            str(row.get("coordinate_basis", "")).strip() or "<empty>"
            for row in provenance_rows
            if str(row.get("mapping_posture", "")).strip() == "mappable_point"
            and str(row.get("coordinate_basis", "")).strip()
            not in allowed_mappable_bases
        }
    )
    if unknown_mappable_bases:
        raise ValueError(
            "Animal map-readiness found unsupported mappable coordinate bases: "
            + ", ".join(unknown_mappable_bases)
        )
    direct_coordinate_backed = sum(
        1
        for row in provenance_rows
        if str(row.get("mapping_posture", "")) == "mappable_point"
        and str(row.get("coordinate_basis", ""))
        in {
            "direct_published_coordinates",
            "supplementary_proximal_site_coordinates",
            "supplementary_table_coordinates",
            "archive_coordinates",
        }
    )
    indirectly_geocoded = sum(
        1
        for row in provenance_rows
        if str(row.get("mapping_posture", "")) == "mappable_point"
        and str(row.get("coordinate_basis", "")) == "named_site_geocoding"
    )
    unresolved_sample_count = sum(
        1
        for sample in _load_sample_rows(species_root)
        if str(sample.get("inclusion_status", "")) == "sample_context_blocked"
    )
    refusal_posture_counts = Counter(
        str(row.get("mapping_posture", ""))
        for row in provenance_rows
        if str(row.get("mapping_posture", "")).startswith("refused_")
    )
    refused_coordinate_provenance_count = sum(refusal_posture_counts.values())
    region_only_coordinate_refusal_count = refusal_posture_counts["refused_region_only"]
    unresolved_location_coordinate_refusal_count = refusal_posture_counts[
        "refused_unresolved_location"
    ]
    unknown_refusal_count = refused_coordinate_provenance_count - (
        region_only_coordinate_refusal_count
        + unresolved_location_coordinate_refusal_count
    )
    if unknown_refusal_count:
        raise ValueError("Animal map-readiness found an unknown refusal posture")
    return {
        "species_latin_name": species.latin_name,
        "species_common_name": species.common_name,
        "direct_coordinate_backed": direct_coordinate_backed,
        "indirectly_geocoded": indirectly_geocoded,
        "unresolved_sample_count": unresolved_sample_count,
        "refused_coordinate_provenance_count": (refused_coordinate_provenance_count),
        "region_only_coordinate_refusal_count": (region_only_coordinate_refusal_count),
        "unresolved_location_coordinate_refusal_count": (
            unresolved_location_coordinate_refusal_count
        ),
    }


def _map_publication_accounting(
    data_root: Path,
) -> tuple[Counter[str], list[dict[str, object]]]:
    from bijux_pollenomics.adna.governance.atlas_candidates import (
        build_tracked_animal_atlas_evidence_rows,
    )

    publication_rows = tuple(
        row.as_dict()
        for row in build_tracked_animal_atlas_evidence_rows(Path(data_root))
    )
    publication_counts = Counter(
        str(row.get("species_latin_name", "")) for row in publication_rows
    )
    publication_keys = tuple(
        _map_publication_key(row, project_field="primary_project_accession")
        for row in publication_rows
    )
    if len(publication_keys) != len(set(publication_keys)):
        raise ValueError("Animal atlas publication identity is not unique")
    unmatched_candidates = Counter(publication_keys)
    not_materialized_rows: list[dict[str, object]] = []
    coordinate_keys: set[tuple[str, ...]] = set()
    for species_name in TRACKED_ADNA_SPECIES:
        species_root = _species_root(data_root, species_name)
        sample_rows = _load_sample_rows(species_root)
        locality_rows = _load_locality_rows(species_root)
        for provenance in _load_coordinate_provenance_rows(species_root):
            if str(provenance.get("mapping_posture", "")) != "mappable_point":
                continue
            coordinate_basis = str(provenance.get("coordinate_basis", ""))
            if coordinate_basis not in {
                "archive_coordinates",
                "direct_published_coordinates",
                "named_site_geocoding",
                "supplementary_proximal_site_coordinates",
                "supplementary_table_coordinates",
            }:
                raise ValueError(
                    "Mappable animal coordinate provenance uses an unsupported basis: "
                    f"{coordinate_basis or '<empty>'}"
                )
            key = _map_publication_key(provenance, project_field="project_accession")
            if key in coordinate_keys:
                raise ValueError("Mappable animal coordinate provenance is not unique")
            coordinate_keys.add(key)
            if unmatched_candidates[key]:
                unmatched_candidates[key] -= 1
                continue
            not_materialized_rows.append(
                {
                    "species_latin_name": provenance.get("species_latin_name", ""),
                    "species_common_name": provenance.get("species_common_name", ""),
                    "project_accession": provenance.get("project_accession", ""),
                    "site_label": provenance.get("site_label", ""),
                    "coordinate_basis": provenance.get("coordinate_basis", ""),
                    "source_artifact_path": provenance.get("source_artifact_path", ""),
                    "source_locator": provenance.get("source_locator", ""),
                    "reason_code": _not_materialized_reason_code(
                        species_root=species_root,
                        provenance=provenance,
                        sample_rows=sample_rows,
                        locality_rows=locality_rows,
                    ),
                }
            )
    if sum(unmatched_candidates.values()):
        raise ValueError(
            "Atlas publication rows do not reconcile to mappable coordinate provenance"
        )
    return publication_counts, sorted(
        not_materialized_rows,
        key=lambda row: (
            str(row["species_latin_name"]),
            str(row["project_accession"]),
            str(row["site_label"]),
        ),
    )


def _not_materialized_reason_code(
    *,
    species_root: Path,
    provenance: dict[str, object],
    sample_rows: list[dict[str, object]],
    locality_rows: list[dict[str, object]],
) -> str:
    from bijux_pollenomics.adna.governance.atlas_candidates.chronology import (
        _atlas_chronology_supports_publication,
        _atlas_public_chronology,
        _parse_chronology,
    )
    from bijux_pollenomics.adna.governance.atlas_candidates.sample_support import (
        _atlas_admitted_sample_rows,
    )
    from bijux_pollenomics.adna.governance.atlas_candidates.source_records import (
        _load_project_animal_scope_lookup,
    )
    from bijux_pollenomics.adna.governance.atlas_candidates.validation import (
        _project_sample_animal_scope_resolution_for,
    )

    project_accession = str(provenance.get("project_accession", "")).strip()
    site_label = str(provenance.get("site_label", "")).strip()
    locality = next(
        (
            row
            for row in locality_rows
            if project_accession in _project_accessions(row)
            and str(row.get("locality", "")).strip() == site_label
        ),
        None,
    )
    if locality is None:
        return "no_admitted_sample_backed_locality_candidate"
    locality_identity = locality.get("identity")
    if not isinstance(locality_identity, dict):
        return "no_admitted_sample_backed_locality_candidate"
    locality_token = str(locality_identity.get("stable_token", "")).strip()
    project_accessions = _project_accessions(locality)
    locality_samples = _atlas_admitted_sample_rows(
        tuple(
            row
            for row in sample_rows
            if str(row.get("project_accession", "")).strip() in project_accessions
            and _sample_locality_token(row) == locality_token
        )
    )
    if not locality_samples or not any(
        _sample_stable_token(row) for row in locality_samples
    ):
        return "no_admitted_sample_backed_locality_candidate"
    animal_scope, scope_refusal = _project_sample_animal_scope_resolution_for(
        species_root,
        _load_project_animal_scope_lookup(species_root),
        project_accessions=tuple(sorted(project_accessions)),
        sample_rows=locality_samples,
    )
    if animal_scope is None:
        return scope_refusal or "sample_scope_not_evidenced"
    chronology = locality.get("chronology")
    if not _atlas_chronology_supports_publication(
        _atlas_public_chronology(
            _parse_chronology(chronology if isinstance(chronology, dict) else {})
        )
    ):
        return "chronology_not_supported_for_atlas_publication"
    return "atlas_publication_admission_not_satisfied"


def _project_accessions(row: dict[str, object]) -> set[str]:
    values = row.get("project_accessions")
    if not isinstance(values, list):
        return set()
    return {str(item).strip() for item in values if str(item).strip()}


def _sample_locality_token(row: dict[str, object]) -> str:
    locality_identity = row.get("locality_identity")
    if isinstance(locality_identity, dict):
        return str(locality_identity.get("stable_token", "")).strip()
    return ""


def _sample_stable_token(row: dict[str, object]) -> str:
    identity = row.get("identity")
    if isinstance(identity, dict):
        return str(identity.get("stable_token", "")).strip()
    return ""


def _load_locality_rows(species_root: Path) -> list[dict[str, object]]:
    path = species_root / "normalized" / "locality_summaries.json"
    if not path.is_file():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("localities", [])
    return [row for row in rows if isinstance(row, dict)]


def _map_publication_key(
    row: dict[str, object], *, project_field: str
) -> tuple[str, ...]:
    return (
        str(row.get("species_latin_name", "")),
        str(row.get(project_field, "")),
        str(row.get("coordinate_source_locator", row.get("source_locator", ""))),
        str(row.get("coordinate_basis", "")),
        str(row.get("locality", row.get("site_label", ""))),
        str(row.get("latitude_text", "")),
        str(row.get("longitude_text", "")),
        str(row.get("original_place_text", "")),
        str(row.get("resolved_place_text", "")),
    )
