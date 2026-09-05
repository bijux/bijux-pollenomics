from __future__ import annotations

import unittest

import pytest
import re

from .repository_paths import (
    MERMAID_RESERVED_IDS,
    REPO_ROOT,
)

pytestmark = pytest.mark.generated_artifacts


class DocumentationContentTests(unittest.TestCase):
    @staticmethod
    def _declared_mermaid_node_ids(block: str) -> set[str]:
        ids: set[str] = set()
        for line in block.splitlines():
            match = re.match(r"\s*([A-Za-z_][A-Za-z0-9_-]*)\s*\[", line)
            if match:
                ids.add(match.group(1).lower())
        return ids


    def test_docs_mermaid_diagrams_avoid_reserved_node_ids(self) -> None:
        failures: list[str] = []

        for path in (REPO_ROOT / "docs").rglob("*.md"):
            text = path.read_text(encoding="utf-8")
            for match in re.finditer(r"```mermaid\n([\s\S]*?)\n```", text):
                reserved_ids = sorted(
                    MERMAID_RESERVED_IDS.intersection(
                        self._declared_mermaid_node_ids(match.group(1))
                    )
                )
                if reserved_ids:
                    failures.append(
                        f"{path.relative_to(REPO_ROOT)}: reserved Mermaid ids "
                        + ", ".join(reserved_ids)
                    )

        self.assertFalse(
            failures,
            "Mermaid diagrams use reserved node ids:\n" + "\n".join(failures),
        )


    def test_readme_and_docs_separate_reader_proof_from_test_selection(self) -> None:
        readme_text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        public_quality_text = (
            REPO_ROOT
            / "docs"
            / "public"
            / "pollenomics"
            / "quality"
            / "test-strategy.md"
        ).read_text(encoding="utf-8")
        maintainer_quality_text = (
            REPO_ROOT / "docs" / "internal" / "pollenomics-dev" / "quality-gates.md"
        ).read_text(encoding="utf-8")

        self.assertIn("Apache License 2.0", readme_text)
        self.assertIn("make lock-check", readme_text)
        self.assertIn("make package-check", readme_text)
        self.assertIn("make package-source-smoke", readme_text)
        self.assertIn("make test-unit", readme_text)
        self.assertIn("make test-regression", readme_text)
        self.assertIn("make test-e2e", readme_text)
        self.assertIn("# Verification Evidence", public_quality_text)
        self.assertIn("## Proof Layers", public_quality_text)
        self.assertNotIn("`tests/unit/`", public_quality_text)
        self.assertNotIn("`tests/regression/`", public_quality_text)
        self.assertNotIn("`tests/e2e/`", public_quality_text)
        self.assertIn("`tests/unit/`", maintainer_quality_text)
        self.assertIn("`tests/regression/`", maintainer_quality_text)
        self.assertIn("`tests/e2e/`", maintainer_quality_text)


    def test_docs_home_page_uses_repository_name_for_title_and_h1(self) -> None:
        docs_index = (REPO_ROOT / "docs" / "index.md").read_text(encoding="utf-8")

        self.assertIn("title: Bijux Pollenomics", docs_index)
        self.assertIn("# Bijux Pollenomics", docs_index)
        self.assertNotIn("# Docs Index", docs_index)
        self.assertIn(
            "connects curated evidence to public maps and reports", docs_index
        )
        self.assertIn(
            "the repository is already the full cross-evidence pollenomics engine",
            docs_index,
        )


    def test_public_docs_do_not_ship_reference_grade_phrase(self) -> None:
        failures: list[str] = []

        for path in (REPO_ROOT / "docs").rglob("*.md"):
            text = path.read_text(encoding="utf-8").lower()
            if "reference-grade" in text:
                failures.append(str(path.relative_to(REPO_ROOT)))

        self.assertFalse(
            failures,
            "Public docs still ship the forbidden reference-grade phrase:\n"
            + "\n".join(failures),
        )


    def test_top_level_product_descriptions_stay_pollenomics_first(self) -> None:
        root_readme = " ".join(
            (REPO_ROOT / "README.md").read_text(encoding="utf-8").split()
        )
        runtime_readme = " ".join(
            (REPO_ROOT / "packages" / "bijux-pollenomics" / "README.md")
            .read_text(encoding="utf-8")
            .split()
        )
        alias_readme = (REPO_ROOT / "packages" / "pollenomics" / "README.md").read_text(
            encoding="utf-8"
        )
        runtime_index = (
            REPO_ROOT / "docs" / "public" / "pollenomics" / "index.md"
        ).read_text(encoding="utf-8")
        data_index = (
            REPO_ROOT / "docs" / "public" / "pollenomics-data" / "index.md"
        ).read_text(encoding="utf-8")
        atlas_index = (
            REPO_ROOT / "docs" / "public" / "nordic-atlas" / "index.md"
        ).read_text(encoding="utf-8")
        atlas_files = sorted(
            path.name
            for path in (REPO_ROOT / "docs" / "public" / "nordic-atlas").glob("*.md")
        )

        self.assertIn("curated evidence and publication system", root_readme)
        self.assertIn(
            "records without adequate sample, locality, chronology, or coordinate support stay qualified or excluded",
            root_readme,
        )
        self.assertIn(
            "keeps pollen, environmental archaeology, boundaries, lake registries, human ancient DNA",
            runtime_readme,
        )
        self.assertIn("short-name distribution", alias_readme)
        self.assertIn(
            "turns heterogeneous scientific and spatial sources", runtime_index
        )
        self.assertIn("The system keeps unlike evidence unlike", runtime_index)
        self.assertIn("preserves the chain between an upstream source", data_index)
        self.assertIn("comparison surface", atlas_index)
        self.assertEqual(atlas_files, ["index.md"])
        self.assertIn("Point publication rules", atlas_index)
        self.assertIn("Filters and popups", atlas_index)
        self.assertIn("Current limits", atlas_index)


    def test_top_level_landings_keep_pollenomics_scope_and_source_breadth(self) -> None:
        readme_text = (REPO_ROOT / "README.md").read_text(encoding="utf-8").lower()
        docs_index = (REPO_ROOT / "docs" / "index.md").read_text(encoding="utf-8")
        data_index = (
            REPO_ROOT / "docs" / "public" / "pollenomics-data" / "index.md"
        ).read_text(encoding="utf-8")
        source_index = (
            (
                REPO_ROOT
                / "docs"
                / "public"
                / "pollenomics-data"
                / "sources"
                / "index.md"
            )
            .read_text(encoding="utf-8")
            .lower()
        )

        for expected in (
            "landclim",
            "neotoma",
            "sead",
            "raä",
            "boundaries",
            "aadr",
        ):
            self.assertIn(expected, readme_text)
            self.assertIn(expected, source_index)
        self.assertIn("Open the product guide", docs_index)
        self.assertIn("Open the report portal", docs_index)
        self.assertIn("How to read the report tree", docs_index)
        self.assertIn("How A Claim Earns Trust", docs_index)
        self.assertIn("No single map popup answers all five questions", docs_index)
        self.assertNotIn("Open the internal guide", docs_index)
        self.assertIn("preserves the chain between an upstream source", data_index)
        self.assertIn(
            "[report portal](../../../report/index.md)",
            (
                REPO_ROOT
                / "docs"
                / "public"
                / "pollenomics-data"
                / "publications"
                / "reports.md"
            ).read_text(encoding="utf-8"),
        )
        self.assertIn(
            'href="../../report/">Open the report portal</a>',
            (REPO_ROOT / "docs" / "public" / "nordic-atlas" / "index.md").read_text(
                encoding="utf-8"
            ),
        )
        self.assertFalse((REPO_ROOT / "docs" / "public" / "index.md").exists())
        self.assertTrue((REPO_ROOT / "docs" / "internal" / "index.md").is_file())


    def test_package_readmes_keep_sharp_audiences(self) -> None:
        runtime_readme = (
            REPO_ROOT / "packages" / "bijux-pollenomics" / "README.md"
        ).read_text(encoding="utf-8")
        alias_readme = (REPO_ROOT / "packages" / "pollenomics" / "README.md").read_text(
            encoding="utf-8"
        )
        maintainer_readme = (
            REPO_ROOT / "packages" / "bijux-pollenomics-dev" / "README.md"
        ).read_text(encoding="utf-8")

        self.assertIn("is the canonical runtime", runtime_readme)
        self.assertIn("## Evidence guarantees", runtime_readme)
        self.assertIn("is the short-name distribution", alias_readme)
        self.assertIn("## Compatibility contract", alias_readme)
        self.assertIn("Maintainer-only package", maintainer_readme)
        self.assertIn("It is not the owner of runtime commands", maintainer_readme)


    def test_runtime_package_boundary_doc_names_durable_scientific_ownership(
        self,
    ) -> None:
        boundary_doc = (
            REPO_ROOT / "packages" / "bijux-pollenomics" / "docs" / "boundaries.md"
        ).read_text(encoding="utf-8")

        self.assertIn("# Runtime Package Boundaries", boundary_doc)
        self.assertIn("## Runtime Command Surface", boundary_doc)
        self.assertIn("## Source Collection And Intake", boundary_doc)
        self.assertIn("## Evidence Normalization", boundary_doc)
        self.assertIn("## Evidence Review", boundary_doc)
        self.assertIn("## Publication Assembly", boundary_doc)
        self.assertIn("## Public Artifact Writing", boundary_doc)
        self.assertIn("## Package Split", boundary_doc)
        self.assertIn("bijux_pollenomics.adna.projects.registry.sites", boundary_doc)
        self.assertIn("bijux_pollenomics.reporting.review", boundary_doc)


    def test_module_map_mentions_adna_runtime_boundary(self) -> None:
        module_map = (
            REPO_ROOT
            / "docs"
            / "public"
            / "pollenomics"
            / "architecture"
            / "module-map.md"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "`command_line/` owns parsing, dispatch, and the durable command registry",
            module_map,
        )
        self.assertIn(
            "`collection/workflow/planning/` and `collection/workflow/materialization/`",
            module_map,
        )
        self.assertIn("`collection/sources/`", module_map)
        self.assertIn("`collection/sources/sead/catalog/site_inventory/`", module_map)
        self.assertIn(
            "`analysis/review/fieldwork/` owns candidate-site review",
            module_map,
        )
        self.assertIn("`reporting/presentation/`", module_map)
        self.assertIn("`reporting/review/`", module_map)
        self.assertIn("compatibility shims", module_map)
        self.assertIn("alias distribution", module_map)
        self.assertIn("`src/bijux_pollenomics/adna/`", module_map)


    def test_directory_layout_docs_mentions_curated_species_roots(self) -> None:
        directory_layout = (
            REPO_ROOT
            / "docs"
            / "public"
            / "pollenomics-data"
            / "overview"
            / "data-directory-layout.md"
        ).read_text(encoding="utf-8")

        self.assertIn("species-centered animal ancient DNA recovery", directory_layout)
        self.assertIn("data/adna/final/", directory_layout)
        self.assertIn("`data/adna/species/equus_caballus/`", directory_layout)
        self.assertIn("`data/adna/species/bos_taurus/`", directory_layout)
        self.assertIn("`data/adna/species/canis_lupus_familiaris/`", directory_layout)
        self.assertIn("`data/adna/species/camelus_dromedarius/`", directory_layout)
        self.assertIn("`data/adna/species/rangifer_tarandus/`", directory_layout)
        self.assertIn("`data/adna/species/equus_asinus/`", directory_layout)
        self.assertIn("`data/adna/species/felis_catus/`", directory_layout)


    def test_fieldwork_page_embeds_video_from_site_root_gallery(self) -> None:
        fieldwork_text = (
            REPO_ROOT
            / "docs"
            / "public"
            / "fieldwork"
            / "lyngsjon-lake-fieldwork"
            / "index.md"
        ).read_text(encoding="utf-8")

        self.assertIn(
            '<source src="../../../gallery/2026-02-26-data-collection.mp4"',
            fieldwork_text,
        )
        self.assertIn(
            '<a href="../../../gallery/2026-02-26-data-collection.mp4">',
            fieldwork_text,
        )


    def test_public_atlas_and_fieldwork_pages_use_local_site_paths(self) -> None:
        atlas_text = (
            REPO_ROOT / "docs" / "public" / "nordic-atlas" / "index.md"
        ).read_text(encoding="utf-8")
        fieldwork_index_text = (
            REPO_ROOT / "docs" / "public" / "fieldwork" / "index.md"
        ).read_text(encoding="utf-8")
        fieldwork_detail_text = (
            REPO_ROOT
            / "docs"
            / "public"
            / "fieldwork"
            / "lyngsjon-lake-fieldwork"
            / "index.md"
        ).read_text(encoding="utf-8")

        self.assertIn('href="../../report/"', atlas_text)
        self.assertIn(
            'href="../../report/regions/nordic/nordic_map.html"',
            atlas_text,
        )
        self.assertIn(
            'src="../../report/regions/nordic/nordic_map.html"',
            atlas_text,
        )
        self.assertNotIn("https://bijux.io/bijux-pollenomics/report/", atlas_text)

        self.assertIn(
            'href="../../report/regions/nordic/nordic_map.html"',
            fieldwork_index_text,
        )
        self.assertIn('href="../pollenomics-data/"', fieldwork_index_text)
        self.assertNotIn(
            "https://bijux.io/bijux-pollenomics/public/", fieldwork_index_text
        )
        self.assertNotIn(
            "https://bijux.io/bijux-pollenomics/report/", fieldwork_index_text
        )

        self.assertIn(
            'href="../../../report/regions/nordic/nordic_map.html"',
            fieldwork_detail_text,
        )
        self.assertIn(
            'href="../../../gallery/2026-02-26-data-collection.mp4"',
            fieldwork_detail_text,
        )


    def test_engineering_docs_describe_clean_verification_and_docs_asset_checks(
        self,
    ) -> None:
        automation_workflows = (
            REPO_ROOT
            / "docs"
            / "internal"
            / "maintain"
            / "gh-workflows"
            / "deploy-docs.md"
        ).read_text(encoding="utf-8")
        testing_and_evidence = (
            REPO_ROOT
            / "docs"
            / "internal"
            / "pollenomics-dev"
            / "documentation-integrity.md"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "`deploy-docs.yml` builds the strict MkDocs site", automation_workflows
        )
        self.assertIn(
            "workflow follows the shared Bijux docs contract",
            automation_workflows,
        )
        self.assertIn("`mkdocs.shared.yml`", automation_workflows)
        self.assertIn("strict MkDocs builds", testing_and_evidence)
        self.assertIn("`docs/assets/site-icons/`", testing_and_evidence)
        self.assertIn("shared Bijux docs theme contract", testing_and_evidence)



if __name__ == "__main__":
    unittest.main()
