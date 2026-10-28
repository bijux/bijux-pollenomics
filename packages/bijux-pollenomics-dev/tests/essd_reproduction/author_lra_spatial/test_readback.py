"""Independent literal nested-selection populations, losses and custody roles."""

from __future__ import annotations

from copy import deepcopy
import math
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial.readback import (
    _metrics,
    audit_evaluation,
)

from .test_audit import complete as complete
from .test_audit import sha

PREDICTION = "f" * 64
SELECTION = "e" * 64
BASELINES = ("training_mean", "nearest_site", "inverse_distance_squared")


def literal_metrics(pollen: list[float], observed: list[float]) -> dict[str, float]:
    absolute = sum(abs(p - o) for p, o in zip(pollen, observed, strict=True))
    # A separate square-root difference is adequate for these far-from-equal
    # fixture baselines; near-equality gets its own analytical control below.
    h = math.sqrt(
        sum(
            (math.sqrt(p) - math.sqrt(o)) ** 2
            for p, o in zip(pollen, observed, strict=True)
        )
        / 2
    )
    return {
        "mae_fraction": absolute / 30,
        "total_variation": absolute / 2,
        "hellinger": h,
    }


@pytest.fixture(scope="module")
def evaluated(complete: tuple[dict[str, Any], list[dict[str, Any]]]) -> tuple[Any, ...]:
    packet, candidates = deepcopy(complete)
    taxa, sites = packet["taxa"], sorted(packet["groups"])
    counts = {site: dict(zip(taxa, [2, 1] + [0] * 28, strict=True)) for site in sites}
    refs = {
        site: {
            "record_id": site,
            "path": site + "-raw.json",
            "bytes": 100,
            "sha256": sha(site),
        }
        for site in sites
    }
    packet["observation_refs"] = list(refs.values())
    baseline_vectors = (
        [2 / 3, 1 / 3] + [0.0] * 28,
        [1.0] + [0.0] * 29,
        [0.5, 0.5] + [0.0] * 28,
    )
    for context in packet["contexts"]:
        context["reference_baselines"] = [
            {
                "baseline": name,
                "vegetation_fraction": dict(zip(taxa, [1.0] + [0.0] * 29, strict=True)),
                "pollen_fraction": dict(zip(taxa, vector, strict=True)),
            }
            for name, vector in zip(BASELINES, baseline_vectors, strict=True)
        ]
    by_role = {(row["outer_target"], row["target"]): row for row in packet["contexts"]}
    predictions = {
        (row["context_id"], row["length_scale_km"]): row for row in candidates
    }
    inner_scores, choices, outer_scores, accesses = [], [], [], []
    zero = {"mae_fraction": 0.0, "total_variation": 0.0, "hellinger": 0.0}
    for outer in sites:
        local_scores, outcome_refs = [], []
        for target in sorted(set(sites) - {outer}):
            context = by_role[(outer, target)]
            for scale in (20.0, 100.0):
                prediction = predictions[(context["context_id"], scale)]
                local_scores.append(
                    {
                        "outer_target": outer,
                        "inner_target": target,
                        "context_id": context["context_id"],
                        "length_scale_km": scale,
                        "prediction_sha256": sha(prediction),
                        "status": "scored",
                        "metrics": deepcopy(zero),
                    }
                )
            outcome_refs.append(refs[target])
            accesses.append(
                {
                    "outer_target": outer,
                    "observed_record_id": target,
                    "role": "inner_training",
                    "observation_reference": refs[target],
                    "freeze_sha256": PREDICTION,
                }
            )
        inner_scores.extend(local_scores)
        prediction = predictions[(by_role[(outer, outer)]["context_id"], 20.0)]
        choice = {
            "outer_target": outer,
            "criteria": [
                {
                    "length_scale_km": scale,
                    "scored_inner_targets": 14,
                    "eligible": True,
                    "mean_inner_hellinger": 0.0,
                }
                for scale in (20.0, 100.0)
            ],
            "selected_scale_km": 20.0,
            "tied_best_scales_km": [20.0, 100.0],
            "selection_status": "selected_exact_loss_tie",
            "allowed_selection_inputs": {
                "inner_score_sha256s": [sha(row) for row in local_scores],
                "inner_outcome_references": outcome_refs,
                "whole_file_hashes_role": "accounting_only",
            },
            "prediction": deepcopy(prediction),
        }
        choice["choice_sha256"] = sha(choice)
        choices.append(choice)
        outer_scores.append(
            {
                "outer_target": outer,
                "status": "scored",
                "choice_sha256": choice["choice_sha256"],
                "selected_scale_km": 20.0,
                "observed_count": 3,
                "observed_reference": refs[outer],
                "metrics": deepcopy(zero),
                "matched_baselines": {
                    name: literal_metrics(vector, baseline_vectors[0])
                    for name, vector in zip(BASELINES, baseline_vectors, strict=True)
                },
                "vegetation_accuracy": "not_evaluated_no_measured_observation",
            }
        )
    accesses.extend(
        {
            "outer_target": site,
            "observed_record_id": site,
            "role": "outer_scoring",
            "observation_reference": refs[site],
            "freeze_sha256": SELECTION,
        }
        for site in sites
    )
    return packet, candidates, inner_scores, choices, outer_scores, accesses, counts


def check(values: tuple[Any, ...]) -> dict[str, Any]:
    return audit_evaluation(
        *values, prediction_freeze_sha256=PREDICTION, selection_freeze_sha256=SELECTION
    )


def replace_choice_hash(choice: dict[str, Any]) -> None:
    choice["choice_sha256"] = sha(
        {key: value for key, value in choice.items() if key != "choice_sha256"}
    )


def test_complete_zero_loss_ties_choose_lower_scale_with_all_role_accesses(
    evaluated: tuple[Any, ...],
) -> None:
    result = check(evaluated)
    assert result["inner_scores_verified"] == 420
    assert result["choices_verified"] == result["outer_scores_verified"] == 15
    assert result["outer_statuses"] == {"scored": 15}
    assert result["accesses_verified"] == 225


@pytest.mark.parametrize(
    "defect",
    [
        "missing_inner",
        "missing_choice",
        "missing_outer",
        "wrong_loss",
        "partial_eligibility",
        "tolerance_tie",
        "choice_hash",
        "global_score_parent",
        "own_outcome_parent",
        "prediction_parent",
        "baseline_loss",
        "wrong_count_N",
        "missing_access",
        "own_inner_access",
        "outer_before_inner",
        "wrong_prediction_freeze",
        "wrong_selection_freeze",
    ],
)
def test_selection_scoring_and_access_contract_tampering_refuses(
    evaluated: tuple[Any, ...], defect: str
) -> None:
    values = deepcopy(evaluated)
    packet, candidates, inner, choices, outer, accesses, counts = values
    if defect == "missing_inner":
        inner.pop()
    elif defect == "missing_choice":
        choices.pop()
    elif defect == "missing_outer":
        outer.pop()
    elif defect == "wrong_loss":
        inner[0]["metrics"]["hellinger"] = 0.1
    elif defect == "partial_eligibility":
        choices[0]["criteria"][0]["scored_inner_targets"] = 13
        choices[0]["criteria"][0]["eligible"] = True
        replace_choice_hash(choices[0])
    elif defect == "tolerance_tie":
        choices[0]["criteria"][0]["mean_inner_hellinger"] = 1e-16
        replace_choice_hash(choices[0])
    elif defect == "choice_hash":
        choices[0]["choice_sha256"] = "d" * 64
    elif defect == "global_score_parent":
        choices[0]["allowed_selection_inputs"]["whole_score_file_sha256"] = "d" * 64
        replace_choice_hash(choices[0])
    elif defect == "own_outcome_parent":
        choices[0]["allowed_selection_inputs"]["inner_outcome_references"][0] = packet[
            "observation_refs"
        ][0]
        replace_choice_hash(choices[0])
    elif defect == "prediction_parent":
        inner[0]["prediction_sha256"] = "d" * 64
    elif defect == "baseline_loss":
        outer[0]["matched_baselines"]["nearest_site"]["total_variation"] = 0.0
    elif defect == "wrong_count_N":
        counts[next(iter(counts))][packet["taxa"][0]] = 3
    elif defect == "missing_access":
        accesses.pop()
    elif defect == "own_inner_access":
        accesses[0]["observed_record_id"] = accesses[0]["outer_target"]
    elif defect == "outer_before_inner":
        accesses.insert(0, accesses.pop())
    elif defect == "wrong_prediction_freeze":
        accesses[0]["freeze_sha256"] = SELECTION
    else:
        accesses[-1]["freeze_sha256"] = PREDICTION
    with pytest.raises(ValueError):
        check(values)


def test_an_inner_gap_suppresses_selection_without_dropping_slots(
    evaluated: tuple[Any, ...],
) -> None:
    values = deepcopy(evaluated)
    packet, candidates, inner, choices, outer, accesses, _ = values
    context_id = inner[0]["context_id"]
    for row in candidates:
        if row["context_id"] == context_id:
            metadata = {
                key: value
                for key, value in row.items()
                if key
                in (
                    "context_id",
                    "kind",
                    "outer_target",
                    "target",
                    "length_scale_km",
                    "scientific_input_sha256",
                    "scientific_refs",
                    "uncertainty_status",
                )
            }
            row.clear()
            row.update(
                **metadata,
                status="refused",
                reason="hellinger_weight_underflow",
                detail="Synthetic refusal",
            )
    for row in inner[:2]:
        prediction = next(
            value
            for value in candidates
            if value["context_id"] == context_id
            and value["length_scale_km"] == row["length_scale_km"]
        )
        row.pop("metrics")
        row.update(
            status="refused",
            reason="hellinger_weight_underflow",
            prediction_sha256=sha(prediction),
        )
    choice = choices[0]
    for criterion in choice["criteria"]:
        criterion.update(
            scored_inner_targets=13, eligible=False, mean_inner_hellinger=None
        )
    skipped = inner[0]["inner_target"]
    choice.update(
        selected_scale_km=None,
        tied_best_scales_km=[],
        selection_status="refused_incomplete_inner_support",
        prediction=None,
    )
    choice["allowed_selection_inputs"]["inner_score_sha256s"] = [
        sha(row) for row in inner[:28]
    ]
    choice["allowed_selection_inputs"]["inner_outcome_references"] = [
        row
        for row in choice["allowed_selection_inputs"]["inner_outcome_references"]
        if row["record_id"] != skipped
    ]
    replace_choice_hash(choice)
    outer[0] = {
        "outer_target": choice["outer_target"],
        "status": "refused",
        "choice_sha256": choice["choice_sha256"],
    }
    accesses[:] = [
        row
        for row in accesses
        if not (
            row["outer_target"] == choice["outer_target"]
            and (row["role"] == "outer_scoring" or row["observed_record_id"] == skipped)
        )
    ]
    result = check(values)
    assert result["inner_statuses"] == {"refused": 2, "scored": 418}
    assert result["outer_statuses"] == {"refused": 1, "scored": 14}
    assert result["accesses_verified"] == 223


def test_stable_hellinger_retains_adjacent_composition_difference() -> None:
    first = math.nextafter(0.5, 1.0)
    score = _metrics([first, 1 - first], ["a", "b"], {"a": 1, "b": 1})
    assert score["hellinger"] > 0
    assert score["hellinger"] == pytest.approx(
        abs(first - 0.5) / math.sqrt(2), rel=1e-15
    )
    assert score["total_variation"] == abs(first - 0.5)


def test_binary64_near_tie_is_not_changed_into_a_tolerance_tie(
    evaluated: tuple[Any, ...],
) -> None:
    values = deepcopy(evaluated)
    packet, candidates, inner, choices, outer, _, counts = values
    context_id = inner[0]["context_id"]
    row = next(
        value
        for value in candidates
        if value["context_id"] == context_id and value["length_scale_km"] == 20.0
    )
    first = math.nextafter(2 / 3, 1.0)
    row["pollen_fraction"] = [first, 1 - first] + [0.0] * 28
    observation = [
        counts[inner[0]["inner_target"]][taxon] / 3 for taxon in packet["taxa"]
    ]
    delta = [
        (p - o) / (math.sqrt(p) + math.sqrt(o)) if p or o else 0.0
        for p, o in zip(row["pollen_fraction"], observation, strict=True)
    ]
    h = math.hypot(*delta) / math.sqrt(2)
    assert 0 < h < 1e-12
    absolute = sum(
        abs(p - o) for p, o in zip(row["pollen_fraction"], observation, strict=True)
    )
    inner[0].update(
        prediction_sha256=sha(row),
        metrics={
            "mae_fraction": absolute / 30,
            "total_variation": absolute / 2,
            "hellinger": h,
        },
    )
    choice = choices[0]
    choice["criteria"][0]["mean_inner_hellinger"] = h / 14
    choice.update(
        selected_scale_km=100.0,
        tied_best_scales_km=[100.0],
        selection_status="selected",
    )
    choice["prediction"] = deepcopy(
        next(
            value
            for value in candidates
            if value["context_id"] == choice["prediction"]["context_id"]
            and value["length_scale_km"] == 100.0
        )
    )
    choice["allowed_selection_inputs"]["inner_score_sha256s"] = [
        sha(value) for value in inner[:28]
    ]
    replace_choice_hash(choice)
    outer[0].update(choice_sha256=choice["choice_sha256"], selected_scale_km=100.0)
    assert check(values)["status"] == "passed"


def test_outer_refusal_does_not_select_an_available_scale_using_outer_information(
    evaluated: tuple[Any, ...],
) -> None:
    values = deepcopy(evaluated)
    _, candidates, _, choices, outer, accesses, _ = values
    choice = choices[0]
    context_id = choice["prediction"]["context_id"]
    row = next(
        value
        for value in candidates
        if value["context_id"] == context_id and value["length_scale_km"] == 20.0
    )
    metadata = {
        key: value
        for key, value in row.items()
        if key
        in (
            "context_id",
            "kind",
            "outer_target",
            "target",
            "length_scale_km",
            "scientific_input_sha256",
            "scientific_refs",
            "uncertainty_status",
        )
    }
    row.clear()
    row.update(
        **metadata,
        status="refused",
        reason="hellinger_weight_underflow",
        detail="Selected outer prediction unavailable",
    )
    choice["prediction"] = deepcopy(row)
    replace_choice_hash(choice)
    outer[0] = {
        "outer_target": choice["outer_target"],
        "status": "refused",
        "choice_sha256": choice["choice_sha256"],
    }
    accesses[:] = [
        access
        for access in accesses
        if not (
            access["outer_target"] == choice["outer_target"]
            and access["role"] == "outer_scoring"
        )
    ]
    result = check(values)
    assert choice["selected_scale_km"] == 20.0
    assert result["outer_statuses"] == {"refused": 1, "scored": 14}
    assert result["accesses_verified"] == 224
