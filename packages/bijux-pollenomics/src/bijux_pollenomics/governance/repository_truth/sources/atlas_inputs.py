"""Atlas input lineage and refresh-anchor assessments."""

from __future__ import annotations

from pathlib import Path
from typing import TypedDict, cast

from ..metrics import _atlas_input_row, _format_metric_map
from .core_counts import _build_source_assessment_counts as _build_core_counts

__all__ = [
    "build_repository_atlas_input_audit",
    "render_repository_atlas_input_audit_markdown",
]

_AtlasInputRow = TypedDict(
    "_AtlasInputRow",
    {
        "display_name": str,
        "domain_role": str,
        "refresh_anchor": str,
        "metrics": dict[str, object],
        "note": str,
    },
)
_AtlasInputPayload = TypedDict(
    "_AtlasInputPayload",
    {"row_count": int, "rows": list[_AtlasInputRow]},
)


def build_repository_atlas_input_audit(
    *,
    data_root: Path,
    docs_root: Path,
    report_root: Path,
) -> dict[str, object]:
    """Audit how each main atlas layer is sourced and refreshed."""
    counts = _build_core_counts(data_root, docs_root, report_root)
    rows = [
        _atlas_input_row(
            "landclim",
            "LandClim pollen context",
            "primary_domain",
            ["data/landclim/raw/landclim_sources.json"],
            [
                "data/landclim/normalized/nordic_pollen_site_sequences.geojson",
                "data/landclim/normalized/nordic_reveals_grid_cells.geojson",
                "data/landclim/normalized/nordic_reveals_temporal_grid_cells.geojson",
                "data/landclim/normalized/landclim_bibliography.json",
            ],
            [
                "docs/report/regions/nordic/nordic_pollen_site_sequences.geojson",
                "docs/report/regions/nordic/nordic_reveals_temporal_grid_cells.geojson",
            ],
            "data/landclim/normalized/landclim_summary.json",
            {
                "site_count": counts["tracked_landclim_site_count"],
                "grid_cell_count": counts["tracked_landclim_grid_cell_count"],
            },
            "LandClim is a first-class pollen context family, not generic map decoration.",
        ),
        _atlas_input_row(
            "neotoma",
            "Neotoma pollen context",
            "primary_domain",
            ["data/neotoma/raw/neotoma_pollen_dataset_inventory.json"],
            ["data/neotoma/normalized/nordic_pollen_sites.geojson"],
            ["docs/report/regions/nordic/nordic_pollen_sites.geojson"],
            "data/neotoma/raw/neotoma_pollen_sites.json",
            {"site_count": counts["tracked_neotoma_site_count"]},
            "Neotoma broadens the pollen story with its own site inventory and should remain distinct from LandClim.",
        ),
        _atlas_input_row(
            "sead",
            "SEAD archaeology context",
            "contextual_domain",
            ["data/sead/raw/nordic_sites.json"],
            ["data/sead/normalized/nordic_environmental_sites.geojson"],
            ["docs/report/regions/nordic/nordic_environmental_sites.geojson"],
            "data/sead/raw/nordic_sites.json",
            {"site_count": counts["tracked_sead_site_count"]},
            "SEAD is broader environmental archaeology context and should stay visible as its own source family.",
        ),
        _atlas_input_row(
            "raa",
            "RAÄ archaeology context",
            "contextual_domain",
            [
                "data/raa/raw/arkreg_v1_0_wfs_capabilities.xml",
                "data/raa/raw/fornsok_domains.json",
            ],
            [
                "data/raa/normalized/sweden_archaeology_density.geojson",
                "data/raa/normalized/sweden_archaeology_layer.json",
            ],
            (
                [
                    "docs/report/regions/nordic/sweden_archaeology_density.geojson",
                    "docs/report/regions/nordic/sweden_archaeology_layer.json",
                ]
                if counts["raa_density_admitted"]
                else ["docs/report/regions/nordic/sweden_archaeology_layer.json"]
            ),
            "data/raa/normalized/sweden_archaeology_layer.json",
            {
                "publication_status": (
                    "admitted"
                    if counts["raa_density_admitted"]
                    else "refused_not_publication_ready"
                ),
                "published_site_count": (
                    counts["tracked_raa_published_site_count"]
                    if counts["raa_density_admitted"]
                    else None
                ),
                "density_cell_count": (
                    counts["tracked_raa_density_cell_count"]
                    if counts["raa_density_admitted"]
                    else None
                ),
                "reason_codes": counts["raa_density_reason_codes"],
            },
            "RAÄ is explicitly Sweden-scoped and should never be mistaken for Nordic-wide archaeology coverage.",
        ),
        _atlas_input_row(
            "boundaries",
            "Nordic boundary framing",
            "framing_domain",
            [
                "data/boundaries/raw/denmark.geojson",
                "data/boundaries/raw/finland.geojson",
                "data/boundaries/raw/norway.geojson",
                "data/boundaries/raw/sweden.geojson",
            ],
            ["data/boundaries/normalized/nordic_country_boundaries.geojson"],
            ["docs/report/regions/nordic/nordic_country_boundaries.geojson"],
            "data/boundaries/normalized/nordic_country_boundaries.geojson",
            {"country_feature_count": counts["tracked_boundary_feature_count"]},
            "Boundary geometry is framing, not scientific evidence, but it still changes how every mapped layer is interpreted.",
        ),
        _atlas_input_row(
            "animal_adna",
            "Animal aDNA publication surface",
            "contextual_domain",
            [
                "data/adna/governance/source_library/project_source_evidence_matrix.json",
                "data/adna/governance/cross_species_map_readiness.json",
            ],
            [
                "data/adna/final/atlas/animal_atlas_point_candidates.json",
                "data/adna/final/atlas/animal_atlas_point_candidates.csv",
            ],
            [
                "docs/report/world/world_animal_atlas_evidence.json",
                "docs/report/world/world_animal_point_traceability.json",
            ],
            "docs/report/animal_sample_database_review.json",
            {
                "sample_accounting_available": counts[
                    "animal_sample_database_review_available"
                ],
                "coordinate_accounting_available": counts[
                    "animal_map_readiness_available"
                ],
                "published_point_count": counts["published_atlas_point_count"],
                "tracked_sample_count": counts["animal_tracked_sample_count"],
                "unresolved_sample_count": counts["animal_unresolved_sample_count"],
                "coordinate_provenance_count": counts[
                    "animal_coordinate_provenance_count"
                ],
                "refused_coordinate_provenance_count": counts[
                    "animal_coordinate_refused_provenance_count"
                ],
            },
            "Animal aDNA is still a partial recovery program whose public map surface depends on sample-owned support reviews and release gates.",
        ),
    ]
    return {
        "schema_version": "repository-atlas-input-audit.v2",
        "row_count": len(rows),
        "rows": rows,
    }


def render_repository_atlas_input_audit_markdown(payload: dict[str, object]) -> str:
    audit = cast(_AtlasInputPayload, payload)
    lines = [
        "# Repository atlas input audit",
        "",
        f"- Atlas input rows: `{audit['row_count']}`",
        "",
        "| Atlas input | Domain role | Refresh anchor | Tracked metrics | Note |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in audit["rows"]:
        lines.append(
            f"| {row['display_name']} | `{row['domain_role']}` | "
            f"`{row['refresh_anchor']}` | {_format_metric_map(row['metrics'])} | {row['note']} |"
        )
    return "\n".join(lines) + "\n"
