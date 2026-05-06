from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from bijux_pollenomics.data_downloader.data_layout import (
    AVAILABLE_SOURCES,
    DATA_LAYOUT_INDEX,
    DATA_SOURCE_INDEX,
    build_source_output_roots,
    ensure_homo_sapiens_adna_layout,
    render_data_root_readme_for,
    write_data_directory_readme,
)


class DataLayoutUnitTests(unittest.TestCase):
    def test_build_source_output_roots_covers_all_tracked_sources(self) -> None:
        roots = build_source_output_roots(Path("/tmp/custom-data"), "v62.0")

        self.assertEqual(roots["aadr"], "/tmp/custom-data/aadr")
        self.assertEqual(roots["aadr_version_dir"], "/tmp/custom-data/aadr/v62.0")
        self.assertEqual(
            {key for key in roots if key not in {"aadr", "aadr_version_dir"}},
            set(AVAILABLE_SOURCES) - {"aadr"},
        )

    def test_render_data_root_readme_for_uses_requested_root_name(self) -> None:
        readme = render_data_root_readme_for(Path("/tmp/custom-data"), "v99.1")

        self.assertIn(
            "Tracked source data and governed species-owned ancient-DNA views live directly",
            readme,
        )
        self.assertIn("`custom-data/`", readme)
        self.assertIn("│   └── homo_sapiens", readme)
        self.assertIn("│       │   └── aadr -> ../../../aadr", readme)
        self.assertIn("│   └── v99.1", readme)
        self.assertIn("collection_summary.json", readme)
        self.assertIn("`Homo sapiens` ancient DNA is governed under", readme)
        self.assertIn(
            "[`docs/02-bijux-pollenomics-data/sources/index.md`]"
            f"({DATA_SOURCE_INDEX})",
            readme,
        )
        self.assertIn(
            "[`docs/02-bijux-pollenomics-data/foundation/directory-layout.md`]"
            f"({DATA_LAYOUT_INDEX})",
            readme,
        )

    def test_write_data_directory_readme_writes_readme_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "custom-data"
            output_root.mkdir(parents=True, exist_ok=True)

            write_data_directory_readme(output_root, "v62.0")

            self.assertTrue((output_root / "README.md").exists())

    def test_ensure_homo_sapiens_adna_layout_creates_species_view(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"
            output_root.mkdir(parents=True, exist_ok=True)

            ensure_homo_sapiens_adna_layout(output_root)

            species_root = output_root / "adna" / "homo_sapiens"
            self.assertTrue((species_root / "normalized").is_dir())
            self.assertTrue((species_root / "manifests").is_dir())
            self.assertTrue((species_root / "reports").is_dir())
            self.assertTrue((species_root / "review").is_dir())
            raw_aadr = species_root / "raw" / "aadr"
            self.assertTrue(raw_aadr.is_symlink())
            self.assertEqual(raw_aadr.readlink().as_posix(), "../../../aadr")
