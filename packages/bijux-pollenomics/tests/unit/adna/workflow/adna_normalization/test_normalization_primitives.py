from __future__ import annotations

import unittest

from bijux_pollenomics.adna import (
    normalize_breed_label,
    normalize_chronology_text,
    normalize_coordinate_resolution,
    normalize_explicit_bp_window,
    normalize_species_anchor,
)

from .marks import GENERATED_ARTIFACTS

pytestmark = GENERATED_ARTIFACTS


class AdnaNormalizationUnitTests(unittest.TestCase):
    def test_normalize_species_anchor_accepts_alias_and_rejects_mismatch(self) -> None:
        species = normalize_species_anchor(
            "pig", expected_species_name="Sus scrofa domesticus"
        )

        self.assertEqual(species.latin_name, "Sus scrofa domesticus")
        with self.assertRaisesRegex(ValueError, "Species anchor mismatch"):
            normalize_species_anchor("horse", expected_species_name="pig")

    def test_normalize_breed_label_keeps_meaningful_text_only(self) -> None:
        self.assertEqual(
            normalize_breed_label(" Przewalski_Associated "), "przewalski associated"
        )
        self.assertIsNone(normalize_breed_label("unknown"))
        self.assertIsNone(normalize_breed_label("   "))

    def test_normalize_coordinate_resolution_parses_pairs_and_allows_withheld(
        self,
    ) -> None:
        exact = normalize_coordinate_resolution(
            latitude_text="59.1",
            longitude_text="17.3",
            geographic_basis="exact_coordinates",
        )
        withheld = normalize_coordinate_resolution(
            latitude_text="",
            longitude_text="",
            geographic_basis="country_only",
        )

        self.assertEqual(exact.confidence, "exact")
        self.assertIsNotNone(exact.coordinate)
        assert exact.coordinate is not None
        self.assertEqual(exact.coordinate.latitude, 59.1)
        self.assertIsNone(withheld.coordinate)
        self.assertEqual(withheld.confidence, "withheld")

    def test_normalize_coordinate_resolution_refuses_invalid_pairs(self) -> None:
        with self.assertRaisesRegex(ValueError, "both latitude and longitude"):
            normalize_coordinate_resolution(
                latitude_text="59.1",
                longitude_text="",
                geographic_basis="site_level_localities",
            )
        with self.assertRaisesRegex(ValueError, "Latitude out of range"):
            normalize_coordinate_resolution(
                latitude_text="120",
                longitude_text="17.3",
                geographic_basis="site_level_localities",
            )

    def test_normalize_chronology_text_parses_bp_and_calendar_ranges(self) -> None:
        bp_window = normalize_chronology_text(
            "1200-1500 BP", dating_basis="radiocarbon"
        )
        bp_point = normalize_chronology_text("5500 BP", dating_basis="radiocarbon")
        cal_bce = normalize_chronology_text(
            "803-425 calBCE (2562±47 BP)",
            dating_basis="mixed_radiocarbon_and_archaeological_context",
        )
        vague = normalize_chronology_text(
            "Late Bronze Age",
            dating_basis="archaeological_period",
        )

        self.assertEqual((bp_window.time_start_bp, bp_window.time_end_bp), (1200, 1500))
        self.assertEqual((bp_point.time_start_bp, bp_point.time_end_bp), (5500, 5500))
        self.assertEqual(cal_bce.time_start_bp, 2374)
        self.assertEqual(cal_bce.time_end_bp, 2752)
        self.assertIsNone(vague.time_start_bp)
        self.assertEqual(vague.dating_basis, "archaeological_period")

    def test_normalize_chronology_text_refuses_censored_bounds(self) -> None:
        for source_text in (
            ">49900 BP",
            ">=49900 BP",
            "≥49900 BP",
            "<1200 BP",
            "<=1200 BP",
            "≤1200 BP",
        ):
            with self.subTest(source_text=source_text):
                chronology = normalize_chronology_text(
                    source_text,
                    dating_basis="radiocarbon",
                )
                self.assertEqual(chronology.original_text, source_text)
                self.assertIsNone(chronology.time_start_bp)
                self.assertIsNone(chronology.time_end_bp)
                self.assertIsNone(chronology.time_mean_bp)

    def test_normalize_explicit_bp_window_refuses_inverted_ranges(self) -> None:
        chronology = normalize_explicit_bp_window(
            1200,
            1500,
            original_text="1200-1500 BP",
        )

        self.assertEqual(chronology.time_mean_bp, 1350)
        with self.assertRaisesRegex(ValueError, "younger-to-older"):
            normalize_explicit_bp_window(1500, 1200, original_text="1500-1200 BP")
