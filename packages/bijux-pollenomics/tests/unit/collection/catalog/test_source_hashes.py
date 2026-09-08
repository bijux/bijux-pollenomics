from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from bijux_pollenomics.collection.catalog.hashes import build_source_hashes


class SourceHashesUnitTests(unittest.TestCase):
    def test_build_source_hashes_hashes_snapshot_and_normalized_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source_root = Path(tmp) / "landclim"
            (source_root / "raw").mkdir(parents=True, exist_ok=True)
            (source_root / "normalized").mkdir(parents=True, exist_ok=True)
            (source_root / "raw" / "one.txt").write_text("one", encoding="utf-8")
            (source_root / "normalized" / "two.txt").write_text("two", encoding="utf-8")
            hashes = build_source_hashes(
                source_output_roots={"landclim": str(source_root)},
                selected_sources=("landclim",),
            )

            self.assertIn("landclim", hashes)
            self.assertEqual(len(hashes["landclim"].snapshot_sha256), 64)
            self.assertEqual(len(hashes["landclim"].normalized_sha256), 64)

    def test_build_source_hashes_ignores_nested_finder_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source_root = Path(tmp) / "landclim"
            normalized_root = source_root / "normalized"
            normalized_root.mkdir(parents=True)
            (source_root / "source.txt").write_text("source", encoding="utf-8")
            (normalized_root / "evidence.csv").write_text(
                "site_id\nsite-1\n", encoding="utf-8"
            )
            baseline = build_source_hashes(
                source_output_roots={"landclim": str(source_root)},
                selected_sources=("landclim",),
            )["landclim"]

            (source_root / ".DS_Store").write_bytes(b"root finder metadata")
            (normalized_root / ".DS_Store").write_bytes(b"normalized finder metadata")
            with_finder_metadata = build_source_hashes(
                source_output_roots={"landclim": str(source_root)},
                selected_sources=("landclim",),
            )["landclim"]

            self.assertEqual(with_finder_metadata, baseline)

    def test_build_source_hashes_changes_for_scientific_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source_root = Path(tmp) / "landclim"
            normalized_root = source_root / "normalized"
            normalized_root.mkdir(parents=True)
            scientific_path = normalized_root / "evidence.csv"
            scientific_path.write_text("site_id\nsite-1\n", encoding="utf-8")
            baseline = build_source_hashes(
                source_output_roots={"landclim": str(source_root)},
                selected_sources=("landclim",),
            )["landclim"]

            scientific_path.write_text("site_id\nsite-2\n", encoding="utf-8")
            changed = build_source_hashes(
                source_output_roots={"landclim": str(source_root)},
                selected_sources=("landclim",),
            )["landclim"]

            self.assertNotEqual(changed.snapshot_sha256, baseline.snapshot_sha256)
            self.assertNotEqual(changed.normalized_sha256, baseline.normalized_sha256)

    def test_build_source_hashes_keeps_other_dotfiles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source_root = Path(tmp) / "landclim"
            source_root.mkdir()
            baseline = build_source_hashes(
                source_output_roots={"landclim": str(source_root)},
                selected_sources=("landclim",),
            )["landclim"]

            (source_root / ".source-receipt.json").write_text(
                '{"source":"landclim"}\n', encoding="utf-8"
            )
            with_dotfile = build_source_hashes(
                source_output_roots={"landclim": str(source_root)},
                selected_sources=("landclim",),
            )["landclim"]

            self.assertNotEqual(with_dotfile.snapshot_sha256, baseline.snapshot_sha256)
            self.assertEqual(with_dotfile.normalized_sha256, baseline.normalized_sha256)


if __name__ == "__main__":
    unittest.main()
