from __future__ import annotations

import csv
import json
from pathlib import Path
import tempfile
import unittest

import pytest

from bijux_pollenomics.reporting import (
    generate_country_report,
)


from ..fixtures.aadr import write_anno


pytestmark = pytest.mark.generated_artifacts


class CountryReportTests(unittest.TestCase):
    def test_generate_country_report_writes_expected_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            output = Path(tmp) / "docs" / "report" / "sweden"
            write_anno(
                root / "1240k" / "v62.0_1240k_public.anno",
                [
                    "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tAG\tF",
                    "SE2\tSE2\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperB\t2021\t600 BCE\t2550\tAG\tM",
                ],
            )
            write_anno(
                root / "ho" / "v62.0_HO_public.anno",
                [
                    "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tHO\tF",
                ],
            )

            report = generate_country_report(root, "Sweden", output)

            self.assertEqual(report.total_unique_samples, 2)
            self.assertEqual(report.total_unique_localities, 1)
            self.assertTrue((output / "README.md").exists())
            self.assertTrue((output / "sweden_aadr_v62.0_samples.csv").exists())
            self.assertTrue((output / "sweden_aadr_v62.0_localities.csv").exists())
            self.assertTrue((output / "sweden_aadr_v62.0_samples.geojson").exists())
            self.assertTrue((output / "sweden_aadr_v62.0_samples.md").exists())
            self.assertTrue((output / "sweden_aadr_v62.0_bundle.json").exists())
            self.assertTrue((output / "sweden_aadr_v62.0_summary.json").exists())
            self.assertFalse((output / "sweden_aadr_v62.0_map.html").exists())

            with (output / "sweden_aadr_v62.0_samples.csv").open(
                newline="", encoding="utf-8"
            ) as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["political_entity"], "Sweden")
            with (output / "sweden_aadr_v62.0_localities.csv").open(
                newline="", encoding="utf-8"
            ) as handle:
                locality_rows = list(csv.DictReader(handle))
            self.assertEqual(locality_rows[0]["time_start_bp"], "2450")
            self.assertEqual(locality_rows[0]["time_end_bp"], "2550")
            self.assertEqual(locality_rows[0]["time_label"], "2450-2550 BP")

            geojson = json.loads(
                (output / "sweden_aadr_v62.0_samples.geojson").read_text(
                    encoding="utf-8"
                )
            )
            summary = json.loads(
                (output / "sweden_aadr_v62.0_summary.json").read_text(encoding="utf-8")
            )
            self.assertEqual(geojson["type"], "FeatureCollection")
            self.assertEqual(len(geojson["features"]), 2)
            self.assertEqual(
                summary["artifacts"]["bundle_manifest"],
                "sweden_aadr_v62.0_bundle.json",
            )
            self.assertEqual(
                summary["artifacts"]["samples_csv"], "sweden_aadr_v62.0_samples.csv"
            )
            self.assertEqual(
                summary["artifacts"]["summary_json"], "sweden_aadr_v62.0_summary.json"
            )

    def test_generate_country_report_can_link_to_shared_map(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            output = Path(tmp) / "docs" / "report" / "sweden"
            write_anno(
                root / "ho" / "v62.0_HO_public.anno",
                [
                    "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tHO\tF",
                ],
            )

            generate_country_report(
                root,
                "Sweden",
                output,
                map_reference=(
                    "Nordic Evidence Atlas",
                    "../nordic-atlas/nordic-atlas_map.html",
                ),
            )

            readme_text = (output / "README.md").read_text(encoding="utf-8")
            self.assertIn("Shared interactive map", readme_text)
            self.assertIn("../nordic-atlas/nordic-atlas_map.html", readme_text)
            self.assertIn(
                "Environmental and archaeology context layers are published in the shared map bundle",
                readme_text,
            )

    def test_generate_country_report_uses_country_specific_copy_and_locality_placeholder(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            output = Path(tmp) / "docs" / "report" / "finland"
            write_anno(
                root / "ho" / "v62.0_HO_public.anno",
                [
                    "FI1\tFI1\tFinland_Group\t\tFinland\t60.2\t24.9\tPaperA\t2022\t500 BCE\t2450\tHO\tF",
                ],
            )

            generate_country_report(root, "Finland", output)

            readme_text = (output / "README.md").read_text(encoding="utf-8")
            samples_csv = (output / "finland_aadr_v62.0_samples.csv").read_text(
                encoding="utf-8"
            )
            self.assertIn("| Dataset | Finland rows |", readme_text)
            self.assertIn(
                "| Locality | Samples | Latitude | Longitude | BP coverage | Datasets |",
                readme_text,
            )
            self.assertIn(
                "It inventories only Homo sapiens aDNA sample rows that match the `Finland` country filter.",
                readme_text,
            )
            self.assertIn(
                "combined inventory for `Finland` contains `1` unique Homo sapiens aDNA samples",
                readme_text,
            )
            self.assertIn("Unspecified locality", readme_text)
            self.assertIn("Unspecified locality", samples_csv)

    def test_generate_country_report_handles_zero_matching_samples(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            output = Path(tmp) / "docs" / "report" / "iceland"
            write_anno(
                root / "ho" / "v62.0_HO_public.anno",
                [
                    "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tHO\tF",
                ],
            )

            report = generate_country_report(root, "Iceland", output)

            self.assertEqual(report.total_unique_samples, 0)
            self.assertEqual(report.total_unique_localities, 0)
            readme_text = (output / "README.md").read_text(encoding="utf-8")
            samples_markdown = (output / "iceland_aadr_v62.0_samples.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("Unique Homo sapiens aDNA samples: `0`", readme_text)
            self.assertIn("No latitude values available", readme_text)
            self.assertIn("No matching localities", readme_text)
            self.assertIn("Machine-readable summary", readme_text)
            self.assertIn(
                "This country bundle is valid even when the filter returns zero Homo sapiens aDNA samples.",
                readme_text,
            )
            self.assertIn("Total Homo sapiens aDNA samples: `0`.", samples_markdown)
