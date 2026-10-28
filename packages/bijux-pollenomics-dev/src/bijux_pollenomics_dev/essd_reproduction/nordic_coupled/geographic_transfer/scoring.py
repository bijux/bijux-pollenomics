"""Match fixed geographic sensitivities on identical defined replicate IDs."""

from __future__ import annotations

from math import fsum
from typing import Any

import numpy as np

from bijux_pollenomics.analysis.lra_validation.metrics import (
    hellinger_distance,
    score_pollen,
)

from ..predictive_uncertainty.predictions import ensemble_summary
from .geometry import require

AXIS = ["Betula", "Ulmus"]
METRICS = ["mae_fraction", "total_variation", "hellinger"]
METHODS = ("training_mean", "nearest_site", "inverse_distance_squared")


def loss(pollen: list[float], counts: dict[str, int]) -> dict[str, Any]:
    require(
        set(counts) == set(AXIS) and len(pollen) == 2,
        "Same two-taxon scoring denominator required",
    )
    fractions = dict(zip(AXIS, pollen, strict=True))
    scored = score_pollen(fractions, counts)
    require(scored.status == "scored", "A compatible source observation is required")
    observation = {taxon: counts[taxon] / sum(counts.values()) for taxon in AXIS}
    return {
        "mae_fraction": scored.mae_fraction,
        "total_variation": scored.total_variation,
        "hellinger": hellinger_distance(fractions, observation),
        "count_conditioned_deviance": scored.count_conditioned_deviance,
        "zero_probability_positive_count": scored.zero_probability_positive_count,
    }


def _series(
    pollen: list[list[float | None]],
    mask: list[bool],
    counts: dict[str, int],
    *,
    masked_status: str = "undefined_prediction",
) -> dict[str, Any]:
    require(
        len(pollen) == len(mask) and all(type(value) is bool for value in mask),
        "Aligned score replicate inventory required",
    )
    values = np.full((len(mask), 3), np.nan)
    rows = []
    impossible = []
    deviances = []
    for index, valid in enumerate(mask):
        if not valid:
            rows.append({"replicate_id": index, "status": masked_status})
            continue
        vector = pollen[index]
        require(
            len(vector) == 2 and all(type(value) in (int, float) for value in vector),
            "A defined prediction requires its full numerical axis",
        )
        metrics = loss([float(value) for value in vector if value is not None], counts)
        values[index] = [metrics[key] for key in METRICS]
        rows.append({"replicate_id": index, "status": "scored", **metrics})
        if metrics["zero_probability_positive_count"]:
            impossible.append(index)
        else:
            require(
                metrics["count_conditioned_deviance"] is not None,
                "Finite count deviance is missing",
            )
            deviances.append(metrics["count_conditioned_deviance"])
    return {
        "rows": rows,
        "scoring_population": "candidate_defined_predictions"
        if masked_status == "undefined_prediction"
        else "common_defined_comparison_replicates",
        "bounded_metric_axis": list(METRICS),
        "bounded_metric_summary": ensemble_summary(
            values, np.asarray(mask, dtype=bool)
        ),
        "count_deviance": {
            "impossible_positive_count_replicate_ids": impossible,
            "conditional_mean_on_defined_predictions": fsum(deviances) / len(deviances)
            if deviances and not impossible
            else None,
            "status": "infinite_positive_count_loss"
            if impossible
            else "finite_conditional_only"
            if deviances
            else "unavailable_no_defined_predictions",
            "unconditional_status": "defined"
            if all(mask) and not impossible
            else "refused_incomplete_scoring_population_or_infinite_loss",
        },
    }


def score_candidate(
    candidate: dict[str, Any], prediction: dict[str, Any], counts: dict[str, int]
) -> dict[str, Any]:
    """Treat draws as a conditional working law, never as independent sites."""
    require(
        prediction["case_id"] == candidate["case"]["case_id"]
        and prediction["target_id"] == candidate["case"]["target_id"],
        "Prediction/source case changed",
    )
    ensemble = prediction["ensemble"]
    total = prediction["replicates"]
    mask = ensemble["valid_mask"]
    require(total == len(mask), "Complete candidate replicate population required")
    result: dict[str, Any] = {
        "case_id": prediction["case_id"],
        "target_id": prediction["target_id"],
        "length_scale_km": prediction["length_scale_km"],
        "observed_total_count": sum(counts.values()),
        "observed_counts": dict(counts),
        "nominal": loss(prediction["nominal"]["pollen"], counts)
        if prediction["nominal"]["status"] == "predicted"
        else {"status": "refused", "refusal": prediction["nominal"]["refusal"]},
        "ensemble": _series(ensemble["pollen"], mask, counts),
        "comparisons": [],
        "vegetation_accuracy": "not_evaluated_no_measured_observation",
        "scope": "one_geographic_target_block_conditional_working_law_not_field_coverage",
    }
    for method in METHODS:
        reference = candidate["cached_fit"]["methods"][method]
        for channel, reference_mask in (
            ("physical", reference["valid_mask"]),
            ("direct_pollen", [True] * total),
        ):
            pollen = reference["pollen" if channel == "physical" else "direct_pollen"]
            require(
                len(pollen) == len(reference_mask) == total,
                "Complete original reference population required",
            )
            common = [
                first and second
                for first, second in zip(mask, reference_mask, strict=True)
            ]
            ids = [index for index, valid in enumerate(common) if valid]
            paired = np.full((total, 3), np.nan)
            for index in ids:
                first = loss(ensemble["pollen"][index], counts)
                second = loss(pollen[index], counts)
                paired[index] = [first[key] - second[key] for key in METRICS]
            result["comparisons"].append(
                {
                    "reference_method": method,
                    "reference_channel": channel,
                    "common_defined_replicate_ids": ids,
                    "excluded_replicates": total - len(ids),
                    "reference_scores": _series(
                        pollen,
                        common,
                        counts,
                        masked_status="excluded_from_common_comparison",
                    ),
                    "metric_axis": list(METRICS),
                    "model_minus_reference": ensemble_summary(
                        paired, np.asarray(common, dtype=bool)
                    ),
                }
            )
    return result
