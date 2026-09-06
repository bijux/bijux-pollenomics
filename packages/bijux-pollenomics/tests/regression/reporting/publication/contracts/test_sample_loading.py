from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pytest
from bijux_pollenomics.reporting import (
    load_country_samples,
)

from ..fixtures.aadr import write_anno

pytestmark = pytest.mark.generated_artifacts


class CountryReportTests(unittest.TestCase):
    def test_load_country_samples_deduplicates_across_datasets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            write_anno(
                root / "1240k" / "v62.0_1240k_public.anno",
                [
                    "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tAG\tF",
                    "SE2\tSE2\tSweden_Group\tSigtuna\tSweden\t59.61731\t17.72361\tPaperB\t2021\t600 BCE\t2550\tAG\tM",
                    "NO1\tNO1\tNorway_Group\tOslo\tNorway\t59.9139\t10.7522\tPaperC\t2020\t700 BCE\t2650\tAG\tM",
                ],
            )
            write_anno(
                root / "ho" / "v62.0_HO_public.anno",
                [
                    "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tHO\tF",
                    "SE3\tSE3\tSweden_Group\tBirka\tSweden\t59.3350\t17.5420\tPaperD\t2023\t700 CE\t1250\tHO\tU",
                ],
            )

            samples, dataset_counts = load_country_samples(root, "Sweden")

            self.assertEqual(dataset_counts["1240k"], 2)
            self.assertEqual(dataset_counts["ho"], 2)
            self.assertEqual(len(samples), 3)
            datasets_by_id = {sample.genetic_id: sample.datasets for sample in samples}
            self.assertEqual(datasets_by_id["SE1"], ("1240k", "ho"))
            self.assertEqual(datasets_by_id["SE2"], ("1240k",))
            self.assertEqual(datasets_by_id["SE3"], ("ho",))

    def test_load_country_samples_skips_rows_without_identity_or_numeric_coordinates(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            write_anno(
                root / "1240k" / "v62.0_1240k_public.anno",
                [
                    "\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tAG\tF",
                    "SE2\tSE2\tSweden_Group\tBirka\tSweden\tbad\t17.5420\tPaperB\t2021\t600 BCE\t2550\tAG\tM",
                    "SE3\tSE3\tSweden_Group\tSigtuna\tSweden\t59.61731\t17.72361\tPaperC\t2020\t700 BCE\t2650\tAG\tM",
                ],
            )

            samples, dataset_counts = load_country_samples(root, "Sweden")

            self.assertEqual(dataset_counts["1240k"], 1)
            self.assertEqual(len(samples), 1)
            self.assertEqual(samples[0].genetic_id, "SE3")

    def test_load_country_samples_derives_bp_interval_from_mean_and_stddev_when_available(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            anno_path = root / "ho" / "v62.0_HO_public.anno"
            anno_path.parent.mkdir(parents=True, exist_ok=True)
            anno_path.write_text(
                "Genetic ID\tMaster ID\tGroup ID\tLocality\tPolitical Entity\t"
                "Lat.\tLong.\tPublication abbreviation\tYear first published\t"
                "Full Date\tDate mean in BP\tDate standard deviation in BP\t"
                "Data type\tMolecular Sex\n"
                "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\t125\tHO\tF\n",
                encoding="utf-8",
            )

            samples, _ = load_country_samples(root, "Sweden")

            self.assertEqual(len(samples), 1)
            self.assertEqual(samples[0].date_stddev_bp, "125")
            self.assertEqual(samples[0].time_start_bp, 2200)
            self.assertEqual(samples[0].time_end_bp, 2700)
            self.assertEqual(samples[0].time_mean_bp, 2450)
            self.assertEqual(samples[0].time_label, "500 BCE")
