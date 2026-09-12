from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

import bijux_pollenomics_lra as lra
from bijux_pollenomics_lra.models.configuration import RevealsConfig
from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.reconstruction.draws import (
    maher_counts,
    multidraw,
    rMaher,
    rmultinom_reveals,
    rnorm_reveals,
)
from bijux_pollenomics_lra.reconstruction.regional import (
    REVEALS,
    REVEALSinR,
    reveals_cover,
)
from bijux_pollenomics_lra.resources.examples import DATASETS, load_dataset
from bijux_pollenomics_lra.workflows.regional import run_reveals


def test_source_compatible_api_is_complete() -> None:
    assert callable(lra.run_reveals)
    assert callable(lra.run_love)
    assert not hasattr(lra, "REVEALS")
    assert not hasattr(lra, "LOVEr")


@pytest.mark.parametrize("name", DATASETS)
def test_bundled_datasets_are_fresh(name: str) -> None:
    first = load_dataset(name)
    second = load_dataset(name)
    assert first is not second
    assert first.keys() == second.keys()


def test_reveals_closed_form_and_scale_invariance() -> None:
    pollen = np.array([20.0, 30.0, 50.0])
    productivity = np.array([1.0, 2.0, 3.0])
    deposition = np.array([0.2, 0.3, 0.5])
    expected = (
        100
        * (pollen / (productivity * deposition))
        / np.sum(pollen / (productivity * deposition))
    )
    np.testing.assert_array_equal(
        reveals_cover(pollen, productivity, deposition), np.round(expected, 3)
    )
    np.testing.assert_array_equal(
        reveals_cover(10 * pollen, 8 * productivity, deposition),
        np.round(expected, 3),
    )


def test_reveals_supplied_draws_and_sample_sd() -> None:
    count_draws = np.array([[20, 30, 50], [30, 20, 50], [40, 10, 50]], dtype=float)
    ppe_draws = np.array([[1, 2, 3], [2, 2, 3], [1, 3, 4]], dtype=float)
    params = pd.DataFrame({"ppe": [1, 2, 3], "ppe.error": [0.1, 0.2, 0.3]})
    deposition = np.array([0.2, 0.3, 0.5])
    result = REVEALS(
        [100, 20, 30, 50],
        3,
        params,
        deposition=deposition,
        ppe_draws=ppe_draws,
        pollen_draws=count_draws,
        return_samples=True,
    )
    expected = np.array(
        [
            reveals_cover(counts, productivity, deposition)
            for counts, productivity in zip(count_draws, ppe_draws, strict=True)
        ]
    )
    np.testing.assert_array_equal(result["samples"], expected)
    np.testing.assert_allclose(result["sdsim"], np.std(expected, axis=0, ddof=1))
    np.testing.assert_allclose(result["q10sim"], np.quantile(expected, 0.1, axis=0))


def test_single_draw_sd_and_callbacks() -> None:
    params = pd.DataFrame({"ppe": [1, 2], "ppe.error": [0, 0]})
    result = REVEALS(
        [1, 20, 30],
        1,
        params,
        deposition=[0.2, 0.3],
        ppefun=lambda n, mean, sd: mean,
        pollenfun=lambda n, pollen: pollen,
    )
    assert np.isnan(result["sdsim"]).all()


def test_sampling_reproducibility_and_dimensions() -> None:
    first = rmultinom_reveals(50, [20, 30, 50], rng=42)
    second = rmultinom_reveals(50, [20, 30, 50], rng=42)
    np.testing.assert_array_equal(first, second)
    np.testing.assert_allclose(first.sum(axis=0), 100)
    assert multidraw([20, 30, 50], rng=1).sum() == 100
    assert np.all(rnorm_reveals(20, np.ones(20), np.ones(20) * 2, rng=7) >= 0)
    with pytest.raises(ValidationError):
        rnorm_reveals(2, [-1, 2], [0, 0])
    assert (
        rMaher(2, [999, 10, 20], rng=1).shape == maher_counts(2, [10, 20], rng=1).shape
    )


def test_full_bundled_record_and_parameter_reordering(tmp_path) -> None:
    dataset = load_dataset("Tiefer_See")
    params = dataset["paramsTS"]
    pollen = dataset["pollenTS"]
    one = REVEALSinR(
        pollen,
        params,
        "lake",
        600,
        n=2,
        stochastic=False,
        verbose=False,
    )
    two = REVEALSinR(
        pollen,
        params.iloc[::-1],
        "lake",
        600,
        n=2,
        stochastic=False,
        verbose=False,
    )
    pd.testing.assert_frame_equal(one, two)
    assert one.shape == (45, 108)
    np.testing.assert_allclose(one.filter(regex=r"\.mean$").sum(axis=1), 100, atol=0.01)
    with pytest.raises(
        ValidationError, match="Numerical functions do not write artifacts"
    ):
        REVEALSinR(
            pollen.head(2),
            params,
            "lake",
            600,
            n=2,
            stochastic=False,
            writeresults=True,
            output_dir=tmp_path,
            verbose=False,
        )
    assert not list(tmp_path.iterdir())


def test_typed_reveals_result_and_artifacts(tmp_path) -> None:
    dataset = load_dataset("Tiefer_See")
    config = RevealsConfig(
        "lake", 600, iterations=3, stochastic=False, retain_samples=True
    )
    result = run_reveals(dataset["pollenTS"].head(2), dataset["paramsTS"], config)
    assert result.samples is not None
    assert result.samples.shape == (2, 3, 21)
    assert result.manifest.algorithm == "REVEALS"
    path = result.write(tmp_path / "reveals")
    assert (path / "reconstruction.csv").is_file()
    assert (path / "deposition_factors.csv").is_file()
    assert (path / "monte_carlo_samples.npz").is_file()
    assert (path / "run_manifest.json").is_file()
    assert (path / "checksums.json").is_file()


@pytest.mark.parametrize(
    "kwargs",
    [
        {"basin_type": "ocean", "basin_diameter_m": 100},
        {"basin_type": "lake", "basin_diameter_m": 1},
        {"basin_type": "lake", "basin_diameter_m": 100, "iterations": 0},
        {
            "basin_type": "lake",
            "basin_diameter_m": 100,
            "region_cutoff_m": 40,
        },
        {
            "basin_type": "lake",
            "basin_diameter_m": 100,
            "stochastic": "yes",
        },
    ],
)
def test_reveals_config_validation(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        RevealsConfig(**kwargs)  # type: ignore[arg-type]
