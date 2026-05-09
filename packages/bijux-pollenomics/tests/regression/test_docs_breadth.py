from __future__ import annotations

from pathlib import Path
import unittest

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]

pytestmark = pytest.mark.generated_artifacts


class DocsBreadthRegressionTests(unittest.TestCase):
    def test_docs_home_routes_readers_before_repo_details(self) -> None:
        docs_index = (REPO_ROOT / "docs" / "index.md").read_text(encoding="utf-8")
        internal_index = (REPO_ROOT / "docs" / "internal" / "index.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("public evidence surfaces about Nordic pollenomics", docs_index)
        self.assertIn("Open the product guide", docs_index)
        self.assertIn("Open the report portal", docs_index)
        self.assertNotIn("Open the public guide", docs_index)
        self.assertIn("for maintainers", internal_index)
        self.assertIn("Open the maintainer handbook", internal_index)

    def test_runtime_handbook_keeps_reader_routes_to_breadth_pages(self) -> None:
        runtime_index = (
            REPO_ROOT / "docs" / "public" / "pollenomics" / "index.md"
        ).read_text(encoding="utf-8")

        for path in (
            "docs/public/pollenomics/architecture/runtime-system-model.md",
            "docs/public/pollenomics/foundation/end-state-product-model.md",
            "docs/public/pollenomics/foundation/runtime-scope-and-ownership.md",
            "docs/public/pollenomics/interfaces/entrypoints-and-examples.md",
            "docs/public/pollenomics/operations/common-workflows.md",
            "docs/public/pollenomics/operations/operational-boundaries.md",
            "docs/public/pollenomics/quality/runtime-invariants-and-limits.md",
        ):
            self.assertTrue((REPO_ROOT / path).is_file(), path)

        self.assertIn("What You Can Learn Here", runtime_index)
        self.assertIn("Routes By Question", runtime_index)
        self.assertIn("[entrypoints and examples]", runtime_index)
        self.assertIn("[common workflows]", runtime_index)
        self.assertIn("[runtime invariants and limits]", runtime_index)

    def test_data_handbook_keeps_cross_domain_system_coverage(self) -> None:
        data_index = (
            REPO_ROOT / "docs" / "public" / "pollenomics-data" / "index.md"
        ).read_text(encoding="utf-8")
        overview_index = (
            REPO_ROOT / "docs" / "public" / "pollenomics-data" / "overview" / "index.md"
        ).read_text(encoding="utf-8")

        for path in (
            "docs/public/pollenomics-data/overview/provenance-and-publication-linkage.md",
            "docs/public/pollenomics-data/overview/source-selection-and-refresh.md",
            "docs/public/pollenomics-data/overview/coverage-and-naming.md",
            "docs/public/pollenomics-data/sources/landclim.md",
            "docs/public/pollenomics-data/sources/neotoma.md",
            "docs/public/pollenomics-data/sources/sead.md",
            "docs/public/pollenomics-data/sources/raa.md",
            "docs/public/pollenomics-data/sources/boundaries.md",
            "docs/public/pollenomics-data/sources/aadr.md",
        ):
            self.assertTrue((REPO_ROOT / path).is_file(), path)

        self.assertIn("Restored System Coverage", data_index)
        self.assertIn("overview/provenance-and-publication-linkage/", data_index)
        self.assertIn("overview/source-selection-and-refresh/", data_index)
        self.assertIn("overview/coverage-and-naming/", data_index)
        self.assertIn("Restored Foundation Topics", overview_index)

    def test_maintainer_handbook_restores_repository_health_breadth(self) -> None:
        maintain_index = (
            REPO_ROOT / "docs" / "internal" / "maintain" / "index.md"
        ).read_text(encoding="utf-8")

        for path in (
            "docs/internal/pollenomics-dev/future-country-onboarding-playbook.md",
            "docs/internal/pollenomics-dev/repository-governance.md",
            "docs/internal/maintain/gh-workflows/verification-and-release.md",
            "docs/internal/maintain/makes/make-system-contracts.md",
        ):
            self.assertTrue((REPO_ROOT / path).is_file(), path)

        self.assertIn("repository-governance overview", maintain_index)
        self.assertIn("country onboarding playbook", maintain_index)
        self.assertIn("command-routing boundary", maintain_index)
        self.assertIn("workflow verification and release map", maintain_index)

    def test_report_root_ships_docs_recovery_packets(self) -> None:
        report_root = REPO_ROOT / "docs" / "report"
        for name, heading in (
            (
                "repository_docs_restoration_ledger.md",
                "Repository docs restoration ledger",
            ),
            (
                "repository_docs_scope_validation.md",
                "Repository docs scope validation",
            ),
            (
                "repository_docs_recovery_review.md",
                "Repository docs recovery review",
            ),
            (
                "repository_product_model.md",
                "Repository product model",
            ),
            (
                "repository_credibility_dashboard.md",
                "Repository credibility dashboard",
            ),
            (
                "repository_generated_output_policy.md",
                "Repository generated output policy",
            ),
            (
                "repository_final_release_refusal.md",
                "Repository final release refusal",
            ),
        ):
            path = report_root / name
            self.assertTrue(path.is_file(), name)
            self.assertIn(heading, path.read_text(encoding="utf-8"))

    def test_report_root_ships_reader_portal_families(self) -> None:
        report_root = REPO_ROOT / "docs" / "report"
        for name, heading in (
            ("index.md", "Report Portal"),
            ("how-to-read.md", "How To Read Reports"),
            ("maps/index.md", "Map Surfaces"),
            ("scopes/index.md", "Scope-Filtered Outputs"),
            ("reviews/index.md", "Evidence Reviews"),
            ("caveats/index.md", "Scientific Caveats"),
            ("maintenance/index.md", "Maintainer Truth Surfaces"),
            ("report_surface_registry.md", "Report surface registry"),
            (
                "report_narrative_quality_review.md",
                "Report narrative quality review",
            ),
        ):
            path = report_root / name
            self.assertTrue(path.is_file(), name)
            self.assertIn(heading, path.read_text(encoding="utf-8"))
