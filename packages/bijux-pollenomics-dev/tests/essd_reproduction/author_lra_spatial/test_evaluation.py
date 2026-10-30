"""Train-only scale selection, matched outer comparisons and local ancestry."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial import (
    evaluation,
    prediction,
)
from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial.outcomes import (
    OutcomeReader,
)

from .test_outcomes import PREDICTION_FREEZE, SELECTION_FREEZE, saved_outcomes


def selection_fixture(
    root: Path, *, first_counts: tuple[int, int] = (3, 1)
) -> tuple[dict[str, Any], list[dict[str, Any]], OutcomeReader]:
    archive, packet, protocol = saved_outcomes(root, first_counts=first_counts)
    owners = [row["record_id"] for row in packet["observation_refs"]]
    contexts, candidates = [], []
    for outer in owners:
        for target in owners:
            kind = "outer" if target == outer else "inner"
            context_id = kind + ":" + outer + ":" + target
            context = {
                "context_id": context_id,
                "kind": kind,
                "outer_target": outer,
                "target": target,
                "reference_baselines": [
                    {
                        "baseline": method,
                        "pollen_fraction": {"a": first, "b": 1 - first},
                    }
                    for method, first in (
                        ("training_mean", 0.5),
                        ("nearest_site", 0.75),
                        ("inverse_distance_squared", 1.0),
                    )
                ],
            }
            contexts.append(context)
            for scale, pollen in ((20.0, [0.75, 0.25]), (100.0, [0.25, 0.75])):
                candidates.append(
                    {
                        "context_id": context_id,
                        "kind": kind,
                        "outer_target": outer,
                        "target": target,
                        "length_scale_km": scale,
                        "status": "predicted",
                        "pollen_fraction": pollen,
                    }
                )
    packet["contexts"] = contexts
    return (
        packet,
        candidates,
        OutcomeReader(archive, packet, protocol, PREDICTION_FREEZE),
    )


def test_complete_fourteen_target_selection_is_train_only(tmp_path: Path) -> None:
    packet, candidates, reader = selection_fixture(tmp_path)
    scores, choices = evaluation.select_scales(packet, candidates, reader)
    assert len(scores) == 420 and len(choices) == 15
    assert all(
        row["selected_scale_km"] == 20.0 and row["selection_status"] == "selected"
        for row in choices
    )
    assert len(reader.accesses) == 210
    assert {row["role"] for row in reader.accesses} == {"inner_training"}
    assert all(
        row["observed_record_id"] != row["outer_target"] for row in reader.accesses
    )
    for choice in choices:
        assert all(
            row["scored_inner_targets"] == 14 and row["eligible"] is True
            for row in choice["criteria"]
        )
        assert len(choice["allowed_selection_inputs"]["inner_score_sha256s"]) == 28
        assert len(choice["allowed_selection_inputs"]["inner_outcome_references"]) == 14
        assert choice["outer_target"] not in {
            row["record_id"]
            for row in choice["allowed_selection_inputs"]["inner_outcome_references"]
        }


def test_exact_loss_ties_choose_the_predeclared_smaller_scale(tmp_path: Path) -> None:
    packet, candidates, reader = selection_fixture(tmp_path)
    for row in candidates:
        row["pollen_fraction"] = [0.75, 0.25]
    _, choices = evaluation.select_scales(packet, candidates, reader)
    assert all(
        row["selection_status"] == "selected_exact_loss_tie"
        and row["selected_scale_km"] == 20.0
        and row["tied_best_scales_km"] == [20.0, 100.0]
        for row in choices
    )


@pytest.mark.parametrize("both", [False, True])
def test_thirteen_scored_inner_targets_never_qualify_scale(
    tmp_path: Path, both: bool
) -> None:
    packet, candidates, reader = selection_fixture(tmp_path)
    first = next(row for row in candidates if row["kind"] == "inner")
    for row in candidates:
        if row["context_id"] == first["context_id"] and (
            both or row["length_scale_km"] == 20.0
        ):
            row["status"] = "refused"
            row["reason"] = "synthetic_domain_refusal"
            del row["pollen_fraction"]
    scores, choices = evaluation.select_scales(packet, candidates, reader)
    choice = next(
        row for row in choices if row["outer_target"] == first["outer_target"]
    )
    assert choice["criteria"][0]["scored_inner_targets"] == 13
    assert choice["criteria"][0]["eligible"] is False
    assert choice["criteria"][0]["mean_inner_hellinger"] is None
    if both:
        assert choice["selected_scale_km"] is None and choice["prediction"] is None
        assert choice["selection_status"] == "refused_incomplete_inner_support"
        assert Counter(row["status"] for row in scores) == {"scored": 418, "refused": 2}
        assert len(reader.accesses) == 209
    else:
        assert choice["selected_scale_km"] == 100.0
        assert Counter(row["status"] for row in scores) == {"scored": 419, "refused": 1}


def test_all_refusals_preserve_population_without_label_reads(tmp_path: Path) -> None:
    packet, candidates, reader = selection_fixture(tmp_path)
    for row in candidates:
        row["status"] = "refused"
        row["reason"] = "synthetic_domain_refusal"
        del row["pollen_fraction"]
    scores, choices = evaluation.select_scales(packet, candidates, reader)
    assert len(scores) == 420 and all(row["status"] == "refused" for row in scores)
    assert len(choices) == 15 and all(row["prediction"] is None for row in choices)
    outer = evaluation.score_outer(packet, choices, reader)
    assert len(outer) == 15 and all(row["status"] == "refused" for row in outer)
    assert reader.accesses == []


def test_matched_outer_comparators_share_exact_fifteen_count_denominators(
    tmp_path: Path,
) -> None:
    packet, candidates, reader = selection_fixture(tmp_path)
    _, choices = evaluation.select_scales(packet, candidates, reader)
    with pytest.raises(ValueError, match="freeze"):
        evaluation.score_outer(packet, choices, reader)
    assert len(reader.accesses) == 210
    reader.selection_freeze = SELECTION_FREEZE
    scores = evaluation.score_outer(packet, choices, reader)
    assert len(scores) == 15 and {row["status"] for row in scores} == {"scored"}
    accesses = [row for row in reader.accesses if row["role"] == "outer_scoring"]
    assert len(accesses) == len({row["observed_record_id"] for row in accesses}) == 15
    assert all(row["freeze_sha256"] == SELECTION_FREEZE for row in accesses)
    for score in scores:
        assert score["observed_count"] == 4
        assert score["metrics"] == evaluation.losses(
            [0.75, 0.25], packet["taxa"], {"a": 3, "b": 1}
        )
        assert set(score["matched_baselines"]) == {
            "training_mean",
            "nearest_site",
            "inverse_distance_squared",
        }
        for baseline, first in (
            ("training_mean", 0.5),
            ("nearest_site", 0.75),
            ("inverse_distance_squared", 1.0),
        ):
            assert score["matched_baselines"][baseline] == evaluation.losses(
                [first, 1 - first], packet["taxa"], {"a": 3, "b": 1}
            )
        assert score["vegetation_accuracy"] == "not_evaluated_no_measured_observation"


def test_outer_label_perturbation_cannot_change_its_own_train_only_choice(
    tmp_path: Path,
) -> None:
    packet, candidates, reader = selection_fixture(tmp_path / "original")
    _, choices = evaluation.select_scales(packet, candidates, reader)
    changed_packet, changed_candidates, changed_reader = selection_fixture(
        tmp_path / "changed", first_counts=(1, 3)
    )
    _, changed_choices = evaluation.select_scales(
        changed_packet, changed_candidates, changed_reader
    )
    first_owner = packet["observation_refs"][0]["record_id"]
    assert next(row for row in choices if row["outer_target"] == first_owner) == next(
        row for row in changed_choices if row["outer_target"] == first_owner
    )
    assert all(
        row["observed_record_id"] != first_owner
        for row in changed_reader.accesses
        if row["outer_target"] == first_owner
    )


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "incomplete_inner"])
def test_candidate_and_context_denominators_fail_closed(
    tmp_path: Path, mutation: str
) -> None:
    packet, candidates, reader = selection_fixture(tmp_path)
    if mutation == "missing":
        candidates.pop()
    elif mutation == "duplicate":
        candidates[-1] = deepcopy(candidates[0])
    else:
        packet["contexts"].pop(-2)
    with pytest.raises(ValueError):
        evaluation.select_scales(packet, candidates, reader)


def prediction_fixture() -> tuple[dict[str, Any], list[str]]:
    taxa = ["a", "b", "zero"]
    context = {
        "context_id": "context:example",
        "kind": "outer",
        "target": "held",
        "outer_target": "held",
        "scientific_refs": {
            "training_record_ids": ["local-a", "local-b", "anchor"],
            "selected_fit_ids": ["fit-a", "fit-b"],
        },
        "predictors": [
            {
                "record_id": "local-a",
                "group_id": "group-a",
                "covers_by_ring": [[0.0, 1.0, 0.0], [1.0, 0.0, 0.0]],
            },
            {
                "record_id": "local-b",
                "group_id": "group-b",
                "covers_by_ring": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
            },
        ],
        "forward": {
            "distances_km": {"group-a": 10.0, "group-b": 20.0},
            "forward_inputs": {
                "taxa": taxa,
                "regional_deposition": [0.0, 0.0, 0.0],
                "local_k": [[1.0, 1.0, 1.0], [1.0, 1.0, 1.0]],
                "terrestrial_fraction": [0.5, 0.5],
                "ppe": [1.0, 1.0, 1.0],
            },
        },
    }
    return context, taxa


def test_prediction_uses_selected_ring_preserves_zeros_and_ignores_held_labels() -> (
    None
):
    context, taxa = prediction_fixture()
    original = deepcopy(context)
    result = prediction.predict_context(context, taxa, 20.0)
    assert result["status"] == "predicted"
    assert result["vegetation_fraction"][0] > result["vegetation_fraction"][1] > 0
    assert result["vegetation_fraction"][2] == result["pollen_fraction"][2] == 0.0
    assert result["pollen_fraction"] == pytest.approx(
        result["vegetation_fraction"], abs=1e-15
    )
    assert context == original
    context["held_out_counts"] = {"a": 10**8, "b": 0, "zero": 0}
    context["whole_file_accounting_sha256"] = "f" * 64
    assert prediction.predict_context(context, taxa, 20.0) == result


@pytest.mark.parametrize(
    "mutation",
    [
        "target_training",
        "target_predictor",
        "foreign_predictor",
        "duplicate_owner",
        "duplicate_group",
        "distance_membership",
    ],
)
def test_prediction_owner_ancestry_is_explicit(mutation: str) -> None:
    context, taxa = prediction_fixture()
    if mutation == "target_training":
        context["scientific_refs"]["training_record_ids"].append(context["target"])
    elif mutation == "target_predictor":
        context["predictors"][0]["record_id"] = context["target"]
    elif mutation == "foreign_predictor":
        context["predictors"][0]["record_id"] = "foreign"
    elif mutation == "duplicate_owner":
        context["predictors"][0]["record_id"] = context["predictors"][1]["record_id"]
    elif mutation == "duplicate_group":
        context["predictors"][0]["group_id"] = context["predictors"][1]["group_id"]
    else:
        context["forward"]["distances_km"]["foreign-group"] = 1.0
    with pytest.raises(ValueError, match="withheld|Predictor|groups"):
        prediction.predict_context(context, taxa, 20.0)


@pytest.mark.parametrize("refusal", ["invalid_cover", "zero_deposition"])
def test_prediction_domain_refusals_remain_explicit(refusal: str) -> None:
    context, taxa = prediction_fixture()
    if refusal == "invalid_cover":
        context["predictors"][0]["covers_by_ring"][1] = [-1.0, 2.0, 0.0]
    else:
        context["forward"]["forward_inputs"]["local_k"] = [[0.0] * 3, [0.0] * 3]
    result = prediction.predict_context(context, taxa, 20.0)
    assert result["status"] == "refused" and result["reason"]
    assert "pollen_fraction" not in result and "vegetation_fraction" not in result
    assert result["context_id"] == context["context_id"]
