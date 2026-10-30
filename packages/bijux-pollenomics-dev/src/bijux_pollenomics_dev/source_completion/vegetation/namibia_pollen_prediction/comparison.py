"""Frozen conditional forward-pollen development protocol.

All fifteen native radius labels and nine nominal spatial exclusion groups are
retained. T4/T5 are held out together. Each group/radius trains one response
model on the other groups: 135 attempts produce 150 held-out-site predictions
per method. This predicts pollen GIVEN deposited mapped-area quantities, not
vegetation, PPE, ERV, a physical source radius or a Nordic lake reconstruction.

For native positive areas A and counts n, q_si=A_si*w_i/sum_j(A_sj*w_j).
Positive response weights have a common-scale gauge; output sets Combretaceae
weight to one. Setting v=w/sum(w) gives EXACTLY the maintained heterogeneous
multinomial likelihood, so its mathematical optimizer applies while v here is
an empirical response multiplier, not ecological cover. The objective is
-sum(n_si*log(q_si))/sum(N_s), with natural integer-grain effort, NOT equal-group
training weights or the earlier inverse log-compositional objective.

Use score tolerance 1e-12, relative-count tolerance 1e-10, 200 Newton steps and
all existing floating-information/positive-probability refusals. Steps are
returned steps; objective evaluation count is not exposed and is not invented.
No failed fit is rescued. Baselines are closed target areas, pooled training
counts and the geographically nearest eligible training event's count fractions
(sphere 6371000 m; exact distance ties use lexical event ID). Fits/predictors
receive no held-out pollen or held-out grain effort. All predictions precede
scoring, but all source outcomes were previously exposed.

Primary score is per-site, per-grain cross entropy; secondary scores are
five-taxon MAE and squared Hellinger distance (half the squared root difference
sum). Retain every radius, both equal-site and equal-group means, coverage,
signed model-minus-baseline differences and all poorer outcomes. Score ties
mean exact binary64 equality; no best-radius selection, significance test,
accuracy threshold, uncertainty interval or independent field claim is made.
Dates, image-sector masks, map classification and campaign independence remain
unresolved. The source comprises ten samples/6894 grains once, not 150 samples.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import math
from typing import Any

import numpy as np

from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.reconstruction.likelihood.multisite_likelihood import (
    fit_multisite_likelihood,
)

from .inputs import GROUPS, RADII, SITES, TAXA, NativeSource, distance

METHODS = ("empirical", "area_only", "training_mean", "nearest_site")
METRICS = ("mean_nll", "mae", "hellinger_squared")
BASELINES = METHODS[1:]
CSV_FIELDS = (
    "radius_label_m",
    "heldout_site",
    "heldout_group",
    "fit_id",
    "training_sites",
    "training_grains",
    "fit_status",
    "fit_stop_reason",
    "fit_steps",
    "fit_score_residual",
    "fit_relative_count_residual",
    "fit_minimum_relative_information",
    "fit_information_resolution_floor",
    "fit_hessian_condition_number",
    "empirical_status",
    "empirical_reason",
    "nearest_site",
    "nearest_distance_m",
    *(f"observed_{taxon}" for taxon in TAXA),
    *(f"area_m2_{taxon}" for taxon in TAXA),
    *(f"response_multiplier_{taxon}" for taxon in TAXA),
    *(f"{method}_{taxon}" for method in METHODS for taxon in TAXA),
    *(f"{method}_{metric}" for method in METHODS for metric in METRICS),
    *(
        f"empirical_minus_{baseline}_{metric}"
        for baseline in BASELINES
        for metric in METRICS
    ),
)


@dataclass(frozen=True)
class TrainingSite:
    """Only eligible training observations enter calibration or baselines."""

    site: str
    counts: tuple[int, ...]
    areas: tuple[float, ...]
    coordinate: tuple[float, float]


@dataclass(frozen=True)
class TargetSite:
    """Prediction covariates contain neither target pollen nor target effort."""

    site: str
    areas: tuple[float, ...]
    area_tokens: tuple[str, ...]
    coordinate: tuple[float, float]


def close(values: Sequence[float]) -> tuple[float, ...]:
    """Close positive finite quantities without pseudocounts or zero repair."""
    if len(values) != 5 or any(
        not math.isfinite(value) or value <= 0 for value in values
    ):
        raise ValueError("Positive finite five-taxon prediction quantities required")
    scale = max(values)
    scaled = tuple(value / scale for value in values)
    total = math.fsum(scaled)
    result = tuple(value / total for value in scaled)
    if any(value <= 0 or not math.isfinite(value) for value in result):
        raise ValueError("Positive prediction probability is not representable")
    return result


def forward(areas: Sequence[float], weights: Sequence[float]) -> tuple[float, ...]:
    """Evaluate response multiplication in log space, retaining numeric refusals."""
    if (
        len(areas) != 5
        or len(weights) != 5
        or any(not math.isfinite(value) or value <= 0 for value in (*areas, *weights))
    ):
        raise ValueError(
            "Positive finite mapped areas and response multipliers required"
        )
    logs = tuple(
        math.log(area) + math.log(weight)
        for area, weight in zip(areas, weights, strict=True)
    )
    offset = max(logs)
    return close(tuple(math.exp(value - offset) for value in logs))


def fit_training(
    training: Sequence[TrainingSite],
) -> tuple[dict[str, Any], tuple[float, ...] | None]:
    """Fit the declared count objective, with no target outcome argument."""
    if not training or any(
        len(site.counts) != 5 or any(type(n) is not int or n <= 0 for n in site.counts)
        for site in training
    ):
        return {
            "fit_status": "refused",
            "fit_stop_reason": "positive_native_integer_training_counts_required",
        }, None
    counts = np.asarray([site.counts for site in training])
    areas = np.asarray([site.areas for site in training])
    try:
        fit = fit_multisite_likelihood(
            counts,
            areas,
            taxon_measured=np.ones(counts.shape, dtype=bool),
            score_tolerance=1e-12,
            relative_count_tolerance=1e-10,
            max_steps=200,
        )
    except ValidationError as exc:
        return {"fit_status": "refused", "fit_stop_reason": str(exc)}, None
    diagnostics = {
        "fit_status": "converged" if fit.converged else "not_converged",
        "fit_stop_reason": fit.stop_reason,
        "fit_steps": fit.steps,
        "fit_score_residual": fit.score_residual,
        "fit_relative_count_residual": fit.relative_count_residual,
        "fit_minimum_relative_information": fit.minimum_relative_information,
        "fit_information_resolution_floor": fit.information_resolution_floor,
        "fit_hessian_condition_number": fit.hessian_condition_number,
    }
    if not fit.converged:
        return diagnostics, None
    with np.errstate(over="ignore", invalid="ignore"):
        weights = tuple(float(value / fit.cover[-1]) for value in fit.cover)
    if any(not math.isfinite(value) or value <= 0 for value in weights):
        diagnostics.update(
            fit_status="refused",
            fit_stop_reason="response_multiplier_gauge_not_representable",
        )
        return diagnostics, None
    return diagnostics, weights


def predict_group(
    training: Sequence[TrainingSite], targets: Sequence[TargetSite], radius: int
) -> list[dict[str, Any]]:
    """Make all method predictions on exactly the same permitted training sites."""
    if (
        not training
        or not targets
        or {site.site for site in training} & {site.site for site in targets}
    ):
        raise ValueError("Disjoint nonempty training and target groups required")
    diagnostics, weights = fit_training(training)
    pooled = close(
        tuple(float(sum(site.counts[i] for site in training)) for i in range(5))
    )
    group = "|".join(site.site for site in targets)
    rows = []
    for target in targets:
        nearest = min(
            training,
            key=lambda site: (distance(target.coordinate, site.coordinate), site.site),
        )
        predictions = {
            "area_only": close(target.areas),
            "training_mean": pooled,
            "nearest_site": close(nearest.counts),
        }
        reason = ""
        if weights is None:
            status, reason = (
                "fit_" + diagnostics["fit_status"],
                diagnostics["fit_stop_reason"],
            )
        else:
            try:
                predictions["empirical"] = forward(target.areas, weights)
                status = "computed"
            except ValueError as exc:
                status, reason = "prediction_refused", str(exc)
        row: dict[str, Any] = dict.fromkeys(CSV_FIELDS, "")
        row.update(
            radius_label_m=radius,
            heldout_site=target.site,
            heldout_group=group,
            fit_id=f"{radius}:{group}",
            training_sites="|".join(site.site for site in training),
            training_grains=sum(sum(site.counts) for site in training),
            empirical_status=status,
            empirical_reason=reason,
            nearest_site=nearest.site,
            nearest_distance_m=distance(target.coordinate, nearest.coordinate),
            **diagnostics,
        )
        for i, taxon in enumerate(TAXA):
            row[f"area_m2_{taxon}"] = target.area_tokens[i]
            if weights is not None:
                row[f"response_multiplier_{taxon}"] = weights[i]
            for method, prediction in predictions.items():
                row[f"{method}_{taxon}"] = prediction[i]
        rows.append(row)
    return rows


def predict(
    source: NativeSource, *, radii: Sequence[int] = RADII
) -> tuple[Mapping[str, Any], ...]:
    """Freeze predictions for all groups before any target scoring access."""
    from types import MappingProxyType

    result: list[Mapping[str, Any]] = []
    for radius in radii:
        for group in GROUPS:
            training = [
                TrainingSite(
                    site,
                    source.counts[site],
                    source.areas[(site, radius)],
                    source.coordinates[site],
                )
                for site in SITES
                if site not in group
            ]
            targets = [
                TargetSite(
                    site,
                    source.areas[(site, radius)],
                    source.area_tokens[(site, radius)],
                    source.coordinates[site],
                )
                for site in group
            ]
            result.extend(
                MappingProxyType(row)
                for row in predict_group(training, targets, radius)
            )
    return tuple(result)


def score(counts: Sequence[int], probabilities: Sequence[float]) -> dict[str, float]:
    """Use native target counts only after prediction, with the five-taxon sum."""
    total = sum(counts)
    if (
        len(counts) != 5
        or any(type(value) is not int or value < 0 for value in counts)
        or total <= 0
    ):
        raise ValueError("Measured integer target counts and positive effort required")
    if (
        len(probabilities) != 5
        or any(not math.isfinite(value) or value <= 0 for value in probabilities)
        or abs(math.fsum(probabilities) - 1) > 1e-12
    ):
        raise ValueError("Positive closed five-taxon prediction required")
    observed = tuple(value / total for value in counts)
    return {
        "mean_nll": math.fsum(
            -n * math.log(q) for n, q in zip(counts, probabilities, strict=True)
        )
        / total,
        "mae": math.fsum(
            abs(p - q) for p, q in zip(observed, probabilities, strict=True)
        )
        / 5,
        "hellinger_squared": math.fsum(
            (math.sqrt(p) - math.sqrt(q)) ** 2
            for p, q in zip(observed, probabilities, strict=True)
        )
        / 2,
    }


def score_predictions(
    source: NativeSource, predictions: Sequence[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    """Retain failed model predictions and every independently computed baseline."""
    rows = []
    for prediction in predictions:
        row = dict(prediction)
        counts = source.counts[row["heldout_site"]]
        for taxon, count in zip(TAXA, counts, strict=True):
            row[f"observed_{taxon}"] = count
        for method in METHODS:
            if row[f"{method}_{TAXA[0]}"] == "":
                continue
            values = tuple(row[f"{method}_{taxon}"] for taxon in TAXA)
            for metric, value in score(counts, values).items():
                row[f"{method}_{metric}"] = value
        if row["empirical_status"] == "computed":
            for baseline in BASELINES:
                for metric in METRICS:
                    row[f"empirical_minus_{baseline}_{metric}"] = (
                        row[f"empirical_{metric}"] - row[f"{baseline}_{metric}"]
                    )
        rows.append(row)
    return rows


def summarize(rows: Sequence[Mapping[str, Any]]) -> dict[int, dict[str, Any]]:
    """Give full-support site/group means and all signed comparison populations."""
    result: dict[int, dict[str, Any]] = {}
    for radius in sorted({int(row["radius_label_m"]) for row in rows}):
        selected = [row for row in rows if int(row["radius_label_m"]) == radius]
        entry: dict[str, Any] = {"sites": len(selected), "methods": {}, "contrasts": {}}
        for method in METHODS:
            complete = [row for row in selected if row[f"{method}_mean_nll"] != ""]
            means: dict[str, Any] = {
                "scored_sites": len(complete),
                "full_support": len(complete) == len(SITES),
            }
            for metric in METRICS:
                values = [float(row[f"{method}_{metric}"]) for row in complete]
                means[f"site_mean_{metric}"] = (
                    math.fsum(values) / 10 if len(values) == 10 else None
                )
                group_values = [
                    [
                        float(row[f"{method}_{metric}"])
                        for row in complete
                        if row["heldout_site"] in group
                    ]
                    for group in GROUPS
                ]
                means[f"group_mean_{metric}"] = (
                    math.fsum(
                        math.fsum(values) / len(values) for values in group_values
                    )
                    / 9
                    if all(
                        len(values) == len(group)
                        for values, group in zip(group_values, GROUPS, strict=True)
                    )
                    else None
                )
            entry["methods"][method] = means
        for baseline in BASELINES:
            entry["contrasts"][baseline] = {}
            for metric in METRICS:
                values = [
                    float(row[f"empirical_minus_{baseline}_{metric}"])
                    for row in selected
                    if row[f"empirical_minus_{baseline}_{metric}"] != ""
                ]
                entry["contrasts"][baseline][metric] = {
                    "paired_sites": len(values),
                    "better": sum(v < 0 for v in values),
                    "tie": sum(v == 0 for v in values),
                    "poorer": sum(v > 0 for v in values),
                }
        result[radius] = entry
    return result
