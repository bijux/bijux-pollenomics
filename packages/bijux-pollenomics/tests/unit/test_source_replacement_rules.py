from __future__ import annotations

import unittest

from bijux_pollenomics.data_downloader.source_replacement_rules import (
    build_source_replacement_rules,
)


class SourceReplacementRulesUnitTests(unittest.TestCase):
    def test_build_source_replacement_rules_marks_destructive_refresh(self) -> None:
        rules = build_source_replacement_rules(
            selected_sources=("neotoma",),
            source_output_roots={"neotoma": "/tmp/data/neotoma"},
        )

        self.assertIn("neotoma", rules)
        self.assertTrue(rules["neotoma"].destructive_refresh)
        self.assertTrue(rules["neotoma"].preserves_previous_on_failure)
        self.assertEqual(rules["neotoma"].refresh_mode, "staging_swap")
        self.assertEqual(rules["neotoma"].final_output_root, "/tmp/data/neotoma")
        self.assertEqual(rules["neotoma"].staging_output_root, "/tmp/data/.neotoma.tmp")


if __name__ == "__main__":
    unittest.main()
