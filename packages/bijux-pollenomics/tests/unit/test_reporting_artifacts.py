from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from bijux_pollenomics.reporting import rendering
from bijux_pollenomics.reporting.rendering import artifacts as rendering_artifacts


class ReportingArtifactsTests(unittest.TestCase):
    def test_copy_map_assets_copies_vendor_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            destination = rendering.copy_map_assets(Path(tmp))

            self.assertTrue((destination / "leaflet" / "leaflet.js").exists())
            self.assertTrue((destination / "markercluster" / "leaflet.markercluster.js").exists())

    def test_copy_map_assets_rejects_incomplete_vendor_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source_dir = Path(tmp) / "source"
            output_dir = Path(tmp) / "output"
            (source_dir / "leaflet").mkdir(parents=True, exist_ok=True)
            (source_dir / "markercluster").mkdir(parents=True, exist_ok=True)
            (source_dir / "leaflet" / "leaflet.css").write_text("leaflet", encoding="utf-8")

            original = rendering_artifacts.MAP_ASSET_SOURCE_DIR
            rendering_artifacts.MAP_ASSET_SOURCE_DIR = source_dir
            try:
                with self.assertRaisesRegex(FileNotFoundError, "Vendored map asset bundle is incomplete"):
                    rendering.copy_map_assets(output_dir)
            finally:
                rendering_artifacts.MAP_ASSET_SOURCE_DIR = original


if __name__ == "__main__":
    unittest.main()
