from __future__ import annotations

from collections import Counter
from pathlib import Path

from bijux_pollenomics.adna.species.tracked_species import TRACKED_ADNA_SPECIES
from .repository import (
    _load_coordinate_provenance_rows,
    _load_sample_rows,
    _species_root,
)


def build_cross_species_map_readiness(data_root: Path) -> dict[str, object]:
    """Report coordinate posture and publication admission across tracked animals."""
    publication_counts, not_materialized_rows = _map_publication_accounting(
        Path(data_root)
    )
    not_materialized_counts = Counter(
        str(row["species_latin_name"]) for row in not_materialized_rows
    )
    rows = []
    totals = {
        "direct_coordinate_backed": 0,
        "indirectly_geocoded": 0,
        "unresolved": 0,
        "refused_from_mapping": 0,
        "coordinate_provenance_mappable_count": 0,
        "publication_candidate_count": 0,
        "not_materialized_count": 0,
    }
    for species_name in TRACKED_ADNA_SPECIES:
        row = _build_species_map_readiness_row(Path(data_root), species_name)
        species_latin_name = str(row["species_latin_name"])
        coordinate_mappable_count = int(row["direct_coordinate_backed"]) + int(
            row["indirectly_geocoded"]
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
        row.update(
            {
                "coordinate_provenance_mappable_count": coordinate_mappable_count,
                "publication_candidate_count": publication_candidate_count,
                "not_materialized_count": not_materialized_count,
            }
        )
        rows.append(row)
        for key in totals:
            totals[key] += int(row[key])
    return {
        "schema_version": "adna-cross-species-map-readiness.v2",
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
                "A coordinate-ready provenance row did not join to a sample-backed "
                "locality candidate and remains excluded from point publication."
            ),
        },
    }


def _build_species_map_readiness_row(
    data_root: Path, species_name: str
) -> dict[str, object]:
    from bijux_pollenomics.adna.species.definitions import resolve_species_definition

    species = resolve_species_definition(species_name)
    species_root = _species_root(data_root, species_name)
    provenance_rows = _load_coordinate_provenance_rows(species_root)
    direct_coordinate_backed = sum(
        1
        for row in provenance_rows
        if str(row.get("mapping_posture", "")) == "mappable_point"
        and str(row.get("coordinate_basis", ""))
        in {
            "direct_published_coordinates",
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
    unresolved = sum(
        1
        for sample in _load_sample_rows(species_root)
        if str(sample.get("inclusion_status", "")) == "sample_context_blocked"
    )
    refused_from_mapping = sum(
        1
        for row in provenance_rows
        if str(row.get("mapping_posture", "")) == "refused_region_only"
    )
    return {
        "species_latin_name": species.latin_name,
        "species_common_name": species.common_name,
        "direct_coordinate_backed": direct_coordinate_backed,
        "indirectly_geocoded": indirectly_geocoded,
        "unresolved": unresolved,
        "refused_from_mapping": refused_from_mapping,
    }


def _map_publication_accounting(
    data_root: Path,
) -> tuple[Counter[str], list[dict[str, object]]]:
    from bijux_pollenomics.reporting.adna import (
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
        for provenance in _load_coordinate_provenance_rows(species_root):
            if str(provenance.get("mapping_posture", "")) != "mappable_point":
                continue
            coordinate_basis = str(provenance.get("coordinate_basis", ""))
            if coordinate_basis not in {
                "archive_coordinates",
                "direct_published_coordinates",
                "named_site_geocoding",
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
                    "reason_code": "no_sample_backed_locality_candidate",
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
