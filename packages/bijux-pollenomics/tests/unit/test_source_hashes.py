from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from bijux_pollenomics.data_downloader.source_hashes import build_source_hashes


class SourceHashesUnitTests(unittest.TestCase):
    def test_build_source_hashes_hashes_snapshot_and_normalized_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source_root = Path(tmp) / "landclim"
            (source_root / "raw").mkdir(parents=True, exist_ok=True)
            (source_root / "normalized").mkdir(parents=True, exist_ok=True)
            (source_root / "raw" / "one.txt").write_text("one", encoding="utf-8")
            (source_root / "normalized" / "two.txt").write_text(
                "two", encoding="utf-8"
            )
            hashes = build_source_hashes(
                source_output_roots={"landclim": str(source_root)},
                selected_sources=("landclim",),
            )

            self.assertIn("landclim", hashes)
            self.assertEqual(len(hashes["landclim"].snapshot_sha256), 64)
            self.assertEqual(len(hashes["landclim"].normalized_sha256), 64)


if __name__ == "__main__":
    unittest.main()
