from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from bijux_pollenomics.data_downloader.staging import build_staging_output_dir, collect_into_staging_dir


class StagingUnitTests(unittest.TestCase):
    def test_build_staging_output_dir_uses_hidden_sibling_directory(self) -> None:
        final_output_root = Path("/tmp/data/neotoma")

        self.assertEqual(build_staging_output_dir(final_output_root), Path("/tmp/data/.neotoma.tmp"))

    def test_collect_into_staging_dir_swaps_in_completed_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            final_output_root = Path(tmp) / "neotoma"

            def collect(staging_root: Path) -> str:
                (staging_root / "normalized").mkdir(parents=True, exist_ok=True)
                (staging_root / "normalized" / "fresh.csv").write_text("fresh", encoding="utf-8")
                return "ok"

            report = collect_into_staging_dir(final_output_root, collect)

            self.assertEqual(report, "ok")
            self.assertTrue((final_output_root / "normalized" / "fresh.csv").exists())

    def test_collect_into_staging_dir_removes_failed_staging_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            final_output_root = Path(tmp) / "neotoma"
            staging_output_root = build_staging_output_dir(final_output_root)

            def collect(staging_root: Path) -> None:
                (staging_root / "partial.csv").write_text("partial", encoding="utf-8")
                raise RuntimeError("boom")

            with self.assertRaisesRegex(RuntimeError, "boom"):
                collect_into_staging_dir(final_output_root, collect)

            self.assertFalse(staging_output_root.exists())
