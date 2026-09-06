"""Regression coverage for data-collector source selection."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pytest
from bijux_pollenomics.collection.workflow.collection import (
    AVAILABLE_SOURCES,
    collect_data,
    normalize_requested_sources,
)

pytestmark = pytest.mark.generated_artifacts


class SourceSelectionTests(unittest.TestCase):
    def test_normalize_requested_sources_expands_all(self) -> None:
        self.assertEqual(normalize_requested_sources(["all"]), AVAILABLE_SOURCES)

    def test_normalize_requested_sources_deduplicates_preserving_order(self) -> None:
        self.assertEqual(
            normalize_requested_sources(["raa", "aadr", "raa"]),
            ("raa", "aadr"),
        )

    def test_collect_data_rejects_unsupported_sources_without_writing_output(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"

            with self.assertRaisesRegex(
                ValueError, "Unsupported data source: unsupported"
            ):
                collect_data(
                    output_root=output_root, sources=("unsupported",), version="v62.0"
                )

            self.assertFalse(output_root.exists())
