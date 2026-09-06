"""Regression coverage for data-collector replacement rollback."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pytest
from bijux_pollenomics.collection.workflow.collection import (
    collect_data,
)

pytestmark = pytest.mark.generated_artifacts


class ReplacementRollbackTests(unittest.TestCase):
    def test_collect_data_replaces_selected_source_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "custom-data"
            stale_file = output_root / "neotoma" / "stale.txt"
            stale_file.parent.mkdir(parents=True, exist_ok=True)
            stale_file.write_text("stale", encoding="utf-8")

            with (
                patch(
                    "bijux_pollenomics.collection.workflow.collection.fetch_country_boundaries"
                ) as fetch_boundaries,
                patch(
                    "bijux_pollenomics.collection.workflow.collection.collect_neotoma_data"
                ) as collect_neotoma,
            ):
                fetch_boundaries.return_value = {"Sweden": {"features": []}}

                def write_fresh_dataset(
                    *,
                    output_root: Path,
                    country_boundaries: dict[str, object],
                    bbox: tuple[float, ...],
                ) -> object:
                    normalized_dir = output_root / "normalized"
                    normalized_dir.mkdir(parents=True, exist_ok=True)
                    (normalized_dir / "fresh.csv").write_text("fresh", encoding="utf-8")

                    class Report:
                        point_count = 1

                    return Report()

                collect_neotoma.side_effect = write_fresh_dataset
                collect_data(
                    output_root=output_root, sources=("neotoma",), version="v62.0"
                )

            self.assertFalse(stale_file.exists())
            self.assertTrue(
                (output_root / "neotoma" / "normalized" / "fresh.csv").exists()
            )

    def test_collect_data_preserves_previous_source_dir_when_recollection_fails(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"
            preserved_file = output_root / "neotoma" / "normalized" / "kept.csv"
            preserved_file.parent.mkdir(parents=True, exist_ok=True)
            preserved_file.write_text("kept", encoding="utf-8")

            with (
                patch(
                    "bijux_pollenomics.collection.workflow.collection.fetch_country_boundaries"
                ) as fetch_boundaries,
                patch(
                    "bijux_pollenomics.collection.workflow.collection.collect_neotoma_data"
                ) as collect_neotoma,
            ):
                fetch_boundaries.return_value = {"Sweden": {"features": []}}

                def fail_after_partial_write(
                    *,
                    output_root: Path,
                    country_boundaries: dict[str, object],
                    bbox: tuple[float, ...],
                ) -> object:
                    normalized_dir = output_root / "normalized"
                    normalized_dir.mkdir(parents=True, exist_ok=True)
                    (normalized_dir / "partial.csv").write_text(
                        "partial", encoding="utf-8"
                    )
                    raise RuntimeError("upstream failure")

                collect_neotoma.side_effect = fail_after_partial_write
                with self.assertRaisesRegex(RuntimeError, "upstream failure"):
                    collect_data(
                        output_root=output_root, sources=("neotoma",), version="v62.0"
                    )

            self.assertTrue(preserved_file.exists())
            self.assertFalse((output_root / ".neotoma.staging").exists())

    def test_collect_data_preserves_root_contract_files_when_collection_fails(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"
            readme_path = output_root / "README.md"
            summary_path = output_root / "collection_summary.json"
            output_root.mkdir(parents=True, exist_ok=True)
            readme_path.write_text("kept readme", encoding="utf-8")
            summary_path.write_text('{"status": "kept"}', encoding="utf-8")

            with patch(
                "bijux_pollenomics.collection.workflow.collection.download_aadr_anno_files"
            ) as download_aadr:
                download_aadr.side_effect = RuntimeError("download failure")

                with self.assertRaisesRegex(RuntimeError, "download failure"):
                    collect_data(
                        output_root=output_root, sources=("aadr",), version="v62.0"
                    )

            self.assertEqual(readme_path.read_text(encoding="utf-8"), "kept readme")
            self.assertEqual(
                summary_path.read_text(encoding="utf-8"), '{"status": "kept"}'
            )
