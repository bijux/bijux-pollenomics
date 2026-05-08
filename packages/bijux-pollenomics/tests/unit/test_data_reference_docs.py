from __future__ import annotations

from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[4]


class DataReferenceDocsUnitTests(unittest.TestCase):
    def test_data_reference_tree_stays_within_directory_budget(self) -> None:
        data_docs_root = REPO_ROOT / "docs" / "02-bijux-pollenomics-data"
        child_directories = sorted(
            path.name for path in data_docs_root.iterdir() if path.is_dir()
        )

        self.assertEqual(
            child_directories,
            ["evidence", "outputs", "overview", "sources"],
        )

    def test_data_reference_index_routes_readers_to_public_sections(self) -> None:
        data_index = (
            REPO_ROOT / "docs" / "02-bijux-pollenomics-data" / "index.md"
        ).read_text(encoding="utf-8")

        self.assertIn("public guide to the repository's evidence", data_index)
        self.assertIn("[Overview](overview/index.md)", data_index)
        self.assertIn("[Sources](sources/index.md)", data_index)
        self.assertIn("[Evidence](evidence/index.md)", data_index)
        self.assertIn("[Outputs](outputs/index.md)", data_index)


if __name__ == "__main__":
    unittest.main()
