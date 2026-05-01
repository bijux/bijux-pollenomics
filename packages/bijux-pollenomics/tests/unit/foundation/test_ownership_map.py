from __future__ import annotations

import unittest

from bijux_pollenomics.foundation import OwnershipMapEntry, build_ownership_map


class OwnershipMapUnitTests(unittest.TestCase):
    def test_ownership_map_covers_data_ranking_and_publication(self) -> None:
        ownership = build_ownership_map()

        self.assertTrue(all(isinstance(entry, OwnershipMapEntry) for entry in ownership))
        concerns = {entry.concern for entry in ownership}
        self.assertEqual(
            concerns,
            {
                "source_data_logic",
                "candidate_ranking_logic",
                "publication_logic",
            },
        )


if __name__ == "__main__":
    unittest.main()
