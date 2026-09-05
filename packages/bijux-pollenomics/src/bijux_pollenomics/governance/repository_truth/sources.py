"""Repository source-family, atlas-input, and acquisition assessments."""

from __future__ import annotations

from pathlib import Path

from .metrics import (
    _atlas_input_row,
    _build_core_counts,
    _build_source_explainer_audit_row,
    _cross_domain_matrix_row,
    _format_metric_map,
    _source_family_row,
)

__all__ = [
    "build_repository_source_explainer_audit",
    "render_repository_source_explainer_audit_markdown",
    "build_repository_source_ecosystem_review",
    "render_repository_source_ecosystem_review_markdown",
    "build_repository_source_family_matrix",
    "render_repository_source_family_matrix_markdown",
    "build_repository_atlas_input_audit",
    "render_repository_atlas_input_audit_markdown",
    "build_repository_cross_domain_evidence_matrix",
    "render_repository_cross_domain_evidence_matrix_markdown",
    "build_repository_source_acquisition_queue",
    "render_repository_source_acquisition_queue_markdown",
    "build_repository_scientific_progress_audit",
    "render_repository_scientific_progress_audit_markdown",
]


def build_repository_source_explainer_audit(
    *,
    data_root: Path,
    docs_root: Path,
    report_root: Path,
) -> dict[str, object]:
    """Audit whether cross-domain data explainers exist in useful form."""
    _ = data_root
    _ = report_root
    rows = []
    expectations = (
        (
            "source_family",
            "LandClim source explainer",
            "docs/public/pollenomics-data/sources/landclim.md",
            ["data/landclim/normalized/", "pollen context"],
            None,
        ),
        (
            "source_family",
            "Neotoma source explainer",
            "docs/public/pollenomics-data/sources/neotoma.md",
            ["data/neotoma/normalized/", "pollen-site context"],
            None,
        ),
        (
            "source_family",
            "SEAD source explainer",
            "docs/public/pollenomics-data/sources/sead.md",
            ["data/sead/normalized/", "archaeology context"],
            None,
        ),
        (
            "source_family",
            "RAÄ source explainer",
            "docs/public/pollenomics-data/sources/raa.md",
            ["data/raa/normalized/", "Sweden"],
            None,
        ),
        (
            "source_family",
            "Boundary source explainer",
            "docs/public/pollenomics-data/sources/boundaries.md",
            ["data/boundaries/normalized/", "country filtering"],
            None,
        ),
        (
            "source_family",
            "AADR source explainer",
            "docs/public/pollenomics-data/sources/aadr.md",
            ["data/aadr/v66/", "human ancient DNA"],
            None,
        ),
        (
            "infrastructure_network",
            "PalaeOpen network explainer",
            "docs/public/pollenomics-data/sources/palaeopen.md",
            ["metadata harmonization", "not a direct source"],
            "restore the PalaeOpen page so collaboration and interoperability work does not get mislabeled as direct evidence capture",
        ),
        (
            "recovery_rule",
            "Refresh policy explainer",
            "docs/public/pollenomics-data/sources/refresh-policy.md",
            ["data/collection_summary.json", "refresh"],
            "restore the refresh-policy page so readers can separate evidence refresh from silent maintenance",
        ),
        (
            "recovery_rule",
            "Shared normalization explainer",
            "docs/public/pollenomics-data/sources/shared-normalization.md",
            ["docs/report/world/", "normalized"],
            "restore the shared-normalization page so readers can see how cross-family output shapes differ from source identity",
        ),
        (
            "output_family",
            "Normalized LandClim outputs explainer",
            "docs/public/pollenomics-data/publications/landclim-exports.md",
            ["data/landclim/normalized/", "LandClim"],
            "restore the LandClim output page so pollen context is not explained only through map presence",
        ),
        (
            "output_family",
            "Normalized Neotoma outputs explainer",
            "docs/public/pollenomics-data/publications/neotoma-exports.md",
            ["data/neotoma/normalized/", "Neotoma"],
            "restore the Neotoma output page so pollen-site context stays visible as its own family",
        ),
        (
            "output_family",
            "Normalized SEAD outputs explainer",
            "docs/public/pollenomics-data/publications/sead-exports.md",
            ["data/sead/normalized/", "SEAD"],
            "restore the SEAD output page so environmental archaeology context does not vanish behind animal publication work",
        ),
        (
            "output_family",
            "Normalized RAÄ outputs explainer",
            "docs/public/pollenomics-data/publications/raa-exports.md",
            ["data/raa/normalized/", "Sweden-specific"],
            "restore the RAÄ output page so Swedish archaeology scope remains explicit",
        ),
        (
            "output_family",
            "Normalized boundary outputs explainer",
            "docs/public/pollenomics-data/publications/boundary-exports.md",
            ["data/boundaries/normalized/", "boundary"],
            "restore the boundary output page so framing layers stay explainable on their own terms",
        ),
        (
            "output_family",
            "Normalized AADR outputs explainer",
            "docs/public/pollenomics-data/publications/aadr-exports.md",
            ["data/aadr/v66/", "AADR"],
            "restore the AADR output page so versioned human context remains inspectable from source to publication",
        ),
        (
            "output_family",
            "Collection summary explainer",
            "docs/public/pollenomics-data/publications/collection-summary.md",
            ["data/collection_summary.json", "summary"],
            "restore the collection summary page so refresh diagnostics are not mistaken for balanced domain coverage",
        ),
    )
    for (
        surface_kind,
        display_name,
        page_path,
        required_snippets,
        restoration_plan,
    ) in expectations:
        rows.append(
            _build_source_explainer_audit_row(
                docs_root=docs_root,
                surface_kind=surface_kind,
                display_name=display_name,
                page_path=page_path,
                required_snippets=required_snippets,
                restoration_plan=restoration_plan,
            )
        )

    status_counts = {
        "present_useful_form": sum(
            1 for row in rows if row["status"] == "present_useful_form"
        ),
        "restoration_plan_required": sum(
            1 for row in rows if row["status"] == "restoration_plan_required"
        ),
    }
    return {
        "schema_version": "repository-source-explainer-audit.v1",
        "row_count": len(rows),
        "status_counts": status_counts,
        "rows": rows,
    }


def render_repository_source_explainer_audit_markdown(
    payload: dict[str, object],
) -> str:
    lines = [
        "# Repository source explainer audit",
        "",
        f"- Explainer rows: `{payload['row_count']}`",
        f"- Present in useful form: `{payload['status_counts']['present_useful_form']}`",
        f"- Still needing a restoration plan: `{payload['status_counts']['restoration_plan_required']}`",
        "",
        "| Explainer | Surface kind | Status | Notes |",
        "| --- | --- | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| `{row['page_path']}` | `{row['surface_kind']}` | `{row['status']}` | {row['notes']} |"
        )
    return "\n".join(lines) + "\n"


def build_repository_source_ecosystem_review(
    *,
    data_root: Path,
    docs_root: Path,
    report_root: Path,
) -> dict[str, object]:
    """Describe high-value source ecosystems that shape repository reuse."""
    _ = data_root
    _ = docs_root
    _ = report_root
    rows = [
        {
            "ecosystem_key": "sead",
            "display_name": "SEAD",
            "ecosystem_role": "direct_source_infrastructure",
            "fit_posture": "high_value_direct_context_partner",
            "repository_role": (
                "environmental archaeology context with strong Sweden, "
                "Scandinavia, and wider European relevance"
            ),
            "official_entry_points": [
                "https://www.sead.se/",
                "https://browser.sead.se/",
                "https://www.umu.se/en/staff/philip-buckland/",
            ],
            "strengths": [
                "direct environmental-archaeology source infrastructure rather than a loose index",
                "good fit for Sweden lake context enrichment because repository rankings already use SEAD site density",
                "supports broader archaeology interpretation beyond a Sweden-only registry",
            ],
            "limits": [
                "context layer, not sample-owned proof of lake identity, chronology, or coordinates",
                "temporal resolution and reference visibility remain uneven across individual SEAD sites even when linked rows are preserved in the checked-in inventory",
            ],
            "recommended_repository_actions": [
                "keep linked temporal and bibliography fields refreshed in checked-in SEAD inventories and surface them in Sweden review products with explicit context-only caveats",
                "use SEAD-rich top Sweden lake candidates as review anchors for context validation and ambiguity checks",
            ],
        },
        {
            "ecosystem_key": "palaeopen",
            "display_name": "PalaeOpen",
            "ecosystem_role": "open_data_network",
            "fit_posture": "high_value_interoperability_network",
            "repository_role": (
                "metadata, taxonomy, and multi-repository palaeoecology alignment "
                "for cross-proxy lake comparison"
            ),
            "official_entry_points": [
                "https://palaeopen.github.io/",
                "https://palaeopen.github.io/About/about.html",
                "https://palaeopen.github.io/join_us.html",
            ],
            "strengths": [
                "explicitly targets open palaeoecological data, taxonomy harmonization, and metadata alignment",
                "bridges terrestrial and aquatic palaeoecology, which matches lake-centered comparison work",
                "useful for turning Sweden lake ranking outputs into broader interoperable comparison surfaces",
            ],
            "limits": [
                "not a direct evidence family and should not be described as one",
                "does not replace local source capture from SEAD, Neotoma, LandClim, or ancient DNA programs",
            ],
            "recommended_repository_actions": [
                "use top-ranked multi-proxy Sweden lakes as concrete interoperability examples rather than vague collaboration claims",
                "align lake registry fields, source-name variants, and cross-proxy terminology with wider palaeoecological metadata practice",
            ],
        },
    ]
    return {
        "schema_version": "repository-source-ecosystem-review.v1",
        "row_count": len(rows),
        "rows": rows,
    }


def render_repository_source_ecosystem_review_markdown(
    payload: dict[str, object],
) -> str:
    lines = [
        "# Repository source ecosystem review",
        "",
        "This packet names upstream source ecosystems that matter to repository",
        "growth even when they are not all direct checked-in evidence families.",
        "",
        f"- Ecosystem rows: `{payload['row_count']}`",
        "",
        "| Ecosystem | Role | Fit posture | Repository role |",
        "| --- | --- | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row['display_name']} | `{row['ecosystem_role']}` | "
            f"`{row['fit_posture']}` | {row['repository_role']} |"
        )
    lines.extend(["", "## Recommended Actions", ""])
    for row in payload["rows"]:
        lines.append(f"### {row['display_name']}")
        lines.append("")
        lines.append(
            "- Official entry points: "
            + ", ".join(f"`{value}`" for value in row["official_entry_points"])
        )
        for action in row["recommended_repository_actions"]:
            lines.append(f"- {action}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


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
    lines = [
        "# Repository source family matrix",
        "",
        f"- Source-family rows: `{payload['row_count']}`",
        "",
        "| Source family | Role | Visible count | Acquisition posture | Main gap |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row['display_name']} | `{row['role']}` | {row['visible_count']} | "
            f"`{row['acquisition_posture']}` | {row['main_gap']} |"
        )
    return "\n".join(lines) + "\n"


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
                "published_point_count": counts["published_atlas_point_count"],
                "unresolved_row_count": counts["animal_map_unresolved_rows"],
            },
            "Animal aDNA is still a partial recovery program whose public map surface depends on sample-owned support reviews and release gates.",
        ),
    ]
    return {
        "schema_version": "repository-atlas-input-audit.v1",
        "row_count": len(rows),
        "rows": rows,
    }


def render_repository_atlas_input_audit_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Repository atlas input audit",
        "",
        f"- Atlas input rows: `{payload['row_count']}`",
        "",
        "| Atlas input | Domain role | Refresh anchor | Tracked metrics | Note |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row['display_name']} | `{row['domain_role']}` | "
            f"`{row['refresh_anchor']}` | {_format_metric_map(row['metrics'])} | {row['note']} |"
        )
    return "\n".join(lines) + "\n"


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
                "tracked_paper_count": counts["tracked_paper_count"],
                "published_atlas_point_count": counts["published_atlas_point_count"],
                "unresolved_map_rows": counts["animal_map_unresolved_rows"],
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
        "schema_version": "repository-cross-domain-evidence-matrix.v1",
        "row_count": len(rows),
        "rows": rows,
    }


def render_repository_cross_domain_evidence_matrix_markdown(
    payload: dict[str, object],
) -> str:
    lines = [
        "# Repository cross-domain evidence matrix",
        "",
        f"- Domain rows: `{payload['row_count']}`",
        "",
        "| Domain | Role | Evidence units | Coverage posture | Current gap |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row['display_name']} | `{row['domain_role']}` | "
            f"{_format_metric_map(row['tracked_metrics'])} | `{row['coverage_posture']}` | {row['current_gap']} |"
        )
    return "\n".join(lines) + "\n"


def build_repository_source_acquisition_queue(
    *,
    data_root: Path,
    docs_root: Path,
    report_root: Path,
) -> dict[str, object]:
    """Publish the next real acquisition or reader-truth work across source families."""
    counts = _build_core_counts(data_root, docs_root, report_root)
    animal_gap_row = {
        "queue_key": "animal_adna_repo_ingestion",
        "source_family": "animal_adna",
        "priority": "high",
        "current_gap": "local reference supplements exceed repository supplement capture",
        "required_outcome": "ingest staged paper and supplement assets into governed repo surfaces, then extract sample, site, and chronology rows",
        "evidence_anchor": "data/adna/governance/source_library/reference_stash_reconciliation.json",
    }
    if (
        counts["papers_with_local_reference_supplements"]
        <= counts["papers_with_archived_supplements"]
    ):
        animal_gap_row = {
            "queue_key": "animal_adna_sample_extraction",
            "source_family": "animal_adna",
            "priority": "high",
            "current_gap": "repository supplement capture now matches visible local staging, but sample, site, and chronology extraction still lags",
            "required_outcome": "use the archived paper supplements to publish sample-owned identity, locality, chronology, and coordinate evidence",
            "evidence_anchor": "data/adna/governance/source_library/project_source_evidence_matrix.json",
        }
    rows = [
        animal_gap_row,
    ]
    surface_to_source = {
        "landclim_site_count": "landclim",
        "landclim_grid_cell_count": "landclim",
        "neotoma_point_count": "neotoma",
        "sead_point_count": "sead",
        "raa_total_site_count": "raa",
        "raa_heritage_site_count": "raa",
    }
    for surface in counts["zero_collection_summary_surfaces"]:
        rows.append(
            {
                "queue_key": f"{surface}_collection_summary_repair",
                "source_family": surface_to_source.get(surface, "source_collection"),
                "priority": "medium",
                "current_gap": f"collection summary still reports `{surface}` as zero",
                "required_outcome": "rebuild the collection summary so public cross-domain counts stop understating the tracked source family",
                "evidence_anchor": "data/collection_summary.json",
            }
        )
    return {
        "schema_version": "repository-source-acquisition-queue.v1",
        "row_count": len(rows),
        "rows": rows,
    }


def render_repository_source_acquisition_queue_markdown(
    payload: dict[str, object],
) -> str:
    lines = [
        "# Repository source acquisition queue",
        "",
        "This queue names the source families whose current tracked capture still",
        "lags the public story. It is a recovery surface, not a vague wishlist:",
        "each row states the concrete source-family gap that still blocks a more",
        "credible publication posture.",
        "",
        f"- Queue rows: `{payload['row_count']}`",
        "",
        "| Source family | Priority | Current gap | Required outcome |",
        "| --- | --- | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| `{row['source_family']}` | `{row['priority']}` | {row['current_gap']} | {row['required_outcome']} |"
        )
    return "\n".join(lines) + "\n"


def build_repository_scientific_progress_audit(
    *,
    data_root: Path,
    docs_root: Path,
    report_root: Path,
) -> dict[str, object]:
    """Describe progress using evidence depth instead of artifact count."""
    counts = _build_core_counts(data_root, docs_root, report_root)
    zero_collection_surfaces = counts["zero_collection_summary_surfaces"]
    return {
        "schema_version": "repository-scientific-progress-audit.v1",
        "overall_progress_posture": "data_recovery_required",
        "progress_measures": [
            "paper-by-paper supplement coverage",
            "sample-owned locality and chronology support depth",
            "mappable animal rows with traceable site and coordinate evidence",
            "non-aDNA source-family explanation breadth",
        ],
        "anti_measures": [
            "checked-in JSON file count",
            "country bundle count without sample-depth context",
            "atlas bundle existence without mapped evidence depth",
        ],
        "findings": [
            (
                f"all {counts['tracked_paper_count']} tracked papers now ship archived supplementary material, but sample-owned extraction still lags behind supplement recovery"
                if counts["papers_with_archived_supplements"]
                >= counts["tracked_paper_count"]
                else f"only {counts['papers_with_archived_supplements']} of {counts['tracked_paper_count']} tracked papers currently ship archived supplementary material"
            ),
            f"the shipped animal atlas still exposes only {counts['published_atlas_point_count']} published animal point rows",
            f"{counts['animal_map_unresolved_rows']} animal rows remain unresolved for mapping and {counts['animal_map_refused_rows']} are refused from mapping",
            (
                "collection_summary still reports zero counts for "
                + ", ".join(zero_collection_surfaces)
                if zero_collection_surfaces
                else "collection_summary keeps non-aDNA counts visible"
            ),
        ],
    }


def render_repository_scientific_progress_audit_markdown(
    payload: dict[str, object],
) -> str:
    lines = [
        "# Repository scientific progress audit",
        "",
        f"- Overall progress posture: `{payload['overall_progress_posture']}`",
        "",
        "## Use These Measures",
        "",
    ]
    for row in payload["progress_measures"]:
        lines.append(f"- {row}")
    lines.extend(
        [
            "",
            "## Do Not Use These As Progress",
            "",
        ]
    )
    for row in payload["anti_measures"]:
        lines.append(f"- {row}")
    lines.extend(
        [
            "",
            "## Current Findings",
            "",
        ]
    )
    for row in payload["findings"]:
        lines.append(f"- {row}")
    return "\n".join(lines) + "\n"
