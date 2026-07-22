from __future__ import annotations

from pathlib import Path
import unittest

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]

pytestmark = pytest.mark.generated_artifacts


class DocsBreadthRegressionTests(unittest.TestCase):
    def test_docs_home_leads_with_public_evidence_routes(self) -> None:
        docs_index = (REPO_ROOT / "docs" / "index.md").read_text(encoding="utf-8")
        internal_index = (REPO_ROOT / "docs" / "internal" / "index.md").read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "connects curated evidence to public maps and reports", docs_index
        )
        self.assertIn("From Source To Public Claim", docs_index)
        self.assertIn("Evidence Surfaces", docs_index)
        self.assertIn("Open the product guide", docs_index)
        self.assertIn("Open the report portal", docs_index)
        self.assertNotIn("Open the public guide", docs_index)
        self.assertIn("This handbook is for people changing the repository", internal_index)
        self.assertIn("Reader And Maintainer Surfaces", internal_index)
        self.assertIn("unlisted repository handbook", internal_index)
        self.assertIn("Open the maintainer handbook", internal_index)

    def test_data_handbook_covers_cross_domain_system(self) -> None:
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
            "docs/public/pollenomics-data/database/querying-evidence.md",
            "docs/public/pollenomics-data/curation/decision-records.md",
            "docs/public/pollenomics-data/sources/landclim.md",
            "docs/public/pollenomics-data/sources/neotoma.md",
            "docs/public/pollenomics-data/sources/sead.md",
            "docs/public/pollenomics-data/sources/raa.md",
            "docs/public/pollenomics-data/sources/boundaries.md",
            "docs/public/pollenomics-data/sources/aadr.md",
        ):
            self.assertTrue((REPO_ROOT / path).is_file(), path)

        self.assertIn("Database Architecture", data_index)
        self.assertIn("Curation Is Evidence Work", data_index)
        self.assertIn("database/querying-evidence.md", data_index)
        self.assertIn("overview/provenance-and-publication-linkage.md", data_index)
        self.assertIn("overview/source-selection-and-refresh.md", data_index)
        self.assertIn("overview/coverage-and-naming.md", data_index)
        self.assertIn("Evidence Lifecycle", overview_index)
        self.assertIn("Authority Boundaries", overview_index)

    def test_species_evidence_views_preserve_projection_boundaries(self) -> None:
        species_views = (
            REPO_ROOT
            / "docs"
            / "public"
            / "pollenomics-data"
            / "evidence"
            / "species-evidence-views.md"
        ).read_text(encoding="utf-8")
        evidence_index = (
            REPO_ROOT / "docs" / "public" / "pollenomics-data" / "evidence" / "index.md"
        ).read_text(encoding="utf-8")

        self.assertIn("# Species Evidence Views", species_views)
        self.assertIn("## Two Lifecycle Models", species_views)
        self.assertIn("## Cross-Species Comparison Contract", species_views)
        self.assertIn("## Reuse Packet", species_views)
        self.assertIn("```mermaid", species_views)
        self.assertIn("species-evidence-views.md", evidence_index)

    def test_decision_records_preserve_scoped_outcomes(self) -> None:
        decision_records = (
            REPO_ROOT
            / "docs"
            / "public"
            / "pollenomics-data"
            / "curation"
            / "decision-records.md"
        ).read_text(encoding="utf-8")
        curation_index = (
            REPO_ROOT / "docs" / "public" / "pollenomics-data" / "curation" / "index.md"
        ).read_text(encoding="utf-8")

        self.assertIn("# Evidence Decision Records", decision_records)
        self.assertIn("## Evidence, Product, And Release Decisions Differ", decision_records)
        self.assertIn("## Audit A Decision", decision_records)
        self.assertIn("```mermaid", decision_records)
        self.assertIn("decision-records.md", curation_index)

    def test_geographic_lineage_preserves_parent_meaning(self) -> None:
        lineage = (
            REPO_ROOT
            / "docs"
            / "public"
            / "pollenomics-data"
            / "publications"
            / "geographic-lineage.md"
        ).read_text(encoding="utf-8")
        publication_index = (
            REPO_ROOT
            / "docs"
            / "public"
            / "pollenomics-data"
            / "publications"
            / "index.md"
        ).read_text(encoding="utf-8")

        self.assertIn("# Geographic Publication Lineage", lineage)
        self.assertIn("## Subset Validation", lineage)
        self.assertIn("## Explain Absence From A Child Scope", lineage)
        self.assertIn("```mermaid", lineage)
        self.assertIn("geographic-lineage.md", publication_index)

    def test_maintainer_handbook_covers_repository_health(self) -> None:
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

        self.assertIn("Classify The Change", maintain_index)
        self.assertIn("Governed State And Build State", maintain_index)
        self.assertIn("makes/make-system-contracts.md", maintain_index)
        self.assertIn("gh-workflows/verification-and-release.md", maintain_index)

    def test_report_root_preserves_documentation_accountability(self) -> None:
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

    def test_nordic_atlas_documents_sweden_lake_decision_support(self) -> None:
        atlas_index = (
            REPO_ROOT / "docs" / "public" / "nordic-atlas" / "index.md"
        ).read_text(encoding="utf-8")
        lake_page = (
            REPO_ROOT
            / "docs"
            / "public"
            / "nordic-atlas"
            / "sweden-lake-priorities"
            / "index.md"
        ).read_text(encoding="utf-8")

        atlas_text = " ".join(atlas_index.split())
        lake_text = " ".join(lake_page.split())

        self.assertIn("./sweden-lake-priorities/", atlas_index)
        self.assertIn("derived decision-support products", atlas_text)
        self.assertIn("disabled by default", lake_text)
        self.assertIn("ranks 6,763 SMHI SVAR registry lakes", lake_text)
        self.assertIn("fieldwork-preparation top 20", lake_text)
        self.assertIn("does not contain governed bathymetry", lake_text)
        self.assertIn("sweden_lake_evidence_richness_v66.md", lake_page)
