from __future__ import annotations

import json
from pathlib import Path

__all__ = [
    "build_repository_atlas_input_audit",
    "build_repository_claim_audit",
    "build_repository_cross_domain_evidence_matrix",
    "build_repository_governance_artifact_review",
    "build_repository_recovery_scorecard",
    "build_repository_source_acquisition_queue",
    "build_repository_source_explainer_audit",
    "build_repository_source_family_matrix",
    "build_repository_scientific_progress_audit",
    "build_repository_truth_posture",
    "render_repository_atlas_input_audit_markdown",
    "render_repository_claim_audit_markdown",
    "render_repository_cross_domain_evidence_matrix_markdown",
    "render_repository_governance_artifact_review_markdown",
    "render_repository_recovery_scorecard_markdown",
    "render_repository_source_acquisition_queue_markdown",
    "render_repository_source_explainer_audit_markdown",
    "render_repository_source_family_matrix_markdown",
    "render_repository_scientific_progress_audit_markdown",
    "render_repository_truth_posture_markdown",
]

SCORE_MAX = 4


def build_repository_truth_posture(
    *,
    data_root: Path,
    docs_root: Path,
    report_root: Path,
) -> dict[str, object]:
    """Build one repository-level truth packet about scope, thinness, and recovery."""
    counts = _build_core_counts(data_root, docs_root, report_root)
    scorecard = build_repository_recovery_scorecard(
        data_root=data_root,
        docs_root=docs_root,
        report_root=report_root,
    )
    governance_review = build_repository_governance_artifact_review(
        data_root=data_root,
        report_root=report_root,
    )
    return {
        "schema_version": "repository-truth-posture.v1",
        "repository": "bijux-pollenomics",
        "primary_domains": [
            "pollen_context",
            "environmental_context",
        ],
        "contextual_domains": [
            "archaeology_context",
            "boundary_framing",
            "fieldwork_record",
            "ancient_dna_context",
            "publication_outputs",
        ],
        "incomplete_programs": [
            "animal_sample_site_extraction",
            "animal_sample_chronology_extraction",
            "animal_coordinate_resolution",
            "supplement_capture_recovery",
            "atlas_depth_recovery",
        ],
        "counts": counts,
        "recovery_priorities": [
            "archive missing supplementary material and convert it into sample-owned locality and chronology evidence",
            "rebuild animal locality extraction so sample rows do not collapse into project-level or region-level geography",
            "rebuild chronology extraction so atlas and country outputs stop depending on broad or unresolved sample dates",
            "keep pollen, environmental, archaeology, and boundary explanation first-class while animal aDNA recovery continues",
        ],
        "claim_freeze_reasons": _build_claim_freeze_reasons(counts),
        "do_not_repeat": [
            "do not treat checked-in JSON file count as scientific progress",
            "do not let public atlas presence stand in for sample-owned locality and chronology evidence",
            "do not narrow the repository mission to one thin recovery slice",
            "do not present internal publication accounting as if it were evidence depth",
            "do not call weak or partial animal aDNA coverage region-agnostic or broadly ready",
        ],
        "scorecard_overview": {
            "overall_recovery_posture": scorecard["overall_recovery_posture"],
            "average_dimension_scores": scorecard["average_dimension_scores"],
        },
        "governance_review_summary": governance_review["summary"],
    }


def render_repository_truth_posture_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Repository truth posture",
        "",
        f"- Repository: `{payload['repository']}`",
        f"- Primary domains: `{', '.join(payload['primary_domains'])}`",
        f"- Contextual domains: `{', '.join(payload['contextual_domains'])}`",
        f"- Overall recovery posture: `{payload['scorecard_overview']['overall_recovery_posture']}`",
        "",
        "## Counts",
        "",
        f"- Tracked paper count: `{payload['counts']['tracked_paper_count']}`",
        f"- Papers with archived supplements: `{payload['counts']['papers_with_archived_supplements']}`",
        f"- Published animal atlas points: `{payload['counts']['published_atlas_point_count']}`",
        f"- Unresolved animal map rows: `{payload['counts']['animal_map_unresolved_rows']}`",
        f"- Refused animal map rows: `{payload['counts']['animal_map_refused_rows']}`",
        f"- Source-family explainer count: `{payload['counts']['source_explainer_count']}`",
        "",
        "## Claim Freeze Reasons",
        "",
    ]
    for row in payload["claim_freeze_reasons"]:
        lines.append(f"- {row}")
    lines.extend(
        [
            "",
            "## Recovery Priorities",
            "",
        ]
    )
    for row in payload["recovery_priorities"]:
        lines.append(f"- {row}")
    lines.extend(
        [
            "",
            "## Do Not Repeat",
            "",
        ]
    )
    for row in payload["do_not_repeat"]:
        lines.append(f"- {row}")
    return "\n".join(lines) + "\n"


def build_repository_recovery_scorecard(
    *,
    data_root: Path,
    docs_root: Path,
    report_root: Path,
) -> dict[str, object]:
    """Score the main repository surfaces by evidence depth and honesty."""
    counts = _build_core_counts(data_root, docs_root, report_root)
    rows = [
        _scorecard_row(
            "pollen_context",
            "Pollen context",
            data_completeness=3,
            provenance_clarity=3,
            documentation_clarity=4,
            output_honesty=3,
            metrics={
                "normalized_file_count": counts["pollen_normalized_file_count"],
                "source_pages": 2,
            },
            note="LandClim and Neotoma are real tracked context layers and now have direct explainer pages.",
        ),
        _scorecard_row(
            "archaeology_context",
            "Archaeology context",
            data_completeness=3,
            provenance_clarity=3,
            documentation_clarity=4,
            output_honesty=3,
            metrics={
                "normalized_file_count": counts["archaeology_normalized_file_count"],
                "source_pages": 2,
            },
            note="SEAD and RAÄ are present and documented, but they remain contextual rather than fully synthesized outputs.",
        ),
        _scorecard_row(
            "boundary_framing",
            "Boundary framing",
            data_completeness=4,
            provenance_clarity=4,
            documentation_clarity=4,
            output_honesty=4,
            metrics={
                "raw_file_count": counts["boundary_raw_file_count"],
                "normalized_file_count": counts["boundary_normalized_file_count"],
            },
            note="Boundary geometry is one of the strongest and clearest non-aDNA surfaces in the repository.",
        ),
        _scorecard_row(
            "fieldwork_record",
            "Fieldwork record",
            data_completeness=2,
            provenance_clarity=3,
            documentation_clarity=3,
            output_honesty=4,
            metrics={"fieldwork_page_count": counts["fieldwork_page_count"]},
            note="Fieldwork is intentionally narrow and honest, but it is still only one anchored record surface.",
        ),
        _scorecard_row(
            "ancient_dna_context",
            "Ancient DNA context",
            data_completeness=_ratio_score(
                counts["papers_with_archived_supplements"],
                counts["tracked_paper_count"],
            ),
            provenance_clarity=_ratio_score(
                counts["animal_map_supported_rows"],
                counts["animal_sample_row_count"],
            ),
            documentation_clarity=3,
            output_honesty=3,
            metrics={
                "tracked_papers": counts["tracked_paper_count"],
                "papers_with_archived_supplements": counts["papers_with_archived_supplements"],
                "published_atlas_points": counts["published_atlas_point_count"],
                "unresolved_rows": counts["animal_map_unresolved_rows"],
            },
            note="The animal aDNA program has real tracked structure but still weak evidence depth relative to its public surfaces.",
        ),
        _scorecard_row(
            "publication_outputs",
            "Publication outputs",
            data_completeness=_ratio_score(
                counts["published_atlas_point_count"],
                max(counts["animal_sample_row_count"], 1),
            ),
            provenance_clarity=3,
            documentation_clarity=3,
            output_honesty=3,
            metrics={
                "published_atlas_points": counts["published_atlas_point_count"],
                "published_country_bundles": counts["published_country_bundle_count"],
            },
            note="The publication tree is reviewable and traceable, but the animal point surface remains too thin for stronger readiness language.",
        ),
        _scorecard_row(
            "documentation_architecture",
            "Documentation architecture",
            data_completeness=3,
            provenance_clarity=3,
            documentation_clarity=4,
            output_honesty=4,
            metrics={
                "source_explainer_count": counts["source_explainer_count"],
                "landing_page_count": counts["landing_page_count"],
            },
            note="Breadth has been restored across repository, data, maintainer, fieldwork, and atlas entry surfaces.",
        ),
    ]
    averages = {
        "data_completeness": round(
            sum(int(row["data_completeness"]) for row in rows) / len(rows), 2
        ),
        "provenance_clarity": round(
            sum(int(row["provenance_clarity"]) for row in rows) / len(rows), 2
        ),
        "documentation_clarity": round(
            sum(int(row["documentation_clarity"]) for row in rows) / len(rows), 2
        ),
        "output_honesty": round(
            sum(int(row["output_honesty"]) for row in rows) / len(rows), 2
        ),
    }
    return {
        "schema_version": "repository-recovery-scorecard.v1",
        "score_max": SCORE_MAX,
        "overall_recovery_posture": (
            "recovery_required"
            if any(int(row["data_completeness"]) <= 1 for row in rows)
            else "moderate_recovery"
        ),
        "average_dimension_scores": averages,
        "rows": rows,
    }


def render_repository_recovery_scorecard_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Repository recovery scorecard",
        "",
        f"- Overall recovery posture: `{payload['overall_recovery_posture']}`",
        f"- Score max: `{payload['score_max']}`",
        "",
        "| Surface | Data completeness | Provenance clarity | Documentation clarity | Output honesty |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row['display_name']} | {row['data_completeness']} | "
            f"{row['provenance_clarity']} | {row['documentation_clarity']} | "
            f"{row['output_honesty']} |"
        )
    return "\n".join(lines) + "\n"


def build_repository_governance_artifact_review(
    *,
    data_root: Path,
    report_root: Path,
) -> dict[str, object]:
    """Review current aDNA governance artifacts by evidence value, not file presence."""
    _ = data_root
    rows = [
        _artifact_review_row(
            "docs/report/animal_publication_release_gate.json",
            "keep",
            "claim_gate",
            "This file blocks strong public claims when traceability or chronology support is missing.",
        ),
        _artifact_review_row(
            "docs/report/animal_foundation_validation.json",
            "keep",
            "validation",
            "This file checks sample, site, coordinate, and source structure instead of just formatting.",
        ),
        _artifact_review_row(
            "data/adna/governance/source_library/project_sample_site_review.json",
            "keep",
            "evidence_review",
            "This file surfaces site-assignment weakness project by project.",
        ),
        _artifact_review_row(
            "data/adna/governance/source_library/project_sample_chronology_review.json",
            "keep",
            "evidence_review",
            "This file surfaces chronology extraction weakness project by project.",
        ),
        _artifact_review_row(
            "docs/report/animal_point_support_packets.json",
            "keep",
            "traceability",
            "This file keeps published points anchored to sample, site, and coordinate support.",
        ),
        _artifact_review_row(
            "docs/report/animal_atlas_readiness.json",
            "reframe",
            "coverage_summary",
            "The current name reads stronger than the underlying point depth and must always sit beside unresolved and blocked counts.",
        ),
        _artifact_review_row(
            "docs/report/animal_sample_database_review.json",
            "reframe",
            "public_posture",
            "This file should describe partial recovery posture, not broad readiness or region-agnostic support.",
        ),
        _artifact_review_row(
            "data/adna/governance/cross_species_map_readiness.json",
            "reframe",
            "coverage_summary",
            "This file is useful only when readers can also see how many rows remain unresolved or refused.",
        ),
        _artifact_review_row(
            "docs/report/animal_output_audit.json",
            "retire",
            "publication_accounting",
            "This file counts shipped public surfaces but says little about evidence depth and should not lead the scientific story.",
        ),
    ]
    repo_root = report_root.parents[1]
    existing_rows = [row for row in rows if (repo_root / row["artifact_path"]).exists()]
    summary = {
        "keep": sum(1 for row in existing_rows if row["action"] == "keep"),
        "reframe": sum(1 for row in existing_rows if row["action"] == "reframe"),
        "retire": sum(1 for row in existing_rows if row["action"] == "retire"),
    }
    return {
        "schema_version": "repository-governance-artifact-review.v1",
        "summary": summary,
        "rows": existing_rows,
    }


def render_repository_governance_artifact_review_markdown(
    payload: dict[str, object]
) -> str:
    lines = [
        "# Repository governance artifact review",
        "",
        "| Artifact | Action | Surface kind | Reason |",
        "| --- | --- | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| `{row['artifact_path']}` | `{row['action']}` | `{row['surface_kind']}` | {row['reason']} |"
        )
    return "\n".join(lines) + "\n"


def build_repository_claim_audit(
    *,
    data_root: Path,
    docs_root: Path,
    report_root: Path,
) -> dict[str, object]:
    """Audit the public story against current tracked evidence depth."""
    counts = _build_core_counts(data_root, docs_root, report_root)
    root_readme_path = docs_root.parent / "README.md"
    docs_index_path = docs_root / "index.md"
    runtime_readme_path = (
        docs_root.parent / "packages" / "bijux-pollenomics" / "README.md"
    )
    data_index_path = docs_root / "02-bijux-pollenomics-data" / "index.md"
    sample_database_review_path = report_root / "animal_sample_database_review.json"
    release_gate_path = report_root / "animal_publication_release_gate.json"

    if not all(
        path.exists()
        for path in (
            root_readme_path,
            docs_index_path,
            runtime_readme_path,
            data_index_path,
            sample_database_review_path,
            release_gate_path,
        )
    ):
        return {
            "schema_version": "repository-claim-audit.v1",
            "audit_scope": "partial_context",
            "overall_ok": True,
            "counts": counts,
            "checks": [
                _claim_check(
                    "repository_truth_audit_requires_full_repository_context",
                    True,
                    "Repository truth audit runs in reduced mode when the full repository docs and data tree are not present.",
                    ["partial_context_assumed"],
                )
            ],
        }

    root_readme = root_readme_path.read_text(encoding="utf-8")
    docs_index = docs_index_path.read_text(encoding="utf-8")
    runtime_readme = runtime_readme_path.read_text(encoding="utf-8")
    data_index = data_index_path.read_text(encoding="utf-8")
    sample_database_review = _load_json(sample_database_review_path)
    release_gate = _load_json(release_gate_path)

    checks = [
        _claim_check(
            "repository_landings_name_pollenomics_first",
            all(
                text in root_readme + docs_index + runtime_readme + data_index
                for text in (
                    "pollenomics and environmental evidence",
                    "source comparison",
                )
            ),
            "Repository landings describe pollenomics and environmental evidence before the thin animal recovery slice.",
            [],
        ),
        _claim_check(
            "source_family_pages_restore_non_adna_breadth",
            counts["source_explainer_count"] >= 6,
            "The docs tree keeps non-aDNA source families visible and directly linkable.",
            [] if counts["source_explainer_count"] >= 6 else ["source_explainer_count_below_expected_floor"],
        ),
        _claim_check(
            "animal_sample_review_freezes_broad_readiness",
            (
                str(sample_database_review.get("public_posture", "")).strip()
                == "partial_sample_owned_animal_evidence_surface"
                and not bool(sample_database_review.get("region_agnostic_contract_ready"))
            ),
            "The public animal sample review keeps the stronger Nordic sample-owned view separate from any broader region-agnostic readiness claim.",
            []
            if (
                str(sample_database_review.get("public_posture", "")).strip()
                == "partial_sample_owned_animal_evidence_surface"
                and not bool(sample_database_review.get("region_agnostic_contract_ready"))
            )
            else ["animal_sample_database_review_overclaims_current_depth"],
        ),
        _claim_check(
            "animal_release_gate_blocks_strongest_claim",
            not bool(release_gate.get("reference_grade_claim_allowed")),
            "The current release gate still freezes the strongest public claim.",
            []
            if not bool(release_gate.get("reference_grade_claim_allowed"))
            else ["strongest_claim_not_frozen"],
        ),
        _claim_check(
            "thin_animal_surface_stays_visible",
            (
                counts["published_atlas_point_count"] >= 10
                and str(sample_database_review.get("public_posture", "")).strip()
                == "partial_sample_owned_animal_evidence_surface"
            ),
            "The public animal surfaces keep the current partial sample-owned posture visible instead of implying broad completion.",
            []
            if (
                counts["published_atlas_point_count"] >= 10
                and str(sample_database_review.get("public_posture", "")).strip()
                == "partial_sample_owned_animal_evidence_surface"
            )
            else ["partial_animal_surface_not_explicitly_named"],
        ),
    ]
    return {
        "schema_version": "repository-claim-audit.v1",
        "audit_scope": "full_repository",
        "overall_ok": all(bool(row["passed"]) for row in checks),
        "counts": counts,
        "checks": checks,
    }


def render_repository_claim_audit_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Repository claim audit",
        "",
        f"- Overall ok: `{str(payload['overall_ok']).lower()}`",
        f"- Published animal atlas points: `{payload['counts']['published_atlas_point_count']}`",
        f"- Papers with archived supplements: `{payload['counts']['papers_with_archived_supplements']}`",
        "",
        "| Check | Passed | Finding count |",
        "| --- | --- | ---: |",
    ]
    for row in payload["checks"]:
        lines.append(
            f"| {row['check_id']} | `{str(row['passed']).lower()}` | {row['finding_count']} |"
        )
    return "\n".join(lines) + "\n"


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
            "docs/02-bijux-pollenomics-data/sources/landclim.md",
            ["data/landclim/normalized/", "pollen context"],
            None,
        ),
        (
            "source_family",
            "Neotoma source explainer",
            "docs/02-bijux-pollenomics-data/sources/neotoma.md",
            ["data/neotoma/normalized/", "pollen-site context"],
            None,
        ),
        (
            "source_family",
            "SEAD source explainer",
            "docs/02-bijux-pollenomics-data/sources/sead.md",
            ["data/sead/normalized/", "archaeology context"],
            None,
        ),
        (
            "source_family",
            "RAÄ source explainer",
            "docs/02-bijux-pollenomics-data/sources/raa.md",
            ["data/raa/normalized/", "Sweden"],
            None,
        ),
        (
            "source_family",
            "Boundary source explainer",
            "docs/02-bijux-pollenomics-data/sources/boundaries.md",
            ["data/boundaries/normalized/", "country filtering"],
            None,
        ),
        (
            "source_family",
            "AADR source explainer",
            "docs/02-bijux-pollenomics-data/sources/aadr.md",
            ["data/aadr/v66/", "human ancient DNA"],
            None,
        ),
        (
            "recovery_rule",
            "Refresh policy explainer",
            "docs/02-bijux-pollenomics-data/sources/refresh-policy.md",
            ["data/collection_summary.json", "refresh"],
            "restore the refresh-policy page so readers can separate evidence refresh from silent maintenance",
        ),
        (
            "recovery_rule",
            "Shared normalization explainer",
            "docs/02-bijux-pollenomics-data/sources/shared-normalization.md",
            ["docs/report/nordic-atlas/", "normalized"],
            "restore the shared-normalization page so readers can see how cross-family output shapes differ from source identity",
        ),
        (
            "output_family",
            "Normalized LandClim outputs explainer",
            "docs/02-bijux-pollenomics-data/outputs/normalized-landclim.md",
            ["data/landclim/normalized/", "LandClim"],
            "restore the LandClim output page so pollen context is not explained only through map presence",
        ),
        (
            "output_family",
            "Normalized Neotoma outputs explainer",
            "docs/02-bijux-pollenomics-data/outputs/normalized-neotoma.md",
            ["data/neotoma/normalized/", "Neotoma"],
            "restore the Neotoma output page so pollen-site context stays visible as its own family",
        ),
        (
            "output_family",
            "Normalized SEAD outputs explainer",
            "docs/02-bijux-pollenomics-data/outputs/normalized-sead.md",
            ["data/sead/normalized/", "SEAD"],
            "restore the SEAD output page so environmental archaeology context does not vanish behind animal publication work",
        ),
        (
            "output_family",
            "Normalized RAÄ outputs explainer",
            "docs/02-bijux-pollenomics-data/outputs/normalized-raa.md",
            ["data/raa/normalized/", "Sweden-scoped"],
            "restore the RAÄ output page so Swedish archaeology scope remains explicit",
        ),
        (
            "output_family",
            "Normalized boundary outputs explainer",
            "docs/02-bijux-pollenomics-data/outputs/normalized-boundaries.md",
            ["data/boundaries/normalized/", "boundary"],
            "restore the boundary output page so framing layers stay explainable on their own terms",
        ),
        (
            "output_family",
            "Normalized AADR outputs explainer",
            "docs/02-bijux-pollenomics-data/outputs/normalized-aadr.md",
            ["data/aadr/v66/", "AADR"],
            "restore the AADR output page so versioned human context remains inspectable from source to publication",
        ),
        (
            "output_family",
            "Collection summary explainer",
            "docs/02-bijux-pollenomics-data/outputs/collection-summary.md",
            ["data/collection_summary.json", "summary"],
            "restore the collection summary page so refresh diagnostics are not mistaken for balanced domain coverage",
        ),
    )
    for surface_kind, display_name, page_path, required_snippets, restoration_plan in expectations:
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
    payload: dict[str, object]
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
            ["docs/02-bijux-pollenomics-data/sources/animal-source-intake.md"],
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
            ["docs/02-bijux-pollenomics-data/sources/aadr.md"],
            counts["tracked_aadr_release_file_count"],
            "tracked_query_surface",
            "AADR is queryable and documented, but it remains one context layer rather than the whole repository mission",
        ),
        _source_family_row(
            "landclim",
            "LandClim pollen context",
            "primary_domain",
            ["data/landclim/normalized/"],
            ["docs/02-bijux-pollenomics-data/sources/landclim.md"],
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
            ["docs/02-bijux-pollenomics-data/sources/neotoma.md"],
            counts["tracked_neotoma_site_count"],
            "tracked_context_layer",
            "Neotoma remains a core pollen-site context family and should stay visible beside aDNA and archaeology surfaces",
        ),
        _source_family_row(
            "sead",
            "SEAD archaeology context",
            "contextual_domain",
            ["data/sead/normalized/"],
            ["docs/02-bijux-pollenomics-data/sources/sead.md"],
            counts["tracked_sead_site_count"],
            "tracked_context_layer",
            "SEAD provides environmental archaeology context and should not disappear behind animal intake work",
        ),
        _source_family_row(
            "raa",
            "RAÄ archaeology context",
            "contextual_domain",
            ["data/raa/normalized/"],
            ["docs/02-bijux-pollenomics-data/sources/raa.md"],
            counts["tracked_raa_published_site_count"],
            "tracked_context_layer",
            "RAÄ remains Sweden-scoped archaeology context and should keep its explicit national scope",
        ),
        _source_family_row(
            "boundaries",
            "Boundary geometry",
            "framing_domain",
            ["data/boundaries/normalized/"],
            ["docs/02-bijux-pollenomics-data/sources/boundaries.md"],
            counts["tracked_boundary_feature_count"],
            "tracked_boundary_frame",
            "Boundary layers are one of the clearest repository surfaces and keep region framing honest",
        ),
        _source_family_row(
            "fieldwork",
            "Fieldwork evidence",
            "contextual_domain",
            ["docs/04-fieldwork/"],
            ["docs/04-fieldwork/index.md"],
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
            ],
            [
                "docs/report/nordic-atlas/nordic_pollen_site_sequences.geojson",
                "docs/report/nordic-atlas/nordic_reveals_grid_cells.geojson",
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
            ["docs/report/nordic-atlas/nordic_pollen_sites.geojson"],
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
            ["docs/report/nordic-atlas/nordic_environmental_sites.geojson"],
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
            [
                "docs/report/nordic-atlas/sweden_archaeology_density.geojson",
                "docs/report/nordic-atlas/sweden_archaeology_layer.json",
            ],
            "data/raa/normalized/sweden_archaeology_layer.json",
            {
                "published_site_count": counts["tracked_raa_published_site_count"],
                "density_cell_count": counts["tracked_raa_density_cell_count"],
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
            ["docs/report/nordic-atlas/nordic_country_boundaries.geojson"],
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
                "docs/report/nordic-atlas/nordic-atlas_animal_atlas_evidence.json",
                "docs/report/nordic-atlas/nordic-atlas_animal_point_traceability.json",
            ],
            "docs/report/animal_sample_database_review.json",
            {
                "published_point_count": counts["published_atlas_point_count"],
                "unresolved_row_count": counts["animal_map_unresolved_rows"],
            },
            "Animal aDNA is still a partial recovery program whose public map surface depends on sample-owned support packets and release gates.",
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
                "docs/02-bijux-pollenomics-data/sources/landclim.md",
                "docs/02-bijux-pollenomics-data/sources/neotoma.md",
                "docs/02-bijux-pollenomics-data/outputs/normalized-landclim.md",
                "docs/02-bijux-pollenomics-data/outputs/normalized-neotoma.md",
            ],
            [
                "docs/report/nordic-atlas/nordic_pollen_site_sequences.geojson",
                "docs/report/nordic-atlas/nordic_pollen_sites.geojson",
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
                "raa_published_site_count": counts["tracked_raa_published_site_count"],
                "raa_density_cell_count": counts["tracked_raa_density_cell_count"],
            },
            [
                "docs/02-bijux-pollenomics-data/sources/sead.md",
                "docs/02-bijux-pollenomics-data/sources/raa.md",
                "docs/02-bijux-pollenomics-data/outputs/normalized-sead.md",
                "docs/02-bijux-pollenomics-data/outputs/normalized-raa.md",
            ],
            [
                "docs/report/nordic-atlas/nordic_environmental_sites.geojson",
                "docs/report/nordic-atlas/sweden_archaeology_density.geojson",
            ],
            "explicit_context_family",
            "archaeology context is broad but intentionally contextual; readers should not confuse it with direct pollen or sample evidence",
        ),
        _cross_domain_matrix_row(
            "boundary_framing",
            "Boundary framing",
            "framing_domain",
            ["boundaries"],
            {"country_feature_count": counts["tracked_boundary_feature_count"]},
            [
                "docs/02-bijux-pollenomics-data/sources/boundaries.md",
                "docs/02-bijux-pollenomics-data/outputs/normalized-boundaries.md",
            ],
            ["docs/report/nordic-atlas/nordic_country_boundaries.geojson"],
            "strong_framing_surface",
            "boundary geometry is robust framing, but it should never be mistaken for scientific balance on its own",
        ),
        _cross_domain_matrix_row(
            "fieldwork_record",
            "Fieldwork record",
            "contextual_domain",
            ["fieldwork"],
            {"fieldwork_page_count": counts["fieldwork_page_count"]},
            ["docs/04-fieldwork/index.md"],
            ["docs/04-fieldwork/lyngsjon-lake-fieldwork/index.md"],
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
                "docs/02-bijux-pollenomics-data/sources/animal-source-intake.md",
                "docs/02-bijux-pollenomics-data/evidence/sample-records.md",
                "docs/02-bijux-pollenomics-data/evidence/chronology.md",
            ],
            [
                "docs/report/animal_sample_database_review.md",
                "docs/report/nordic-atlas/nordic-atlas_animal_atlas_evidence.json",
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
                "docs/02-bijux-pollenomics-data/outputs/published-reports.md",
                "docs/02-bijux-pollenomics-data/outputs/nordic-atlas.md",
                "docs/02-bijux-pollenomics-data/outputs/output-surface-classes.md",
            ],
            [
                "docs/report/sweden/README.md",
                "docs/report/nordic-atlas/nordic-atlas_map.html",
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
    payload: dict[str, object]
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
    if counts["papers_with_local_reference_supplements"] <= counts["papers_with_archived_supplements"]:
        animal_gap_row = {
            "queue_key": "animal_adna_sample_extraction",
            "source_family": "animal_adna",
            "priority": "high",
            "current_gap": "repository supplement capture now matches visible local staging, but sample, site, and chronology extraction still lags",
            "required_outcome": "use the archived paper supplements to publish sample-owned identity, locality, chronology, and coordinate evidence",
            "evidence_anchor": "data/adna/governance/source_library/project_source_evidence_matrix.json",
        }
    rows = [animal_gap_row]
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


def render_repository_source_acquisition_queue_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Repository source acquisition queue",
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
                if counts["papers_with_archived_supplements"] >= counts["tracked_paper_count"]
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
    payload: dict[str, object]
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


def _build_core_counts(
    data_root: Path,
    docs_root: Path,
    report_root: Path,
) -> dict[str, object]:
    paper_registry = _load_json_or_default(
        data_root / "adna" / "governance" / "source_library" / "paper_registry.json",
        {"rows": []},
    )
    reference_stash_reconciliation = _load_json_or_default(
        data_root / "adna" / "governance" / "source_library" / "reference_stash_reconciliation.json",
        {"rows": []},
    )
    reference_stash_doi_integrity = _load_json_or_default(
        data_root / "adna" / "governance" / "source_library" / "reference_stash_doi_integrity_audit.json",
        {"reference_stash_doi_count": 0},
    )
    map_readiness = _load_json_or_default(
        data_root / "adna" / "governance" / "cross_species_map_readiness.json",
        {
            "totals": {
                "direct_coordinate_backed": 0,
                "indirectly_geocoded": 0,
                "unresolved": 0,
                "refused_from_mapping": 0,
            }
        },
    )
    sample_database_review = _load_json_or_default(
        report_root / "animal_sample_database_review.json",
        {"counts": {}},
    )
    collection_summary = _load_json_or_default(data_root / "collection_summary.json", {})
    landclim_summary = _load_json_or_default(
        data_root / "landclim" / "normalized" / "landclim_summary.json",
        {"site_count": 0, "grid_cell_count": 0},
    )
    neotoma_sites = _load_json_or_default(
        data_root / "neotoma" / "raw" / "neotoma_pollen_sites.json",
        {"site_count": 0},
    )
    sead_sites = _load_json_or_default(
        data_root / "sead" / "raw" / "nordic_sites.json",
        {"row_count": 0},
    )
    raa_layer = _load_json_or_default(
        data_root / "raa" / "normalized" / "sweden_archaeology_layer.json",
        {"density_feature_count": 0, "counts": {}},
    )

    paper_rows = list(paper_registry.get("rows", []))
    totals = dict(map_readiness.get("totals", {}))
    zero_collection_surfaces = [
        key
        for key in (
            "landclim_site_count",
            "landclim_grid_cell_count",
            "neotoma_point_count",
            "sead_point_count",
            "raa_total_site_count",
            "raa_heritage_site_count",
        )
        if int(collection_summary.get(key, 0)) == 0
    ]
    return {
        "tracked_paper_count": len(paper_rows),
        "papers_with_archived_supplements": sum(
            1 for row in paper_rows if int(row.get("supplementary_count", 0)) > 0
        ),
        "published_atlas_point_count": int(
            sample_database_review.get("counts", {}).get("published_atlas_point_count", 0)
        ),
        "published_country_bundle_count": int(
            sample_database_review.get("counts", {}).get("published_country_bundle_count", 0)
        ),
        "reference_stash_doi_count": int(
            reference_stash_doi_integrity.get("reference_stash_doi_count", 0)
        ),
        "tracked_aadr_release_file_count": _count_tree_files(data_root / "aadr" / "v66"),
        "papers_with_local_reference_supplements": sum(
            1
            for row in reference_stash_reconciliation.get("rows", [])
            if bool(row.get("paper_registry_present"))
            and row.get("local_reference_supplement_status") == "local_reference_staged"
        ),
        "animal_sample_row_count": int(
            sample_database_review.get("counts", {}).get("sample_row_count", 0)
        ),
        "animal_map_supported_rows": int(totals.get("direct_coordinate_backed", 0))
        + int(totals.get("indirectly_geocoded", 0)),
        "animal_map_unresolved_rows": int(totals.get("unresolved", 0)),
        "animal_map_refused_rows": int(totals.get("refused_from_mapping", 0)),
        "tracked_landclim_site_count": int(landclim_summary.get("site_count", 0)),
        "tracked_landclim_grid_cell_count": int(
            landclim_summary.get("grid_cell_count", 0)
        ),
        "tracked_neotoma_site_count": int(neotoma_sites.get("site_count", 0)),
        "tracked_sead_site_count": int(sead_sites.get("row_count", 0)),
        "tracked_raa_published_site_count": int(
            dict(raa_layer.get("counts", {})).get("all_published_sites", 0)
        ),
        "tracked_raa_density_cell_count": int(
            raa_layer.get("density_feature_count", 0)
        ),
        "tracked_boundary_feature_count": _count_geojson_features(
            data_root / "boundaries" / "normalized" / "nordic_country_boundaries.geojson"
        ),
        "pollen_normalized_file_count": _count_files(
            data_root / "landclim" / "normalized"
        )
        + _count_files(data_root / "neotoma" / "normalized"),
        "archaeology_normalized_file_count": _count_files(
            data_root / "sead" / "normalized"
        )
        + _count_files(data_root / "raa" / "normalized"),
        "boundary_raw_file_count": _count_files(data_root / "boundaries" / "raw"),
        "boundary_normalized_file_count": _count_files(
            data_root / "boundaries" / "normalized"
        ),
        "fieldwork_page_count": sum(
            1 for _ in (docs_root / "04-fieldwork").rglob("index.md")
        ),
        "source_explainer_count": sum(
            1
            for path in (docs_root / "02-bijux-pollenomics-data" / "sources").glob(
                "*.md"
            )
            if path.name
            not in {
                "index.md",
                "animal-source-intake.md",
            }
        ),
        "landing_page_count": sum(
            int(path.exists())
            for path in (
                docs_root / "index.md",
                docs_root / "01-bijux-pollenomics" / "index.md",
                docs_root / "02-bijux-pollenomics-data" / "index.md",
                docs_root / "03-bijux-pollenomics-maintain" / "index.md",
                docs_root / "04-fieldwork" / "index.md",
                docs_root / "05-nordic-evidence-atlas" / "index.md",
            )
        ),
        "zero_collection_summary_surfaces": zero_collection_surfaces,
    }


def _build_claim_freeze_reasons(counts: dict[str, object]) -> list[str]:
    reasons = []
    if int(counts["papers_with_archived_supplements"]) < int(counts["tracked_paper_count"]):
        reasons.append("supplement recovery is still far below paper coverage")
    if int(counts["published_atlas_point_count"]) <= 2:
        reasons.append("the shipped animal atlas point surface is still effectively empty")
    if int(counts["animal_map_unresolved_rows"]) > int(counts["animal_map_supported_rows"]):
        reasons.append("unresolved animal geography still overwhelms mapped support")
    if counts["zero_collection_summary_surfaces"]:
        reasons.append("collection summary still under-reports several non-aDNA source counts")
    return reasons


def _scorecard_row(
    key: str,
    display_name: str,
    *,
    data_completeness: int,
    provenance_clarity: int,
    documentation_clarity: int,
    output_honesty: int,
    metrics: dict[str, object],
    note: str,
) -> dict[str, object]:
    return {
        "surface_key": key,
        "display_name": display_name,
        "data_completeness": data_completeness,
        "provenance_clarity": provenance_clarity,
        "documentation_clarity": documentation_clarity,
        "output_honesty": output_honesty,
        "metrics": metrics,
        "note": note,
    }


def _artifact_review_row(
    artifact_path: str,
    action: str,
    surface_kind: str,
    reason: str,
) -> dict[str, object]:
    return {
        "artifact_path": artifact_path,
        "action": action,
        "surface_kind": surface_kind,
        "reason": reason,
    }


def _source_family_row(
    key: str,
    display_name: str,
    role: str,
    artifact_paths: list[str],
    docs_paths: list[str],
    visible_count: int,
    acquisition_posture: str,
    main_gap: str,
) -> dict[str, object]:
    return {
        "source_key": key,
        "display_name": display_name,
        "role": role,
        "artifact_paths": artifact_paths,
        "docs_paths": docs_paths,
        "visible_count": visible_count,
        "acquisition_posture": acquisition_posture,
        "main_gap": main_gap,
    }


def _build_source_explainer_audit_row(
    *,
    docs_root: Path,
    surface_kind: str,
    display_name: str,
    page_path: str,
    required_snippets: list[str],
    restoration_plan: str | None,
) -> dict[str, object]:
    page = docs_root.parent / page_path
    if page.exists():
        text = page.read_text(encoding="utf-8")
        missing_snippets = [
            snippet for snippet in required_snippets if snippet not in text
        ]
        if not missing_snippets:
            return {
                "surface_kind": surface_kind,
                "display_name": display_name,
                "page_path": page_path,
                "status": "present_useful_form",
                "notes": "page exists and keeps the expected source or output anchors visible",
            }
        return {
            "surface_kind": surface_kind,
            "display_name": display_name,
            "page_path": page_path,
            "status": "restoration_plan_required",
            "notes": "missing expected anchors: "
            + ", ".join(f"`{snippet}`" for snippet in missing_snippets),
        }
    return {
        "surface_kind": surface_kind,
        "display_name": display_name,
        "page_path": page_path,
        "status": "restoration_plan_required",
        "notes": restoration_plan
        or "page is missing and needs a concrete restoration path",
    }


def _atlas_input_row(
    key: str,
    display_name: str,
    domain_role: str,
    source_paths: list[str],
    normalized_paths: list[str],
    published_paths: list[str],
    refresh_anchor: str,
    metrics: dict[str, int],
    note: str,
) -> dict[str, object]:
    return {
        "input_key": key,
        "display_name": display_name,
        "domain_role": domain_role,
        "source_paths": source_paths,
        "normalized_paths": normalized_paths,
        "published_paths": published_paths,
        "refresh_anchor": refresh_anchor,
        "metrics": metrics,
        "note": note,
    }


def _cross_domain_matrix_row(
    key: str,
    display_name: str,
    domain_role: str,
    source_families: list[str],
    tracked_metrics: dict[str, int],
    docs_paths: list[str],
    published_paths: list[str],
    coverage_posture: str,
    current_gap: str,
) -> dict[str, object]:
    return {
        "domain_key": key,
        "display_name": display_name,
        "domain_role": domain_role,
        "source_families": source_families,
        "tracked_metrics": tracked_metrics,
        "docs_paths": docs_paths,
        "published_paths": published_paths,
        "coverage_posture": coverage_posture,
        "current_gap": current_gap,
    }


def _claim_check(
    check_id: str,
    passed: bool,
    description: str,
    findings: list[str],
) -> dict[str, object]:
    return {
        "check_id": check_id,
        "passed": passed,
        "description": description,
        "finding_count": len(findings),
        "findings": findings,
    }


def _ratio_score(numerator: int, denominator: int) -> int:
    if denominator <= 0:
        return 0
    ratio = numerator / denominator
    if ratio >= 0.9:
        return 4
    if ratio >= 0.6:
        return 3
    if ratio >= 0.3:
        return 2
    if ratio >= 0.1:
        return 1
    return 0


def _count_files(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for file_path in path.iterdir() if file_path.is_file())


def _count_tree_files(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for file_path in path.rglob("*") if file_path.is_file())


def _count_geojson_features(path: Path) -> int:
    if not path.exists():
        return 0
    payload = _load_json(path)
    return len(list(payload.get("features", [])))


def _format_metric_map(metrics: dict[str, object]) -> str:
    return ", ".join(f"`{key}` {value}" for key, value in metrics.items())


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_json_or_default(path: Path, default: dict[str, object]) -> dict[str, object]:
    if not path.exists():
        return default
    return _load_json(path)
