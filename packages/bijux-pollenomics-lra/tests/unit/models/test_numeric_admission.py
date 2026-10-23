"""Scientific numeric arrays retain flags until public input admission."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import pytest

from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.models.validation import (
    matrix,
    normalise_parameters,
    sample_counts,
    vector,
)
from bijux_pollenomics_lra.reconstruction import analytical, regional
from bijux_pollenomics_lra.reconstruction.forward import forward_deposition
from bijux_pollenomics_lra.reconstruction.inputs import _regional_cover


@pytest.mark.parametrize(
    "value",
    [
        [False, 5],
        [2, np.bool_(True)],
        (True, 2.0),
        np.array([True, False]),
        np.array([False, 5], dtype=object),
        pd.Series([False, 5], dtype=object),
        pd.Series([True, False]),
    ],
)
def test_vector_refuses_boolean_scalar_provenance(value: Any) -> None:
    with pytest.raises(ValidationError, match="booleans"):
        vector(value, "pollen", finite=False)


@pytest.mark.parametrize(
    "value",
    [
        [[False, 5]],
        [[1.0, np.bool_(True)]],
        np.array([[True, False]]),
        np.array([[False, 5]], dtype=object),
        pd.DataFrame({"a": [False], "b": [5]}),
    ],
)
def test_matrix_refuses_boolean_scalar_provenance(value: Any) -> None:
    with pytest.raises(ValidationError, match="booleans"):
        matrix(value, "local_k", finite=False)


@pytest.mark.parametrize(
    "validator,value",
    [
        (vector, [10**400, 1]),
        (matrix, [[10**400, 1]]),
        (vector, ["not numeric", "2"]),
        (matrix, [["not numeric", "2"]]),
        (matrix, [[1], [1, 2]]),
    ],
)
def test_conversion_failures_use_public_validation_error(
    validator: Any, value: Any
) -> None:
    with pytest.raises(ValidationError):
        validator(value, "measurement")


def test_valid_numbers_numeric_text_zero_and_native_array_fast_path_remain() -> None:
    np.testing.assert_array_equal(vector([0, 5], "pollen"), [0.0, 5.0])
    np.testing.assert_array_equal(vector(["0", "2.5"], "pollen"), [0.0, 2.5])
    np.testing.assert_array_equal(
        matrix(pd.DataFrame({"a": ["0"], "b": ["2.5"]}), "source"), [[0.0, 2.5]]
    )
    source = np.array([0.0, 2.5])
    source.flags.writeable = False
    result = vector(source, "pollen")
    assert np.shares_memory(result, source) and not result.flags.writeable
    np.testing.assert_array_equal(result, source)
    np.testing.assert_array_equal(
        vector([np.nan, np.inf], "response", finite=False), [np.nan, np.inf]
    )


def parameters() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "species": ["A", "B"],
            "fallspeed": [0.02, 0.03],
            "ppe": [1.0, 2.0],
            "ppe.error": [0.0, 0.1],
        }
    )


@pytest.mark.parametrize("column", ["ppe", "ppe.error", "fallspeed"])
def test_parameter_tables_refuse_boolean_values_before_float_conversion(
    column: str,
) -> None:
    params = parameters().astype({column: object})
    params.loc[0, column] = column != "ppe.error"
    with pytest.raises(ValidationError, match="booleans"):
        normalise_parameters(params)


def test_parameter_numeric_text_and_both_taxon_layouts_remain_supported() -> None:
    source = parameters()
    source[["fallspeed", "ppe", "ppe.error"]] = source[
        ["fallspeed", "ppe", "ppe.error"]
    ].astype(str)
    expected = source.set_index("species")
    pd.testing.assert_frame_equal(normalise_parameters(source), expected)
    pd.testing.assert_frame_equal(normalise_parameters(expected), expected)


def test_sample_counts_refuses_false_instead_of_inventing_observed_zero() -> None:
    pollen = pd.DataFrame({"age": [0], "A": [False], "B": [5]})
    with pytest.raises(ValidationError, match="booleans"):
        sample_counts(pollen)
    counts, taxa, age = sample_counts(
        pd.DataFrame({"age": ["0"], "A": ["0"], "B": ["5"]})
    )
    np.testing.assert_array_equal(counts, [0.0, 5.0])
    assert taxa == ["A", "B"] and age == 0


@pytest.mark.parametrize(
    "changes",
    [
        {"pollen": [False, 5]},
        {"ppe": [True, 2]},
        {"deposition": [[True], [1]]},
        {"pollen": [10**400, 1]},
        {"deposition": [10**400, 1]},
    ],
)
def test_real_reveals_cover_refuses_flags_and_overflow(changes: dict[str, Any]) -> None:
    inputs: dict[str, Any] = {
        "pollen": [5, 5],
        "ppe": [1.0, 1.0],
        "deposition": [1.0, 1.0],
    }
    inputs.update(changes)
    with pytest.raises(ValidationError):
        regional.reveals_cover(**inputs)


def test_real_forward_consumer_refuses_boolean_geometry_kernel() -> None:
    with pytest.raises(ValidationError, match="booleans"):
        forward_deposition([0.5, 0.5], [0, 0], [[True, False]], [1], [1, 1])
    result = forward_deposition([0.5, 0.5], [0, 0], [[1, 0]], [1], [1, 1])
    np.testing.assert_array_equal(result.pollen_fraction, [1.0, 0.0])


@pytest.mark.parametrize(
    "changes",
    [
        {"pollen": [0, False, 5]},
        {"pollen": [[0, False, 5]]},
        {"deposition": [[True], [1]]},
        {"ppe_draws": [[True, 2.0]]},
        {"pollen_draws": [[False, 5]]},
        {"ppes": pd.DataFrame({"ppe": [True, 2.0], "ppe.error": [0, 0]})},
        {"ppefun": lambda *args: [True, 2.0]},
        {"pollenfun": lambda **kwargs: [False, 5]},
        {"pollen": [0, 10**400, 1]},
        {"ppe_draws": [[10**400, 1]]},
    ],
)
def test_actual_reveals_boundary_preserves_flags_until_admission(
    changes: dict[str, Any],
) -> None:
    inputs: dict[str, Any] = {
        "pollen": [0, 5, 5],
        "n": 1,
        "ppes": pd.DataFrame({"ppe": [1.0, 1.0], "ppe.error": [0.0, 0.0]}),
        "deposition": [1.0, 1.0],
        "stochastic": False,
    }
    inputs.update(changes)
    with pytest.raises(ValidationError):
        regional.REVEALS(**inputs)


def test_valid_reveals_flattened_numeric_text_and_explicit_draws_remain_exact() -> None:
    result = regional.REVEALS(
        [["0", "0", "5"]],
        n=1,
        ppes=[["1", "0"], ["1", "0"]],
        deposition=[["1"], ["1"]],
        stochastic=False,
        ppe_draws=[["1", "1"]],
        pollen_draws=[["0", "5"]],
        return_samples=True,
    )
    np.testing.assert_array_equal(result["samples"], [[0.0, 100.0]])


@pytest.mark.parametrize("role", ["pollen", "ppe_draws", "pollen_draws"])
def test_public_frame_wrapper_refuses_boolean_pollen_or_draws(
    role: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(regional, "DispersalFactorK", lambda *args: 1.0)
    inputs: dict[str, Any] = {
        "pollen": pd.DataFrame({"age": [0], "A": [5], "B": [5]}),
        "params": parameters(),
        "tBasin": "lake",
        "dBasin": 100,
        "n": 1,
        "stochastic": False,
        "verbose": False,
    }
    if role == "pollen":
        inputs["pollen"] = pd.DataFrame({"age": [0], "A": [False], "B": [5]})
    else:
        inputs[role] = [[[False, 5]]]
    with pytest.raises(ValidationError, match="booleans"):
        regional.REVEALSinR(**inputs)


def love_inputs() -> dict[str, Any]:
    return {
        "pollenLoc": pd.DataFrame({"age": [0], "A": [9], "B": [1]}),
        "pollenReg": pd.DataFrame({"age": [0], "A": [5], "B": [5]}),
        "lParams": {
            "ppes": parameters(),
            "fallspeed": [0.02, 0.03],
            "dBasinLocal": 10.0,
            "error": False,
        },
        "dfRadii": pd.DataFrame({"inner": [20.0], "outer": [40.0], "mean": [30.0]}),
        "maxRingLove": 1,
        "repeats": 1,
        "stochastic": False,
        "regional_cover_draws": [[0.5, 0.5]],
        "return_samples": True,
    }


@pytest.mark.parametrize(
    "sr",
    [[False, 0.1], [[True, 0.1]], np.array([False, 0.1], dtype=object), [10**400, 0.1]],
)
def test_public_analytical_love_refuses_flagged_or_overflowing_background(
    sr: Any,
) -> None:
    inputs = love_inputs()
    with pytest.raises(ValidationError):
        analytical.lov(inputs["pollenLoc"], sr, inputs["lParams"], stochastic=False)


@pytest.mark.parametrize("draws", [[[True, False]], [[10**400, 1]]])
def test_shared_regional_cover_selector_refuses_before_float_conversion(
    draws: Any,
) -> None:
    with pytest.raises(ValidationError):
        _regional_cover(
            None, parameters(), {}, np.random.default_rng(0), False, draws, 0
        )
    valid = _regional_cover(
        None, parameters(), {}, np.random.default_rng(0), False, ["0", "1"], 0
    )
    np.testing.assert_array_equal(valid, [0.0, 1.0])


@pytest.mark.parametrize(
    "changes",
    [
        {"regional_cover_draws": [[True, False]]},
        {"regional_cover_draws": [[10**400, 1]]},
        {"local_ppe_draws": [[[True, 2.0]]]},
        {"local_count_draws": [[[False, 1]]]},
        {"local_ppe_draws": [[[10**400, 2.0]]]},
        {"local_count_draws": [[[10**400, 1]]]},
        {"pollenReg": pd.DataFrame({"age": [0], "A": [False], "B": [5]})},
    ],
)
def test_actual_love_draw_boundary_refuses_numeric_flags(
    changes: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(analytical, "DispersalFactorK", lambda *args: 1.0)
    inputs = love_inputs()
    inputs.update(changes)
    with pytest.raises(ValidationError):
        analytical.LOVEr(**inputs)


def test_publication_profile_draws_are_guarded_before_closure_test(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(analytical, "DispersalFactorK", lambda *args: 1.0)
    inputs = love_inputs()
    inputs["lParams"].update(
        fall_speed_profile="landclimii-2016-gpm-neutral-analytical-v1",
        dwm="gpm neutral",
    )
    inputs["regional_cover_draws"] = [[True, False]]
    with pytest.raises(ValidationError, match="booleans"):
        analytical.LOVEr(**inputs)


@pytest.mark.parametrize("column", ["inner", "outer", "mean"])
def test_love_ring_geometry_flags_do_not_become_numeric_radii(column: str) -> None:
    inputs = love_inputs()
    inputs["dfRadii"] = pd.DataFrame(
        {"inner": [0.0], "outer": [2.0], "mean": [1.0]}
    ).astype({column: object})
    inputs["dfRadii"].loc[0, column] = column != "inner"
    with pytest.raises(ValidationError, match="booleans"):
        analytical.LOVEr(**inputs)


@pytest.mark.parametrize("diameter", [True, np.bool_(True), [True], 10**400])
def test_love_local_basin_flags_and_overflow_use_public_error(diameter: Any) -> None:
    inputs = love_inputs()
    inputs["lParams"]["dBasinLocal"] = diameter
    with pytest.raises(ValidationError):
        analytical.LOVEr(**inputs)


def test_valid_love_numeric_text_shapes_and_signed_results_remain(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(analytical, "DispersalFactorK", lambda *args: 1.0)
    inputs = love_inputs()
    baseline = analytical.LOVEr(**inputs)
    relative = np.array([9.0, 0.5]) / 9.5
    expected = relative * 2 - 0.5
    np.testing.assert_array_equal(baseline["samples"][0, 0], expected)
    assert baseline["samples"][0, 0, 1] < 0
    inputs.update(
        regional_cover_draws=[".5", ".5"],
        local_ppe_draws=[[["1", "2"]]],
        local_count_draws=[[["9", "1"]]],
    )
    inputs["lParams"]["dBasinLocal"] = "10.0"
    inputs["dfRadii"] = inputs["dfRadii"].astype(str)
    result = analytical.LOVEr(**inputs)
    np.testing.assert_array_equal(result["samples"], baseline["samples"])
    low_level = analytical.lov(
        inputs["pollenLoc"], [[".5", ".5"]], inputs["lParams"], stochastic=False
    )
    np.testing.assert_array_equal(low_level, expected)
