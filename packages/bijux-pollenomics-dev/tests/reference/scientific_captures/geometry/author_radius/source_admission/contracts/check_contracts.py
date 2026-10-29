"""Exercise exact retained scientific guards without running the paired producer."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
from typing import Any
import unittest

from contracts import (
    EXPECTED,
    PRODUCER_SHA,
    qualify_pairs,
    source_identity_only,
    typed_equal,
)
from custody import A, B, R, output_path, validate_terminal
from prepare import BASE, FAMILY, NAME


def fixture() -> list[Any]:
    root = R / FAMILY
    old = json.loads((root / "radius-sensitivity/paired/report.json").read_bytes())
    report = deepcopy(old)
    report["source_sha256"] = EXPECTED
    report["producer_sha256"] = PRODUCER_SHA
    scores = (root / "radius-sensitivity/paired/paired-scores.csv").read_bytes()
    return [
        report,
        old,
        scores,
        scores,
        (B / "scored/scores.csv").read_bytes(),
        (root / "direct-pollen/matched-scores.csv").read_bytes(),
        json.loads((root / "direct-pollen/paired-hellinger.json").read_bytes()),
    ]


class Contracts(unittest.TestCase):
    def test_complete_retained_source_joins(self) -> None:
        result = qualify_pairs(*fixture())
        self.assertEqual(result["paired_rows"], 126)
        self.assertFalse(result["new_fit_forward_R_or_optimizer_executed"])

    def test_exact_three_identity_literals_only(self) -> None:
        import subprocess

        original = subprocess.check_output(["git", "show", BASE + ":" + NAME], cwd=R)
        proposed = (A / "proposal" / NAME).read_bytes()
        source_identity_only(original, proposed)
        with self.assertRaises(AssertionError):
            source_identity_only(original, proposed.replace(b"1e-15", b"1e-14"))

    def test_stale_source_hash_refused(self) -> None:
        args = fixture()
        args[0]["source_sha256"] = args[1]["source_sha256"]
        with self.assertRaises(AssertionError):
            qualify_pairs(*args)

    def test_changed_metric_refused(self) -> None:
        args = fixture()
        args[0]["summary"][0]["direct_mae_fraction"] += 0.001
        with self.assertRaises(AssertionError):
            qualify_pairs(*args)

    def test_boolean_count_refused(self) -> None:
        args = fixture()
        args[0]["matched_sites"] = True
        with self.assertRaises(AssertionError):
            qualify_pairs(*args)

    def test_summary_order_refused(self) -> None:
        args = fixture()
        args[0]["summary"].reverse()
        with self.assertRaises(AssertionError):
            qualify_pairs(*args)

    def test_missing_paired_population_refused(self) -> None:
        args = fixture()
        args[0]["paired_rows"] = 125
        with self.assertRaises(AssertionError):
            qualify_pairs(*args)

    def test_csv_spelling_refused(self) -> None:
        args = fixture()
        args[2] = args[2].replace(b"\n", b"\r\n")
        with self.assertRaises(AssertionError):
            qualify_pairs(*args)

    def test_observation_native_identity_refused(self) -> None:
        args = fixture()
        args[6]["site_method_rows"][0]["target_raw_sha256"] = "0" * 64
        with self.assertRaises(AssertionError):
            qualify_pairs(*args)

    def test_prediction_native_identity_refused(self) -> None:
        args = fixture()
        args[6]["site_method_rows"][0]["lra_prediction_identity"] = "0" * 64
        with self.assertRaises(AssertionError):
            qualify_pairs(*args)

    def test_null_numeric_type_not_conflated(self) -> None:
        for left, right in [(None, 0), (1, 1.0), (True, 1)]:
            self.assertFalse(typed_equal(left, right))

    def test_actual_terminal_boolean_exit_refused(self) -> None:
        plan, terminal, outer = [
            json.loads((B / n).read_bytes())
            for n in ["plan.json", "terminal.json", "radius-terminal.json"]
        ]
        validate_terminal(plan, terminal, outer)
        terminal["stages"][0]["actual_exit"] = False
        with self.assertRaises(AssertionError):
            validate_terminal(plan, terminal, outer)

    def test_actual_native_argv_refused(self) -> None:
        plan, terminal, outer = [
            json.loads((B / n).read_bytes())
            for n in ["plan.json", "terminal.json", "radius-terminal.json"]
        ]
        terminal["stages"][0]["argv"].append("--unsafe")
        with self.assertRaises(AssertionError):
            validate_terminal(plan, terminal, outer)

    def test_output_traversal_and_existing_refused(self) -> None:
        for path in [A, A / "child/../../escaped"]:
            with self.assertRaises(AssertionError):
                output_path(path)

    def test_output_symlink_ancestor_refused(self) -> None:
        with tempfile.TemporaryDirectory(dir=A / "preflight") as raw:
            root = Path(raw)
            (root / "target").mkdir()
            (root / "alias").symlink_to(root / "target", target_is_directory=True)
            with self.assertRaises(AssertionError):
                output_path(root / "alias/out")


if __name__ == "__main__":
    unittest.main()
