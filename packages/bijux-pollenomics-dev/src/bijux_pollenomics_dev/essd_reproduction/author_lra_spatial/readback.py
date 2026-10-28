"""Independent nested selection, loss arithmetic and role-specific log checks.

Counts and frozen product identities are supplied by a separate source audit.
Saved inner Hellinger scalars are checked numerically before their exact native
binary64 criterion/tie semantics are checked, without adding a tolerance tie.
"""

from __future__ import annotations

from collections import Counter
import hashlib
import json
import math
import re
from typing import Any

SCALES = (20.0, 100.0)
BASELINES = ("training_mean", "nearest_site", "inverse_distance_squared")


def _require(condition: object, message: str) -> None:
    if not condition:
        raise ValueError("Independent spatial readback: " + message)


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode()
    ).hexdigest()


def _exact(actual: Any, expected: Any) -> None:
    _require(
        type(actual) is type(expected)
        and json.dumps(actual, sort_keys=True, separators=(",", ":"), allow_nan=False)
        == json.dumps(expected, sort_keys=True, separators=(",", ":"), allow_nan=False),
        "literal frozen metadata disagreement",
    )


def _number(value: Any) -> float:
    _require(
        type(value) in (int, float) and math.isfinite(value), "finite score scalar"
    )
    return float(value)


def _metrics(
    pollen: list[float], taxa: list[str], counts: dict[str, int]
) -> dict[str, float]:
    _require(
        len(pollen) == len(taxa) and set(counts) == set(taxa),
        "complete scoring taxon axis",
    )
    _require(
        all(type(value) is int and value >= 0 for value in counts.values())
        and 0 < sum(counts.values()) <= 2**53,
        "positive exact integer scoring denominator",
    )
    p = [_number(value) for value in pollen]
    _require(
        min(p) >= 0 and max(p) <= 1 and abs(math.fsum(p) - 1) <= 1e-9,
        "scored fraction composition",
    )
    observed = [counts[taxon] / sum(counts.values()) for taxon in taxa]
    absolute_error = math.fsum(
        abs(value - truth) for value, truth in zip(p, observed, strict=True)
    )
    # Rationalizing the square-root difference avoids cancellation for nearby
    # fractions; hypot avoids premature squaring underflow.
    differences = [
        (value - truth) / (math.sqrt(value) + math.sqrt(truth))
        if value or truth
        else 0.0
        for value, truth in zip(p, observed, strict=True)
    ]
    return {
        "mae_fraction": absolute_error / len(taxa),
        "total_variation": absolute_error / 2,
        "hellinger": math.hypot(*differences) / math.sqrt(2),
    }


def _check_metrics(actual: dict[str, Any], expected: dict[str, float]) -> None:
    _require(
        type(actual) is dict and set(actual) == set(expected), "three loss metrics"
    )
    for key, reference in expected.items():
        value = _number(actual[key])
        _require(
            value >= 0 and abs(value - reference) <= 1e-12 + 1e-10 * abs(reference),
            "independent loss disagreement",
        )


def audit_evaluation(
    packet: dict[str, Any],
    candidates: list[dict[str, Any]],
    inner_scores: list[dict[str, Any]],
    choices: list[dict[str, Any]],
    outer_scores: list[dict[str, Any]],
    accesses: list[dict[str, Any]],
    counts_by_record: dict[str, dict[str, int]],
    *,
    prediction_freeze_sha256: str,
    selection_freeze_sha256: str,
) -> dict[str, Any]:
    """Audit supplied closed products; do not reopen sources or produce new predictions."""
    for identity in (prediction_freeze_sha256, selection_freeze_sha256):
        _require(
            type(identity) is str
            and re.fullmatch(r"[a-f0-9]{64}", identity) is not None,
            "closed stage SHA256",
        )
    taxa, groups = packet["taxa"], packet["groups"]
    _require(
        len(taxa) == len(set(taxa)) == 30 and len(groups) == 15,
        "fixed source population",
    )
    _require(set(counts_by_record) == set(groups), "all source-bound outcome owners")
    for counts in counts_by_record.values():
        _require(
            set(counts) == set(taxa)
            and all(type(value) is int and value >= 0 for value in counts.values())
            and 0 < sum(counts.values()) <= 2**53,
            "complete source-bound integer count denominator",
        )
    refs = {row["record_id"]: row for row in packet["observation_refs"]}
    _require(
        len(refs) == len(packet["observation_refs"]) == 15 and set(refs) == set(groups),
        "fifteen exact observation references",
    )
    contexts = {row["context_id"]: row for row in packet["contexts"]}
    _require(len(contexts) == len(packet["contexts"]) == 225, "225 unique contexts")
    roles = {(row["outer_target"], row["target"]): row for row in contexts.values()}
    _require(
        len(roles) == 225
        and set(roles) == {(outer, target) for outer in groups for target in groups},
        "complete outer/inner source roles",
    )
    candidate_index = {
        (row["context_id"], row["length_scale_km"]): row for row in candidates
    }
    _require(
        len(candidate_index) == len(candidates) == 450
        and set(candidate_index)
        == {(context, scale) for context in contexts for scale in SCALES},
        "450 unique frozen candidate rows",
    )
    _require(
        len(inner_scores) == 420 and len(choices) == len(outer_scores) == 15,
        "complete 420/15/15 readback populations",
    )
    expected_accesses, expected_outer = [], []
    position = 0
    for outer_index, outer in enumerate(sorted(groups)):
        local_scores, outcome_refs = [], []
        for target in sorted(set(groups) - {outer}):
            context = roles[(outer, target)]
            _require(
                context["kind"] == "inner"
                and outer not in context["scientific_refs"]["training_record_ids"]
                and target not in context["scientific_refs"]["training_record_ids"],
                "withheld owners excluded from selection predictors",
            )
            rows = [candidate_index[(context["context_id"], scale)] for scale in SCALES]
            _require(
                all(row["status"] in ("predicted", "refused") for row in rows),
                "closed candidate dispositions",
            )
            if any(row["status"] == "predicted" for row in rows):
                outcome_refs.append(refs[target])
                expected_accesses.append(
                    {
                        "outer_target": outer,
                        "observed_record_id": target,
                        "role": "inner_training",
                        "observation_reference": refs[target],
                        "freeze_sha256": prediction_freeze_sha256,
                    }
                )
            for row in rows:
                actual = inner_scores[position]
                position += 1
                metadata = {
                    "outer_target": outer,
                    "inner_target": target,
                    "context_id": context["context_id"],
                    "length_scale_km": row["length_scale_km"],
                    "prediction_sha256": _digest(row),
                    "status": "scored" if row["status"] == "predicted" else "refused",
                }
                if row["status"] == "predicted":
                    _require(
                        set(actual) == set(metadata) | {"metrics"},
                        "inner scored fields",
                    )
                    _exact({key: actual[key] for key in metadata}, metadata)
                    _check_metrics(
                        actual["metrics"],
                        _metrics(
                            row["pollen_fraction"], taxa, counts_by_record[target]
                        ),
                    )
                else:
                    _exact(
                        actual,
                        {**metadata, "reason": row.get("reason", "prediction_refused")},
                    )
                local_scores.append(actual)
        criteria: list[dict[str, Any]] = []
        for scale in SCALES:
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
                    "mean_inner_hellinger": math.fsum(
                        row["metrics"]["hellinger"] for row in complete
                    )
                    / 14
                    if len(complete) == 14
                    else None,
                }
            )
        eligible = [row for row in criteria if row["eligible"]]
        minimum = min((row["mean_inner_hellinger"] for row in eligible), default=None)
        tied: list[float] = [
            row["length_scale_km"]
            for row in eligible
            if row["mean_inner_hellinger"] == minimum
        ]
        selected_scale = min(tied) if tied else None
        outer_context = roles[(outer, outer)]
        _require(outer_context["kind"] == "outer", "one outer scoring context")
        expected_choice = {
            "outer_target": outer,
            "criteria": criteria,
            "selected_scale_km": selected_scale,
            "tied_best_scales_km": tied,
            "selection_status": "refused_incomplete_inner_support"
            if selected_scale is None
            else "selected_exact_loss_tie"
            if len(tied) > 1
            else "selected",
            "allowed_selection_inputs": {
                "inner_score_sha256s": [_digest(row) for row in local_scores],
                "inner_outcome_references": outcome_refs,
                "whole_file_hashes_role": "accounting_only",
            },
            "prediction": candidate_index[(outer_context["context_id"], selected_scale)]
            if selected_scale is not None
            else None,
        }
        expected_choice["choice_sha256"] = _digest(expected_choice)
        _exact(choices[outer_index], expected_choice)
        prediction = expected_choice["prediction"]
        if prediction is None or prediction["status"] != "predicted":
            expected_outer.append(
                {
                    "outer_target": outer,
                    "status": "refused",
                    "choice_sha256": expected_choice["choice_sha256"],
                }
            )
            continue
        baseline = outer_context["reference_baselines"]
        _require(
            [row["baseline"] for row in baseline] == list(BASELINES),
            "three matched baseline identities",
        )
        _require(
            all(set(row["pollen_fraction"]) == set(taxa) for row in baseline),
            "matched baseline denominator",
        )
        expected_outer.append(
            {
                "outer_target": outer,
                "status": "scored",
                "choice_sha256": expected_choice["choice_sha256"],
                "selected_scale_km": selected_scale,
                "observed_count": sum(counts_by_record[outer].values()),
                "observed_reference": refs[outer],
                "metrics": _metrics(
                    prediction["pollen_fraction"], taxa, counts_by_record[outer]
                ),
                "matched_baselines": {
                    row["baseline"]: _metrics(
                        [row["pollen_fraction"][taxon] for taxon in taxa],
                        taxa,
                        counts_by_record[outer],
                    )
                    for row in baseline
                },
                "vegetation_accuracy": "not_evaluated_no_measured_observation",
            }
        )
    for actual, expected in zip(outer_scores, expected_outer, strict=True):
        if expected["status"] == "refused":
            _exact(actual, expected)
        else:
            _require(set(actual) == set(expected), "outer scored fields")
            _exact(
                {
                    key: value
                    for key, value in actual.items()
                    if key not in ("metrics", "matched_baselines")
                },
                {
                    key: value
                    for key, value in expected.items()
                    if key not in ("metrics", "matched_baselines")
                },
            )
            _check_metrics(actual["metrics"], expected["metrics"])
            _require(
                set(actual["matched_baselines"]) == set(BASELINES),
                "complete outer baseline scores",
            )
            for baseline in BASELINES:
                _check_metrics(
                    actual["matched_baselines"][baseline],
                    expected["matched_baselines"][baseline],
                )
            outer = expected["outer_target"]
            expected_accesses.append(
                {
                    "outer_target": outer,
                    "observed_record_id": outer,
                    "role": "outer_scoring",
                    "observation_reference": refs[outer],
                    "freeze_sha256": selection_freeze_sha256,
                }
            )
    _exact(accesses, expected_accesses)
    return {
        "status": "passed",
        "inner_scores_verified": 420,
        "choices_verified": 15,
        "outer_scores_verified": 15,
        "inner_statuses": dict(Counter(row["status"] for row in inner_scores)),
        "outer_statuses": dict(Counter(row["status"] for row in outer_scores)),
        "accesses_verified": len(accesses),
        "tie_semantics": "Exact native binary64 criteria from independently checked closed inner losses; no tolerance ties",
        "scope": "Supplied source-bound counts, numerical losses, nested selection and recorded role/freeze admission; no independent dynamic filesystem trace or field validation",
    }
