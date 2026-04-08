from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from bijux_pollenomics.data_downloader.data_layout import (
    AVAILABLE_SOURCES,
    build_source_output_roots,
    render_data_root_readme_for,
    write_data_directory_readme,
)


class DataLayoutUnitTests(unittest.TestCase):
    def test_build_source_output_roots_covers_all_tracked_sources(self) -> None:
        roots = build_source_output_roots(Path("/tmp/custom-data"), "v62.0")

        self.assertEqual(roots["aadr"], "/tmp/custom-data/aadr")
        self.assertEqual(roots["aadr_version_dir"], "/tmp/custom-data/aadr/v62.0")
        self.assertEqual({key for key in roots if key not in {"aadr", "aadr_version_dir"}}, set(AVAILABLE_SOURCES) - {"aadr"})

    def test_render_data_root_readme_for_uses_requested_root_name(self) -> None:
        readme = render_data_root_readme_for(Path("/tmp/custom-data"), "v99.1")

        self.assertIn("Tracked source data lives directly under `custom-data/`", readme)
        self.assertIn("│   └── v99.1", readme)
        self.assertIn("collection_summary.json", readme)
        self.assertIn("[`docs/data-sources/index.md`](../docs/data-sources/index.md)", readme)
        self.assertIn("[`docs/reference/data-layout.md`](../docs/reference/data-layout.md)", readme)

    def test_write_data_directory_readme_writes_readme_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "custom-data"
            output_root.mkdir(parents=True, exist_ok=True)

            write_data_directory_readme(output_root, "v62.0")

            self.assertTrue((output_root / "README.md").exists())
