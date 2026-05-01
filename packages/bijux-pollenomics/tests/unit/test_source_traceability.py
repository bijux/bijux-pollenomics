from __future__ import annotations

import unittest

from bijux_pollenomics.data_downloader.models import SourceAcquisitionMetadata
from bijux_pollenomics.data_downloader.source_traceability import (
    build_source_traceability_records,
)


class SourceTraceabilityUnitTests(unittest.TestCase):
    def test_build_source_traceability_records_emits_dispute_tokens(self) -> None:
        records = build_source_traceability_records(
            selected_sources=("sead",),
            source_metadata={
                "sead": SourceAcquisitionMetadata(
                    source="sead",
                    version="v62.0",
                    license="source-specific terms",
                    retrieved_on="2026-05-01",
                    acquisition_method="collector_pipeline",
                )
            },
            source_hashes={
                "sead": {
                    "snapshot_sha256": "f" * 64,
                    "normalized_sha256": "e" * 64,
                }
            },
        )

        self.assertEqual(records["sead"].source_identity, "sead")
        self.assertEqual(records["sead"].source_version, "v62.0")
        self.assertEqual(records["sead"].snapshot_sha256, "f" * 64)
        self.assertEqual(records["sead"].normalized_sha256, "e" * 64)
        self.assertEqual(records["sead"].dispute_token, "sead@v62.0:ffffffffffff")


if __name__ == "__main__":
    unittest.main()
