"""Pure comparison controls read retained numbers; they execute no forward model."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from contracts import qualify_outputs, typed_equal, validate_pin_population
from prepare import output_path

R = Path(__file__).absolute().parents[3]
D = Path(__file__).absolute().parent
ROOT = R / "docs/report/pollen-reconstruction/author-lra-constrained/radius-sensitivity"
WORK = R / "artifacts/science/current-constrained-author-complete-source/retained-work"


def fixture():
    old = json.loads((ROOT / "frozen/predictions.json").read_bytes())
    old_report = json.loads((ROOT / "scored/report.json").read_bytes())
    scores = (ROOT / "scored/scores.csv").read_bytes()
    original_rows = json.loads((WORK / "predictions/predictions.json").read_bytes())
    source = {key: hashlib.sha256(key.encode()).hexdigest() for key in old["source"]}
    current = deepcopy(old)
    current["source"] = source
    by_key = {(r["fold_id"], r["record_id"], r["baseline"]): r for r in original_rows}
    for row in current["rows"]:
        row["published_prediction_sha256"] = by_key[
            row["fold_id"], row["record_id"], row["method"]
        ]["prediction_manifest_sha256"]
    report = deepcopy(old_report)
    report["source"] = source
    report["prediction_freeze_sha256"] = "f" * 64
    return [
        current,
        report,
        scores,
        old,
        old_report,
        scores,
        source,
        original_rows,
        "f" * 64,
    ]


class Contracts(unittest.TestCase):
    def test_full_retained_projection_only(self):
        review = qualify_outputs(*fixture())
        self.assertEqual(review["frozen_rows"], 126)
        self.assertEqual(review["training_refused"], 3)

    def test_numeric_delta_refused(self):
        args = fixture()
        pollen = args[0]["rows"][0]["pollen_fraction"]
        pollen[next(iter(pollen))] += 0.01
        with self.assertRaises(AssertionError):
            qualify_outputs(*args)

    def test_null_to_zero_refused(self):
        self.assertFalse(typed_equal(None, 0))
        self.assertFalse(typed_equal(True, 1))
        self.assertFalse(typed_equal(1, 1.0))

    def test_factor_or_support_hull_refused(self):
        args = fixture()
        args[0]["rows"][0]["radius_factor"] = 0.7
        with self.assertRaises(AssertionError):
            qualify_outputs(*args)

    def test_missing_record_refused(self):
        args = fixture()
        args[0]["rows"].pop()
        with self.assertRaises(AssertionError):
            qualify_outputs(*args)

    def test_duplicate_record_refused(self):
        args = fixture()
        args[0]["rows"][1] = deepcopy(args[0]["rows"][0])
        with self.assertRaises(AssertionError):
            qualify_outputs(*args)

    def test_refusal_cannot_be_erased(self):
        args = fixture()
        args[1]["refused_site"] = None
        with self.assertRaises(AssertionError):
            qualify_outputs(*args)

    def test_report_metric_delta_refused(self):
        args = fixture()
        args[1]["site_macro"][0]["site_macro_mae_fraction"] += 0.01
        with self.assertRaises(AssertionError):
            qualify_outputs(*args)

    def test_csv_wire_delta_refused(self):
        args = fixture()
        args[2] = args[2].replace(b"\n", b"\r\n")
        with self.assertRaises(AssertionError):
            qualify_outputs(*args)

    def test_prediction_identity_delta_refused(self):
        args = fixture()
        args[0]["rows"][0]["published_prediction_sha256"] = "0" * 64
        with self.assertRaises(AssertionError):
            qualify_outputs(*args)

    def test_actual_model_population_cannot_expand(self):
        args = fixture()
        args[7].append(deepcopy(args[7][0]))
        with self.assertRaises(AssertionError):
            qualify_outputs(*args)

    def test_temporal_or_scientific_array_order_not_erased(self):
        args = fixture()
        args[0]["rows"].reverse()
        with self.assertRaises(AssertionError):
            qualify_outputs(*args)

    def test_exact_sealed_original_pin_population(self):
        from custody import validate_original_pin_population

        path = (
            R / "artifacts/science/current-constrained-author-complete-source/plan.json"
        )
        self.assertEqual(
            hashlib.sha256(path.read_bytes()).hexdigest(),
            "7a75256e79a577280d8bd828380ebb8438b80914e3aa8c5ddc390fa428e6428c",
        )
        pins = json.loads(path.read_bytes())["input_pins"]
        validate_original_pin_population(pins)
        with self.assertRaises(AssertionError):
            validate_original_pin_population(pins[:-1])

    def test_custody_order_is_not_scientific_order(self):
        rows = [
            {"path": "/a", "sha256": "a" * 64, "bytes": 1},
            {"path": "/a-b", "sha256": "b" * 64, "bytes": 2},
        ]
        validate_pin_population(rows, list(reversed(rows)))
        with self.assertRaises(AssertionError):
            validate_pin_population(rows, [rows[0], rows[0]])
        changed = deepcopy(rows)
        changed[1]["sha256"] = "c" * 64
        with self.assertRaises(AssertionError):
            validate_pin_population(rows, changed)
        changed = deepcopy(rows)
        changed[0]["bytes"] = True
        with self.assertRaises(AssertionError):
            validate_pin_population(rows, changed)

    def test_output_must_be_new_and_confined(self):
        preflight = D / "preflight"
        with tempfile.TemporaryDirectory(dir=preflight) as name:
            root = Path(name)
            self.assertEqual(output_path(root / "comparison"), root / "comparison")
            with self.assertRaises(AssertionError):
                output_path(root)
            with self.assertRaises(AssertionError):
                output_path(root / ".." / "escape")
            (root / "link").symlink_to(root, target_is_directory=True)
            with self.assertRaises(AssertionError):
                output_path(root / "link" / "comparison")


if __name__ == "__main__":
    unittest.main()
