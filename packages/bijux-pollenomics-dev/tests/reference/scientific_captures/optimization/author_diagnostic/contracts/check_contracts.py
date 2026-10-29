"""Ensure complete diagnostics cannot silently change acceptance or scalar meaning."""

import copy
import json
from pathlib import Path
import unittest

from contracts import refusal_contract, typed_equal

R = Path(__file__).absolute().parents[3]
G = (
    R
    / "docs/report/pollen-reconstruction/author-lra-constrained/optimizer-gradient/report.json"
)
F = (
    R
    / "docs/report/pollen-reconstruction/author-lra-optimized-feasibility/finite-candidate.json"
)


class OriginalDiagnosticGuards(unittest.TestCase):
    def setUp(self):
        self.gradient = json.loads(G.read_bytes())
        self.finite = json.loads(F.read_bytes())

    def test_actual_original_reports(self):
        refusal_contract(self.gradient, self.finite)
        typed_equal(copy.deepcopy(self.gradient), self.gradient)
        typed_equal(copy.deepcopy(self.finite), self.finite)

    def test_false_not_zero(self):
        with self.assertRaises(ValueError):
            typed_equal({"converged": 0}, {"converged": False})

    def test_zero_not_null(self):
        with self.assertRaises(ValueError):
            typed_equal({"score": None}, {"score": 0})

    def test_integer_not_float(self):
        with self.assertRaises(ValueError):
            typed_equal({"count": 3.0}, {"count": 3})

    def test_single_numeric_leaf_changed(self):
        value = copy.deepcopy(self.finite)
        value["rows"][0]["optimizer"]["fun"] += 1e-12
        with self.assertRaises(ValueError):
            typed_equal(value, self.finite)

    def test_removed_and_added_leaves_refused(self):
        for value in ({"a": 0}, {"a": 0, "b": None, "new": False}):
            with self.assertRaises(ValueError):
                typed_equal(value, {"a": 0, "b": None})

    def test_missing_ring_refused(self):
        self.gradient["items"][0]["rings"].pop()
        with self.assertRaises(ValueError):
            refusal_contract(self.gradient, self.finite)

    def test_new_prediction_or_fold_acceptance_refused(self):
        for key, value in (
            ("held_out_prediction_count", 1),
            ("beckham_fold_status", "complete"),
        ):
            gradient = copy.deepcopy(self.gradient)
            gradient[key] = value
            with self.assertRaises(ValueError):
                refusal_contract(gradient, self.finite)

    def test_convergence_cannot_be_truthy_zero(self):
        self.finite["all_optimizers_converged"] = 0
        with self.assertRaises(ValueError):
            refusal_contract(self.gradient, self.finite)

    def test_nonfinite_not_waived(self):
        for value in (float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                typed_equal(value, value)


if __name__ == "__main__":
    unittest.main()
