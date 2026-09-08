"""Cross-domain evidence coverage assessments."""

from __future__ import annotations

from pathlib import Path
from typing import TypedDict, cast

from ..metrics import _cross_domain_matrix_row, _format_metric_map
from .core_counts import _build_source_assessment_counts as _build_core_counts

__all__ = [
    "build_repository_cross_domain_evidence_matrix",
    "render_repository_cross_domain_evidence_matrix_markdown",
]


class _CrossDomainRow(TypedDict):
    display_name: str
    domain_role: str
    tracked_metrics: dict[str, object]
    coverage_posture: str
    current_gap: str


class _CrossDomainPayload(TypedDict):
    row_count: int
    rows: list[_CrossDomainRow]


def build_repository_cross_domain_evidence_matrix(
    *,
    data_root: Path,
    docs_root: Path,
    report_root: Path,
) -> dict[str, object]:
    """Describe balanced cross-domain coverage using evidence units, not file counts."""
    counts = _build_core_counts(data_root, docs_root, report_root)
    rows = [
        _cross_domain_matrix_row(
            "pollen_context",
            "Pollen context",
            "primary_domain",
            ["landclim", "neotoma"],
            {
                "landclim_site_count": counts["tracked_landclim_site_count"],
                "landclim_grid_cell_count": counts["tracked_landclim_grid_cell_count"],
                "neotoma_site_count": counts["tracked_neotoma_site_count"],
            },
            [
                "docs/public/pollenomics-data/sources/landclim.md",
                "docs/public/pollenomics-data/sources/neotoma.md",
                "docs/public/pollenomics-data/publications/landclim-exports.md",
                "docs/public/pollenomics-data/publications/neotoma-exports.md",
            ],
            [
                "docs/report/regions/nordic/nordic_pollen_site_sequences.geojson",
                "docs/report/regions/nordic/nordic_pollen_sites.geojson",
            ],
            "first_class_context_family",
            "pollen context is strong as tracked context, but it still needs more pollenomics-first synthesis than the current atlas-facing slices provide",
        ),
        _cross_domain_matrix_row(
            "archaeology_context",
            "Archaeology context",
            "contextual_domain",
            ["sead", "raa"],
            {
                "sead_site_count": counts["tracked_sead_site_count"],
                "raa_publication_status": (
                    "admitted"
                    if counts["raa_density_admitted"]
                    else "refused_not_publication_ready"
                ),
                "raa_published_site_count": (
                    counts["tracked_raa_published_site_count"]
                    if counts["raa_density_admitted"]
                    else None
                ),
                "raa_density_cell_count": (
                    counts["tracked_raa_density_cell_count"]
                    if counts["raa_density_admitted"]
                    else None
                ),
                "raa_reason_codes": counts["raa_density_reason_codes"],
            },
            [
                "docs/public/pollenomics-data/sources/sead.md",
                "docs/public/pollenomics-data/sources/raa.md",
                "docs/public/pollenomics-data/publications/sead-exports.md",
                "docs/public/pollenomics-data/publications/raa-exports.md",
            ],
            (
                [
                    "docs/report/regions/nordic/nordic_environmental_sites.geojson",
                    "docs/report/regions/nordic/sweden_archaeology_density.geojson",
                ]
                if counts["raa_density_admitted"]
                else ["docs/report/regions/nordic/nordic_environmental_sites.geojson"]
            ),
            (
                "explicit_context_family"
                if counts["raa_density_admitted"]
                else "raa_density_refused"
            ),
            "archaeology context remains contextual; RAÄ density is omitted until its authority decision is admitted",
        ),
        _cross_domain_matrix_row(
            "boundary_framing",
            "Boundary framing",
            "framing_domain",
            ["boundaries"],
            {"country_feature_count": counts["tracked_boundary_feature_count"]},
            [
                "docs/public/pollenomics-data/sources/boundaries.md",
                "docs/public/pollenomics-data/publications/boundary-exports.md",
            ],
            ["docs/report/regions/nordic/nordic_country_boundaries.geojson"],
            "strong_framing_surface",
            "boundary geometry is robust framing, but it should never be mistaken for scientific balance on its own",
        ),
        _cross_domain_matrix_row(
            "fieldwork_record",
            "Fieldwork record",
            "contextual_domain",
            ["fieldwork"],
            {"fieldwork_page_count": counts["fieldwork_page_count"]},
            ["docs/public/fieldwork/index.md"],
            ["docs/public/fieldwork/lyngsjon-lake-fieldwork/index.md"],
            "narrow_honest_surface",
            "fieldwork is deliberately narrow and should stay explicit rather than being implied by atlas presence",
        ),
        _cross_domain_matrix_row(
            "animal_adna_context",
            "Animal aDNA context",
            "contextual_domain",
            ["animal_adna"],
            {
                "sample_accounting_available": counts[
                    "animal_sample_database_review_available"
                ],
                "coordinate_accounting_available": counts[
                    "animal_map_readiness_available"
                ],
                "tracked_paper_count": counts["tracked_paper_count"],
                "published_atlas_point_count": counts["published_atlas_point_count"],
                "tracked_sample_count": counts["animal_tracked_sample_count"],
                "unresolved_sample_count": counts["animal_unresolved_sample_count"],
                "coordinate_provenance_count": counts[
                    "animal_coordinate_provenance_count"
                ],
                "refused_coordinate_provenance_count": counts[
                    "animal_coordinate_refused_provenance_count"
                ],
            },
            [
                "docs/public/pollenomics-data/sources/animal-source-intake.md",
                "docs/public/pollenomics-data/evidence/sample-records.md",
                "docs/public/pollenomics-data/evidence/chronology.md",
            ],
            [
                "docs/report/animal_sample_database_review.md",
                "docs/report/world/world_animal_atlas_evidence.json",
            ],
            "partial_sample_owned_surface",
            "animal aDNA is real and now traceable, but it is still a thinner and more recovery-bound surface than the repository's context families",
        ),
        _cross_domain_matrix_row(
            "publication_outputs",
            "Publication outputs",
            "downstream_surface",
            ["country_reports", "nordic_atlas"],
            {
                "sample_accounting_available": counts[
                    "animal_sample_database_review_available"
                ],
                "country_bundle_count": counts["published_country_bundle_count"],
                "animal_point_count": counts["published_atlas_point_count"],
            },
            [
                "docs/public/pollenomics-data/publications/reports.md",
                "docs/public/pollenomics-data/publications/maps.md",
                "docs/public/pollenomics-data/publications/publication-types.md",
            ],
            [
                "docs/report/countries/sweden/README.md",
                "docs/report/world/world_map.html",
            ],
            "downstream_not_governing",
            "reports and atlas bundles summarize upstream evidence; they do not prove balanced coverage by themselves",
        ),
    ]
    return {
        "schema_version": "repository-cross-domain-evidence-matrix.v2",
        "row_count": len(rows),
        "rows": rows,
    }


def render_repository_cross_domain_evidence_matrix_markdown(
    payload: dict[str, object],
) -> str:
    matrix = cast(_CrossDomainPayload, payload)
    lines = [
        "# Repository cross-domain evidence matrix",
        "",
        f"- Domain rows: `{matrix['row_count']}`",
        "",
        "| Domain | Role | Evidence units | Coverage posture | Current gap |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in matrix["rows"]:
        lines.append(
            f"| {row['display_name']} | `{row['domain_role']}` | "
            f"{_format_metric_map(row['tracked_metrics'])} | `{row['coverage_posture']}` | {row['current_gap']} |"
        )
    return "\n".join(lines) + "\n"
