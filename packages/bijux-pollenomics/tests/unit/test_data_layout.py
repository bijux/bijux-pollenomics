from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from bijux_pollenomics.adna.tracked_data import materialize_tracked_species_root
from bijux_pollenomics.data_downloader.data_layout import (
    AVAILABLE_SOURCES,
    DATA_LAYOUT_INDEX,
    DATA_SOURCE_INDEX,
    build_source_output_roots,
    ensure_curated_species_adna_layout,
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
        self.assertIn("│   ├── equus_caballus", readme)
        self.assertIn("│   ├── bos_taurus", readme)
        self.assertIn("│   ├── canis_lupus_familiaris", readme)
        self.assertIn("│   ├── camelus_dromedarius", readme)
        self.assertIn("│   ├── rangifer_tarandus", readme)
        self.assertIn("│   ├── felis_catus", readme)
        self.assertIn("│   ├── equus_asinus", readme)
        self.assertIn("│   └── homo_sapiens", readme)
        self.assertIn("│       │   └── aadr -> ../../../aadr", readme)
        self.assertIn("│   └── v99.1", readme)
        self.assertIn("collection_summary.json", readme)
        self.assertIn("`Homo sapiens` ancient DNA is governed under", readme)
        self.assertIn("`adna/equus_caballus/`", readme)
        self.assertIn("`adna/bos_taurus/`", readme)
        self.assertIn("`adna/canis_lupus_familiaris/`", readme)
        self.assertIn("`adna/camelus_dromedarius/`", readme)
        self.assertIn("`adna/rangifer_tarandus/`", readme)
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

    def test_ensure_curated_species_adna_layout_creates_nonhuman_species_roots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"
            output_root.mkdir(parents=True, exist_ok=True)

            ensure_curated_species_adna_layout(output_root)

            horse_root = output_root / "adna" / "equus_caballus"
            dog_root = output_root / "adna" / "canis_lupus_familiaris"
            camel_root = output_root / "adna" / "camelus_dromedarius"
            donkey_root = output_root / "adna" / "equus_asinus"

            for root in (horse_root, dog_root, camel_root, donkey_root):
                self.assertTrue((root / "raw").is_dir())
                self.assertTrue((root / "normalized").is_dir())
                self.assertTrue((root / "manifests").is_dir())
                self.assertTrue((root / "reports").is_dir())
                self.assertTrue((root / "review").is_dir())

    def test_materialize_tracked_species_root_writes_real_reviewable_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"
            output_root.mkdir(parents=True, exist_ok=True)

            materialize_tracked_species_root(output_root, "horse")

            horse_root = output_root / "adna" / "equus_caballus"
            self.assertTrue((horse_root / "README.md").is_file())
            self.assertTrue((horse_root / "raw" / "archive_inventory.json").is_file())
            self.assertTrue((horse_root / "raw" / "archive_inventory.csv").is_file())
            self.assertTrue((horse_root / "raw" / "source_snapshot.json").is_file())
            self.assertTrue((horse_root / "raw" / "source_snapshot.csv").is_file())
            self.assertTrue((horse_root / "normalized" / "project_summaries.csv").is_file())
            self.assertTrue((horse_root / "normalized" / "project_summaries.json").is_file())
            self.assertTrue(
                (horse_root / "manifests" / "species_manifest.json").is_file()
            )
            self.assertTrue(
                (horse_root / "manifests" / "curation_manifest.json").is_file()
            )
            self.assertTrue(
                (horse_root / "manifests" / "project_manifest.json").is_file()
            )
            self.assertTrue(
                (horse_root / "manifests" / "runtime_manifest.json").is_file()
            )
            self.assertTrue(
                (horse_root / "manifests" / "normalization_bundle.json").is_file()
            )
            self.assertTrue(
                (horse_root / "manifests" / "citation_manifest.csv").is_file()
            )
            self.assertTrue(
                (horse_root / "reports" / "support_summary.json").is_file()
            )
            self.assertTrue((horse_root / "reports" / "support_summary.md").is_file())
            self.assertTrue((horse_root / "review" / "species_review.json").is_file())
            self.assertTrue(
                (horse_root / "review" / "archive_integrity.json").is_file()
            )
            self.assertTrue((horse_root / "review" / "species_review.md").is_file())
