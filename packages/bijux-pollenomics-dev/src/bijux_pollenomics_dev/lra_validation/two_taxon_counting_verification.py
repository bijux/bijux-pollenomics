"""Verify saved intervals with Decimal binomial sums and root bisection."""

from __future__ import annotations

from decimal import Decimal, localcontext
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


def binomial_probabilities(total: int, probability: Decimal) -> list[Decimal]:
    if probability == 0:
        return [Decimal(1)] + [Decimal(0)] * total
    if probability == 1:
        return [Decimal(0)] * total + [Decimal(1)]
    complement = 1 - probability
    result = [complement**total]
    for count in range(total):
        result.append(
            result[-1] * (total - count) / (count + 1) * probability / complement
        )
    return result


def binomial_cdf(total: int, count: int, probability: Decimal) -> Decimal:
    if count < 0:
        return Decimal(0)
    if count >= total:
        return Decimal(1)
    if count > total // 2:
        return 1 - binomial_cdf(total, total - count - 1, 1 - probability)
    if probability in (0, 1):
        return Decimal(1) if probability == 0 else Decimal(0)
    complement = 1 - probability
    term = complement**total
    result = term
    for index in range(count):
        term *= Decimal(total - index) / (index + 1) * probability / complement
        result += term
    return result


def bounds(total: int, count: int, confidence: float) -> tuple[Decimal, Decimal]:
    tail = (1 - Decimal.from_float(confidence)) / 2
    result: list[Decimal] = []
    for upper in [False, True]:
        if count == (total if upper else 0):
            result.append(Decimal(1 if upper else 0))
            continue
        left, right = Decimal(0), Decimal(1)
        for _ in range(220):
            middle = (left + right) / 2
            if upper:
                # P_p(X <= k) decreases with p.
                if binomial_cdf(total, count, middle) > tail:
                    left = middle
                else:
                    right = middle
            elif 1 - binomial_cdf(total, count - 1, middle) < tail:
                left = middle
            else:
                right = middle
        result.append((left + right) / 2)
    return result[0], result[1]


def transform(probability: Decimal, scenario: dict[str, Any]) -> Decimal:
    first = Decimal(1) / (
        Decimal.from_float(float(scenario["deposition"][0]))
        * Decimal.from_float(float(scenario["ppe"][0]))
    )
    second = Decimal(1) / (
        Decimal.from_float(float(scenario["deposition"][1]))
        * Decimal.from_float(float(scenario["ppe"][1]))
    )
    return first * probability / (first * probability + second * (1 - probability))


def main() -> None:
    protocol_path, saved_path, output_path = map(Path, sys.argv[1:])
    protocol: dict[str, Any] = json.loads(protocol_path.read_text())
    saved: dict[str, Any] = json.loads(saved_path.read_text())
    if (
        saved["protocol_sha256"]
        != hashlib.sha256(protocol_path.read_bytes()).hexdigest()
    ):
        raise ValueError("Numerical output protocol binding differs")
    rows = saved["rows"]
    indexed: dict[tuple[str, int, float, int], dict[str, Any]] = {}
    for row in rows:
        key = (
            row["scenario_id"],
            row["total_count"],
            row["confidence_level"],
            row["counts"][0],
        )
        if key in indexed:
            raise ValueError("Duplicate numerical cell")
        indexed[key] = row
    expected = (
        len(protocol["fixed_responses"])
        * len(protocol["confidence_levels"])
        * sum(n + 1 for n in protocol["counting_totals"])
    )
    if len(indexed) != expected:
        raise ValueError("Incomplete full-count domain")
    maximum_error = Decimal(0)
    endpoint_comparisons = 0
    endpoint_containment_checks = 0
    coverage_rows: list[dict[str, Any]] = []
    extra_outward_memberships = 0
    with localcontext() as context:
        context.prec = 80
        reference: dict[tuple[int, int, float], tuple[Decimal, Decimal]] = {}
        for total in protocol["counting_totals"]:
            counts = (
                range(total + 1)
                if total <= 50
                else sorted({0, 1, 5, total // 2, total - 5, total - 1, total})
            )
            for count in counts:
                for confidence in protocol["confidence_levels"]:
                    reference[(total, count, confidence)] = bounds(
                        total, count, confidence
                    )
        for scenario in protocol["fixed_responses"]:
            for total in protocol["counting_totals"]:
                for confidence in protocol["confidence_levels"]:
                    values = [
                        indexed[(scenario["id"], total, confidence, count)]
                        for count in range(total + 1)
                    ]
                    for count, row in enumerate(values):
                        if (
                            row["counts"] != [count, total - count]
                            or row["profile"] != protocol["profile"]
                        ):
                            raise ValueError("Saved count/profile identity differs")
                        point = transform(Decimal(count) / total, scenario)
                        for expected_point, actual_point in zip(
                            (point, 1 - point), row["cover"], strict=True
                        ):
                            maximum_error = max(
                                maximum_error,
                                abs(expected_point - Decimal.from_float(actual_point)),
                            )
                        saved_lower, saved_upper = map(
                            Decimal.from_float, row["pollen_probability_interval"]
                        )
                        transformed_lower, transformed_upper = (
                            transform(saved_lower, scenario),
                            transform(saved_upper, scenario),
                        )
                        for expected_pair, actual_pair in [
                            (
                                (transformed_lower, 1 - transformed_upper),
                                row["cover_lower"],
                            ),
                            (
                                (transformed_upper, 1 - transformed_lower),
                                row["cover_upper"],
                            ),
                        ]:
                            for expected_bound, actual_bound in zip(
                                expected_pair, actual_pair, strict=True
                            ):
                                maximum_error = max(
                                    maximum_error,
                                    abs(
                                        expected_bound
                                        - Decimal.from_float(actual_bound)
                                    ),
                                )
                        if (total, count, confidence) not in reference:
                            continue
                        lower, upper = reference[(total, count, confidence)]
                        oracle_precision = Decimal(
                            protocol["oracle_containment_tolerance"]
                        )
                        cover_low, cover_high = (
                            transform(lower, scenario),
                            transform(upper, scenario),
                        )
                        if (
                            saved_lower > lower + oracle_precision
                            or saved_upper < upper - oracle_precision
                        ):
                            raise ValueError(
                                "Binary64 pollen bounds do not contain independent root: "
                                + repr((total, count, confidence))
                            )
                        for expected_bounds, actual_bounds, lower_bound in [
                            ((cover_low, 1 - cover_high), row["cover_lower"], True),
                            ((cover_high, 1 - cover_low), row["cover_upper"], False),
                        ]:
                            for expected_bound, actual_bound in zip(
                                expected_bounds, actual_bounds, strict=True
                            ):
                                if (
                                    Decimal.from_float(actual_bound)
                                    > expected_bound + oracle_precision
                                    if lower_bound
                                    else Decimal.from_float(actual_bound)
                                    < expected_bound - oracle_precision
                                ):
                                    raise ValueError(
                                        "Binary64 cover bounds do not contain independent transformed root: "
                                        + repr(
                                            (scenario["id"], total, count, confidence)
                                        )
                                    )
                        endpoint_containment_checks += 6
                        targets = [
                            lower,
                            upper,
                            transform(lower, scenario),
                            transform(upper, scenario),
                        ]
                        observed = [
                            *row["pollen_probability_interval"],
                            row["cover_lower"][0],
                            row["cover_upper"][0],
                        ]
                        for target, actual in zip(targets, observed, strict=True):
                            maximum_error = max(
                                maximum_error, abs(target - Decimal.from_float(actual))
                            )
                            endpoint_comparisons += 1
                    for text in protocol["true_pollen_probabilities"]:
                        probability = Decimal(text)
                        probabilities = binomial_probabilities(total, probability)
                        if abs(sum(probabilities, Decimal(0)) - 1) > Decimal("1e-65"):
                            raise ValueError(
                                "Independent probability mass does not close"
                            )
                        truth = transform(probability, scenario)
                        accumulated = Decimal(0)
                        ideal = Decimal(0)
                        actual = Decimal(0)
                        ideal_count = actual_count = 0
                        tail = (1 - Decimal.from_float(confidence)) / 2
                        for count, (mass, row) in enumerate(
                            zip(probabilities, values, strict=True)
                        ):
                            right_tail = 1 - accumulated
                            accumulated += mass
                            theory_includes = accumulated >= tail and right_tail >= tail
                            implementation_includes = (
                                Decimal.from_float(row["cover_lower"][0])
                                <= truth
                                <= Decimal.from_float(row["cover_upper"][0])
                            )
                            if theory_includes and not implementation_includes:
                                raise ValueError(
                                    "Numerical interval excludes exact binomial confidence member: "
                                    + repr(
                                        (scenario["id"], total, confidence, text, count)
                                    )
                                )
                            if theory_includes:
                                ideal += mass
                                ideal_count += 1
                            if implementation_includes:
                                actual += mass
                                actual_count += 1
                            if implementation_includes and not theory_includes:
                                extra_outward_memberships += 1
                        if ideal < Decimal.from_float(confidence) - Decimal("1e-65"):
                            raise ValueError(
                                "Exact conditional binomial coverage below nominal"
                            )
                        if actual < ideal - Decimal("1e-65"):
                            raise ValueError(
                                "Implementation coverage below exact construction"
                            )
                        coverage_rows.append(
                            {
                                "scenario_id": scenario["id"],
                                "total_count": total,
                                "confidence_level": confidence,
                                "true_pollen_probability": text,
                                "conditional_true_cover": str(truth),
                                "exact_binomial_coverage": str(ideal),
                                "binary64_interval_coverage": str(actual),
                                "ideal_accepted_counts": ideal_count,
                                "actual_accepted_counts": actual_count,
                            }
                        )
    if maximum_error > Decimal(protocol["absolute_tolerance"]):
        raise ValueError(
            "Independent endpoint/transform difference exceeds frozen tolerance"
        )
    if any(
        name.split(".")[0] in {"numpy", "scipy", "bijux_pollenomics_lra"}
        for name in sys.modules
    ):
        raise ValueError(
            "Independent observer loaded a production numerical dependency"
        )
    output_path.write_text(
        json.dumps(
            {
                "native_exit": 0,
                "protocol_sha256": hashlib.sha256(
                    protocol_path.read_bytes()
                ).hexdigest(),
                "saved_output_sha256": hashlib.sha256(
                    saved_path.read_bytes()
                ).hexdigest(),
                "full_count_cells": len(indexed),
                "endpoint_comparisons": endpoint_comparisons,
                "endpoint_containment_checks": endpoint_containment_checks,
                "containment_scope": "Only the frozen endpoint domain at Decimal80/bisection220 precision; not rigorous universal binary64 enclosure certification",
                "maximum_absolute_error": str(maximum_error),
                "coverage_population_count": len(coverage_rows),
                "extra_outward_memberships": extra_outward_memberships,
                "coverage_rows": coverage_rows,
                "oracle": "Decimal80 positive binomial recurrence, cumulative-tail membership, 220-step bisection; no NumPy/SciPy/production interval helper imported",
                "scope": protocol["scope"],
                "scientific_admission": False,
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
