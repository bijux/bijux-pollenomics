"""Falsify unsupported hotspot claims without running numerical workloads."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from boundary import assess
from storage import destination, write_json
from workloads import digest, normalized


class ProfileAdmission(unittest.TestCase):
    def result(self, **changes):
        arguments = {
            "baseline": [1.0] * 3,
            "passthrough": [1.0] * 3,
            "instrumented": [1.01] * 3,
            "inside": [0.75] * 3,
            "clock_cost": [0.001] * 3,
            "outputs_exact": True,
            "inputs_exact": True,
        }
        return assess(**(arguments | changes))

    def test_dominant_boundary_still_cannot_authorize_compile(self):
        result = self.result()
        self.assertIs(result["qualified_measured_hotspot"], True)
        self.assertIs(result["allows_compilation"], False)

    def test_below_half_refused(self):
        self.assertIs(
            self.result(inside=[0.49] * 3)["qualified_measured_hotspot"], False
        )

    def test_instrumentation_cost_refused(self):
        self.assertIs(
            self.result(instrumented=[1.1] * 3)["qualified_measured_hotspot"], False
        )

    def test_spread_not_best_repeat(self):
        self.assertIs(
            self.result(baseline=[1.0, 2.0, 3.0])["qualified_measured_hotspot"], False
        )

    def test_output_change_refused(self):
        self.assertIs(
            self.result(outputs_exact=False)["qualified_measured_hotspot"], False
        )

    def test_input_change_refused(self):
        self.assertIs(
            self.result(inputs_exact=False)["qualified_measured_hotspot"], False
        )

    def test_truthy_not_true(self):
        self.assertIs(self.result(outputs_exact=1)["qualified_measured_hotspot"], False)

    def test_boolean_timing_refused(self):
        with self.assertRaises(ValueError):
            self.result(baseline=[True, 1.0, 1.0])

    def test_null_timing_refused(self):
        with self.assertRaises(ValueError):
            self.result(inside=[None, 0.75, 0.75])

    def test_nonfinite_timing_refused(self):
        for bad in (float("nan"), float("inf"), -1.0):
            with self.assertRaises(ValueError):
                self.result(inside=[bad] * 3)

    def test_boundary_cannot_outgrow_public_call(self):
        with self.assertRaises(ValueError):
            self.result(inside=[2.0] * 3)

    def test_three_repeats_required(self):
        with self.assertRaises(ValueError):
            self.result(inside=[0.75])

    def test_zero_missing_and_boolean_are_distinct(self):
        self.assertEqual(len({digest([0]), digest([None]), digest([False])}), 3)

    def test_nonfinite_output_is_not_measured_zero(self):
        self.assertEqual(
            normalized([float("nan"), float("inf"), 0.0]),
            [{"nonfinite": "nan"}, {"nonfinite": "inf"}, 0.0],
        )


class ObservationStorage(unittest.TestCase):
    def setUp(self):
        parent = Path(__file__).absolute().parent / "source-preflight"
        parent.mkdir(exist_ok=True)
        self.space = tempfile.TemporaryDirectory(dir=parent)
        self.addCleanup(self.space.cleanup)
        self.root = Path(self.space.name)

    def test_exclusive_existing_output(self):
        path = self.root / "nested/result.json"
        write_json(self.root, path, {"zero": 0, "missing": None})
        with self.assertRaises(ValueError):
            write_json(self.root, path, {})
        self.assertIn('"zero": 0', path.read_text())
        self.assertIn('"missing": null', path.read_text())

    def test_traversal_refused_without_creation(self):
        with self.assertRaises(ValueError):
            destination(self.root, self.root / "unused/../escape.json")
        self.assertFalse((self.root / "unused").exists())

    def test_external_root_refused(self):
        with self.assertRaises(ValueError):
            destination(self.root, self.root.parent / "escape.json")

    def test_symlink_ancestor_refused(self):
        (self.root / "real").mkdir()
        (self.root / "alias").symlink_to(self.root / "real", target_is_directory=True)
        with self.assertRaises(ValueError):
            destination(self.root, self.root / "alias/result.json")
        self.assertFalse((self.root / "real/result.json").exists())


if __name__ == "__main__":
    unittest.main()
