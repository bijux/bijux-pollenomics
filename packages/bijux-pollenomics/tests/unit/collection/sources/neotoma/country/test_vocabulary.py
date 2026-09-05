from __future__ import annotations

import unittest

from bijux_pollenomics.collection.sources.neotoma.relational.country import (
    country_attribution,
    country_code,
)
from bijux_pollenomics.collection.spatial import CountryAttributionDecision


class NeotomaCountryVocabularyTests(unittest.TestCase):
    def test_country_codes_and_names_are_case_insensitive(self) -> None:
        expected_codes = {
            "se": "SE",
            " Se ": "SE",
            "SWEDEN": "SE",
            "denmark": "DK",
            "NORWAY": "NO",
            "Finland": "FI",
            "unknown": "UNASSIGNED",
        }

        for value, expected in expected_codes.items():
            with self.subTest(value=value):
                self.assertEqual(country_code(value), expected)

    def test_assigned_boundary_name_casing_does_not_block_propagation(self) -> None:
        decision = CountryAttributionDecision(
            derived_country="sweden",
            decision_status="assigned",
            decision_method="strict_boundary_containment",
            ambiguity_reason=None,
            refusal_reason=None,
            raw_country="SWEDEN",
            raw_country_comparison="agrees",
            candidate_countries=("sweden",),
            boundary_artifact_digest="sha256:boundary-fixture",
            boundary_version="boundary-fixture-v1",
        )

        attribution = country_attribution(decision)

        self.assertEqual(attribution.final_country_code, "SE")
        self.assertTrue(attribution.propagation_eligible)


if __name__ == "__main__":
    unittest.main()
