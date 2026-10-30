"""Actual adapter control flow on synthetic places, counts and fixed responses."""

from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.physical_forward.country_transfer.prediction import (
    predict_all,
    predict_context,
)
from bijux_pollenomics_lra.models.errors import ValidationError

from .fixtures import forward_callback, inverse_callback, packet_fixture


def context(
    target: str = "abborrtjarnen",
    scope: str = "pooled_nordic",
    experiment: str = "swedish_training_scope",
    profile_index: int = 0,
) -> dict[str, Any]:
    packet, profile, responses = packet_fixture()
    return predict_context(
        packet,
        profile,
        responses,
        profile["profiles"][profile_index],
        experiment,
        target,
        profile["windows"][0],
        scope,
        {},
        inverse=inverse_callback,
        forward=forward_callback,
    )


def test_complete216_contexts432slots_and_fixed_country_exclusion() -> None:
    packet, profile, responses = packet_fixture()
    before = deepcopy(packet)
    rows = predict_all(
        packet, profile, responses, inverse=inverse_callback, forward=forward_callback
    )
    assert len(rows) == 216 and sum(len(r["families"]) for r in rows) == 432
    assert len({r["context_id"] for r in rows}) == 216 and packet == before
    for row in rows:
        target = row["target"]
        sources = row["required_sources"]
        assert (
            "counts" not in target
            and "source_ref" not in target
            and "panel_N" not in target
        )
        assert all(r["physical_family"] != target["physical_family"] for r in sources)
        assert sum(Fraction(r["weight_exact"]) for r in sources) == 1
        assert len(sources) + len(row["excluded_sources"]) == 7
        if row["identity"]["experiment"] == "country_holdout":
            assert all(r["country"] != target["country"] for r in sources)
        assert not ({"solsoe81", "solsoe83"} <= {r["core"] for r in sources})


def test_density_weights_are_per_country_then_place_not_grain_counts() -> None:
    row = context(profile_index=1)
    values = {r["core"]: Fraction(r["weight_exact"]) for r in row["required_sources"]}
    assert values == {
        "bokesjon": Fraction(1, 8),
        "bussjosjon": Fraction(1, 8),
        "solsoe83": Fraction(1, 4),
        "laihalampi": Fraction(1, 4),
        "dalmutladdo": Fraction(1, 4),
    }
    row = context(
        target="solsoe83",
        scope="outside_target_country",
        experiment="country_holdout",
        profile_index=1,
    )
    values = {r["core"]: Fraction(r["weight_exact"]) for r in row["required_sources"]}
    assert (
        values["abborrtjarnen"]
        == values["bokesjon"]
        == values["bussjosjon"]
        == Fraction(1, 9)
    )
    assert values["laihalampi"] == values["dalmutladdo"] == Fraction(1, 3)


def test_same_country_or_one_place_per_country_weightings_coincide() -> None:
    assert (
        context(scope="swedish_only", profile_index=0)["families"]
        == context(scope="swedish_only", profile_index=1)["families"]
    )
    assert (
        context(
            scope="outside_target_country",
            experiment="country_holdout",
            profile_index=0,
        )["families"]
        == context(
            scope="outside_target_country",
            experiment="country_holdout",
            profile_index=1,
        )["families"]
    )


def test_held_target_and_all_held_country_counts_are_not_numerical_parents() -> None:
    packet, profile, responses = packet_fixture()
    p = profile["profiles"][0]

    def predict() -> dict[str, Any]:
        return predict_context(
            packet,
            profile,
            responses,
            p,
            "country_holdout",
            "abborrtjarnen",
            profile["windows"][0],
            "outside_target_country",
            {},
            inverse=inverse_callback,
            forward=forward_callback,
        )

    before = predict()
    for key in ("abborrtjarnen", "bokesjon", "bussjosjon", "solsoe81"):
        packet["cores"][key]["windows"] = "unreadable excluded outcome channel"
    after = predict()
    assert before == after


def test_required_window_refuses_both_without_dropping_or_renormalizing() -> None:
    packet, profile, responses = packet_fixture()
    p = profile["profiles"][2]
    row = predict_context(
        packet,
        profile,
        responses,
        p,
        "swedish_training_scope",
        "abborrtjarnen",
        profile["windows"][-1],
        "pooled_nordic",
        {},
        inverse=inverse_callback,
        forward=forward_callback,
    )
    assert len(row["required_sources"]) == 5
    assert all(r["weight_exact"] == "1/5" for r in row["required_sources"])
    assert all(
        f["status"] == "refused"
        and f["reason"] == "required_training_source_unavailable"
        for f in row["families"].values()
    )
    assert all(r["inverse"]["status"] == "not_run" for r in row["required_sources"])


def test_empty_target_can_have_complete_geometry_only_forecasts() -> None:
    packet, profile, responses = packet_fixture()
    row = predict_context(
        packet,
        profile,
        responses,
        profile["profiles"][2],
        "country_holdout",
        "solsoe81",
        profile["windows"][-1],
        "outside_target_country",
        {},
        inverse=inverse_callback,
        forward=forward_callback,
    )
    assert all(f["status"] == "predicted" for f in row["families"].values())
    assert "counts" not in row["target"]


@pytest.mark.parametrize("which", ["target", "source"])
def test_response_failure_refuses_physical_only_with_unchanged_direct(
    which: str,
) -> None:
    packet, profile, responses = packet_fixture()
    p = profile["profiles"][0]
    before = predict_context(
        packet,
        profile,
        responses,
        p,
        "swedish_training_scope",
        "abborrtjarnen",
        profile["windows"][0],
        "pooled_nordic",
        {},
        inverse=inverse_callback,
        forward=forward_callback,
    )
    radius = 98 if which == "target" else 80
    for r in responses["rows"]:
        if r["receiver_radius_m"] == radius:
            r.update(status="refused", factor=None)
    row = predict_context(
        packet,
        profile,
        responses,
        p,
        "swedish_training_scope",
        "abborrtjarnen",
        profile["windows"][0],
        "pooled_nordic",
        {},
        inverse=inverse_callback,
        forward=forward_callback,
    )
    assert (
        row["families"]["direct_panel_mean"] == before["families"]["direct_panel_mean"]
    )
    assert row["families"]["physical_forward"]["status"] == "refused"
    assert row["families"]["physical_forward"]["reason"] == "response_unavailable"
    assert [r["weight_exact"] for r in row["required_sources"]] == [
        r["weight_exact"] for r in before["required_sources"]
    ]
    if which == "source":
        assert row["required_sources"][0]["inverse"]["status"] == "refused"


def test_exact_covariance_is_passed_and_point_formula_matches_preclosure() -> None:
    packet, profile, responses = packet_fixture()
    seen = []

    def inverse(
        vector: tuple[int, int],
        kernel: tuple[float, ...],
        ppe: tuple[float, ...],
        covariance: tuple[tuple[float, ...], ...],
    ) -> tuple[float, ...]:
        seen.append(covariance)
        return inverse_callback(vector, kernel, ppe, covariance)

    row = predict_context(
        packet,
        profile,
        responses,
        profile["profiles"][0],
        "swedish_training_scope",
        "abborrtjarnen",
        profile["windows"][0],
        "swedish_only",
        {},
        inverse=inverse,
        forward=forward_callback,
    )
    assert seen == [packet["covariance"], packet["covariance"]]
    for source in row["required_sources"]:
        expected = [
            source["counts"][i] / (source["kernels"][i] * source["ppe"][i])
            for i in range(2)
        ]
        assert source["inverse"]["preclosure"] == pytest.approx(expected, abs=1e-14)
    family = row["families"]["physical_forward"]
    target = row["target"]
    expected = [
        target["kernels"][i] * target["ppe"][i] * family["cover"][i] for i in range(2)
    ]
    assert family["preclosure"] == pytest.approx(expected, abs=1e-14)
    assert family["pollen_fraction"] == pytest.approx(
        [v / sum(expected) for v in expected], abs=1e-14
    )


def test_known_inverse_refusal_retains_baseline_and_programming_fault_propagates() -> (
    None
):
    packet, profile, responses = packet_fixture()

    def refused(*_: object) -> tuple[float, ...]:
        raise ValidationError("known inverse", reason_code="known")

    row = predict_context(
        packet,
        profile,
        responses,
        profile["profiles"][0],
        "swedish_training_scope",
        "abborrtjarnen",
        profile["windows"][0],
        "swedish_only",
        {},
        inverse=refused,
        forward=forward_callback,
    )
    assert row["families"]["physical_forward"]["reason"] == "source_inverse_refused"
    assert row["families"]["direct_panel_mean"]["status"] == "predicted"
    assert all(
        r["inverse"]["refusal"]["reason_code"] == "known"
        for r in row["required_sources"]
    )

    def broken(*_: object) -> tuple[float, ...]:
        raise RuntimeError("bug")

    with pytest.raises(RuntimeError, match="bug"):
        predict_context(
            packet,
            profile,
            responses,
            profile["profiles"][0],
            "swedish_training_scope",
            "abborrtjarnen",
            profile["windows"][0],
            "swedish_only",
            {},
            inverse=broken,
            forward=forward_callback,
        )
