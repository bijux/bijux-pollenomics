"""Shared evidence counts and typed row construction for repository truth."""

from __future__ import annotations

import json
from pathlib import Path

from ...collection.sources.raa import assess_raa_density_authority

SCORE_MAX = 4

__all__ = []


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
        data_root
        / "adna"
        / "governance"
        / "source_library"
        / "reference_stash_reconciliation.json",
        {"rows": []},
    )
    reference_stash_doi_integrity = _load_json_or_default(
        data_root
        / "adna"
        / "governance"
        / "source_library"
        / "reference_stash_doi_integrity_audit.json",
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
    collection_summary = _load_json_or_default(
        data_root / "collection_summary.json", {}
    )
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
    raa_authority = assess_raa_density_authority(data_root)

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
            sample_database_review.get("counts", {}).get(
                "published_atlas_point_count", 0
            )
        ),
        "published_country_bundle_count": int(
            sample_database_review.get("counts", {}).get(
                "published_country_bundle_count", 0
            )
        ),
        "reference_stash_doi_count": int(
            reference_stash_doi_integrity.get("reference_stash_doi_count", 0)
        ),
        "tracked_aadr_release_file_count": _count_tree_files(
            data_root / "aadr" / "v66"
        ),
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
        "tracked_raa_published_site_count": (
            int(dict(raa_layer.get("counts", {})).get("all_published_sites", 0))
            if raa_authority.admitted
            else 0
        ),
        "tracked_raa_density_cell_count": (
            int(raa_layer.get("density_feature_count", 0))
            if raa_authority.admitted
            else 0
        ),
        "raa_density_admitted": raa_authority.admitted,
        "raa_density_reason_codes": list(raa_authority.reason_codes),
        "tracked_boundary_feature_count": _count_geojson_features(
            data_root
            / "boundaries"
            / "normalized"
            / "nordic_country_boundaries.geojson"
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
            1 for _ in (docs_root / "public" / "fieldwork").rglob("index.md")
        ),
        "source_explainer_count": sum(
            1
            for path in (docs_root / "public" / "pollenomics-data" / "sources").glob(
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
                docs_root / "public" / "index.md",
                docs_root / "public" / "pollenomics" / "index.md",
                docs_root / "public" / "pollenomics-data" / "index.md",
                docs_root / "internal" / "index.md",
                docs_root / "public" / "fieldwork" / "index.md",
                docs_root / "public" / "nordic-atlas" / "index.md",
            )
        ),
        "zero_collection_summary_surfaces": zero_collection_surfaces,
    }


def _build_claim_freeze_reasons(counts: dict[str, object]) -> list[str]:
    reasons = []
    if int(counts["papers_with_archived_supplements"]) < int(
        counts["tracked_paper_count"]
    ):
        reasons.append("supplement recovery is still far below paper coverage")
    if int(counts["published_atlas_point_count"]) <= 2:
        reasons.append(
            "the shipped animal atlas point surface is still effectively empty"
        )
    if int(counts["animal_map_unresolved_rows"]) > int(
        counts["animal_map_supported_rows"]
    ):
        reasons.append("unresolved animal geography still overwhelms mapped support")
    if (
        int(counts["animal_map_unresolved_rows"]) > 0
        or int(counts["animal_map_refused_rows"]) > 0
    ):
        reasons.append(
            "tracked animal geography still leaves unresolved or refused rows outside the published surface"
        )
    if counts["zero_collection_summary_surfaces"]:
        reasons.append(
            "collection summary still under-reports several non-aDNA source counts"
        )
    if not counts["raa_density_admitted"]:
        reasons.append(
            "RAÄ density remains refused until source inventory and qualified review reconcile"
        )
    return reasons


def _recovery_review_row(
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
    metrics: dict[str, object],
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
    tracked_metrics: dict[str, object],
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


def _docs_restoration_expectations() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    rows.extend(
        _docs_restoration_group(
            [
                "docs/01-bijux-pollenomics/architecture/architecture-risks.md",
                "docs/01-bijux-pollenomics/architecture/code-navigation.md",
                "docs/01-bijux-pollenomics/architecture/dependency-direction.md",
                "docs/01-bijux-pollenomics/architecture/error-model.md",
                "docs/01-bijux-pollenomics/architecture/execution-model.md",
                "docs/01-bijux-pollenomics/architecture/extensibility-model.md",
                "docs/01-bijux-pollenomics/architecture/integration-seams.md",
                "docs/01-bijux-pollenomics/architecture/state-and-persistence.md",
            ],
            decision="merged",
            current_path="docs/public/pollenomics/architecture/runtime-system-model.md",
            required_snippets=[
                "Execution Path",
                "Dependency Direction",
                "State And Persistence",
                "Integration Seams",
                "Error Model",
                "Extensibility Posture",
                "Code Navigation",
            ],
            rationale="architecture coverage is now consolidated into one runtime system model page instead of several thin fragments",
        )
    )
    rows.extend(
        _docs_restoration_group(
            [
                "docs/01-bijux-pollenomics/foundation/capability-map.md",
                "docs/01-bijux-pollenomics/foundation/change-principles.md",
                "docs/01-bijux-pollenomics/foundation/dependencies-and-adjacencies.md",
                "docs/01-bijux-pollenomics/foundation/domain-language.md",
                "docs/01-bijux-pollenomics/foundation/lifecycle-overview.md",
                "docs/01-bijux-pollenomics/foundation/ownership-boundary.md",
                "docs/01-bijux-pollenomics/foundation/ownership-map.md",
                "docs/01-bijux-pollenomics/foundation/package-overview.md",
                "docs/01-bijux-pollenomics/foundation/scope-and-non-goals.md",
                "docs/01-bijux-pollenomics/foundation/surface-map.md",
            ],
            decision="merged",
            current_path="docs/public/pollenomics/foundation/runtime-scope-and-ownership.md",
            required_snippets=[
                "Capability Map",
                "Surface Map",
                "Ownership Boundary",
                "Domain Language",
                "Lifecycle",
                "Change Principles",
                "Dependencies And Adjacencies",
            ],
            rationale="foundation topics now live in one ownership-and-scope page that keeps package purpose, language, and boundaries together",
        )
    )
    rows.extend(
        _docs_restoration_group(
            ["docs/01-bijux-pollenomics/interfaces/api-surface.md"],
            decision="restored",
            current_path="docs/public/pollenomics/interfaces/api-surface.md",
            required_snippets=["Python Surface", "Compatibility Posture"],
            rationale="the API boundary page is restored directly because it remains a durable contract surface",
        )
    )
    rows.extend(
        _docs_restoration_group(
            [
                "docs/01-bijux-pollenomics/interfaces/compatibility-commitments.md",
                "docs/01-bijux-pollenomics/interfaces/public-imports.md",
            ],
            decision="merged",
            current_path="docs/public/pollenomics/interfaces/api-surface.md",
            required_snippets=["Python Surface", "Compatibility Posture"],
            rationale="compatibility and public-import expectations are merged into the restored API surface page",
        )
    )
    rows.extend(
        _docs_restoration_group(
            ["docs/01-bijux-pollenomics/interfaces/configuration-surface.md"],
            decision="merged",
            current_path="docs/public/pollenomics/interfaces/cli-surface.md",
            required_snippets=[
                "`--output-root` defaults to `data` for collection",
                "for collection or `docs/report` for",
            ],
            rationale="configuration defaults remain part of the CLI contract page because operators encounter them through command usage",
        )
    )
    rows.extend(
        _docs_restoration_group(
            ["docs/01-bijux-pollenomics/interfaces/data-contracts.md"],
            decision="restored",
            current_path="docs/public/pollenomics/interfaces/data-contracts.md",
            required_snippets=["Governing Roots", "Contract Rules"],
            rationale="data contracts are restored directly because they remain a durable reader-facing contract surface",
        )
    )
    rows.extend(
        _docs_restoration_group(
            ["docs/01-bijux-pollenomics/interfaces/entrypoints-and-examples.md"],
            decision="restored",
            current_path="docs/public/pollenomics/interfaces/entrypoints-and-examples.md",
            required_snippets=[
                "Verification Entry Points",
                "Collection And Publication Examples",
            ],
            rationale="entrypoint examples are restored directly because the repository root already promises them",
        )
    )
    rows.extend(
        _docs_restoration_group(
            ["docs/01-bijux-pollenomics/interfaces/operator-workflows.md"],
            decision="restored",
            current_path="docs/public/pollenomics/interfaces/operator-workflows.md",
            required_snippets=["Verify Only", "Refresh Data", "Publish Outputs"],
            rationale="operator workflows are restored directly because they remain a durable distinction between verify, refresh, and publish",
        )
    )
    rows.extend(
        _docs_restoration_group(
            ["docs/01-bijux-pollenomics/operations/common-workflows.md"],
            decision="restored",
            current_path="docs/public/pollenomics/operations/common-workflows.md",
            required_snippets=[
                "Fresh Checkout",
                "Data Refresh Review",
                "Publication Review",
            ],
            rationale="common workflows are restored directly because the repository needs a concrete rebuild sequence page",
        )
    )
    rows.extend(
        _docs_restoration_group(
            [
                "docs/01-bijux-pollenomics/operations/deployment-boundaries.md",
                "docs/01-bijux-pollenomics/operations/local-development.md",
                "docs/01-bijux-pollenomics/operations/observability-and-diagnostics.md",
                "docs/01-bijux-pollenomics/operations/performance-and-scaling.md",
                "docs/01-bijux-pollenomics/operations/release-and-versioning.md",
                "docs/01-bijux-pollenomics/operations/security-and-safety.md",
            ],
            decision="merged",
            current_path="docs/public/pollenomics/operations/operational-boundaries.md",
            required_snippets=[
                "Local Development",
                "Observability And Diagnostics",
                "Release And Versioning",
                "Security And Safety",
                "Performance Posture",
            ],
            rationale="operational edge cases are merged into one page so local development, release, safety, and diagnostics stay readable together",
        )
    )
    rows.extend(
        _docs_restoration_group(
            ["docs/01-bijux-pollenomics/operations/failure-recovery.md"],
            decision="restored",
            current_path="docs/public/pollenomics/operations/failure-recovery.md",
            required_snippets=["Failure Questions", "Recovery Route"],
            rationale="failure recovery is restored directly because it remains a distinct operational task",
        )
    )
    rows.extend(
        _docs_restoration_group(
            ["docs/01-bijux-pollenomics/quality/change-validation.md"],
            decision="restored",
            current_path="docs/public/pollenomics/quality/change-validation.md",
            required_snippets=["Validation Layers", "Breadth Rule"],
            rationale="change validation is restored directly because it is the clearest location for the docs breadth rule",
        )
    )
    rows.extend(
        _docs_restoration_group(
            [
                "docs/01-bijux-pollenomics/quality/definition-of-done.md",
                "docs/01-bijux-pollenomics/quality/dependency-governance.md",
                "docs/01-bijux-pollenomics/quality/invariants.md",
                "docs/01-bijux-pollenomics/quality/known-limitations.md",
                "docs/01-bijux-pollenomics/quality/risk-register.md",
            ],
            decision="merged",
            current_path="docs/public/pollenomics/quality/runtime-invariants-and-limits.md",
            required_snippets=[
                "Invariants",
                "Definition Of Done",
                "Dependency Governance",
                "Known Limits",
                "Risk Posture",
            ],
            rationale="definition, invariant, limitation, and risk material now lives in one durable runtime limits page",
        )
    )
    rows.extend(
        _docs_restoration_group(
            ["docs/01-bijux-pollenomics/quality/documentation-standards.md"],
            decision="merged",
            current_path="docs/public/pollenomics/quality/change-validation.md",
            required_snippets=["Breadth Rule"],
            rationale="documentation standards now live with validation because breadth loss is enforced as a quality rule",
        )
    )
    rows.extend(
        _docs_restoration_group(
            ["docs/01-bijux-pollenomics/quality/review-checklist.md"],
            decision="restored",
            current_path="docs/public/pollenomics/quality/review-checklist.md",
            required_snippets=["Review Checklist"],
            rationale="review checklist is restored directly because it remains a useful maintainer-facing stop list",
        )
    )
    rows.extend(
        _docs_restoration_group(
            [
                "docs/02-bijux-pollenomics-data/foundation/coordinate-policy.md",
                "docs/02-bijux-pollenomics-data/foundation/provenance-model.md",
                "docs/02-bijux-pollenomics-data/foundation/publication-linkage.md",
            ],
            decision="merged",
            current_path="docs/public/pollenomics-data/overview/provenance-and-publication-linkage.md",
            required_snippets=[
                "Provenance Model",
                "Publication Linkage",
                "Coordinate Policy",
            ],
            rationale="provenance, coordinate, and publication linkage topics now live under the current overview model",
        )
    )
    rows.extend(
        _docs_restoration_group(
            ["docs/02-bijux-pollenomics-data/foundation/data-system-overview.md"],
            decision="merged",
            current_path="docs/public/pollenomics-data/overview/data-system-overview.md",
            required_snippets=[
                "docs/report/",
                "Pollen Evidence Leads The Scientific Model",
            ],
            rationale="the old foundation overview is replaced by the current data-system overview page",
        )
    )
    rows.extend(
        _docs_restoration_group(
            ["docs/02-bijux-pollenomics-data/foundation/directory-layout.md"],
            decision="merged",
            current_path="docs/public/pollenomics-data/overview/data-directory-layout.md",
            required_snippets=["docs/report/", "data/"],
            rationale="the old directory layout page now lives under the current overview layout page",
        )
    )
    rows.extend(
        _docs_restoration_group(
            ["docs/02-bijux-pollenomics-data/foundation/index.md"],
            decision="retired_with_replacement",
            current_path="docs/public/pollenomics-data/overview/index.md",
            required_snippets=[
                "Evidence Foundation Topics",
                "Provenance and publication linkage",
            ],
            rationale="the old foundation subtree was retired in favor of the overview subtree, with explicit replacement links",
        )
    )
    rows.extend(
        _docs_restoration_group(
            [
                "docs/02-bijux-pollenomics-data/foundation/migration-issues.md",
                "docs/02-bijux-pollenomics-data/foundation/source-selection-rules.md",
                "docs/02-bijux-pollenomics-data/foundation/update-lifecycle.md",
            ],
            decision="merged",
            current_path="docs/public/pollenomics-data/overview/source-selection-and-refresh.md",
            required_snippets=[
                "Selection Rules",
                "Refresh Lifecycle",
                "Migration Pressure",
            ],
            rationale="selection rules, lifecycle, and migration pressure now live together in one current overview page",
        )
    )
    rows.extend(
        _docs_restoration_group(
            ["docs/02-bijux-pollenomics-data/foundation/naming-conventions.md"],
            decision="merged",
            current_path="docs/public/pollenomics-data/overview/coverage-and-naming.md",
            required_snippets=["Naming Rules", "Coverage Rule"],
            rationale="naming conventions are merged into the current coverage-and-naming page",
        )
    )
    rows.extend(
        _docs_restoration_group(
            [
                "docs/03-bijux-pollenomics-maintain/bijux-pollenomics-dev/module-map.md",
                "docs/03-bijux-pollenomics-maintain/bijux-pollenomics-dev/package-overview.md",
                "docs/03-bijux-pollenomics-maintain/bijux-pollenomics-dev/schema-governance.md",
                "docs/03-bijux-pollenomics-maintain/bijux-pollenomics-dev/scope-and-non-goals.md",
                "docs/03-bijux-pollenomics-maintain/bijux-pollenomics-dev/security-gates.md",
            ],
            decision="merged",
            current_path="docs/internal/pollenomics-dev/repository-governance.md",
            required_snippets=[
                "Package Boundary",
                "Module Map",
                "Schema And Scope Governance",
                "Security And Release Pressure",
            ],
            rationale="maintainer package governance topics now live in one repository-governance page",
        )
    )
    rows.extend(
        _docs_restoration_group(
            [
                "docs/03-bijux-pollenomics-maintain/gh-workflows/release-publication.md",
                "docs/03-bijux-pollenomics-maintain/gh-workflows/reusable-workflows.md",
                "docs/03-bijux-pollenomics-maintain/gh-workflows/verify.md",
            ],
            decision="merged",
            current_path="docs/internal/maintain/gh-workflows/verification-and-release.md",
            required_snippets=[
                "Verification Surface",
                "Release Surface",
                "Reusable Workflow Pressure",
            ],
            rationale="workflow verification, release, and reusable-automation guidance now lives in one page",
        )
    )
    rows.extend(
        _docs_restoration_group(
            [
                "docs/03-bijux-pollenomics-maintain/makes/authoring-rules.md",
                "docs/03-bijux-pollenomics-maintain/makes/ci-targets.md",
                "docs/03-bijux-pollenomics-maintain/makes/environment-model.md",
                "docs/03-bijux-pollenomics-maintain/makes/make-system-overview.md",
                "docs/03-bijux-pollenomics-maintain/makes/package-contracts.md",
                "docs/03-bijux-pollenomics-maintain/makes/package-dispatch.md",
                "docs/03-bijux-pollenomics-maintain/makes/release-surfaces.md",
                "docs/03-bijux-pollenomics-maintain/makes/repository-layout.md",
                "docs/03-bijux-pollenomics-maintain/makes/root-entrypoints.md",
            ],
            decision="merged",
            current_path="docs/internal/maintain/makes/make-system-contracts.md",
            required_snippets=[
                "Main Files",
                "Repository Layout And Entry Points",
                "Authoring And CI Pressure",
                "Contract Rule",
            ],
            rationale="Make authoring, dispatch, release, and root-entrypoint guidance now lives in one stable contracts page",
        )
    )
    return rows


def _docs_restoration_group(
    legacy_paths: list[str],
    *,
    decision: str,
    current_path: str,
    required_snippets: list[str],
    rationale: str,
) -> list[dict[str, object]]:
    return [
        {
            "legacy_path": legacy_path,
            "decision": decision,
            "current_path": current_path,
            "required_snippets": required_snippets,
            "rationale": rationale,
        }
        for legacy_path in legacy_paths
    ]


def _docs_breadth_expectations() -> list[dict[str, object]]:
    return [
        {
            "section_key": "runtime_handbook",
            "display_name": "Runtime handbook",
            "landing_path": "docs/public/pollenomics/index.md",
            "required_pages": [
                "docs/public/pollenomics/architecture/runtime-system-model.md",
                "docs/public/pollenomics/foundation/runtime-scope-and-ownership.md",
                "docs/public/pollenomics/interfaces/api-surface.md",
                "docs/public/pollenomics/interfaces/data-contracts.md",
                "docs/public/pollenomics/interfaces/entrypoints-and-examples.md",
                "docs/public/pollenomics/interfaces/operator-workflows.md",
                "docs/public/pollenomics/operations/common-workflows.md",
                "docs/public/pollenomics/operations/failure-recovery.md",
                "docs/public/pollenomics/operations/operational-boundaries.md",
                "docs/public/pollenomics/quality/change-validation.md",
                "docs/public/pollenomics/quality/runtime-invariants-and-limits.md",
                "docs/public/pollenomics/quality/review-checklist.md",
            ],
            "required_link_snippets": [
                "foundation/",
                "interfaces/",
                "quality/",
            ],
            "required_topic_snippets": [
                "Bijux Pollenomics Product Guide",
                "runtime system model",
                "repository scope and limits",
            ],
        },
        {
            "section_key": "data_handbook",
            "display_name": "Data handbook",
            "landing_path": "docs/public/pollenomics-data/index.md",
            "required_pages": [
                "docs/public/pollenomics-data/overview/provenance-and-publication-linkage.md",
                "docs/public/pollenomics-data/overview/source-selection-and-refresh.md",
                "docs/public/pollenomics-data/overview/coverage-and-naming.md",
                "docs/public/pollenomics-data/sources/landclim.md",
                "docs/public/pollenomics-data/sources/neotoma.md",
                "docs/public/pollenomics-data/sources/sead.md",
                "docs/public/pollenomics-data/sources/raa.md",
                "docs/public/pollenomics-data/sources/boundaries.md",
                "docs/public/pollenomics-data/sources/aadr.md",
                "docs/public/pollenomics-data/evidence/sample-records.md",
                "docs/public/pollenomics-data/evidence/localities.md",
                "docs/public/pollenomics-data/evidence/chronology.md",
                "docs/public/pollenomics-data/evidence/coordinates.md",
                "docs/public/pollenomics-data/publications/reports.md",
                "docs/public/pollenomics-data/publications/maps.md",
            ],
            "required_link_snippets": [
                "overview/provenance-and-publication-linkage.md",
                "overview/source-selection-and-refresh.md",
                "overview/coverage-and-naming.md",
            ],
            "required_topic_snippets": [
                "Evidence System Coverage",
                "pollen context",
                "boundary framing",
            ],
        },
        {
            "section_key": "maintainer_handbook",
            "display_name": "Maintainer handbook",
            "landing_path": "docs/internal/maintain/index.md",
            "required_pages": [
                "docs/internal/pollenomics-dev/repository-governance.md",
                "docs/internal/pollenomics-dev/documentation-integrity.md",
                "docs/internal/pollenomics-dev/release-support.md",
                "docs/internal/maintain/gh-workflows/verification-and-release.md",
                "docs/internal/maintain/makes/make-system-contracts.md",
            ],
            "required_link_snippets": [
                "../pollenomics-dev/repository-governance.md",
                "gh-workflows/verification-and-release.md",
                "makes/make-system-contracts.md",
            ],
            "required_topic_snippets": [
                "Repository Governance",
                "command-routing",
                "verification and release map",
            ],
        },
    ]


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


def _count_suffix_files(path: Path, suffix: str) -> int:
    if not path.exists():
        return 0
    return sum(1 for file_path in path.rglob(f"*{suffix}") if file_path.is_file())


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
