"""Tracked source-family coverage and acquisition posture."""

from __future__ import annotations

from pathlib import Path
from typing import TypedDict, cast

from ..metrics import _source_family_row
from .core_counts import _build_source_assessment_counts as _build_core_counts

__all__ = [
    "build_repository_source_family_matrix",
    "render_repository_source_family_matrix_markdown",
]


class _SourceFamilyRow(TypedDict):
    display_name: str
    role: str
    visible_count: int
    acquisition_posture: str
    main_gap: str


class _SourceFamilyPayload(TypedDict):
    row_count: int
    rows: list[_SourceFamilyRow]


def build_repository_source_family_matrix(
    *,
    data_root: Path,
    docs_root: Path,
    report_root: Path,
) -> dict[str, object]:
    """Describe the main tracked source families with one cross-domain matrix."""
    counts = _build_core_counts(data_root, docs_root, report_root)
    rows = [
        _source_family_row(
            "animal_adna",
            "Animal aDNA papers and supplements",
            "contextual_domain",
            [
                "data/adna/governance/source_library/project_registry.json",
                "data/adna/governance/source_library/project_source_evidence_matrix.json",
            ],
            ["docs/public/pollenomics-data/sources/animal-source-intake.md"],
            counts["tracked_paper_count"],
            "local_reference_staging_ahead_of_repo_capture"
            if counts["papers_with_local_reference_supplements"]
            > counts["papers_with_archived_supplements"]
            else "repo_capture_matches_visible_staging",
            "tracked animal papers still need more supplement ingestion and sample-owned extraction before the atlas becomes representative",
        ),
        _source_family_row(
            "aadr",
            "AADR human ancient DNA",
            "contextual_domain",
            ["data/aadr/v66/"],
            ["docs/public/pollenomics-data/sources/aadr.md"],
            counts["tracked_aadr_release_file_count"],
            "tracked_query_surface",
            "AADR is queryable and documented, but it remains one context layer rather than the whole repository mission",
        ),
        _source_family_row(
            "landclim",
            "LandClim pollen context",
            "primary_domain",
            ["data/landclim/normalized/"],
            ["docs/public/pollenomics-data/sources/landclim.md"],
            counts["tracked_landclim_site_count"]
            + counts["tracked_landclim_grid_cell_count"],
            "tracked_context_layer",
            "LandClim remains real pollen context and should keep explicit links to its normalized files and REVEALS posture",
        ),
        _source_family_row(
            "neotoma",
            "Neotoma pollen context",
            "primary_domain",
            ["data/neotoma/normalized/"],
            ["docs/public/pollenomics-data/sources/neotoma.md"],
            counts["tracked_neotoma_site_count"],
            "tracked_context_layer",
            "Neotoma remains a core pollen-site context family and should stay visible beside aDNA and archaeology surfaces",
        ),
        _source_family_row(
            "sead",
            "SEAD archaeology context",
            "contextual_domain",
            ["data/sead/normalized/"],
            ["docs/public/pollenomics-data/sources/sead.md"],
            counts["tracked_sead_site_count"],
            "tracked_context_layer",
            "SEAD provides environmental archaeology context and should not disappear behind animal intake work",
        ),
        _source_family_row(
            "raa",
            "RAÄ archaeology context",
            "contextual_domain",
            ["data/raa/normalized/"],
            ["docs/public/pollenomics-data/sources/raa.md"],
            counts["tracked_raa_published_site_count"],
            (
                "tracked_context_layer"
                if counts["raa_density_admitted"]
                else "refused_not_publication_ready"
            ),
            (
                "RAÄ remains Sweden-scoped archaeology context and should keep its explicit national scope"
                if counts["raa_density_admitted"]
                else "RAÄ density is excluded until raw inventory, normalized counts, and qualified review reconcile: "
                + ", ".join(counts["raa_density_reason_codes"])
            ),
        ),
        _source_family_row(
            "boundaries",
            "Boundary geometry",
            "framing_domain",
            ["data/boundaries/normalized/"],
            ["docs/public/pollenomics-data/sources/boundaries.md"],
            counts["tracked_boundary_feature_count"],
            "tracked_boundary_frame",
            "Boundary layers are one of the clearest repository surfaces and keep region framing honest",
        ),
        _source_family_row(
            "fieldwork",
            "Fieldwork evidence",
            "contextual_domain",
            ["docs/public/fieldwork/"],
            ["docs/public/fieldwork/index.md"],
            counts["fieldwork_page_count"],
            "narrow_documented_surface",
            "Fieldwork remains intentionally narrow and should stay explicit instead of being implied by other maps",
        ),
    ]
    return {
        "schema_version": "repository-source-family-matrix.v1",
        "row_count": len(rows),
        "rows": rows,
    }


def render_repository_source_family_matrix_markdown(payload: dict[str, object]) -> str:
    matrix = cast(_SourceFamilyPayload, payload)
    lines = [
        "# Repository source family matrix",
        "",
        f"- Source-family rows: `{matrix['row_count']}`",
        "",
        "| Source family | Role | Visible count | Acquisition posture | Main gap |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for row in matrix["rows"]:
        lines.append(
            f"| {row['display_name']} | `{row['role']}` | {row['visible_count']} | "
            f"`{row['acquisition_posture']}` | {row['main_gap']} |"
        )
    return "\n".join(lines) + "\n"
