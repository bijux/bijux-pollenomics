"""Project source-bundle registry behavior."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from bijux_pollenomics.adna.sources.library import build_project_source_bundles


class ProjectSourceBundleRegistryTests(unittest.TestCase):
    def test_project_source_bundles_flag_missing_local_sources_before_refresh(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"
            bundles = build_project_source_bundles(output_root)

        horse_bundle = next(
            item for item in bundles if item.project_accession == "PRJEB22390"
        )
        self.assertTrue(horse_bundle.paper_required)
        self.assertFalse(horse_bundle.supplement_required)
        self.assertIn("missing_local_paper_evidence", horse_bundle.blockers)
        self.assertNotIn("missing_local_supplementary_material", horse_bundle.blockers)
