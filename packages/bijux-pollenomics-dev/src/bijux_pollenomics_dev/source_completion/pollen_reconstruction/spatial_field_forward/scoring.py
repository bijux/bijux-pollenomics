"""Score already closed prediction bytes on the complete fixed observations."""

from __future__ import annotations

import hashlib
import itertools
import json
import math
from pathlib import Path
from typing import Any

from bijux_pollenomics.analysis.lra_validation.metrics import hellinger_distance

from .sources import AXIS, FAMILIES, require

METRICS = ("mean_absolute_fraction_error", "total_variation", "hellinger_distance")


def metrics(predicted: list[float], observed: list[float]) -> dict[str, float]:
    """Use the maintained stable Hellinger convention on matched closed axes."""
    differences = [abs(p - o) for p, o in zip(predicted, observed, strict=True)]
    return {
        METRICS[0]: math.fsum(differences) / 2,
        METRICS[1]: math.fsum(differences) / 2,
        METRICS[2]: hellinger_distance(
            dict(zip(AXIS, predicted, strict=True)),
            dict(zip(AXIS, observed, strict=True)),
            arithmetic_profile="stable",
        ),
    }


def metric_ranges(
    bounds: list[list[float]], observed: list[float]
) -> dict[str, list[float]]:
    """Two-axis score minima occur nearest the observation; maxima at an end."""
    lo, hi = bounds[0]
    require(0 <= lo <= hi <= 1, "Invalid frozen prediction range")
    nearest = min(hi, max(lo, observed[0]))
    minimum = metrics([nearest, 1 - nearest], observed)
    endpoints = [metrics([p, 1 - p], observed) for p in (lo, hi)]
    return {key: [minimum[key], max(row[key] for row in endpoints)] for key in METRICS}


def averages(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Average all predeclared rows; the caller enforces the denominator."""
    return {
        "metrics": {
            key: math.fsum(row[key] for row in rows) / len(rows) for key in METRICS
        },
        "numerical_ranges": {
            key: [
                math.fsum(row["numerical_ranges"][key][end] for row in rows) / len(rows)
                for end in range(2)
            ]
            for key in METRICS
        },
    }


def summarize(scores: list[dict[str, Any]], core_ids: list[str]) -> dict[str, Any]:
    """Retain every family, and conservative non-joint aggregate enclosures."""
    families = []
    for family in FAMILIES:
        requested = [r for r in scores if r["family"] == family]
        if len(requested) != 18 or any(r["status"] != "scored" for r in requested):
            families.append(
                {
                    "family": family,
                    "status": "refused_incomplete_cohort",
                    "requested_contexts": 18,
                    "scored_contexts": sum(r["status"] == "scored" for r in requested),
                }
            )
            continue
        places = []
        for core in core_ids:
            rows = [r for r in requested if r["core"] == core]
            require(len(rows) == 6, "Place summary denominator differs")
            places.append({"core": core, **averages(rows)})
        aggregate_rows = [
            {**row["metrics"], "numerical_ranges": row["numerical_ranges"]}
            for row in places
        ]
        families.append(
            {
                "family": family,
                "status": "complete_cohort",
                "requested_contexts": 18,
                "scored_contexts": 18,
                "places": places,
                "equal_place": averages(aggregate_rows),
            }
        )
    comparisons = []
    for first, second in itertools.combinations(families, 2):
        row = {"first_family": first["family"], "second_family": second["family"]}
        if (
            first["status"] != "complete_cohort"
            or second["status"] != "complete_cohort"
        ):
            comparisons.append({**row, "status": "refused_incomplete_cohort"})
            continue
        differences = {}
        for key in METRICS:
            a, b = first["equal_place"], second["equal_place"]
            lower = a["numerical_ranges"][key][0] - b["numerical_ranges"][key][1]
            upper = a["numerical_ranges"][key][1] - b["numerical_ranges"][key][0]
            differences[key] = {
                "point_difference": a["metrics"][key] - b["metrics"][key],
                "numerical_difference_range": [lower, upper],
                "resolution": "numerically_unresolved"
                if lower <= 0 <= upper
                else "separated_conditional_numerical_ranges",
            }
        comparisons.append(
            {**row, "status": "matched_complete_cohort", "metrics": differences}
        )
    return {"families": families, "pairwise": comparisons}


def score_frozen(path: Path, observations: list[dict[str, Any]]) -> dict[str, Any]:
    """Open persisted prediction bytes before receiving observed proportions."""
    body = path.read_bytes()
    packet = json.loads(body)
    identity = {
        "path": path.name,
        "bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
    }
    indexed = {
        f"{r['core']}:{r['window'][0]}:{r['window'][1]}": r for r in observations
    }
    require(
        len(indexed) == len(observations) == len(packet["contexts"]) == 18,
        "Scoring observation/context population differs",
    )
    context_ids = [context["context_id"] for context in packet["contexts"]]
    require(
        len(set(context_ids)) == len(context_ids) and set(context_ids) == set(indexed),
        "Frozen prediction context identities differ",
    )
    scores = []
    for context in packet["contexts"]:
        observation = indexed[context["context_id"]]
        require(
            all(
                observation[key] == context["target"][key]
                for key in (
                    "core",
                    "site_id",
                    "dataset_id",
                    "collection_unit_id",
                )
            ),
            "Frozen prediction/observation owner differs",
        )
        require(
            list(observation["window"]) == context["target"]["window"],
            "Frozen prediction/observation window differs",
        )
        require(
            observation["sample_ids"] == context["target"]["sample_ids"],
            "Frozen prediction/observation support differs",
        )
        counts = observation["projected_counts"]
        observed = [n / sum(counts) for n in counts]
        for family in FAMILIES:
            prediction = context["families"][family]
            row = {
                "context_id": context["context_id"],
                "core": observation["core"],
                "window": observation["window"],
                "sample_ids": observation["sample_ids"],
                "family": family,
                "prediction_file_sha256": identity["sha256"],
                "observed_fraction": observed,
            }
            if prediction["status"] != "predicted":
                scores.append(
                    {
                        **row,
                        "status": "refused_prediction",
                        "reason": prediction["reason"],
                    }
                )
                continue
            predicted = prediction["pollen_fraction"]
            scores.append(
                {
                    **row,
                    "status": "scored",
                    "predicted_fraction": predicted,
                    "signed_fraction_error": [
                        p - o for p, o in zip(predicted, observed, strict=True)
                    ],
                    **metrics(predicted, observed),
                    "numerical_ranges": metric_ranges(
                        prediction["prediction_bounds"], observed
                    ),
                }
            )
    require(len(scores) == 54, "Family outcome denominator differs")
    return {
        "prediction_file": identity,
        "scores": scores,
        "summaries": summarize(scores, sorted({r["core"] for r in observations})),
    }
