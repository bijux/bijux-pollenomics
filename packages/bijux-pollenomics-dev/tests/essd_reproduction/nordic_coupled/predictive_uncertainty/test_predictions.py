"""Analytic forwarding, undefined populations and held-target noninterference."""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
import json
from unittest.mock import patch

import numpy as np
import pytest

from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.predictive_uncertainty.draws import (
    CountOwner,
    DrawBank,
    OwnerDraws,
    generate_draw_bank,
    owner_stream_index,
)
from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.predictive_uncertainty.predictions import (
    METHODS,
    FoldCase,
    LocalKernel,
    allowed_input_identity,
    ensemble_summary,
    predict_case,
)


def case() -> FoldCase:
    local = ((2.0, 2.0), (1.0, 1.0))
    distant = ((0.1, 0.1), (0.1, 0.1))
    return FoldCase(
        "window:fold",
        "T",
        "R",
        (LocalKernel("A", local, distant), LocalKernel("B", local, distant)),
        (1.0, 1.0),
        ((0.5, 0.5), (0.5, 0.5)),
        (0.2, 0.2),
        (1.0, 1.0),
        (1.0, 2.0),
    )


def bank(*, first: tuple[int, int] = (3, 1), replicates: int = 3) -> DrawBank:
    owners = tuple(
        OwnerDraws(
            name,
            owner_stream_index(name),
            counts,
            np.tile(np.asarray(counts, dtype=np.int64), (replicates, 1)),
        )
        for name, counts in (("R", (2, 2)), ("A", first), ("B", (1, 3)), ("T", (1, 3)))
    )
    return DrawBank(
        replicates, 20261027, (1.0, 1.0), (0.0, 0.0), np.ones((replicates, 2)), owners
    )


def test_saved_kernel_engine_calls_match_fraction_equations_without_kernel_work() -> (
    None
):
    with patch(
        "bijux_pollenomics_lra.reconstruction.analytical.DispersalFactorK",
        side_effect=AssertionError("No fresh deposition kernel permitted"),
    ) as unused:
        result = predict_case(case(), bank())
        unused.assert_not_called()
    assert result["regional_cover"] == [[0.5, 0.5]] * 3
    assert result["local_signed_cover"][0][0][0] == pytest.approx(
        [float(Fraction(61, 80)), float(Fraction(19, 80))]
    )
    assert result["local_signed_cover"][0][0][1] == pytest.approx([0.775, 0.225])
    for method, expected_cover, direct in (
        ("training_mean", Fraction(1, 2), Fraction(1, 2)),
        ("nearest_site", Fraction(31, 40), Fraction(3, 4)),
        ("inverse_distance_squared", Fraction(133, 200), Fraction(13, 20)),
    ):
        value = result["methods"][method]
        expected = float((expected_cover + Fraction(1, 10)) / Fraction(6, 5))
        assert value["cover"][0][0] == pytest.approx(float(expected_cover), abs=1e-14)
        assert value["pollen"][0][0] == pytest.approx(expected, abs=1e-14)
        assert value["direct_pollen"][0][0] == pytest.approx(float(direct), abs=1e-14)
        assert value["valid_mask"] == [True] * 3
    json.dumps(result, allow_nan=False)


def test_signed_negative_selected_local_refuses_all_methods_without_fallback() -> None:
    result = predict_case(replace(case(), distances_km=(2.0, 1.0)), bank(first=(4, 0)))
    assert result["local_signed_cover"][0][0][1][1] < 0
    assert result["local_refusals"][0][0] == "local_selected_cover_out_of_bounds"
    for value in result["methods"].values():
        assert value["valid_mask"] == [False] * 3
        assert value["pollen"] == [[None, None]] * 3
        assert value["refusals"] == ["required_local_predictor_undefined"] * 3
        assert value["summary"]["defined_replicates"] == 0
        assert value["summary"]["unconditional_status"] == "refused_undefined_mass"
        assert value["direct_summary"]["defined_replicates"] == 3
    json.dumps(result, allow_nan=False)


def test_unselected_negative_ring_is_retained_without_changing_selected_admission() -> (
    None
):
    original = case()
    locals_ = tuple(
        replace(local, regional_k=((10.0, 10.0), (0.1, 0.1)))
        for local in original.local_owners
    )
    result = predict_case(
        replace(original, local_owners=(locals_[0], locals_[1])), bank()
    )
    assert result["local_signed_cover"][0][0][0][1] < 0
    assert result["local_signed_cover"][0][1][0][0] < 0
    assert result["local_refusals"] == [[None, None]] * 3
    for value in result["methods"].values():
        assert value["valid_mask"] == [True] * 3


@pytest.mark.parametrize("undefined_ring", [0, 1])
def test_undefined_ring_diagnostics_preserve_the_selected_ring_admission(
    undefined_ring: int,
) -> None:
    calls = [
        np.asarray([0.6, 0.4]),
        np.asarray([0.6, 0.4]),
        np.asarray([0.4, 0.6]),
        np.asarray([0.4, 0.6]),
    ]
    calls[undefined_ring] = np.asarray([np.nan, np.nan])
    module = "bijux_pollenomics_dev.essd_reproduction.nordic_coupled.predictive_uncertainty.predictions"
    with patch(module + ".lov", side_effect=calls):
        result = predict_case(case(), bank(replicates=1))
    assert result["local_signed_cover"][0][0][undefined_ring] == [None, None]
    if undefined_ring == 0:
        assert result["local_ring_refusals"][0][0][0] == "local_engine_nonfinite"
        assert result["local_refusals"] == [[None, None]]
    else:
        assert result["local_refusals"][0][0] == "local_selected_cover_nonfinite"
    for value in result["methods"].values():
        assert value["valid_mask"] == [undefined_ring == 0]
    json.dumps(result, allow_nan=False)


def test_target_count_changes_cannot_change_own_fold_or_allowed_input_binding() -> None:
    owners = (
        CountOwner("R", (100, 100)),
        CountOwner("A", (60, 40)),
        CountOwner("B", (40, 60)),
        CountOwner("T", (1, 99)),
    )
    first = generate_draw_bank(owners, replicates=12)
    second = generate_draw_bank(
        (*owners[:3], replace(owners[3], counts=(99, 1))), replicates=12
    )
    assert allowed_input_identity(case(), first) == allowed_input_identity(
        case(), second
    )
    assert predict_case(case(), first) == predict_case(case(), second)
    assert [
        row["owner_id"] for row in allowed_input_identity(case(), first)["count_owners"]
    ] == ["R", "A", "B"]
    with pytest.raises(ValueError, match="exclude"):
        predict_case(replace(case(), target_id="A"), first)


def test_ppe_is_shared_across_stages_but_does_not_change_direct_counterpart() -> None:
    original = bank()
    changed = replace(original, ppe=np.tile([1.5, 0.7], (3, 1)))
    before, after = predict_case(case(), original), predict_case(case(), changed)
    assert before["regional_cover"] != after["regional_cover"]
    assert before["local_signed_cover"] != after["local_signed_cover"]
    for method in METHODS:
        assert (
            before["methods"][method]["direct_pollen"]
            == after["methods"][method]["direct_pollen"]
        )
        assert before["methods"][method]["pollen"] != after["methods"][method]["pollen"]


def test_zero_ppe_is_retained_as_refusal_not_redrawn_or_clipped() -> None:
    original = bank()
    result = predict_case(
        case(), replace(original, ppe=np.asarray([[0.0, 1.0], [1.0, 1.0], [1.0, 1.0]]))
    )
    assert result["regional_refusals"] == ["ppe_nonpositive", None, None]
    for value in result["methods"].values():
        assert value["valid_mask"] == [False, True, True]
        assert value["summary"]["undefined_mass"] == 1 / 3
        assert value["summary"]["unconditional_status"] == "refused_undefined_mass"


def test_finite_population_covariance_and_iid_mcse_have_distinct_divisors() -> None:
    result = ensemble_summary([[0.0, 1.0], [1.0, 0.0], [None, None]])
    assert result["defined_replicates"] == 2
    assert result["undefined_mass"] == 1 / 3
    conditional = result["conditional"]
    assert conditional["mean"] == [0.5, 0.5]
    assert conditional["covariance"] == [[0.25, -0.25], [-0.25, 0.25]]
    assert conditional["sd"] == [0.5, 0.5]
    assert conditional["mean_mcse"] == [0.5, 0.5]
    assert conditional["empirical_quantiles"]["0.025"] == pytest.approx([0.025, 0.025])
    single = ensemble_summary([[0.3, 0.7]])["conditional"]
    assert single["covariance"] == [[0.0, 0.0], [0.0, 0.0]]
    assert single["mean_mcse"] is None
    with pytest.raises(ValueError, match="finite"):
        ensemble_summary([[None, None]], [True])


def test_nearest_ties_and_zero_distance_keep_both_predictor_requirement() -> None:
    for distances in ((1.0, 1.0), (0.0, 0.0)):
        result = predict_case(replace(case(), distances_km=distances), bank())
        for method in METHODS:
            assert result["methods"][method]["weights"] == [0.5, 0.5]
    with pytest.raises(ValueError, match="saved"):
        predict_case(replace(case(), forward_local_k=((1.0, 1.0),)), bank())
