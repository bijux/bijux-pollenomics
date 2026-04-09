from __future__ import annotations

import unittest

from bijux_pollenomics.data_downloader.pipeline import (
    CONTEXT_SOURCE_SPECS,
    resolve_context_collect_function,
)


class SourceRegistryUnitTests(unittest.TestCase):
    def test_context_source_specs_keep_expected_sources(self) -> None:
        self.assertEqual(
            tuple(CONTEXT_SOURCE_SPECS), ("landclim", "neotoma", "raa", "sead")
        )
        self.assertTrue(CONTEXT_SOURCE_SPECS["landclim"].requires_bbox)
        self.assertFalse(CONTEXT_SOURCE_SPECS["raa"].requires_bbox)

    def test_resolve_context_collect_function_rejects_unknown_source(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported context source"):
            resolve_context_collect_function("unknown")

    def test_resolve_context_collect_function_returns_callable(self) -> None:
        collector = resolve_context_collect_function("neotoma")

        self.assertTrue(callable(collector))
