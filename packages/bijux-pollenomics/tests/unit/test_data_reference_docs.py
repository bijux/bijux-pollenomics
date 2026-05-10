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


if __name__ == "__main__":
    unittest.main()
