"""Reconstruct predictions and every matched score without new inversions."""

from __future__ import annotations

from fractions import Fraction
from itertools import combinations
import json
from typing import Any

from .exact_arithmetic import Interval, finite, interval, require
from .metrics import METRICS, closure, deposition, metric_bounds
from .sources import CORES, FAMILIES


def same(actual: object, expected: object) -> None:
    require(
        json.dumps(actual, sort_keys=True, allow_nan=False)
        == json.dumps(expected, sort_keys=True, allow_nan=False),
        "typed result structure or value differs",
    )


def encoded(bounds: Interval) -> list[str]:
    return [str(value) for value in bounds]


def verify_contexts(
    packet: dict[str, Any], old: dict[str, Any], geometry: dict[str, dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    rows = {row["context_id"]: row for row in packet["contexts"]}
    originals = {row["context_id"]: row for row in old["contexts"]}
    require(
        len(rows) == len(packet["contexts"]) == len(originals) == 18
        and set(rows) == set(originals),
        "all fixed prediction contexts required",
    )
    ppe = [finite(value) for value in old["ppe"]]
    require(
        len(ppe) == 2 and all(value > 0 for value in ppe),
        "two positive saved PPE constants required",
    )
    result = {}
    for identity, row in rows.items():
        source = originals[identity]
        target, training = source["target"], source["training"]
        core = target["core"]
        require(
            core in CORES and source["geometry_core"] == core and len(training) == 2,
            "target geometry ownership differs",
        )
        require(
            [anchor["core"] for anchor in training] == sorted(set(CORES) - {core})
            and len({anchor["site_id"] for anchor in training}) == 2
            and all(
                anchor["site_id"] != target["site_id"]
                and anchor["window"] == target["window"]
                and not set(anchor["sample_ids"]).intersection(target["sample_ids"])
                for anchor in training
            ),
            "held-place exclusion or source support differs",
        )
        expected: dict[str, Any] = {
            "context_id": identity,
            "core": core,
            "window": target["window"],
        }
        coefficients = geometry[core]["coefficients"]
        if any(value is None for value in coefficients):
            expected.update(
                status="refused_geometry_envelope",
                deposition_bounds_exact=None,
                conditional_spatial_prediction_bounds_exact=None,
                reference_point_membership=False,
                reference_point_status="refused_geometry_envelope",
                legacy_mass_correspondence_status="refused_geometry_envelope",
            )
        else:
            deposits = []
            for index, pair in enumerate(coefficients):
                total, first = pair
                covers = [finite(anchor["cover"][index]) for anchor in training]
                require(
                    all(0 <= value <= 1 for value in covers),
                    "saved finite cover domain differs",
                )
                deposits.append(
                    deposition(total, first, covers[0], covers[1], ppe[index])
                )
            probability = closure(deposits[0], deposits[1])
            old_point = source["families"][FAMILIES[2]]["pollen_fraction"]
            require(len(old_point) == 2, "two legacy component references required")
            membership = all(
                lo <= finite(value) <= hi
                for value, (lo, hi) in zip(old_point, probability, strict=True)
            )
            mass_matches = geometry[core]["mass_matches"]
            expected.update(
                status="finite_mass_envelope",
                deposition_bounds_exact=[encoded(value) for value in deposits],
                conditional_spatial_prediction_bounds_exact=[
                    encoded(value) for value in probability
                ],
                reference_point_membership=membership,
                reference_point_status="passed_finite_scalar_membership"
                if membership and mass_matches
                else "refused_reference_point_correspondence",
                legacy_mass_correspondence_status="passed_numerical_mass_diagnostic"
                if mass_matches
                else "refused_reference_point_correspondence",
            )
        same(row, expected)
        result[identity] = expected
    require(
        all(sum(row["core"] == core for row in result.values()) == 6 for core in CORES),
        "six frozen windows per place required",
    )
    return result


def verify_scores(
    result: dict[str, Any],
    native: dict[str, Any],
    prior: dict[str, Any],
    contexts: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    old_rows = {(row["context_id"], row["family"]): row for row in native["scores"]}
    expected_ids = {(identity, family) for identity in contexts for family in FAMILIES}
    actual = {(row["context_id"], row["family"]): row for row in result["scores"]}
    require(
        len(old_rows)
        == len(native["scores"])
        == len(actual)
        == len(result["scores"])
        == 54
        and set(actual) == set(old_rows) == expected_ids,
        "complete matched score population differs",
    )
    originals = {row["context_id"]: row for row in prior["contexts"]}
    observed: dict[str, list[float]] = {}
    expected_rows = []
    for identity, old in old_rows.items():
        context, family = identity
        saved, reference = contexts[context], originals[context]
        target = reference["target"]
        require(
            old["status"] == "scored"
            and old["core"] == target["core"]
            and old["window"] == target["window"]
            and old["sample_ids"] == target["sample_ids"]
            and old["predicted_fraction"]
            == reference["families"][family]["pollen_fraction"],
            "legacy score/prediction support differs",
        )
        require(
            len(old["observed_fraction"]) == 2, "two saved observed components required"
        )
        if context in observed:
            same(old["observed_fraction"], observed[context])
        else:
            observed[context] = old["observed_fraction"]
        expected: dict[str, Any] = {
            "context_id": context,
            "core": old["core"],
            "window": old["window"],
            "family": family,
            "legacy_point_score": {metric: old[metric] for metric in METRICS},
        }
        if family != FAMILIES[2]:
            ranges = {
                metric: (finite(old[metric]), finite(old[metric])) for metric in METRICS
            }
            expected.update(
                status="fixed_saved_point_reference",
                reference_point_status="fixed_saved_point_reference",
                conditional_metric_ranges_exact={
                    metric: encoded(value) for metric, value in ranges.items()
                },
            )
        elif saved["status"] != "finite_mass_envelope":
            expected.update(
                status="refused_geometry_envelope",
                reference_point_status="refused_geometry_envelope",
                conditional_metric_ranges_exact=None,
            )
        else:
            bounds = interval(saved["conditional_spatial_prediction_bounds_exact"][0])
            observations = (
                finite(old["observed_fraction"][0]),
                finite(old["observed_fraction"][1]),
            )
            ranges = metric_bounds(bounds, observations)
            membership = all(
                lo <= finite(old[metric]) <= hi for metric, (lo, hi) in ranges.items()
            )
            expected.update(
                status="finite_mass_conditional_score_enclosure",
                reference_point_status="passed_finite_scalar_membership"
                if membership
                and saved["reference_point_status"] == "passed_finite_scalar_membership"
                else "refused_reference_point_correspondence",
                conditional_metric_ranges_exact={
                    metric: encoded(value) for metric, value in ranges.items()
                },
            )
        same(actual[identity], expected)
        expected_rows.append(expected)
    return expected_rows


def average_ranges(rows: list[dict[str, Any]]) -> dict[str, list[str]]:
    require(bool(rows), "fixed mean denominator cannot be empty")
    result = {}
    for metric in METRICS:
        bounds = [
            interval(row["conditional_metric_ranges_exact"][metric]) for row in rows
        ]
        lo = sum((value[0] for value in bounds), Fraction(0)) / len(rows)
        hi = sum((value[1] for value in bounds), Fraction(0)) / len(rows)
        result[metric] = encoded((lo, hi))
    return result


def verify_summaries(
    actual: dict[str, Any], rows: list[dict[str, Any]], legacy: dict[str, Any]
) -> None:
    families = []
    for family in FAMILIES:
        selected = [row for row in rows if row["family"] == family]
        old = next(row for row in legacy["families"] if row["family"] == family)
        require(len(selected) == 18, "full family denominator required")
        if any(row["conditional_metric_ranges_exact"] is None for row in selected):
            families.append(
                {
                    "family": family,
                    "status": "refused_incomplete_context",
                    "legacy_point_metrics": old["equal_place"]["metrics"],
                }
            )
            continue
        places = []
        for core in CORES:
            subset = [row for row in selected if row["core"] == core]
            require(len(subset) == 6, "six windows required before place means")
            places.append(
                {
                    "core": core,
                    "conditional_metric_ranges_exact": average_ranges(subset),
                }
            )
        families.append(
            {
                "family": family,
                "status": "complete_conditional_context",
                "places": places,
                "equal_place": {
                    "conditional_metric_ranges_exact": average_ranges(places),
                    "legacy_point_metrics": old["equal_place"]["metrics"],
                },
            }
        )
    pairwise = []
    for a, b in combinations(families, 2):
        identity = {"first_family": a["family"], "second_family": b["family"]}
        if any(family["status"] != "complete_conditional_context" for family in (a, b)):
            pairwise.append({**identity, "status": "refused_incomplete_context"})
            continue
        old = next(
            row
            for row in legacy["pairwise"]
            if row["first_family"] == a["family"]
            and row["second_family"] == b["family"]
        )
        metrics = {}
        for metric in METRICS:
            first, second = (
                interval(a["equal_place"]["conditional_metric_ranges_exact"][metric]),
                interval(b["equal_place"]["conditional_metric_ranges_exact"][metric]),
            )
            difference = first[0] - second[1], first[1] - second[0]
            metrics[metric] = {
                "conditional_difference_range_exact": encoded(difference),
                "legacy_point_difference": old["metrics"][metric]["point_difference"],
                "conditional_resolution": "unresolved_finite_mass_context"
                if difference[0] <= 0 <= difference[1]
                else "separated_finite_mass_context",
            }
        correspondence = all(
            row["reference_point_status"] != "refused_reference_point_correspondence"
            for row in rows
            if row["family"] in (a["family"], b["family"])
        )
        pairwise.append(
            {
                **identity,
                "status": "matched_complete_conditional_context",
                "legacy_comparison_status": "numerical_reference_correspondence_only"
                if correspondence
                else "refused_reference_point_correspondence",
                "metrics": metrics,
            }
        )
    same(actual, {"families": families, "pairwise": pairwise})
