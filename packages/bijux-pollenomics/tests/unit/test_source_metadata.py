from __future__ import annotations

import unittest

from bijux_pollenomics.collection.catalog.metadata import build_source_metadata


class SourceMetadataUnitTests(unittest.TestCase):
    def test_build_source_metadata_covers_selected_sources(self) -> None:
        metadata = build_source_metadata(
            selected_sources=("aadr", "landclim", "raa"), version="v62.0"
        )

        self.assertEqual(tuple(metadata), ("aadr", "landclim", "raa"))
        self.assertEqual(metadata["aadr"].version, "v62.0")
        self.assertEqual(metadata["aadr"].acquisition_method, "collector_pipeline")
        self.assertTrue(metadata["raa"].license)

    def test_boundary_metadata_uses_its_source_version_and_terms(self) -> None:
        metadata = build_source_metadata(
            selected_sources=("aadr", "boundaries"), version="v66"
        )

        self.assertEqual(metadata["aadr"].version, "v66")
        self.assertEqual(metadata["boundaries"].version, "5.1.1")
        self.assertEqual(metadata["boundaries"].license, "Natural Earth public domain")


if __name__ == "__main__":
    unittest.main()
