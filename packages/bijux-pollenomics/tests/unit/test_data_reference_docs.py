from __future__ import annotations

from pathlib import Path
import re
import unittest

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]

pytestmark = pytest.mark.generated_artifacts


class DataReferenceDocsUnitTests(unittest.TestCase):
    def test_data_reference_docs_do_not_publish_relative_links_into_data_tree(
        self,
    ) -> None:
        data_docs_root = REPO_ROOT / "docs" / "public" / "pollenomics-data"
        markdown_link_re = re.compile(r"\]\((?P<target>[^\)]+)\)")

        offending_links: list[str] = []
        for markdown_path in sorted(data_docs_root.rglob("*.md")):
            for match in markdown_link_re.finditer(
                markdown_path.read_text(encoding="utf-8")
            ):
                target = match.group("target")
                if not target.startswith((".", "..")):
                    continue
                resolved = (markdown_path.parent / target).resolve()
                try:
                    resolved.relative_to(REPO_ROOT / "data")
                except ValueError:
                    continue
                offending_links.append(
                    f"{markdown_path.relative_to(REPO_ROOT)} -> {target}"
                )

        self.assertEqual(offending_links, [])

    def test_data_reference_tree_stays_within_directory_budget(self) -> None:
        data_docs_root = REPO_ROOT / "docs" / "public" / "pollenomics-data"
        child_directories = sorted(
            path.name for path in data_docs_root.iterdir() if path.is_dir()
        )

        self.assertEqual(
            child_directories,
            ["evidence", "overview", "publications", "sources"],
        )

    def test_data_reference_index_routes_readers_to_public_sections(self) -> None:
        data_index = (
            REPO_ROOT / "docs" / "public" / "pollenomics-data" / "index.md"
        ).read_text(encoding="utf-8")

        self.assertIn("public guide to the repository's evidence", data_index)
        self.assertIn("[System](overview/index.md)", data_index)
        self.assertIn(
            "[Data architecture handbook](overview/data-architecture-handbook.md)",
            data_index,
        )
        self.assertIn("[Sources](sources/index.md)", data_index)
        self.assertIn("[Evidence](evidence/index.md)", data_index)
        self.assertIn("[Publications](publications/index.md)", data_index)
        self.assertIn("overview/pollenomics-publication-model/", data_index)
        self.assertIn("overview/cross-domain-evidence-matrix/", data_index)

    def test_data_reference_restores_cross_domain_docs_routes(self) -> None:
        overview_index = (
            REPO_ROOT / "docs" / "public" / "pollenomics-data" / "overview" / "index.md"
        ).read_text(encoding="utf-8")
        source_index = (
            REPO_ROOT / "docs" / "public" / "pollenomics-data" / "sources" / "index.md"
        ).read_text(encoding="utf-8")
        outputs_index = (
            REPO_ROOT
            / "docs"
            / "public"
            / "pollenomics-data"
            / "publications"
            / "index.md"
        ).read_text(encoding="utf-8")

        self.assertIn("pollenomics-publication-model.md", overview_index)
        self.assertIn("data-architecture-handbook.md", overview_index)
        self.assertIn("cross-domain-evidence-matrix.md", overview_index)
        self.assertIn("refresh-policy.md", source_index)
        self.assertIn("shared-normalization.md", source_index)
        self.assertIn("non-adna-explainer-recovery.md", source_index)
        self.assertIn("../../../report/index.md", outputs_index)
        self.assertIn("../../../report/how-to-read.md", outputs_index)
        self.assertIn("publication-types.md", outputs_index)
        self.assertIn("map-inputs.md", outputs_index)


if __name__ == "__main__":
    unittest.main()
