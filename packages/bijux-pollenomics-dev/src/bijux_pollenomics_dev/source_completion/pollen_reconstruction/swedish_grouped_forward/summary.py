"""Inspect complete saved ledgers and summarize paired development losses."""

from __future__ import annotations

from collections import Counter
import math
import statistics
from typing import Any

GROUPS = ("all_returned_publication_relations", "primary_publication_relations")
PROFILES = (
    "double_metadata_radius_wind_3",
    "half_metadata_radius_wind_3",
    "metadata_radius_wind_2",
    "metadata_radius_wind_3",
    "metadata_radius_wind_4",
)
METHODS = ("forward_panel_fraction", "count_pooled_pollen", "equal_source_pollen_mean")
METRICS = (
    "absolute_composition_error",
    "squared_composition_error",
    "multinomial_negative_log_likelihood",
)


def _require(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def _key(row: dict[str, Any]) -> tuple[Any, ...]:
    return tuple(
        row[name]
        for name in (
            "grouping_scenario",
            "profile_id",
            "target_dataset_id",
            "target_unit_id",
            "target_chronology_id",
            "window_index",
        )
    )


def _integer(value: object) -> int:
    if type(value) is not int or value < 0:
        raise ValueError("Captured panel count must be a nonnegative integer")
    return value


def _metric(row: dict[str, Any], method: str, metric: str) -> float:
    value = row["metrics"][method][metric]
    if metric == "multinomial_negative_log_likelihood":
        _require(
            isinstance(value, dict) and value["kind"] == "finite",
            "Captured multinomial loss kind differs",
        )
        value = value["value"]
    _require(
        type(value) in (int, float) and math.isfinite(value) and value >= 0,
        "Captured loss is not finite nonnegative",
    )
    return float(value)


def summarize(inputs: dict[str, Any]) -> dict[str, Any]:
    prediction = inputs["prediction-ledger.json"]
    scores = inputs["score-ledger.json"]
    terminal = inputs["native-terminal.json"]
    review = inputs["independent-score-review.json"]
    preflight = inputs["source-preflight.json"]
    protocol = inputs["protocol.json"]
    from .authority import CAPTURE_PINS

    _require(
        terminal["status"] == "PASS"
        and terminal["last_native_exit"] == 0
        and terminal["custody_after_checked"]
        and terminal["custody_after_unchanged"]
        and not terminal["owned_survivors"]
        and not terminal["custody_errors"],
        "Original native terminal did not pass custody",
    )
    _require(
        [row["name"] for row in terminal["stages"]]
        == ["guards", "predict", "score", "independent_scores"]
        and all(row["native_exit"] == 0 for row in terminal["stages"]),
        "Original native stage membership differs",
    )
    _require(
        terminal["prediction_sha256"]
        == review["prediction_sha256"]
        == scores["frozen_prediction_sha256"]
        == CAPTURE_PINS["prediction-ledger.json"],
        "Prediction freeze identity differs",
    )
    _require(
        terminal["scores_sha256"]
        == review["scores_sha256"]
        == CAPTURE_PINS["score-ledger.json"]
        and terminal["independent_score_review_sha256"]
        == CAPTURE_PINS["independent-score-review.json"],
        "Score/review identity differs",
    )
    _require(
        prediction["protocol_sha256"] == CAPTURE_PINS["protocol.json"]
        and prediction["source_preflight_sha256"]
        == scores["source_preflight_sha256"]
        == CAPTURE_PINS["source-preflight.json"],
        "Protocol/preflight identity differs",
    )
    _require(
        prediction["target_count_values_used"] is False
        and prediction["all_profiles_reported_no_outcome_selection"] is True
        and scores["no_profile_selected_by_scores"] is True,
        "Outcome exposure or profile selection changed",
    )
    for owner in (prediction, scores):
        for name in ("historical_reproduction_claim", "untouched_confirmation_claim"):
            _require(owner[name] is False, "Scientific claim scope changed")
    _require(
        prediction["ppe_identification_claim"] is False
        and prediction["vegetation_accuracy_claim"] is False
        and scores["independent_vegetation_accuracy_claim"] is False,
        "Scientific scope differs",
    )
    _require(
        review["all_metric_values_compared"] == 1890
        and review["actual_scored_attempts"] == 210
        and review["Decimal_precision"] == 50
        and review["typed_infinite_multinomial_losses"] == 0,
        "Independent score-review population differs",
    )
    _require(
        review["absolute_tolerance"] == "2e-9"
        and review["relative_tolerance"] == "2e-10",
        "Independent score-review tolerance differs",
    )
    _require(
        float(review["maximum_absolute_difference"]) <= 2e-9,
        "Independent score-review discrepancy exceeds absolute tolerance",
    )
    _require(
        protocol["place_time_panel_support"]["taxon_axis"] == ["Betula", "Poaceae"],
        "Literal panel axis differs",
    )
    p_rows = prediction["results"]
    s_rows = scores["results"]
    _require(
        len(p_rows) == len(s_rows) == 4750, "Complete attempt ledger population differs"
    )
    p_index = {_key(row): row for row in p_rows}
    s_index = {_key(row): row for row in s_rows}
    _require(
        len(p_index) == len(s_index) == 4750 and set(p_index) == set(s_index),
        "Attempt identities duplicate or differ",
    )
    _require(
        set(key[0] for key in p_index) == set(GROUPS)
        and set(key[1] for key in p_index) == set(PROFILES),
        "Grouping/profile population differs",
    )
    dataset_ids = {key[2] for key in p_index}
    _require(
        len(dataset_ids) == 19 and set(key[5] for key in p_index) == set(range(25)),
        "Declared dataset/window domain differs",
    )
    _require(
        set((k[0], k[1], k[2], k[5]) for k in p_index)
        == {
            (g, p, d, w)
            for g in GROUPS
            for p in PROFILES
            for d in dataset_ids
            for w in range(25)
        },
        "Attempt grid is not complete",
    )
    records = {row["dataset_id"]: row for row in preflight["records"]}
    folds = {
        (
            row["grouping_scenario"],
            row["target_dataset_id"],
            row["target_unit_id"],
            row["target_chronology_id"],
            row["window_index"],
        ): row
        for row in preflight["folds"]
    }
    _require(
        len(folds) == len(preflight["folds"]) == 950 and set(records) == dataset_ids,
        "Source preflight folds or dataset identities differ",
    )
    ledger = []
    scored = []
    unique: dict[tuple[Any, ...], tuple[tuple[Any, ...], Any]] = {}
    for key in sorted(p_index):
        p = p_index[key]
        s = s_index[key]
        record = records[key[2]]
        _require(
            (record["collection_unit_id"], record["chronology_id"]) == (key[3], key[4]),
            "Native unit/chronology identity differs",
        )
        fold = folds[(key[0], key[2], key[3], key[4], key[5])]
        _require(
            fold["target_outcome_presence_used_for_prediction"] is False,
            "Source fold consulted outcome availability",
        )
        row = {
            name: p[name]
            for name in (
                "grouping_scenario",
                "profile_id",
                "target_dataset_id",
                "target_unit_id",
                "target_chronology_id",
                "window_index",
            )
        }
        row.update(
            {
                "prediction_status": p["status"],
                "scoring_status": s["status"],
                "window_cal_bp": [
                    fold["younger_cal_bp"],
                    fold["older_cal_bp_exclusive"],
                ],
                "training_dataset_ids": list(p["training_dataset_ids"]),
                "training_dependency_groups": list(p["training_dependency_groups"]),
            }
        )
        if p["status"] == "refused_source_support":
            _require(
                s["status"] == "prediction_refused" and p["causes"] == s["causes"],
                "Source refusal was lost or changed",
            )
            row["causes"] = list(p["causes"])
        else:
            _require(
                p["status"] == "predicted" and p["target_count_values_used"] is False,
                "Prediction source status differs",
            )
            _require(
                len(set(p["training_dependency_groups"])) >= 2
                and key[2] not in p["training_dataset_ids"],
                "Prediction dependency support differs",
            )
            _require(
                s["status"] in {"scored", "refused_target_outcome"},
                "Predicted outcome status differs",
            )
            if s["status"] == "refused_target_outcome":
                _require(
                    s["cause"] == "no_literal_target_panel_in_fixed_window",
                    "Missing target outcome cause differs",
                )
                row["causes"] = [s["cause"]]
            else:
                counts = s["observed_panel_counts"]
                _require(
                    isinstance(counts, list)
                    and len(counts) == 2
                    and sum(_integer(x) for x in counts)
                    == _integer(s["observed_panel_denominator"])
                    > 0,
                    "Observed panel denominator differs",
                )
                unique_key = key[2:]
                signature = (tuple(counts), s["observed_panel_denominator"])
                _require(
                    unique_key not in unique or unique[unique_key] == signature,
                    "Reused target outcome differs across profiles/groupings",
                )
                unique[unique_key] = signature
                metrics = {
                    method: {metric: _metric(s, method, metric) for metric in METRICS}
                    for method in METHODS
                }
                differences: dict[str, dict[str, Any]] = {
                    baseline: {
                        metric: metrics[METHODS[0]][metric] - metrics[baseline][metric]
                        for metric in METRICS
                    }
                    for baseline in METHODS[1:]
                }
                scored.append(
                    {
                        **row,
                        "saved_metrics": metrics,
                        "forward_minus_baseline": differences,
                    }
                )
        ledger.append(row)
    _require(
        len(unique) == 21 and sum(value[1] for value in unique.values()) == 37300,
        "Distinct scored outcome or panel mass differs",
    )
    _require(
        {key[0] for key in unique} == {23013, 53999, 54001}
        and {key[3] for key in unique} == set(range(1, 8)),
        "Scored native source/window support differs",
    )
    for key in unique:
        _require(
            str(records[key[0]]["grid_id"]) == "779", "Scored grid support differs"
        )
    populations = []
    comparisons = []
    for grouping in GROUPS:
        ps = [r for r in ledger if r["grouping_scenario"] == grouping]
        _require(
            Counter(r["prediction_status"] for r in ps)
            == {"predicted": 135, "refused_source_support": 2240},
            "Prediction population differs",
        )
        _require(
            Counter(r["scoring_status"] for r in ps)
            == {
                "scored": 105,
                "refused_target_outcome": 30,
                "prediction_refused": 2240,
            },
            "Scoring/refusal population differs",
        )
        populations.append(
            {
                "grouping_scenario": grouping,
                "attempts": 2375,
                "predictions": 135,
                "scored_records": 105,
                "missing_target_outcomes": 30,
                "source_support_refusals": 2240,
                "overlapping_refusal_cause_counts": dict(
                    Counter(
                        c
                        for r in ps
                        if r["prediction_status"] == "refused_source_support"
                        for c in r["causes"]
                    )
                ),
            }
        )
        for profile in PROFILES:
            rows = [
                r
                for r in scored
                if r["grouping_scenario"] == grouping and r["profile_id"] == profile
            ]
            _require(len(rows) == 21, "Profile target support differs")
            means = {
                method: {
                    metric: statistics.fmean(
                        row["saved_metrics"][method][metric] for row in rows
                    )
                    for metric in METRICS
                }
                for method in METHODS
            }
            differences = {}
            for baseline in METHODS[1:]:
                differences[baseline] = {}
                for metric in METRICS:
                    delta = [
                        row["forward_minus_baseline"][baseline][metric] for row in rows
                    ]
                    differences[baseline][metric] = {
                        "macro_mean_forward_minus_baseline": statistics.fmean(delta),
                        "lower_error": sum(v < 0 for v in delta),
                        "equal_error": sum(v == 0 for v in delta),
                        "higher_error": sum(v > 0 for v in delta),
                        "paired_target_window_denominator": 21,
                    }
            comparisons.append(
                {
                    "grouping_scenario": grouping,
                    "profile_id": profile,
                    "macro_means": means,
                    "matched_differences": differences,
                    "mean_per_taxon_absolute_error_percentage_points": 50
                    * means[METHODS[0]][METRICS[0]],
                    "equal_target_window_denominator": 21,
                }
            )

    def stripped(rows: list[dict[str, Any]], group: str) -> list[dict[str, Any]]:
        return [
            {k: v for k, v in row.items() if k != "grouping_scenario"}
            for row in rows
            if row["grouping_scenario"] == group
        ]

    grouping_equal = stripped(p_rows, GROUPS[0]) == stripped(
        p_rows, GROUPS[1]
    ) and stripped(s_rows, GROUPS[0]) == stripped(s_rows, GROUPS[1])
    _require(grouping_equal, "Original grouping ledger equivalence changed")
    sources = [
        {
            "dataset_id": did,
            "collection_unit_id": records[did]["collection_unit_id"],
            "chronology_id": records[did]["chronology_id"],
            "core_handle": records[did]["core_handle"],
            "grid_context": "779",
            "source_primary_publication_ids": records[did]["primary_publication_ids"],
        }
        for did in sorted({k[0] for k in unique})
    ]
    return {
        "schema_version": "swedish-grouped-forward-development-summary.v1",
        "scope": "Saved-loss aggregation only: conditional, already-exposed Betula/Poaceae forward-pollen development; no fresh physical or model execution.",
        "actual_scientific_candidate": terminal["candidate"],
        "actual_scientific_plan_sha256": terminal["plan_sha256"],
        "literal_taxon_axis": ["Betula", "Poaceae"],
        "populations": {
            "declared_attempts": 4750,
            "predictions": 270,
            "scored_records": 210,
            "missing_target_outcomes": 60,
            "source_support_refusals": 4480,
            "distinct_scored_target_windows": 21,
            "distinct_scored_native_collection_units": 3,
            "distinct_scored_panel_N": 37300,
            "independent_metric_values_checked": 1890,
        },
        "grouping_populations": populations,
        "all_attempt_statuses": ledger,
        "all_scored_fold_comparisons": scored,
        "all_profile_comparisons": comparisons,
        "scored_sources": sources,
        "grouping_full_ledger_equivalence_observed": grouping_equal,
        "no_profile_selected": True,
        "PPE_identification_claim": False,
        "vegetation_accuracy_claim": False,
        "untouched_confirmation_claim": False,
        "historical_reproduction_claim": False,
        "empirical_interval_coverage_claim": False,
        "raw_counts_in_public_output": False,
        "uncertainty": "Fixed point ages/static geometry and exposed outcomes; dependent profiles/groupings are not independent replicate measurements or calibrated uncertainty.",
    }
