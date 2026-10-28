"""Keep upstream metadata substitutions confined to authenticated exact doc rows."""

import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).absolute().parent))
from comparison import compare_report  # noqa: E402
from custody import PREFIX, document_inputs  # noqa: E402


class DocumentationEpochs(unittest.TestCase):
    def setUp(self):
        self.code = [{"path": "current.py", "bytes": 9, "sha256": "b" * 64}]
        self.documents = [
            {"path": PREFIX + "report.json", "bytes": 12, "sha256": "c" * 64},
            {"path": PREFIX + "draws.json", "bytes": 20, "sha256": "d" * 64},
        ]
        self.original = {
            "input_identities": [
                {"path": PREFIX + "report.json", "bytes": 12, "sha256": "a" * 64},
                copy.deepcopy(self.documents[1]),
                {"path": "author/counts.csv", "bytes": 5, "sha256": "e" * 64},
                {"path": "old.py", "bytes": 6, "sha256": "f" * 64},
            ],
            "value": 0,
            "unknown": None,
        }
        self.current = copy.deepcopy(self.original)
        self.current["input_identities"] = [
            *copy.deepcopy(self.documents),
            copy.deepcopy(self.original["input_identities"][2]),
            *copy.deepcopy(self.code),
        ]

    def compare(self):
        compare_report(
            "author-site-profile-comparison",
            self.current,
            self.original,
            self.code,
            self.documents,
        )

    def test_exact_current_document_epoch(self):
        self.compare()

    def test_unapproved_document_sha(self):
        self.current["input_identities"][0]["sha256"] = "9" * 64
        with self.assertRaises(ValueError):
            self.compare()

    def test_unapproved_document_type(self):
        self.current["input_identities"][0]["bytes"] = 12.0
        with self.assertRaises(ValueError):
            self.compare()

    def test_private_source_never_waived(self):
        self.current["input_identities"][2]["sha256"] = "9" * 64
        with self.assertRaises(ValueError):
            self.compare()

    def test_scientific_zero_never_waived(self):
        self.current["value"] = None
        with self.assertRaises(ValueError):
            self.compare()

    def test_duplicate_document_refused(self):
        self.documents[1] = copy.deepcopy(self.documents[0])
        with self.assertRaises(ValueError):
            self.compare()

    def test_arbitrary_document_refused(self):
        self.documents[0]["path"] = "docs/other.json"
        with self.assertRaises(ValueError):
            self.compare()

    def test_missing_document_refused(self):
        self.documents.pop()
        with self.assertRaises(ValueError):
            self.compare()

    def test_actual_recovered_epoch_and_current_physical_docs(self):
        controls = Path(__file__).absolute().parent
        rows, bridge = document_inputs(controls.parents[2], controls)
        self.assertEqual(len(rows), 2)
        self.assertIs(bridge["all_scientific_typed_values_exact"], True)
        self.assertEqual(
            bridge["original_report"]["sha256"],
            "415185927514de10a71b6a7ba6c26d7bc1fd3ed8cc140760ec2e3e9f58f1c243",
        )


if __name__ == "__main__":
    unittest.main()
