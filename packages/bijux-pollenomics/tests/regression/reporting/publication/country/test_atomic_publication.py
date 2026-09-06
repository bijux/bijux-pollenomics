from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pytest

from bijux_pollenomics.reporting import (
    generate_country_report,
)

from ..fixtures.aadr import write_anno

pytestmark = pytest.mark.generated_artifacts


class CountryReportTests(unittest.TestCase):
    def test_generate_country_report_replaces_stale_bundle_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            output = Path(tmp) / "docs" / "report" / "sweden"
            output.mkdir(parents=True, exist_ok=True)
            stale_file = output / "obsolete.txt"
            stale_file.write_text("stale", encoding="utf-8")
            write_anno(
                root / "ho" / "v62.0_HO_public.anno",
                [
                    "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tHO\tF",
                ],
            )

            generate_country_report(root, "Sweden", output)

            self.assertFalse(stale_file.exists())
            self.assertTrue((output / "README.md").exists())

    def test_generate_country_report_preserves_previous_bundle_when_publication_fails(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            output = Path(tmp) / "docs" / "report" / "sweden"
            output.mkdir(parents=True, exist_ok=True)
            preserved_file = output / "README.md"
            preserved_file.write_text("kept", encoding="utf-8")
            write_anno(
                root / "ho" / "v62.0_HO_public.anno",
                [
                    "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tHO\tF",
                ],
            )

            def fail_after_partial_write(path: Path, samples: object) -> None:
                path.write_text("partial", encoding="utf-8")
                raise RuntimeError("write failure")

            with (
                patch(
                    "bijux_pollenomics.reporting.service.write_samples_csv",
                    side_effect=fail_after_partial_write,
                ),
                self.assertRaisesRegex(RuntimeError, "write failure"),
            ):
                generate_country_report(root, "Sweden", output)

            self.assertEqual(preserved_file.read_text(encoding="utf-8"), "kept")
            self.assertFalse((output.parent / ".sweden.staging").exists())
