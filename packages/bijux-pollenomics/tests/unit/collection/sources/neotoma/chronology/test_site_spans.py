from __future__ import annotations

import unittest

from bijux_pollenomics.collection.sources.neotoma.chronology import (
    AgeRangeAggregate,
    merge_age_ranges,
    neotoma_age_range_system,
    neotoma_age_range_units_supported,
    neotoma_time_interval,
    neotoma_time_label,
    numeric_age_value,
)


class NeotomaSiteSpanTests(unittest.TestCase):
    def test_merge_preserves_zero_in_the_primary_source_field(self) -> None:
        aggregates: dict[str, AgeRangeAggregate] = {}

        merge_age_ranges(
            aggregates,
            [
                {
                    "units": "Calendar years BP",
                    "ageold": 800,
                    "ageyoung": 0,
                    "ageyounger": 25,
                }
            ],
        )

        self.assertEqual(aggregates["Calendar years BP"]["ageyoung"], 0)

    def test_numeric_age_admission_rejects_invalid_scientific_values(self) -> None:
        for invalid in (True, False, -1, "-0.1", float("nan"), float("inf")):
            with self.subTest(invalid=invalid):
                self.assertIsNone(numeric_age_value(invalid))
        self.assertEqual(numeric_age_value(0), 0)
        self.assertEqual(numeric_age_value("0"), 0)

    def test_age_systems_require_exact_governed_labels(self) -> None:
        self.assertEqual(
            neotoma_age_range_system("Calibrated radiocarbon years BP"),
            "calibrated_radiocarbon_bp",
        )
        self.assertEqual(
            neotoma_age_range_system("Radiocarbon years BP"),
            "uncalibrated_radiocarbon_bp",
        )
        self.assertEqual(neotoma_age_range_system("Calendar years BP"), "calendar_bp")
        self.assertEqual(neotoma_age_range_system("Varve years BP"), "varve_bp")
        self.assertIsNone(neotoma_age_range_system("estimated BP range"))
        self.assertFalse(neotoma_age_range_units_supported("Radiocarbon years BP"))
        self.assertFalse(neotoma_age_range_units_supported("Varve years BP"))

    def test_mixed_age_systems_are_not_combined(self) -> None:
        ranges = [
            {
                "units": "Radiocarbon years BP",
                "ageold": 9000,
                "ageyoung": 8000,
            },
            {
                "units": "Calendar years BP",
                "ageold": 7000,
                "ageyoung": 6000,
            },
            {
                "units": "Calibrated radiocarbon years BP",
                "ageold": 3600,
                "ageyoung": 20,
            },
        ]

        interval = neotoma_time_interval(ranges)

        self.assertEqual(interval, (20, 3600))
        self.assertEqual(
            neotoma_time_label(ranges, interval),
            "20-3600 Calibrated radiocarbon years BP",
        )

    def test_invalid_ranges_are_not_clamped_or_reordered(self) -> None:
        ranges = [
            {
                "units": "Calibrated radiocarbon years BP",
                "ageold": 100,
                "ageyoung": -20,
            },
            {
                "units": "Calendar years BP",
                "ageold": 100,
                "ageyoung": 200,
            },
        ]

        self.assertIsNone(neotoma_time_interval(ranges))
        self.assertEqual(neotoma_time_label(ranges, None), "")


if __name__ == "__main__":
    unittest.main()
