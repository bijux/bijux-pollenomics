"""Regression coverage for data-collector repository documentation."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pytest
from bijux_pollenomics.collection.workflow.collection import (
    AVAILABLE_SOURCES,
    collect_data,
)

pytestmark = pytest.mark.generated_artifacts


class RepositoryDocumentationTests(unittest.TestCase):
    def test_collect_data_writes_output_root_specific_readme(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "custom-data"

            with patch(
                "bijux_pollenomics.collection.workflow.collection.download_aadr_anno_files"
            ) as download_aadr:
                download_aadr.return_value.downloaded_files = ()
                collect_data(
                    output_root=output_root, sources=("aadr",), version="v62.0"
                )

            readme_text = (output_root / "README.md").read_text(encoding="utf-8")
            normalized_readme = " ".join(readme_text.split())
            self.assertIn(
                "Tracked source data and governed species-owned ancient-DNA views live "
                "directly under `custom-data/`",
                normalized_readme,
            )
            self.assertIn("\ncustom-data\n", readme_text)
            self.assertIn("│   └── v62.0", readme_text)
            summary = json.loads(
                (output_root / "collection_summary.json").read_text(encoding="utf-8")
            )
            self.assertEqual(summary["collected_sources"], ["aadr"])
            self.assertEqual(
                summary["source_output_roots"]["aadr"], str(output_root / "aadr")
            )
            self.assertEqual(
                summary["source_output_roots"]["aadr_version_dir"],
                str(output_root / "aadr" / "v62.0"),
            )
            self.assertIn("contract_artifacts", summary)
            self.assertIn("source_family_state_rows", summary)
            self.assertIsNone(summary["boundary_source"])
            self.assertIn("source_metadata", summary)
            self.assertEqual(
                summary["source_metadata"]["aadr"]["acquisition_method"],
                "collector_pipeline",
            )
            self.assertEqual(summary["source_metadata"]["aadr"]["version"], "v62.0")
            self.assertIn("source_hashes", summary)
            self.assertIn("aadr", summary["source_hashes"])
            self.assertEqual(
                len(summary["source_hashes"]["aadr"]["snapshot_sha256"]), 64
            )
            self.assertIn("source_provenance", summary)
            self.assertIn("aadr", summary["source_provenance"])
            self.assertEqual(summary["source_provenance"]["aadr"]["version"], "v62.0")
            self.assertEqual(
                summary["source_provenance"]["aadr"]["acquisition_method"],
                "collector_pipeline",
            )
            self.assertIn("source_replacement_rules", summary)
            self.assertTrue(
                summary["source_replacement_rules"]["aadr"]["destructive_refresh"]
            )
            self.assertEqual(
                summary["source_replacement_rules"]["aadr"]["refresh_mode"],
                "staging_swap",
            )
            self.assertIn("source_traceability", summary)
            self.assertEqual(
                summary["source_traceability"]["aadr"]["source_version"], "v62.0"
            )
            self.assertTrue(
                summary["source_traceability"]["aadr"]["dispute_token"].startswith(
                    "aadr@v62.0:"
                )
            )
            self.assertEqual(summary["landclim_site_count"], 0)
            self.assertEqual(summary["landclim_grid_cell_count"], 0)
            self.assertEqual(summary["landclim_temporal_grid_feature_count"], 0)
            for source_dir in AVAILABLE_SOURCES:
                self.assertTrue((output_root / source_dir).exists())
