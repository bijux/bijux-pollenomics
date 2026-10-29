"""Independently admit the finite retrospective BECKHAM pollen diagnostic."""

from __future__ import annotations

import hashlib
import math
from typing import Any

from ...contracts import ReportRebuildError

METHODS = ("training_mean", "nearest_site", "inverse_distance_squared")
TARGET = "author:BECKHAM"


def _require(condition: object, reason: str) -> None:
    if not condition:
        raise ReportRebuildError("BECKHAM fixed-start " + reason)


def _object(value: object) -> dict[str, Any]:
    _require(type(value) is dict, "object required")
    assert isinstance(value, dict)
    return value


def _number(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _close(actual: object, expected: float) -> bool:
    return (
        isinstance(actual, (int, float))
        and not isinstance(actual, bool)
        and math.isfinite(actual)
        and math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12)
    )


def _composition(value: object) -> dict[str, float]:
    row = _object(value)
    _require(
        len(row) == 30
        and all(type(key) is str and key for key in row)
        and all(_number(x) and 0 <= x <= 1 for x in row.values())
        and abs(math.fsum(row.values()) - 1) <= 1e-9,
        "closed thirty-taxon fractions required",
    )
    return {key: float(x) for key, x in row.items()}


def validate_prediction_freeze(raw: bytes, pin: dict[str, Any]) -> None:
    """Bind scoring to the exact prediction bytes committed before outcome access."""
    _require(
        type(pin.get("bytes")) is int
        and pin["bytes"] == len(raw)
        and pin.get("sha256") == hashlib.sha256(raw).hexdigest(),
        "frozen prediction bytes differ",
    )


def validate_pollen_scores(
    predictions: list[dict[str, Any]],
    scores: list[dict[str, Any]],
    observed_counts: dict[str, Any],
    *,
    target: str = TARGET,
) -> dict[str, Any]:
    """Recompute descriptive count-conditioned metrics without importing the model."""
    _require(
        len(predictions) == len(scores) == 3
        and {row.get("baseline") for row in predictions} == set(METHODS)
        and {row.get("baseline") for row in scores} == set(METHODS),
        "exact three predeclared spatial methods required",
    )
    _require(
        len(observed_counts) == 30
        and all(type(x) is int and x >= 0 for x in observed_counts.values()),
        "original thirty-taxon integer counts required",
    )
    total = sum(observed_counts.values())
    _require(0 < total <= 2**53, "positive exactly representable count total required")
    by_method = {row["baseline"]: row for row in scores}
    independent = []
    for row in predictions:
        _require(row.get("record_id") == target, "prediction target differs")
        predicted = _composition(row.get("pollen_fraction"))
        _require(set(predicted) == set(observed_counts), "scoring taxon axis differs")
        errors = {
            key: predicted[key] - observed_counts[key] / total
            for key in sorted(predicted)
        }
        values = list(errors.values())
        impossible = any(
            observed_counts[key] > 0 and predicted[key] == 0 for key in predicted
        )
        deviance = (
            None
            if impossible
            else max(
                0.0,
                2
                * math.fsum(
                    observed_counts[key]
                    * (
                        math.log(observed_counts[key] / total)
                        - math.log(predicted[key])
                    )
                    for key in predicted
                    if observed_counts[key] > 0
                ),
            )
        )
        expected = {
            "mae_fraction": math.fsum(abs(x) for x in values) / 30,
            "rmse_fraction": math.sqrt(math.fsum(x * x for x in values) / 30),
            "bias_fraction": math.fsum(values) / 30,
            "total_variation": math.fsum(abs(x) for x in values) / 2,
        }
        scored = by_method[row["baseline"]]
        _require(scored.get("record_id") == target, "score target differs")
        score = scored
        _require(
            score.get("target") == "pollen_composition"
            and score.get("status") == "scored"
            and type(score.get("taxon_count")) is int
            and score["taxon_count"] == 30
            and type(score.get("scored_taxon_count")) is int
            and score["scored_taxon_count"] == 30
            and score.get("missing_observed_taxa") == []
            and type(score.get("observed_total_count")) is int
            and score["observed_total_count"] == total
            and type(score.get("zero_probability_positive_count")) is bool
            and score["zero_probability_positive_count"] is impossible,
            "score denominator, status or impossible-probability flag differs",
        )
        _require(
            all(_close(score.get(key), value) for key, value in expected.items()),
            "saved descriptive metrics differ from independent arithmetic",
        )
        _require(
            score.get("count_conditioned_deviance") is None
            if deviance is None
            else _close(score.get("count_conditioned_deviance"), deviance),
            "count-conditioned deviance differs",
        )
        signed = score.get("signed_error_by_taxon")
        _require(
            type(signed) is list
            and len(signed) == 30
            and all(
                type(pair) is list
                and len(pair) == 2
                and pair[0] == key
                and _close(pair[1], error)
                for pair, (key, error) in zip(signed, errors.items(), strict=True)
            ),
            "signed per-taxon errors differ",
        )
        independent.append(
            {"baseline": row["baseline"], **expected, "deviance": deviance}
        )
    return {"observed_total_count": total, "scores": independent}
