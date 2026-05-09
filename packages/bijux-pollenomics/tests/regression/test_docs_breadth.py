from __future__ import annotations

from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[4]


class DocsBreadthRegressionTests(unittest.TestCase):
    def test_runtime_handbook_restores_runtime_breadth_pages(self) -> None:
        runtime_index = (
            REPO_ROOT / "docs" / "01-bijux-pollenomics" / "index.md"
        ).read_text(encoding="utf-8")

        for path in (
            "docs/01-bijux-pollenomics/architecture/runtime-system-model.md",
            "docs/01-bijux-pollenomics/foundation/runtime-scope-and-ownership.md",
            "docs/01-bijux-pollenomics/interfaces/entrypoints-and-examples.md",
            "docs/01-bijux-pollenomics/operations/common-workflows.md",
            "docs/01-bijux-pollenomics/operations/operational-boundaries.md",
            "docs/01-bijux-pollenomics/quality/runtime-invariants-and-limits.md",
        ):
            self.assertTrue((REPO_ROOT / path).is_file(), path)

        self.assertIn("Breadth Restored", runtime_index)
        self.assertIn("interfaces/entrypoints-and-examples/", runtime_index)
        self.assertIn("operations/common-workflows/", runtime_index)
        self.assertIn("quality/change-validation.md", runtime_index)

    def test_data_handbook_keeps_cross_domain_system_coverage(self) -> None:
        data_index = (
            REPO_ROOT / "docs" / "02-bijux-pollenomics-data" / "index.md"
        ).read_text(encoding="utf-8")
        overview_index = (
            REPO_ROOT
            / "docs"
            / "02-bijux-pollenomics-data"
            / "overview"
            / "index.md"
        ).read_text(encoding="utf-8")

        for path in (
            "docs/02-bijux-pollenomics-data/overview/provenance-and-publication-linkage.md",
            "docs/02-bijux-pollenomics-data/overview/source-selection-and-refresh.md",
            "docs/02-bijux-pollenomics-data/overview/coverage-and-naming.md",
            "docs/02-bijux-pollenomics-data/sources/landclim.md",
            "docs/02-bijux-pollenomics-data/sources/neotoma.md",
            "docs/02-bijux-pollenomics-data/sources/sead.md",
            "docs/02-bijux-pollenomics-data/sources/raa.md",
            "docs/02-bijux-pollenomics-data/sources/boundaries.md",
            "docs/02-bijux-pollenomics-data/sources/aadr.md",
        ):
            self.assertTrue((REPO_ROOT / path).is_file(), path)

        self.assertIn("Restored System Coverage", data_index)
        self.assertIn("overview/provenance-and-publication-linkage/", data_index)
        self.assertIn("overview/source-selection-and-refresh/", data_index)
        self.assertIn("overview/coverage-and-naming/", data_index)
        self.assertIn("Restored Foundation Topics", overview_index)

    def test_maintainer_handbook_restores_repository_health_breadth(self) -> None:
        maintain_index = (
            REPO_ROOT / "docs" / "03-bijux-pollenomics-maintain" / "index.md"
        ).read_text(encoding="utf-8")

        for path in (
            "docs/03-bijux-pollenomics-maintain/bijux-pollenomics-dev/repository-governance.md",
            "docs/03-bijux-pollenomics-maintain/gh-workflows/verification-and-release.md",
            "docs/03-bijux-pollenomics-maintain/makes/make-system-contracts.md",
        ):
            self.assertTrue((REPO_ROOT / path).is_file(), path)

        self.assertIn("repository-governance overview", maintain_index)
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
            ("maintenance/index.md", "Maintainer Truth Packets"),
            ("report_surface_registry.md", "Report surface registry"),
            (
                "report_narrative_quality_review.md",
                "Report narrative quality review",
            ),
        ):
            path = report_root / name
            self.assertTrue(path.is_file(), name)
            self.assertIn(heading, path.read_text(encoding="utf-8"))
