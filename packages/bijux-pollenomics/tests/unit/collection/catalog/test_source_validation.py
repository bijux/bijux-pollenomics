from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from bijux_pollenomics.collection.catalog.validation import validate_source_snapshot
from bijux_pollenomics.collection.contracts.models import SourceAcquisitionMetadata


class SourceValidationUnitTests(unittest.TestCase):
    def test_validate_source_snapshot_accepts_consistent_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"
            source_root = output_root / "aadr"
            source_root.mkdir(parents=True, exist_ok=True)
            source_output_roots = {"aadr": str(source_root)}
            source_metadata = {
                "aadr": SourceAcquisitionMetadata(
                    source="aadr",
                    version="v62.0",
                    license="source-specific terms",
                    retrieved_on="2026-05-01",
                    acquisition_method="collector_pipeline",
                )
            }

            validate_source_snapshot(
                output_root=output_root,
                selected_sources=("aadr",),
                source_output_roots=source_output_roots,
                source_metadata=source_metadata,
                boundary_source=None,
            )

    def test_validate_source_snapshot_rejects_boundary_contradiction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"
            source_root = output_root / "landclim"
            source_root.mkdir(parents=True, exist_ok=True)
            source_output_roots = {"landclim": str(source_root)}
            source_metadata = {
                "landclim": SourceAcquisitionMetadata(
                    source="landclim",
                    version="v62.0",
                    license="source-specific terms",
                    retrieved_on="2026-05-01",
                    acquisition_method="collector_pipeline",
                )
            }

            with self.assertRaisesRegex(ValueError, "contradictory source snapshot"):
                validate_source_snapshot(
                    output_root=output_root,
                    selected_sources=("landclim",),
                    source_output_roots=source_output_roots,
                    source_metadata=source_metadata,
                    boundary_source=None,
                )


if __name__ == "__main__":
    unittest.main()
