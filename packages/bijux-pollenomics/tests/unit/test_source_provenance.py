from __future__ import annotations

import unittest

from bijux_pollenomics.data_downloader.models import SourceAcquisitionMetadata
from bijux_pollenomics.data_downloader.source_provenance import build_source_provenance


class SourceProvenanceUnitTests(unittest.TestCase):
    def test_build_source_provenance_tracks_identity_metadata_and_hashes(self) -> None:
        provenance = build_source_provenance(
            selected_sources=("landclim",),
            source_output_roots={"landclim": "/tmp/data/landclim"},
            source_metadata={
                "landclim": SourceAcquisitionMetadata(
                    source="landclim",
                    version="v62.0",
                    license="source-specific terms",
                    retrieved_on="2026-05-01",
                    acquisition_method="collector_pipeline",
                )
            },
            source_hashes={
                "landclim": {
                    "snapshot_sha256": "a" * 64,
                    "normalized_sha256": "b" * 64,
                }
            },
        )

        self.assertEqual(provenance["landclim"].source, "landclim")
        self.assertEqual(provenance["landclim"].display_name, "LandClim")
        self.assertEqual(
            provenance["landclim"].evidence_family, "pollen_paleoclimate_context"
        )
        self.assertEqual(provenance["landclim"].version, "v62.0")
        self.assertEqual(provenance["landclim"].snapshot_sha256, "a" * 64)
        self.assertEqual(provenance["landclim"].normalized_sha256, "b" * 64)
        self.assertEqual(
            provenance["landclim"].normalized_root, "/tmp/data/landclim/normalized"
        )


if __name__ == "__main__":
    unittest.main()
