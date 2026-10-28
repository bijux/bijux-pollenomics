"""Preserve original source/count types, ordering and declared CSV wire projection."""

import unittest

from comparison import exact, exact_csv


class HoldoutBoundary(unittest.TestCase):
    def test_csv_original_projection(self):
        exact_csv(b"site,count\r\nA,0\r\n", b"site,count\nA,0\n")

    def test_csv_missing_not_zero(self):
        with self.assertRaises(ValueError):
            exact_csv(b"site,count\nA,\n", b"site,count\nA,0\n")

    def test_csv_count_not_float_spelling(self):
        with self.assertRaises(ValueError):
            exact_csv(b"site,count\nA,0.0\n", b"site,count\nA,0\n")

    def test_csv_site_order_exact(self):
        with self.assertRaises(ValueError):
            exact_csv(b"A,2\nB,1\n", b"B,1\nA,2\n")

    def test_json_zero_missing_refused(self):
        with self.assertRaises(ValueError):
            exact({"count": None}, {"count": 0})

    def test_json_bool_integer_refused(self):
        with self.assertRaises(ValueError):
            exact({"refused": False}, {"refused": 0})

    def test_json_fraction_exact(self):
        exact({"score": [0.125, None]}, {"score": [0.125, None]})
        with self.assertRaises(ValueError):
            exact({"score": [0.126, None]}, {"score": [0.125, None]})

    def test_json_taxon_axis_order(self):
        with self.assertRaises(ValueError):
            exact(["oak", "pine"], ["pine", "oak"])


if __name__ == "__main__":
    unittest.main()
