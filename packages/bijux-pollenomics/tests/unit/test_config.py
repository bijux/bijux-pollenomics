from __future__ import annotations

import unittest
from pathlib import Path

from bijux_pollenomics.config import (
    ATLAS_DEFAULTS,
    DATA_DEFAULTS,
    PROJECT_PATHS,
    DEFAULT_AADR_ROOT,
    DEFAULT_AADR_VERSION,
    DEFAULT_ATLAS_SLUG,
    DEFAULT_ATLAS_TITLE,
    DEFAULT_CONTEXT_ROOT,
    DEFAULT_DATA_ROOT,
    DEFAULT_PUBLISHED_COUNTRIES,
    DEFAULT_REPORT_ROOT,
    NORDIC_BBOX,
)


class ConfigDefaultsUnitTests(unittest.TestCase):
    def test_config_module_keeps_canonical_default_values(self) -> None:
        self.assertEqual(DATA_DEFAULTS.aadr_version, "v62.0")
        self.assertEqual(DATA_DEFAULTS.nordic_bbox, (4.0, 54.0, 35.0, 72.0))
        self.assertEqual(ATLAS_DEFAULTS.slug, "nordic-atlas")
        self.assertEqual(ATLAS_DEFAULTS.title, "Nordic Evidence Atlas")
        self.assertEqual(PROJECT_PATHS.data_root, Path("data"))
        self.assertEqual(PROJECT_PATHS.report_root, Path("docs/report"))

    def test_default_exports_match_config_structures(self) -> None:
        self.assertEqual(DEFAULT_AADR_VERSION, DATA_DEFAULTS.aadr_version)
        self.assertEqual(NORDIC_BBOX, DATA_DEFAULTS.nordic_bbox)
        self.assertEqual(DEFAULT_ATLAS_SLUG, ATLAS_DEFAULTS.slug)
        self.assertEqual(DEFAULT_ATLAS_TITLE, ATLAS_DEFAULTS.title)
        self.assertEqual(DEFAULT_PUBLISHED_COUNTRIES, ATLAS_DEFAULTS.published_countries)
        self.assertEqual(DEFAULT_DATA_ROOT, PROJECT_PATHS.data_root)
        self.assertEqual(DEFAULT_AADR_ROOT, PROJECT_PATHS.aadr_root)
        self.assertEqual(DEFAULT_REPORT_ROOT, PROJECT_PATHS.report_root)
        self.assertEqual(DEFAULT_CONTEXT_ROOT, PROJECT_PATHS.context_root)
