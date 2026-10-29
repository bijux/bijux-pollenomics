"""Permit only explicitly authenticated provenance leaves in a scientific replay."""

from __future__ import annotations

import math
import re
from typing import Any

SHA = re.compile(r"[0-9a-f]{64}")


def compare(
    actual: Any,
    original: Any,
    bindings: dict[tuple[str, ...], str],
    path: tuple[str, ...] = (),
) -> list[dict[str, Any]]:
    if type(actual) is not type(original):
        raise ValueError(("scalar/container type changed", path))
    if path in bindings:
        expected = bindings[path]
        if (
            not isinstance(actual, str)
            or not SHA.fullmatch(actual)
            or not isinstance(original, str)
            or not SHA.fullmatch(original)
            or actual != expected
        ):
            raise ValueError(("declared provenance chain binding differs", path))
        return (
            []
            if actual == original
            else [
                {
                    "path": "/" + "/".join(path),
                    "original": original,
                    "actual": actual,
                    "authenticated_current_chain_value": expected,
                }
            ]
        )
    if isinstance(original, dict):
        if actual.keys() != original.keys():
            raise ValueError(("object membership changed", path))
        return [
            row
            for key in original
            for row in compare(actual[key], original[key], bindings, (*path, key))
        ]
    if isinstance(original, list):
        if len(actual) != len(original):
            raise ValueError(("ordered row membership changed", path))
        return [
            row
            for index, (a, b) in enumerate(zip(actual, original, strict=True))
            for row in compare(a, b, bindings, (*path, str(index)))
        ]
    if isinstance(original, float) and (
        not math.isfinite(original) or not math.isfinite(actual)
    ):
        raise ValueError(("nonfinite scientific value", path))
    if actual != original:
        raise ValueError(
            ("undeclared source/scientific/provenance value changed", path)
        )
    return []


def original_denominator(report: dict[str, Any]) -> None:
    required = {
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
    }
    if (
        any(
            type(report.get(key)) is not int or report[key] != value
            for key, value in required.items()
        )
        or report.get("refused_site") != "author:BECKHAM"
        or report.get("measured_vegetation_accuracy") is not None
    ):
        raise ValueError("Original complete study denominator/refusal changed")
