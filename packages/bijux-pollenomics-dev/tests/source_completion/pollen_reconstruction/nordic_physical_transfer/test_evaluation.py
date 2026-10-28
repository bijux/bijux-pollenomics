"""Closed forecast ordering, matched responses and explicit descriptive weights."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial.products import write
from bijux_pollenomics_dev.essd_reproduction.physical_forward.country_transfer.evaluation import (
    native_score,
    score_closed,
    summarize,
)
from bijux_pollenomics_dev.essd_reproduction.physical_forward.country_transfer.prediction import (
    predict_all,
)

from .fixtures import forward_callback, inverse_callback, packet_fixture


def closed(
    directory: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    packet, profile, responses = packet_fixture()
    directory.mkdir()
    response_pin = write(directory, "responses.json", responses, 16 * 1024**2)
    contexts = predict_all(
        packet, profile, responses, inverse=inverse_callback, forward=forward_callback
    )
    freeze = {
        "schema_version": "nordic-physical-predictions.v1",
        "response_file": response_pin,
        "contexts": contexts,
    }
    prediction_pin = write(directory, "prediction-freeze.json", freeze, 16 * 1024**2)
    return packet, profile, prediction_pin, response_pin


def test_all432_slots_and_empty_observation_remain_distinct_from_forecast(
    tmp_path: Path,
) -> None:
    packet, profile, prediction, response = closed(tmp_path / "closed")
    rows = score_closed(tmp_path / "closed", prediction, response, packet, profile)
    assert len(rows) == 432
    unavailable = [r for r in rows if r["status"] == "unavailable_target_observation"]
    assert len(unavailable) == 2
    assert all(
        r["identity"]["target_core"] == "solsoe81"
        and r["pollen_fraction"] is not None
        and r["target_counts"] is None
        and r["metrics"] is None
        for r in unavailable
    )
    for row in rows:
        if row["status"] == "scored":
            assert row["target_panel_N"] == sum(row["target_counts"])
            assert row["metrics"]["mae_fraction"] == pytest.approx(
                row["metrics"]["total_variation"], abs=1e-15
            )
    summary = summarize(rows, profile)
    assert len(summary["matched"]) == 5
    assert all(r["requested_target_windows"] == 18 for r in summary["matched"])
    assert summary["matched"][-1]["unmatched"]
    assert all(
        r["target_core"] != "solsoe81" for r in summary["matched"][-1]["unmatched"]
    )


@pytest.mark.parametrize("member", ["prediction-freeze.json", "responses.json"])
def test_member_byte_tampering_blocks_every_score_call(
    tmp_path: Path, member: str
) -> None:
    packet, profile, prediction, response = closed(tmp_path / "closed")
    path = tmp_path / "closed" / member
    path.write_bytes(path.read_bytes() + b" ")
    calls = []

    def scored(*_: Any) -> dict[str, Any]:
        calls.append(True)
        raise AssertionError("outcome accessed")

    with pytest.raises(ValueError, match="changed"):
        score_closed(
            tmp_path / "closed", prediction, response, packet, profile, score=scored
        )
    assert not calls


def test_known_metric_values_keep_stable_hellinger_and_signed_axis() -> None:
    result = native_score([0.5, 0.5], (3, 1))
    assert result["mae_fraction"] == result["total_variation"] == 0.25
    assert result["signed_error_by_taxon"] == [-0.25, 0.25]
    assert result["hellinger_stable"] == pytest.approx(
        (((0.5**0.5 - 0.75**0.5) ** 2 + (0.5**0.5 - 0.25**0.5) ** 2) / 2) ** 0.5,
        abs=1e-15,
    )


def test_macro_and_native_owner_weights_have_different_exact_denominators(
    tmp_path: Path,
) -> None:
    packet, profile, prediction, response = closed(tmp_path / "closed")
    rows = score_closed(tmp_path / "closed", prediction, response, packet, profile)
    for row in rows:
        if row["identity"]["target_core"] == "abborrtjarnen":
            if row["identity"]["window_cal_bp"] == profile["windows"][0]:
                row.update(target_owner_count=1, target_sample_ids=[1])
            elif row["identity"]["window_cal_bp"] == profile["windows"][1]:
                row.update(target_owner_count=9, target_sample_ids=list(range(2, 11)))
        if row["status"] == "scored":
            value = (
                1.0
                if row["identity"]["target_core"] == "abborrtjarnen"
                and row["identity"]["window_cal_bp"] == profile["windows"][1]
                else 0.0
            )
            row["metrics"].update(
                mae_fraction=value, hellinger_stable=value, total_variation=value
            )
    summary = summarize(rows, profile)
    group = next(
        g
        for g in summary["groups"]
        if g["profile"] == "equal_place_solsoe83"
        and g["experiment"] == "swedish_training_scope"
        and g["scope"] == "swedish_only"
        and g["method"] == "direct_panel_mean"
        and g["country"] == "SE"
    )
    assert group["macro"]["mae_fraction"] == pytest.approx(1 / 18)
    assert group["native_owner_weighted"]["owner_denominator"] == 90
    assert group["native_owner_weighted"]["metrics"]["mae_fraction"] == pytest.approx(
        0.1
    )
    assert group["requested"] == group["scored"] == 18 and group["target_count"] == 3


def test_matched_response_mismatch_cannot_be_paired(tmp_path: Path) -> None:
    packet, profile, prediction, response = closed(tmp_path / "closed")
    rows = score_closed(tmp_path / "closed", prediction, response, packet, profile)
    target = next(r for r in rows if r["status"] == "scored")
    target["target_panel_N"] += 1
    with pytest.raises(ValueError, match="Matched target source response differs"):
        summarize(rows, profile)


def test_pairwise_direction_is_first_minus_second_on_common_support(
    tmp_path: Path,
) -> None:
    packet, profile, prediction, response = closed(tmp_path / "closed")
    rows = score_closed(tmp_path / "closed", prediction, response, packet, profile)
    for row in rows:
        if row["status"] == "scored":
            value = 0.4 if row["method"] == "physical_forward" else 0.1
            for metric in ("mae_fraction", "total_variation", "hellinger_stable"):
                row["metrics"][metric] = value
    summary = summarize(rows, profile)
    pair = next(
        p
        for p in summary["matched"][0]["pairwise"]
        if p["first"]["method"] == "physical_forward"
        and p["second"]["method"] == "direct_panel_mean"
    )
    assert pair["mean_difference"]["mae_fraction"] == pytest.approx(0.3)


def test_missing_disposition_refuses_summary_instead_of_changing_denominator(
    tmp_path: Path,
) -> None:
    packet, profile, prediction, response = closed(tmp_path / "closed")
    rows = score_closed(tmp_path / "closed", prediction, response, packet, profile)
    with pytest.raises(ValueError, match="Complete unique"):
        summarize(deepcopy(rows[:-1]), profile)
