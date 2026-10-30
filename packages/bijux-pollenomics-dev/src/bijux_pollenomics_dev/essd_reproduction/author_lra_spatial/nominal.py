"""Check the saved baseline handoff before a different spatial model is fitted."""

from __future__ import annotations

import math
from typing import Any

from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.reconstruction.forward import forward_deposition

BASELINES = ("training_mean", "nearest_site", "inverse_distance_squared")
ABSOLUTE_TOLERANCE = 1e-12


def _require(condition: object, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _number(value: Any) -> float:
    _require(
        type(value) in (int, float) and math.isfinite(value) and value >= 0,
        "Finite nonnegative saved baseline value required",
    )
    return float(value)


def _cover(values: Any, taxa: list[str]) -> list[float]:
    _require(
        type(values) is dict and set(values) == set(taxa),
        "Complete saved baseline taxon denominator required",
    )
    result = [_number(values[taxon]) for taxon in taxa]
    _require(
        all(value <= 1 for value in result) and abs(sum(result) - 1) <= 1e-9,
        "Closed saved baseline fractions required without renormalization",
    )
    return result


def _reconstruct(
    predictors: list[dict[str, Any]],
    distances: dict[str, Any],
    taxa: list[str],
    method: str,
) -> list[float]:
    """Independently compute the three original arithmetic spatial baselines."""
    _require(method in BASELINES, "Unknown nominal baseline")
    _require(type(predictors) is list and bool(predictors), "Local predictors required")
    rows = {row["group_id"]: row for row in predictors}
    _require(
        len(rows) == len(predictors)
        and all(type(group) is str and group for group in rows)
        and type(distances) is dict
        and set(rows) == set(distances),
        "Unique local groups and exact saved distance membership required",
    )
    groups = sorted(rows)
    covers = {}
    for group in groups:
        rings = rows[group]["covers_by_ring"]
        _require(
            type(rings) is list and len(rings) == 2,
            "Both saved training rings required",
        )
        vector = rings[1]
        _require(
            type(vector) is list and len(vector) == len(taxa),
            "Selected ring taxon axis differs",
        )
        covers[group] = _cover(dict(zip(taxa, vector, strict=True)), taxa)
    numerical_distances = {group: _number(distances[group]) for group in groups}
    nearest = min(numerical_distances.values())
    if method == "training_mean":
        selected = groups
    elif method == "nearest_site" or nearest == 0:
        selected = [group for group in groups if numerical_distances[group] == nearest]
    else:
        selected = groups
    if method == "inverse_distance_squared" and nearest != 0:
        weights = {
            group: (nearest / numerical_distances[group]) ** 2 for group in selected
        }
    else:
        weights = dict.fromkeys(selected, 1.0)
    denominator = sum(weights.values())
    return [
        sum(covers[group][index] * weights[group] for group in selected) / denominator
        for index in range(len(taxa))
    ]


def check_nominal(packet: dict[str, Any]) -> dict[str, Any]:
    """Compare all 675 existing baselines at the fixed absolute 1e-12 gate.

    This observes the source-to-consumer handoff, with no outcomes or model fit.
    Native forward refusals and every mismatching slot remain explicit failures.
    """
    taxa = packet["taxa"]
    contexts = packet["contexts"]
    _require(
        type(taxa) is list
        and bool(taxa)
        and all(type(taxon) is str and taxon for taxon in taxa)
        and len(set(taxa)) == len(taxa),
        "Unique full taxon axis required",
    )
    _require(
        type(contexts) is list
        and len(contexts) == 225
        and len({row["context_id"] for row in contexts}) == 225
        and sum(row["kind"] == "outer" for row in contexts) == 15
        and sum(row["kind"] == "inner" for row in contexts) == 210,
        "Complete unique225 outer/inner contexts required",
    )
    prepared = []
    for context in contexts:
        training = context["scientific_refs"]["training_record_ids"]
        _require(
            context["target"] not in training
            and context["outer_target"] not in training
            and all(row["record_id"] in training for row in context["predictors"]),
            "Held-out owner entered nominal training",
        )
        references = context["reference_baselines"]
        _require(
            type(references) is list
            and len(references) == 3
            and {row["baseline"] for row in references} == set(BASELINES),
            "Complete unique three reference baselines required",
        )
        by_baseline = {row["baseline"]: row for row in references}
        forward = context["forward"]["forward_inputs"]
        _require(forward["taxa"] == taxa, "Forward taxon axis differs")
        for baseline in BASELINES:
            reference = by_baseline[baseline]
            expected_cover = _cover(reference["vegetation_fraction"], taxa)
            expected_pollen = _cover(reference["pollen_fraction"], taxa)
            cover = _reconstruct(
                context["predictors"],
                context["forward"]["distances_km"],
                taxa,
                baseline,
            )
            prepared.append(
                (
                    context["context_id"],
                    baseline,
                    cover,
                    expected_cover,
                    expected_pollen,
                    forward,
                )
            )
    failures = []
    maximum_vegetation_error = 0.0
    maximum_pollen_error = 0.0
    pollen_comparisons = 0
    for (
        context_id,
        baseline,
        cover,
        expected_cover,
        expected_pollen,
        forward,
    ) in prepared:
        vegetation_error = max(
            abs(left - right) for left, right in zip(cover, expected_cover, strict=True)
        )
        maximum_vegetation_error = max(maximum_vegetation_error, vegetation_error)
        if vegetation_error > ABSOLUTE_TOLERANCE:
            failures.append(
                {
                    "context_id": context_id,
                    "baseline": baseline,
                    "stage": "vegetation",
                    "maximum_absolute_error": vegetation_error,
                }
            )
        try:
            result = forward_deposition(
                cover,
                forward["regional_deposition"],
                forward["local_k"],
                forward["terrestrial_fraction"],
                forward["ppe"],
            )
        except ValidationError as error:
            failures.append(
                {
                    "context_id": context_id,
                    "baseline": baseline,
                    "stage": "native_forward",
                    "reason": error.reason_code,
                    "detail": str(error),
                }
            )
            continue
        actual_pollen = [float(value) for value in result.pollen_fraction]
        _require(
            len(actual_pollen) == len(taxa)
            and all(
                math.isfinite(value) and 0 <= value <= 1 for value in actual_pollen
            ),
            "Native nominal forward output is invalid",
        )
        pollen_error = max(
            abs(left - right)
            for left, right in zip(actual_pollen, expected_pollen, strict=True)
        )
        pollen_comparisons += 1
        maximum_pollen_error = max(maximum_pollen_error, pollen_error)
        if pollen_error > ABSOLUTE_TOLERANCE:
            failures.append(
                {
                    "context_id": context_id,
                    "baseline": baseline,
                    "stage": "pollen",
                    "maximum_absolute_error": pollen_error,
                }
            )
    return {
        "passed": not failures,
        "contexts": len(contexts),
        "reference_baselines": len(prepared),
        "vegetation_comparisons": len(prepared),
        "forward_calls": len(prepared),
        "pollen_comparisons": pollen_comparisons,
        "vegetation_component_checks": len(prepared) * len(taxa),
        "pollen_component_checks": pollen_comparisons * len(taxa),
        "absolute_tolerance": ABSOLUTE_TOLERANCE,
        "maximum_vegetation_absolute_error": maximum_vegetation_error,
        "maximum_pollen_absolute_error": maximum_pollen_error,
        "failures": failures,
    }
