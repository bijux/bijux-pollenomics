"""Refuse science/type/source mutations while allowing only exact current code-origin rows."""

import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).absolute().parent))
from comparison import (
    compare_report,  # noqa: E402 - isolated script imports owned helper.
)


class ComparisonBoundary(unittest.TestCase):
    def fixture(self):
        original = {
            "repository_code_inputs": [
                {"path": "old-owner.py", "sha256": "a" * 64, "bytes": 4}
            ],
            "counts": [0, 3],
            "score": 0.125,
            "source": {"refusal": False, "unknown": None},
        }
        code = [{"path": "actual-owner.py", "sha256": "b" * 64, "bytes": 8}]
        current = copy.deepcopy(original)
        current["repository_code_inputs"] = copy.deepcopy(code)
        return original, current, code

    def test_only_current_code_identity_allowed(self):
        original, current, code = self.fixture()
        compare_report("author-site-uncertainty", current, original, code)

    def test_changed_numeric_refused(self):
        original, current, code = self.fixture()
        current["score"] = 0.126
        with self.assertRaises(ValueError):
            compare_report("author-site-uncertainty", current, original, code)

    def test_zero_missing_distinction(self):
        original, current, code = self.fixture()
        current["counts"][0] = None
        with self.assertRaises(ValueError):
            compare_report("author-site-uncertainty", current, original, code)

    def test_integer_float_distinction(self):
        original, current, code = self.fixture()
        current["counts"][1] = 3.0
        with self.assertRaises(ValueError):
            compare_report("author-site-uncertainty", current, original, code)

    def test_code_identity_cannot_float(self):
        original, current, code = self.fixture()
        current["repository_code_inputs"][0]["sha256"] = "c" * 64
        with self.assertRaises(ValueError):
            compare_report("author-site-uncertainty", current, original, code)

    def test_source_refusal_preserved(self):
        original, current, code = self.fixture()
        current["source"]["refusal"] = True
        with self.assertRaises(ValueError):
            compare_report("author-site-uncertainty", current, original, code)

    def test_profile_noncode_inputs_are_not_waived(self):
        original = {
            "input_identities": [
                {"path": "author/counts.csv", "sha256": "a" * 64},
                {"path": "old.py", "sha256": "a" * 64},
            ],
            "value": 0.1,
        }
        current = copy.deepcopy(original)
        code = [{"path": "current.py", "sha256": "b" * 64}]
        current["input_identities"] = [
            copy.deepcopy(original["input_identities"][0]),
            *code,
        ]
        compare_report("author-site-profile-comparison", current, original, code)
        current["input_identities"][0]["sha256"] = "c" * 64
        with self.assertRaises(ValueError):
            compare_report("author-site-profile-comparison", current, original, code)

    def test_axis_reordering_refused(self):
        original, current, code = self.fixture()
        original["axis"] = ["oak", "pine"]
        current["axis"] = ["pine", "oak"]
        with self.assertRaises(ValueError):
            compare_report("author-site-uncertainty", current, original, code)


if __name__ == "__main__":
    unittest.main()
