from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from bijux_pollenomics.data_downloader.pipeline import (
    build_staging_output_dir,
    collect_into_staging_dir,
)


class StagingUnitTests(unittest.TestCase):
    def test_build_staging_output_dir_uses_hidden_sibling_directory(self) -> None:
        final_output_root = Path("/tmp/data/neotoma")

        self.assertEqual(
            build_staging_output_dir(final_output_root),
            Path("/tmp/data/.neotoma.staging"),
        )

    def test_collect_into_staging_dir_swaps_in_completed_output(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            final_output_root = Path(workspace) / "neotoma"

            def collect(staging_root: Path) -> str:
                (staging_root / "normalized").mkdir(parents=True, exist_ok=True)
                (staging_root / "normalized" / "fresh.csv").write_text(
                    "fresh", encoding="utf-8"
                )
                return "ok"

            report = collect_into_staging_dir(final_output_root, collect)

            self.assertEqual(report, "ok")
            self.assertTrue((final_output_root / "normalized" / "fresh.csv").exists())
            self.assertFalse((Path(workspace) / ".neotoma.recovery").exists())

    def test_collect_into_staging_dir_removes_failed_staging_dir(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            final_output_root = Path(workspace) / "neotoma"
            staging_output_root = build_staging_output_dir(final_output_root)

            def collect(staging_root: Path) -> None:
                (staging_root / "partial.csv").write_text("partial", encoding="utf-8")
                raise RuntimeError("boom")

            with self.assertRaisesRegex(RuntimeError, "boom"):
                collect_into_staging_dir(final_output_root, collect)

            self.assertFalse(staging_output_root.exists())

    def test_collect_into_staging_dir_restores_prior_tree_on_rename_failure(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            final_output_root = Path(workspace) / "neotoma"
            final_output_root.mkdir()
            prior_file = final_output_root / "prior.csv"
            prior_file.write_text("prior", encoding="utf-8")
            staging_output_root = build_staging_output_dir(final_output_root)
            original_replace = Path.replace

            def replace_with_candidate_failure(source: Path, target: Path) -> Path:
                if source == staging_output_root:
                    raise OSError("candidate rename failed")
                return original_replace(source, target)

            def collect(staging_root: Path) -> str:
                (staging_root / "candidate.csv").write_text(
                    "candidate", encoding="utf-8"
                )
                return "unreachable"

            with (
                patch.object(Path, "replace", replace_with_candidate_failure),
                self.assertRaisesRegex(OSError, "candidate rename failed"),
            ):
                collect_into_staging_dir(final_output_root, collect)

            self.assertEqual(prior_file.read_text(encoding="utf-8"), "prior")
            self.assertFalse(staging_output_root.exists())
