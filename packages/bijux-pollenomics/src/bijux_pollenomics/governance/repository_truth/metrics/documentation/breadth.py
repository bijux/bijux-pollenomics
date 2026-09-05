"""Current handbook breadth expectations for repository truth."""

from __future__ import annotations

__all__: list[str] = []


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
