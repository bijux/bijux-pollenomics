"""Legacy-document disposition expectations for repository truth."""

from __future__ import annotations


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
