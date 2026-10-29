"""Controlled provenance changes cannot hide scientific or source changes."""

from __future__ import annotations

import copy
import unittest

from contracts import compare, original_denominator


class SourceChainControls(unittest.TestCase):
    def test_exact_source_null_zero_false(self):
        self.assertEqual(
            compare(
                {"zero": 0, "missing": None, "flag": False},
                {"zero": 0, "missing": None, "flag": False},
                {},
            ),
            [],
        )

    def test_undeclared_science_and_provenance_refuse(self):
        for value in (1, None, False, 0.0, "0"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                compare({"value": value}, {"value": 0}, {})

    def test_only_bound_exact_named_hash_leaf_changes(self):
        original = {
            "source_sha256": "a" * 64,
            "prediction_identity": "b" * 64,
            "value": 0,
        }
        actual = dict(original, prediction_identity="c" * 64)
        rows = compare(actual, original, {("prediction_identity",): "c" * 64})
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["path"], "/prediction_identity")
        with self.assertRaises(ValueError):
            compare(
                dict(actual, source_sha256="d" * 64),
                original,
                {("prediction_identity",): "c" * 64},
            )

    def test_unjoined_hash_even_on_named_leaf_refuses(self):
        with self.assertRaises(ValueError):
            compare(
                {"identity": "a" * 64},
                {"identity": "b" * 64},
                {("identity",): "c" * 64},
            )

    def test_invalid_hash_type_refuses(self):
        for value in (None, 0, False, "text"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                compare(
                    {"identity": value},
                    {"identity": "a" * 64},
                    {("identity",): "c" * 64},
                )

    def test_ordered_identity_and_numerical_rows_preserved(self):
        original = [
            {"sample": "first", "value": 0},
            {"sample": "second", "value": None},
        ]
        with self.assertRaises(ValueError):
            compare(list(reversed(original)), original, {})
        with self.assertRaises(ValueError):
            compare([*original, original[0]], original, {})

    def test_missing_extra_keys_refuse(self):
        for actual in ({}, {"a": 1, "b": 2}):
            with self.subTest(actual=actual), self.assertRaises(ValueError):
                compare(actual, {"a": 1}, {})

    def test_nonfinite_never_admitted(self):
        for value in (float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                compare(value, value, {})

    def test_nested_named_hash_changes_enumerated_by_actual_row(self):
        old = {
            "rows": [
                {"target": "first", "prediction_identity": "a" * 64},
                {"target": "second", "prediction_identity": "b" * 64},
            ]
        }
        new = copy.deepcopy(old)
        new["rows"][1]["prediction_identity"] = "c" * 64
        changes = compare(new, old, {("rows", "1", "prediction_identity"): "c" * 64})
        self.assertEqual(changes[0]["path"], "/rows/1/prediction_identity")
        new["rows"][0]["prediction_identity"] = "d" * 64
        with self.assertRaises(ValueError):
            compare(new, old, {("rows", "1", "prediction_identity"): "c" * 64})

    def baseline(self):
        return {
            "author_target_count": 31,
            "model_target_count": 30,
            "original_count_denominator": 20732,
            "excluded_taxon_nisp": 159,
            "requested_folds": 15,
            "predicted_folds": 14,
            "refused_folds": 1,
            "training_items_completed": 192,
            "training_items_refused": 3,
            "predicted_method_rows": 42,
            "scored_method_rows": 42,
            "refused_site": "author:BECKHAM",
            "measured_vegetation_accuracy": None,
        }

    def test_original_refused_fold_is_preserved(self):
        original_denominator(self.baseline())

    def test_dropped_refusal_and_promoted_count_refuse(self):
        for changes in (
            {"refused_folds": 0},
            {"predicted_folds": 15},
            {"training_items_completed": 195},
            {"training_items_refused": 0},
            {"refused_site": "another"},
            {"measured_vegetation_accuracy": 0},
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                original_denominator(self.baseline() | changes)

    def test_count_scalar_type_is_exact(self):
        with self.assertRaises(ValueError):
            original_denominator(self.baseline() | {"refused_folds": True})
        with self.assertRaises(ValueError):
            original_denominator(self.baseline() | {"training_items_refused": 3.0})


if __name__ == "__main__":
    unittest.main()
