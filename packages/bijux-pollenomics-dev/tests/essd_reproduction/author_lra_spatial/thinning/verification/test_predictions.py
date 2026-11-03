"""Analytic source-closure, scalar prediction and numerical tamper controls."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial.thinning.verification.predictions import (
    audit_predictions,
    baseline,
    forward,
)

from . import synthetic


def test_all_fifty_literal_predictions_and_nine_owner_closures() -> None:
    packet, predictions, protocol = synthetic()
    assert audit_predictions(packet, predictions, protocol)["statuses"] == {
        "predicted": 50
    }


@pytest.mark.parametrize(
    "defect",
    [
        "missing",
        "duplicate",
        "wrong_method",
        "target_parent",
        "excluded_parent",
        "target_training",
        "group",
        "selected_ring",
        "global_hash",
        "weights",
        "cover",
        "invented_support",
        "double_regional_ppe",
        "hash",
        "refusal",
        "full_fifteen_ancestry",
    ],
)
def test_complete_population_and_source_numerics_cannot_be_falsified(
    defect: str,
) -> None:
    packet, predictions, protocol = deepcopy(synthetic())
    context, row = packet["contexts"][0], predictions[0]
    if defect == "missing":
        predictions.pop()
    elif defect == "duplicate":
        predictions[-1] = row
    elif defect == "wrong_method":
        row["method_id"] = "hellinger_10km"
    elif defect in ("target_parent", "excluded_parent"):
        context["predictors"][0]["scientific_parent_ids"] = [
            context["predictors"][0]["record_id"],
            context["target"]
            if defect == "target_parent"
            else packet["cohort"]["excluded"][0],
        ]
    elif defect == "target_training":
        context["fold"]["train_record_ids"][0] = context["target"]
    elif defect == "group":
        context["predictors"][0]["group_id"] = "foreign"
    elif defect == "selected_ring":
        context["scientific_refs"]["selected_fit_ids"][0] = context["predictors"][0][
            "fit_refs"
        ][0]
    elif defect == "global_hash":
        row["scientific_refs"]["bank_sha256"] = "a" * 64
    elif defect == "weights":
        row["weights"][next(iter(row["weights"]))] = 0.25
    elif defect == "cover":
        row["vegetation_fraction"] = [0.5, 0.5] + [0.0] * 28
    elif defect == "invented_support":
        row["pollen_fraction"][-1] = 1e-20
    elif defect == "double_regional_ppe":
        row["total_deposition"][1] = 12.0
    elif defect == "hash":
        row["scientific_input_sha256"] = "0" * 64
    elif defect == "refusal":
        row["status"] = "refused"
    else:
        context["scientific_refs"]["training_record_ids"] += packet["cohort"][
            "excluded"
        ]
    with pytest.raises(ValueError):
        audit_predictions(packet, predictions, protocol)


def test_exact_nearest_ties_and_zero_distance_idw_have_same_mean() -> None:
    rows = [[1.0] + [0.0] * 29, [0.0, 1.0] + [0.0] * 28, [0.0, 0.0, 1.0] + [0.0] * 27]
    for method, distances in (
        ("nearest_site", [2.0, 2.0, 9.0]),
        ("inverse_distance_squared", [0.0, 0.0, 9.0]),
    ):
        result = baseline(rows, distances, method)
        assert result["weights"] == [0.5, 0.5, 0.0]
        assert result["fractions"] == [0.5, 0.5] + [0.0] * 28
    weighted = baseline(rows[:2], [1.0, 3.0], "inverse_distance_squared")
    assert weighted["weights"] == [0.9, 0.1]
    assert weighted["fractions"][:2] == [0.9, 0.1]


def test_scalar_forward_keeps_regional_already_ppe_weighted() -> None:
    packet, _, _ = synthetic()
    result = forward(
        [1.0] + [0.0] * 29, packet["contexts"][0]["forward"]["forward_inputs"]
    )
    assert result["local_deposition"][:2] == [5.0, 0.0]
    assert result["total_deposition"][:2] == [8.0, 4.0]
    assert result["pollen_fraction"][:2] == [2 / 3, 1 / 3]


def test_numerical_oracle_does_not_read_original_context_bank() -> None:
    class Forbidden(dict[str, Any]):
        def __getitem__(self, key: str) -> Any:
            raise AssertionError(key)

    packet, predictions, protocol = synthetic()
    packet["upstream_packet"] = Forbidden()
    assert (
        audit_predictions(packet, predictions, protocol)["prediction_slots_verified"]
        == 50
    )
