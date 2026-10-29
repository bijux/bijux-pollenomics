"""Exact diagnostic replay preserves failures and scientific scalar types."""

from __future__ import annotations

import math
from typing import Any


def typed_equal(actual: Any, expected: Any, location: str = "") -> None:
    if type(actual) is not type(expected):
        raise ValueError(f"Scalar/container type changed at {location}")
    if isinstance(expected, dict):
        if actual.keys() != expected.keys():
            raise ValueError(f"Object membership changed at {location}")
        for key in expected:
            typed_equal(actual[key], expected[key], location + "/" + str(key))
    elif isinstance(expected, list):
        if len(actual) != len(expected):
            raise ValueError(f"Array membership changed at {location}")
        for index, (a, e) in enumerate(zip(actual, expected, strict=True)):
            typed_equal(a, e, location + "/" + str(index))
    elif isinstance(expected, float) and not math.isfinite(expected):
        raise ValueError(f"Nonfinite diagnostic at {location}")
    elif actual != expected:
        raise ValueError(
            f"Diagnostic value changed at {location}: {actual!r} != {expected!r}"
        )


def refusal_contract(gradient: dict[str, Any], finite: dict[str, Any]) -> None:
    if (
        gradient.get("schema_version") != "author-love-analytic-gradient-diagnostic.v1"
        or gradient.get("beckham_fold_status") != "refused"
        or type(gradient.get("held_out_prediction_count")) is not int
        or gradient["held_out_prediction_count"] != 0
        or gradient.get("training_items_required") != 3
        or gradient.get("training_items_converged") != 1
        or finite.get("schema_version") != "author-love-finite-candidate-diagnostic.v1"
        or finite.get("all_optimizers_converged") is not False
        or finite.get("taxa") != 30
        or finite.get("original_count_denominator") != 20732
        or finite.get("excluded_filipendula_counts") != 159
    ):
        raise ValueError("Retained diagnostic refusal/denominator contract changed")
    items = gradient.get("items")
    if (
        not isinstance(items, list)
        or {r.get("item_id") for r in items}
        != {"author:CUTHILL2", "author:HANGINGS", "author:LONGBREACH"}
        or len(items) != 3
    ):
        raise ValueError("Exact three training item membership required")
    for item in items:
        if len(item["rings"]) != 2 or any(
            r["baseline_reproduced"] is not True for r in item["rings"]
        ):
            raise ValueError("Both ring baselines must reproduce")
    if len(finite.get("rows", [])) != 2 or any(
        r["optimizer"]["success"] is not False for r in finite["rows"]
    ):
        raise ValueError("Both finite candidate convergence refusals must remain")
