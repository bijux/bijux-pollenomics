"""Joint candidate/spatial selection using only a fixed outer training set."""

from __future__ import annotations

from collections.abc import Callable
import math
from typing import Any

Json = dict[str, Any]
FIELDS = {
    "method",
    "outer_target",
    "inner_target",
    "inner_train_record_ids",
    "inner_train_group_ids",
    "baseline",
    "bin_id",
    "status",
    "metrics",
    "prediction_sha256",
}


METRIC_FIELDS = {
    "bias_fraction",
    "count_conditioned_deviance",
    "mae_fraction",
    "missing_observed_taxa",
    "observed_total_count",
    "rmse_fraction",
    "scored_taxon_count",
    "signed_error_by_taxon",
    "status",
    "target",
    "taxon_count",
    "total_variation",
    "zero_probability_positive_count",
}


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def choose(
    outer: str,
    records: list[str],
    groups: dict[str, str],
    catalogue: list[Json],
    rows: dict[tuple[str, str, str, str], Json],
    eligible: Callable[[Json], bool],
) -> Json:
    """No outer prediction, outer outcome, raw count or alternate-window argument."""
    require(
        len(records) == len(set(records)) == 15 and outer in records,
        "Exact fifteen-record stratum required",
    )
    require(
        set(groups) == set(records) and len(set(groups.values())) == 15,
        "Complete distinct admitted source groups required",
    )
    expected = set(records) - {outer}
    pair_ids = [(p["candidate_id"], p["spatial_id"]) for p in catalogue]
    require(
        len(pair_ids) == len(set(pair_ids)),
        "Unique declared candidate/spatial pairs required",
    )
    source_ids = {
        (p["source_candidate_id"], p["spatial_id"])
        for p in catalogue
        if p["eligibility"] != "prerequisite_refused"
    }
    relevant = {key: row for key, row in rows.items() if key[2] == outer}
    require(
        set(relevant)
        == {
            (candidate, spatial, outer, target)
            for candidate, spatial in source_ids
            for target in expected
        },
        "Complete exact declared pair/fourteen-inner grid required",
    )
    ranking = []
    for pair in catalogue:
        candidate, spatial = pair["candidate_id"], pair["spatial_id"]
        if pair["eligibility"] == "prerequisite_refused":
            ranking.append(
                {
                    "candidate_id": candidate,
                    "spatial_id": spatial,
                    "complete_inner_predictions": 0,
                    "expected_inner_targets": 14,
                    "mean_inner_total_variation": None,
                    "status": "prerequisite_refused",
                    "reason_code": pair["reason_code"],
                    "evidence": pair["evidence"],
                }
            )
            continue
        require(
            pair["eligibility"] in ("saved_prediction", "source_equivalent_alias"),
            "Unknown pair eligibility",
        )
        values = []
        for target in sorted(expected):
            row = relevant[(pair["source_candidate_id"], spatial, outer, target)]
            require(
                set(row) == FIELDS
                and row["outer_target"] == outer
                and row["inner_target"] == target
                and row["baseline"] == spatial
                and row["method"] == pair["method"]
                and row["bin_id"] == "author-TW5",
                "Exact training-only stored-score fields required",
            )
            training = row["inner_train_record_ids"]
            identities = row["inner_train_group_ids"]
            require(
                len(training) == len(set(training)) == 13
                and set(training) == expected - {target},
                "Foreign/duplicate/outer target reached inner training",
            )
            require(
                len(identities) == len(set(identities)) == 13
                and set(identities) == {groups[r] for r in training}
                and groups[outer] not in identities
                and groups[target] not in identities,
                "Whole-group/alias exclusion changed",
            )
            require(
                isinstance(row["prediction_sha256"], str)
                and len(row["prediction_sha256"]) == 64,
                "Frozen inner prediction identity required",
            )
            if row["status"] == "scored":
                metrics = row["metrics"]
                require(
                    isinstance(metrics, dict) and set(metrics) == METRIC_FIELDS,
                    "Exact inner metrics only; no outer label fields",
                )
                errors = metrics["signed_error_by_taxon"]
                require(
                    isinstance(errors, list)
                    and len(errors) == 30
                    and all(
                        isinstance(pair, list)
                        and len(pair) == 2
                        and isinstance(pair[0], str)
                        for pair in errors
                    )
                    and len({pair[0] for pair in errors}) == 30
                    and type(metrics["taxon_count"]) is int
                    and metrics["taxon_count"] == 30
                    and type(metrics["scored_taxon_count"]) is int
                    and metrics["scored_taxon_count"] == 30,
                    "Exact thirty-taxon stored error population required",
                )
            if eligible(row):
                metrics = row["metrics"]
                require(
                    metrics["rmse_fraction"] >= 0
                    and metrics["mae_fraction"] >= 0
                    and type(metrics["observed_total_count"]) is int
                    and metrics["observed_total_count"] > 0,
                    "Valid stored metric population required",
                )
                values.append(metrics["total_variation"])
        complete = len(values)
        ranking.append(
            {
                "candidate_id": candidate,
                "spatial_id": spatial,
                "source_candidate_id": pair["source_candidate_id"],
                "complete_inner_predictions": complete,
                "expected_inner_targets": 14,
                "mean_inner_total_variation": math.fsum(values) / 14
                if complete == 14
                else None,
                "status": "complete" if complete == 14 else "incomplete",
                "eligibility": pair["eligibility"],
                "evidence": pair["evidence"],
            }
        )
    complete_pairs = [row for row in ranking if row["complete_inner_predictions"] == 14]
    winner = (
        min(
            complete_pairs,
            key=lambda p: (
                p["mean_inner_total_variation"],
                p["candidate_id"],
                p["spatial_id"],
            ),
        )
        if complete_pairs
        else None
    )
    return {
        "outer_target": outer,
        "status": "selected" if winner else "refused",
        "selected_pair": {
            k: winner[k] for k in ("candidate_id", "spatial_id", "source_candidate_id")
        }
        if winner
        else None,
        "ranking": ranking,
        "selection_scope": "Exactly fourteen inner targets; full coverage then equal-inner meanTV, candidateID, spatialID. Retrospective exposed development, never an untouched test.",
    }


def freeze_choices(
    choices: list[Json],
    outer_slots: dict[tuple[str, str, str], Json],
    digest: Callable[[Any], str],
) -> list[Json]:
    require(
        len(choices) == len({c["outer_target"] for c in choices}) == 15,
        "All fifteen pair choices required",
    )
    frozen = []
    for choice in choices:
        target, pair = choice["outer_target"], choice["selected_pair"]
        if pair is None:
            frozen.append(
                {
                    "outer_target": target,
                    "status": "selection_refused",
                    "selected_pair": None,
                    "reason_code": "no_complete_fourteen_inner_pair",
                }
            )
            continue
        source = outer_slots[(pair["source_candidate_id"], pair["spatial_id"], target)]
        require(
            source["kind"] == "outer"
            and source["outer_target"] == source["target"] == target
            and source["baseline"] == pair["spatial_id"],
            "Chosen outer prediction identity differs",
        )
        require(
            source["status"] in ("predicted", "refused"),
            "Original outer disposition required",
        )
        frozen.append(
            {
                "outer_target": target,
                "status": source["status"],
                "selected_pair": pair,
                "source_slot_sha256": digest(source),
                "source_prediction_manifest_sha256": source.get("prediction", {}).get(
                    "prediction_manifest_sha256"
                ),
                "source_slot": source,
                "alias_creates_no_new_prediction_manifest": True,
            }
        )
    return frozen
