"""Expanded regional admission retains a bounded, source-identified GPM contract."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

from bijux_pollenomics_lra.dispersal.kernels import dispersal_factor
from bijux_pollenomics_lra.models.configuration import RevealsConfig
from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.models.validation import (
    LANDCLIM_II_GPM_ANALYTICAL_FALL_SPEED_PROFILE,
)
from bijux_pollenomics_lra.version import REFERENCE_ARCHIVE_SHA256
from bijux_pollenomics_lra.workflows.regional import run_reveals

REFERENCE = Path(__file__).resolve().parents[3] / "reference/regional_profiles"
PROFILE = LANDCLIM_II_GPM_ANALYTICAL_FALL_SPEED_PROFILE


def _reference() -> dict[str, Any]:
    value: dict[str, Any] = json.loads(
        (REFERENCE / "landclim_gpm_neutral.json").read_text()
    )
    assert value["source_archive_sha256"] == REFERENCE_ARCHIVE_SHA256
    assert (
        value["generator_sha256"]
        == sha256((REFERENCE / "landclim_gpm_neutral.R").read_bytes()).hexdigest()
    )
    return value


def _inputs(speed: float = 0.006) -> tuple[pd.DataFrame, pd.DataFrame]:
    return pd.DataFrame(
        {"coordinate": [1500], "Filipendula": [20], "Betula": [80]}
    ), pd.DataFrame(
        {
            "species": ["Filipendula", "Betula"],
            "fallspeed": [speed, 0.024],
            "ppe": [1.0, 5.0],
            "ppe.error": [0.0, 0.0],
        }
    )


def test_native_r_kernel_reference_preserves_finite_and_undefined_partitions() -> None:
    reference = _reference()
    finite = undefined = 0
    for case in reference["deposition"]:
        actual = dispersal_factor(
            case["fall_speed_m_s"],
            case["basin"],
            case["diameter_m"],
            "gpm neutral",
            case["cutoff_m"],
        )
        if case["deposition_factor"] is None:
            assert case["basin"] == "lake" and case["cutoff_m"] > 1_000_000
            assert np.isnan(actual)
            undefined += 1
        else:
            np.testing.assert_allclose(
                actual, case["deposition_factor"], **reference["kernel_tolerance"]
            )
            finite += 1
    assert (finite, undefined) == (60, 12)


def test_expanded_facade_matches_native_r_b1_with_generated_counts() -> None:
    reference = _reference()
    for case in reference["cover"]:
        pollen, params = _inputs()
        pollen.loc[0, ["Filipendula", "Betula"]] = case["counts"]
        params.loc[1, "fallspeed"] = case["other_fall_speed_m_s"]
        original = params.copy(deep=True)
        result = run_reveals(
            pollen,
            params,
            RevealsConfig(
                case["basin"],
                case["diameter_m"],
                distance_weighting="gpm neutral",
                region_cutoff_m=case["cutoff_m"],
                stochastic=False,
                iterations=2,
                fall_speed_profile=PROFILE,
            ),
        )
        np.testing.assert_allclose(
            result.table[["Filipendula.mean", "Betula.mean"]].iloc[0],
            case["mean_percent"],
            rtol=0,
            atol=reference["cover_atol_percentage_points"],
        )
        pd.testing.assert_frame_equal(params, original)
    assert len(reference["cover"]) == 48
    assert "<0.01 m/s" in reference["source_wrapper_refusal"]


def test_expanded_regional_manifest_distinguishes_wrapper_admission(
    tmp_path: Path,
) -> None:
    pollen, params = _inputs()
    result = run_reveals(
        pollen,
        params,
        RevealsConfig(
            "peatland",
            100,
            distance_weighting="gpm neutral",
            stochastic=False,
            iterations=2,
            fall_speed_profile=PROFILE,
        ),
    )
    assert (
        result.manifest.compatibility_mode
        == "landclimii-gpm-neutral-expanded-regional-v1"
    )
    contract = result.manifest.parameters["fall_speed_contract"]
    assert contract == {
        "operation": "regional-reveals",
        "domain_m_s": [0.006, 0.15],
        "distance_weighting": "gpm neutral",
        "source_wrapper_domain_m_s": [0.01, 0.15],
        "reference_scope": "disqover-0.9.14-gpm-kernel-and-b1",
        "wrapper_admission": "expanded-python-domain",
    }
    output = result.write(tmp_path / "regional")
    saved = json.loads((output / "run_manifest.json").read_text())
    assert saved["parameters"]["fall_speed_contract"] == contract
    assert saved["reference_archive_sha256"] == REFERENCE_ARCHIVE_SHA256


def test_default_profile_and_undefined_geometry_refusals_remain() -> None:
    pollen, params = _inputs()
    with pytest.raises(ValidationError, match="between 0.01 and 0.15"):
        run_reveals(pollen, params, RevealsConfig("peatland", 100, stochastic=False))
    for speed in (np.nextafter(0.006, 0), np.nextafter(0.15, 1)):
        _, invalid = _inputs(float(speed))
        with pytest.raises(ValidationError, match="between 0.006 and 0.15"):
            run_reveals(
                pollen,
                invalid,
                RevealsConfig(
                    "peatland",
                    100,
                    distance_weighting="gpm neutral",
                    stochastic=False,
                    fall_speed_profile=PROFILE,
                ),
            )
    with pytest.raises(ValidationError, match="requires gpm neutral"):
        RevealsConfig("peatland", 100, fall_speed_profile=PROFILE)
    with pytest.raises(ValidationError, match="undefined or nonpositive"):
        run_reveals(
            pollen,
            params,
            RevealsConfig(
                "lake",
                100,
                distance_weighting="gpm neutral",
                region_cutoff_m=1_000_001,
                stochastic=False,
                fall_speed_profile=PROFILE,
            ),
        )
    ordinary, ordinary_params = _inputs(0.01)
    default = run_reveals(
        ordinary,
        ordinary_params,
        RevealsConfig(
            "peatland",
            100,
            distance_weighting="gpm neutral",
            stochastic=False,
            iterations=2,
        ),
    )
    assert default.manifest.compatibility_mode == "disqover-0.9.14"
    assert "fall_speed_contract" not in default.manifest.parameters
