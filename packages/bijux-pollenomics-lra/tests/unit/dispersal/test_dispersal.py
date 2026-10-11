from __future__ import annotations

import numpy as np
import pytest

from bijux_pollenomics_lra.dispersal.kernels import (
    METHODS,
    DispersalFactorK,
    _lsm_data,
    clear_dispersal_cache,
    dispersal_factor,
    gpm_values,
    lsm_model,
)
from bijux_pollenomics_lra.dispersal.loess import Loess1D
from bijux_pollenomics_lra.models.errors import ValidationError

MODELS = sorted(
    key[: -len("_r_fitted")] for key in _lsm_data() if key.endswith("_r_fitted")
)


@pytest.mark.reference
@pytest.mark.parametrize("name", MODELS)
def test_stored_r_model_evaluation(name: str) -> None:
    data = _lsm_data()
    model = Loess1D(
        data[f"{name}_vertices"],
        data[f"{name}_values"],
        data[f"{name}_derivatives"],
        tuple(data[f"{name}_domain"]),
    )
    np.testing.assert_allclose(
        model(data[f"{name}_x"]),
        data[f"{name}_r_fitted"],
        rtol=0,
        atol=3e-13,
    )


@pytest.mark.reference
@pytest.mark.parametrize("name", MODELS)
def test_independent_refit_against_stored_r_values(name: str) -> None:
    data = _lsm_data()
    model = Loess1D.fit(
        data[f"{name}_x"],
        data[f"{name}_raw_y"],
        span=float(data[f"{name}_span"].item()),
        cell=float(data[f"{name}_cell"].item()),
    )
    np.testing.assert_allclose(
        model(data[f"{name}_x"]),
        data[f"{name}_r_fitted"],
        rtol=0,
        atol=3e-13,
    )


@pytest.mark.parametrize("method", METHODS)
def test_scalar_vector_and_basin_forms(method: str) -> None:
    diameters = np.array([20.0, 60.0, 100.0])
    vector = DispersalFactorK(0.03, "peatland", diameters, method, 100_000)
    assert vector.shape == (3,)
    np.testing.assert_array_equal(
        vector,
        [
            DispersalFactorK(0.03, "peatland", diameter, method, 100_000)
            for diameter in diameters
        ],
    )
    assert np.isfinite(DispersalFactorK(0.03, "lake", 100, method, 100_000))


def test_canonical_alias_matches_source_name() -> None:
    assert dispersal_factor(
        0.03, "peatland", 100, "lsm unstable", 100_000
    ) == DispersalFactorK(0.03, "peatland", 100, "lsm unstable", 100_000)


def test_source_gpm_cutoff_convention() -> None:
    expected = gpm_values(100, 0.03, 0.12, 0.25, 3) - gpm_values(
        100_000, 0.03, 0.12, 0.25, 3
    )
    assert DispersalFactorK(
        0.03, "peatland", 100, "gpm neutral", 100_000
    ) == pytest.approx(expected)
    assert DispersalFactorK(
        0.03, "peatland", 100, "gpm neutral", 10_000_000
    ) == pytest.approx(gpm_values(100, 0.03, 0.12, 0.25, 3))


def test_lsm_rounding_and_no_extrapolation() -> None:
    np.testing.assert_array_equal(
        lsm_model(0.024, low_resolution=True)([10, 100]),
        lsm_model(0.02, low_resolution=True)([10, 100]),
    )
    assert np.isnan(lsm_model(0.03)(100_001))
    assert np.isnan(DispersalFactorK(0.03, "peatland", 100, "lsm unstable", 200_000))
    assert np.isfinite(
        DispersalFactorK(0.03, "peatland", 100, "lsm unstable", 10_000_000)
    )


@pytest.mark.parametrize(
    "override",
    [
        {"vg": 0},
        {"tBasin": "ocean"},
        {"dwm": "unknown"},
        {"dBasin": -1},
        {"regionCutoff": 0},
        {"u": 0},
    ],
)
def test_invalid_dispersal_inputs(override: dict[str, object]) -> None:
    arguments: dict[str, object] = {
        "vg": 0.03,
        "tBasin": "peatland",
        "dBasin": 20,
        "dwm": "lsm unstable",
        "regionCutoff": 100_000,
    }
    arguments.update(override)
    with pytest.raises(ValidationError):
        DispersalFactorK(**arguments)  # type: ignore[arg-type]


def test_loess_exact_quadratic_and_domain() -> None:
    x = np.linspace(0, 10, 101)
    y = 2 + 3 * x + 0.2 * x * x
    model = Loess1D.fit(x, y, span=0.3)
    np.testing.assert_allclose(model(x), y, rtol=1e-12, atol=1e-12)
    assert np.isnan(model(-1))
    assert np.isnan(model(11))


def test_cache_clear_is_safe() -> None:
    before = DispersalFactorK(0.03, "peatland", 100, "lsm unstable", 100_000)
    clear_dispersal_cache()
    after = DispersalFactorK(0.03, "peatland", 100, "lsm unstable", 100_000)
    assert after == before
