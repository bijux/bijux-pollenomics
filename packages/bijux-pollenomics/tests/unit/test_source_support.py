from __future__ import annotations

import unittest

from bijux_pollenomics.data_downloader.source_support import build_source_support_matrix


class SourceSupportUnitTests(unittest.TestCase):
    def test_source_support_matrix_reports_status_and_coverage(self) -> None:
        matrix = build_source_support_matrix()

        self.assertEqual(len(matrix), 6)
        self.assertEqual(matrix[0].source, "aadr")
        self.assertEqual(matrix[0].support_status, "implemented")
        raa_row = [row for row in matrix if row.source == "raa"][0]
        self.assertEqual(raa_row.country_coverage, ("Sweden",))


if __name__ == "__main__":
    unittest.main()
