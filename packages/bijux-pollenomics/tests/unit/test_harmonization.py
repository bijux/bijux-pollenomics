from __future__ import annotations

import unittest

from bijux_pollenomics.analysis import HarmonizationRule, default_harmonization_rules


class HarmonizationUnitTests(unittest.TestCase):
    def test_default_harmonization_rules_are_ordered_and_provenance_required(self) -> None:
        rules = default_harmonization_rules()

        self.assertIsInstance(rules, tuple)
        self.assertTrue(all(isinstance(rule, HarmonizationRule) for rule in rules))
        self.assertEqual(
            [rule.layer for rule in rules],
            ["aadr_context", "archaeology", "paleoclimate", "pollen"],
        )
        self.assertTrue(all(rule.provenance_required for rule in rules))


if __name__ == "__main__":
    unittest.main()
