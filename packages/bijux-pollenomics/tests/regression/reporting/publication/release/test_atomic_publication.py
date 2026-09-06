from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pytest
from bijux_pollenomics.reporting import (
    generate_published_reports,
)

from ..fixtures.aadr import write_anno

pytestmark = pytest.mark.generated_artifacts


class CountryReportTests(unittest.TestCase):
    def test_generate_published_reports_removes_stale_bundle_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            output = Path(tmp) / "docs" / "report"
            write_anno(
                root / "1240k" / "v62.0_1240k_public.anno",
                [
                    "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tAG\tF",
                    "NO1\tNO1\tNorway_Group\tOslo\tNorway\t59.9139\t10.7522\tPaperB\t2021\t600 BCE\t2550\tAG\tM",
                ],
            )

            generate_published_reports(
                version_dir=root,
                countries=["Sweden", "Norway"],
                output_root=output,
                title="Nordic Evidence Atlas",
                slug="nordic-atlas",
            )
            self.assertTrue((output / "countries" / "norway").exists())

            generate_published_reports(
                version_dir=root,
                countries=["Sweden"],
                output_root=output,
                title="Nordic Evidence Atlas",
                slug="nordic-atlas",
            )

            self.assertFalse((output / "countries" / "norway").exists())
            self.assertTrue((output / "countries" / "sweden").exists())

    def test_generate_published_reports_preserves_previous_tree_when_publication_fails(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            output = Path(tmp) / "docs" / "report"
            preserved_file = output / "published_reports_summary.json"
            output.mkdir(parents=True, exist_ok=True)
            preserved_file.write_text("kept", encoding="utf-8")
            write_anno(
                root / "ho" / "v62.0_HO_public.anno",
                [
                    "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tHO\tF",
                ],
            )

            def fail_after_partial_write(
                path: Path, payload: dict[str, object]
            ) -> None:
                path.write_text("partial", encoding="utf-8")
                raise RuntimeError("summary failure")

            with (
                patch(
                    "bijux_pollenomics.reporting.service.write_summary_json",
                    side_effect=fail_after_partial_write,
                ),
                self.assertRaisesRegex(RuntimeError, "summary failure"),
            ):
                generate_published_reports(
                    version_dir=root,
                    countries=["Sweden"],
                    output_root=output,
                    title="Nordic Evidence Atlas",
                    slug="nordic-atlas",
                )

            self.assertEqual(preserved_file.read_text(encoding="utf-8"), "kept")
            self.assertFalse((output.parent / ".report.staging").exists())
