"""Select scales within each training fold and keep outer scoring separate."""

from __future__ import annotations

from collections import defaultdict
from math import fsum
from typing import Any

from bijux_pollenomics.analysis.lra_validation.metrics import (
    hellinger_distance,
    score_pollen,
)

from .inputs import digest, require
from .outcomes import OutcomeReader


def losses(
    pollen: list[float], taxa: list[str], counts: dict[str, int]
) -> dict[str, float]:
    """Use the same reopened count denominator for all compared predictions."""
    fractions = dict(zip(taxa, pollen, strict=True))
    result = score_pollen(fractions, counts)
    require(result.status == "scored", "A compatible pollen score is required")
    assert result.mae_fraction is not None and result.total_variation is not None
    observed = {taxon: counts[taxon] / sum(counts.values()) for taxon in taxa}
    return {
        "mae_fraction": result.mae_fraction,
        "total_variation": result.total_variation,
        "hellinger": hellinger_distance(fractions, observed),
    }


def select_scales(
    packet: dict[str, Any], candidates: list[dict[str, Any]], reader: OutcomeReader
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Require all fourteen inner targets for each eligible outer-fold scale."""
    index = {(row["context_id"], row["length_scale_km"]): row for row in candidates}
    require(len(index) == len(candidates) == 450, "Unique complete candidate inventory")
    scores: list[dict[str, Any]] = []
    by_outer: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for context in packet["contexts"]:
        by_outer[context["outer_target"]].append(context)
    choices: list[dict[str, Any]] = []
    for outer, contexts in sorted(by_outer.items()):
        inner = sorted(
            (context for context in contexts if context["kind"] == "inner"),
            key=lambda context: context["target"],
        )
        outer_rows = [context for context in contexts if context["kind"] == "outer"]
        require(
            len(inner) == 14
            and len({context["target"] for context in inner}) == 14
            and len(outer_rows) == 1,
            "One outer and fourteen distinct inner contexts required",
        )
        local_scores = []
        outcome_refs = []
        for context in inner:
            rows = [index[(context["context_id"], scale)] for scale in (20.0, 100.0)]
            counts = (
                reader.read(
                    context["target"], outer_target=outer, role="inner_training"
                )
                if any(row["status"] == "predicted" for row in rows)
                else None
            )
            if counts is not None:
                outcome_refs.append(reader.refs[context["target"]])
            for row in rows:
                scored = {
                    "outer_target": outer,
                    "inner_target": context["target"],
                    "context_id": context["context_id"],
                    "length_scale_km": row["length_scale_km"],
                    "prediction_sha256": digest(row),
                    "status": "scored" if row["status"] == "predicted" else "refused",
                    **(
                        {
                            "metrics": losses(
                                row["pollen_fraction"], packet["taxa"], counts
                            )
                        }
                        if counts is not None and row["status"] == "predicted"
                        else {"reason": row.get("reason", "prediction_refused")}
                    ),
                }
                local_scores.append(scored)
        criteria: list[dict[str, Any]] = []
        for scale in (20.0, 100.0):
            complete = [
                row
                for row in local_scores
                if row["length_scale_km"] == scale and row["status"] == "scored"
            ]
            criteria.append(
                {
                    "length_scale_km": scale,
                    "scored_inner_targets": len(complete),
                    "eligible": len(complete) == 14,
                    "mean_inner_hellinger": fsum(
                        row["metrics"]["hellinger"] for row in complete
                    )
                    / 14
                    if len(complete) == 14
                    else None,
                }
            )
        eligible = [row for row in criteria if row["eligible"]]
        tied = (
            [
                row["length_scale_km"]
                for row in eligible
                if row["mean_inner_hellinger"]
                == min(item["mean_inner_hellinger"] for item in eligible)
            ]
            if eligible
            else []
        )
        selected = min(tied) if tied else None
        choice = {
            "outer_target": outer,
            "criteria": criteria,
            "selected_scale_km": selected,
            "tied_best_scales_km": tied,
            "selection_status": "refused_incomplete_inner_support"
            if selected is None
            else "selected_exact_loss_tie"
            if len(tied) > 1
            else "selected",
            "allowed_selection_inputs": {
                "inner_score_sha256s": [digest(row) for row in local_scores],
                "inner_outcome_references": outcome_refs,
                "whole_file_hashes_role": "accounting_only",
            },
            "prediction": index[(outer_rows[0]["context_id"], selected)]
            if selected is not None
            else None,
        }
        scores.extend(local_scores)
        choices.append({**choice, "choice_sha256": digest(choice)})
    require(len(scores) == 420 and len(choices) == 15, "Complete selection population")
    return scores, choices


def score_outer(
    packet: dict[str, Any], choices: list[dict[str, Any]], reader: OutcomeReader
) -> list[dict[str, Any]]:
    """Compare only the frozen selected model and three matched LRA baselines."""
    contexts = {
        context["target"]: context
        for context in packet["contexts"]
        if context["kind"] == "outer"
    }
    result: list[dict[str, Any]] = []
    for choice in choices:
        outer = choice["outer_target"]
        prediction = choice["prediction"]
        if prediction is None or prediction["status"] != "predicted":
            result.append(
                {
                    "outer_target": outer,
                    "status": "refused",
                    "choice_sha256": choice["choice_sha256"],
                }
            )
            continue
        counts = reader.read(outer, outer_target=outer, role="outer_scoring")
        baseline = contexts[outer]["reference_baselines"]
        result.append(
            {
                "outer_target": outer,
                "status": "scored",
                "choice_sha256": choice["choice_sha256"],
                "selected_scale_km": choice["selected_scale_km"],
                "observed_count": sum(counts.values()),
                "observed_reference": reader.refs[outer],
                "metrics": losses(
                    prediction["pollen_fraction"], packet["taxa"], counts
                ),
                "matched_baselines": {
                    row["baseline"]: losses(
                        [row["pollen_fraction"][taxon] for taxon in packet["taxa"]],
                        packet["taxa"],
                        counts,
                    )
                    for row in baseline
                },
                "vegetation_accuracy": "not_evaluated_no_measured_observation",
            }
        )
    return result
