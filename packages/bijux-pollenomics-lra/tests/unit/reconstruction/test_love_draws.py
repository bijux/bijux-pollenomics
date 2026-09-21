from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from bijux_pollenomics_lra.models.configuration import LoveConfig
from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.models.regional_draw_source import RegionalCoverDrawSource
from bijux_pollenomics_lra.models.validation import (
    LANDCLIM_II_GPM_ANALYTICAL_FALL_SPEED_PROFILE,
)
from bijux_pollenomics_lra.provenance.identity import sha256_object
from bijux_pollenomics_lra.reconstruction.analytical import LOVEr
from bijux_pollenomics_lra.resources.examples import load_love_example
from bijux_pollenomics_lra.workflows.local import (
    run_love,
    run_love_from_regional_draws,
)


def _love_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    local, regional, params, rings = load_love_example()
    return local, regional, params["ppes"], rings


def test_draw_only_love_preserves_numerics_without_placeholder_pollen() -> None:
    local, regional, params, rings = _love_inputs()
    supported_rings = rings.iloc[8:11].copy(deep=True)
    draws = np.full((2, 10), 0.1)
    source = RegionalCoverDrawSource(
        values=draws,
        taxon_ids=tuple(local.columns[1:]),
        bin_id="bin-50",
        younger_bp=1250,
        older_bp=1750,
        draw_ids=(0, 1),
        regional_site_ids=("site-a", "site-b"),
        eligible_site_ids=("site-a", "site-b"),
        parent_manifest_sha256="a" * 64,
        draw_member_sha256="b" * 64,
        selected_tensor_sha256=sha256_object(draws),
        diagnostic_prefix=True,
    )
    config = LoveConfig(
        "analytical",
        "lake",
        300,
        12.9,
        3,
        distance_weighting="gpm neutral",
        fall_speed_profile=LANDCLIM_II_GPM_ANALYTICAL_FALL_SPEED_PROFILE,
        repeats=2,
        stochastic=False,
        retain_samples=True,
    )
    historical = run_love(
        local,
        regional,
        params,
        supported_rings,
        config,
        regional_cover_draws=draws,
    )
    draw_only = run_love_from_regional_draws(
        local,
        source,
        params,
        supported_rings,
        config,
        local_site_id="site-a",
        local_sample_id="sample-a",
    )
    np.testing.assert_array_equal(
        draw_only.samples["cover"], historical.samples["cover"]
    )
    np.testing.assert_array_equal(
        draw_only.auxiliary["Kreg"].to_numpy(),
        historical.auxiliary["Kreg"].to_numpy(),
    )
    assert "regional_pollen" not in draw_only.manifest.inputs
    assert draw_only.manifest.inputs["regional_cover_draws"] == sha256_object(draws)
    assert (
        draw_only.manifest.parameters["regional_draw_source"]["draw_member_sha256"]
        == "b" * 64
    )
    assert draw_only.manifest.parameters["regional_cohort_overlap"] is True
    assert source.values.flags.writeable is False
    with pytest.raises(ValueError):
        source.values.flags.writeable = True
    draws[0, 0] = 0.9
    assert source.values[0, 0] == 0.1
    regional.iloc[0, 1:] = regional.iloc[0, 1:] + 1
    changed_placeholder = run_love(
        local,
        regional,
        params,
        supported_rings,
        config,
        regional_cover_draws=source.values,
    )
    np.testing.assert_array_equal(
        draw_only.samples["cover"], changed_placeholder.samples["cover"]
    )
    assert (
        historical.manifest.inputs["regional_pollen"]
        != changed_placeholder.manifest.inputs["regional_pollen"]
    )
    with pytest.raises(ValidationError, match="Regional pollen is required"):
        run_love(
            local, None, params, supported_rings, config, regional_cover_draws=draws
        )
    with pytest.raises(ValidationError, match="Draw-only LOVE requires"):
        run_love(
            local,
            None,
            params,
            supported_rings,
            config,
            regional_cover_draws=source.values,
            _draw_source=source,
        )
    with pytest.raises(ValidationError, match="Regional pollen is required"):
        LOVEr(
            local,
            None,
            {
                "ppes": params,
                "fall_speed_profile": LANDCLIM_II_GPM_ANALYTICAL_FALL_SPEED_PROFILE,
            },
            supported_rings,
            3,
            repeats=2,
            regional_cover_draws=source.values,
        )
    with pytest.raises(ValidationError, match="PPE rows"):
        run_love_from_regional_draws(
            local,
            source,
            params.iloc[::-1],
            supported_rings,
            config,
            local_site_id="site-a",
            local_sample_id="sample-a",
        )
    with pytest.raises(ValidationError, match="repeat count"):
        run_love_from_regional_draws(
            local,
            source,
            params,
            supported_rings,
            LoveConfig(
                "analytical",
                "lake",
                300,
                12.9,
                3,
                distance_weighting="gpm neutral",
                fall_speed_profile=LANDCLIM_II_GPM_ANALYTICAL_FALL_SPEED_PROFILE,
                repeats=3,
                stochastic=False,
            ),
            local_site_id="site-a",
            local_sample_id="sample-a",
        )


def test_regional_draw_source_refuses_invalid_counts_axes_and_digests() -> None:
    draws = np.full((2, 2), 0.5)
    values = dict(
        values=draws,
        taxon_ids=("A", "B"),
        bin_id="bin-50",
        younger_bp=1250,
        older_bp=1750,
        draw_ids=(0, 1),
        regional_site_ids=("one", "two"),
        eligible_site_ids=("one", "two"),
        parent_manifest_sha256="a" * 64,
        draw_member_sha256="b" * 64,
        selected_tensor_sha256=sha256_object(draws),
        diagnostic_prefix=True,
    )
    for change in (
        {"draw_ids": (1, 0)},
        {"draw_ids": (False, True)},
        {"younger_bp": False},
        {"younger_bp": "invalid"},
        {"taxon_ids": ("A", "A")},
        {"eligible_site_ids": ("two", "one")},
        {"selected_tensor_sha256": "0" * 64},
        {"draw_member_sha256": "invalid"},
        {"values": np.full((2, 2), 0.25)},
        {"values": np.array([[0.5, np.nan], [0.5, 0.5]])},
        {"diagnostic_prefix": False},
    ):
        with pytest.raises(ValidationError):
            RegionalCoverDrawSource(**(values | change))


def test_draw_only_publication_profile_uses_all_1000_draws(tmp_path) -> None:
    local, _, params, rings = _love_inputs()
    draws = np.full((1000, 10), 0.1)
    common = dict(
        values=draws,
        taxon_ids=tuple(local.columns[1:]),
        bin_id="bin-50",
        younger_bp=1250,
        older_bp=1750,
        draw_ids=tuple(range(1000)),
        regional_site_ids=("site-a", "site-b"),
        eligible_site_ids=("site-a", "site-b"),
        parent_manifest_sha256="a" * 64,
        draw_member_sha256="b" * 64,
        selected_tensor_sha256=sha256_object(draws),
    )
    with pytest.raises(ValidationError, match="exactly 1000"):
        RegionalCoverDrawSource(
            **(common | {"values": draws[:-1], "draw_ids": tuple(range(999))})
        )
    source = RegionalCoverDrawSource(**common)
    config = LoveConfig(
        "analytical",
        "lake",
        300,
        12.9,
        3,
        distance_weighting="gpm neutral",
        fall_speed_profile=LANDCLIM_II_GPM_ANALYTICAL_FALL_SPEED_PROFILE,
        repeats=1000,
        stochastic=False,
        retain_samples=True,
    )
    result = run_love_from_regional_draws(
        local,
        source,
        params,
        rings.iloc[8:11],
        config,
        local_site_id="local-site",
        local_sample_id="local-sample",
    )
    assert result.samples["cover"].shape == (1000, 3, 10)
    assert (
        result.manifest.parameters["regional_draw_source"]["diagnostic_prefix"] is False
    )
    assert "regional_pollen" not in result.manifest.inputs
    bundle = result.write(tmp_path / "draw-only")
    assert (bundle / "run_manifest.json").is_file()
