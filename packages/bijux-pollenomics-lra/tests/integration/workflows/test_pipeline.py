from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from bijux_pollenomics_lra.models.configuration import (
    LoveConfig,
    LRAConfig,
    RevealsConfig,
)
from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.resources.examples import load_love_example
from bijux_pollenomics_lra.workflows.paired import run_lra
from bijux_pollenomics_lra.workflows.series import run_lra_series


def _config(
    *,
    method: str = "analytical",
    seed: int | None = 7,
    retain: bool = False,
    couple: bool = True,
) -> LRAConfig:
    return LRAConfig(
        reveals=RevealsConfig(
            "lake",
            300,
            iterations=4,
            stochastic=False,
            retain_samples=retain,
        ),
        love=LoveConfig(
            method,
            "lake",
            300,
            12.9,
            10,
            repeats=2,
            stochastic=False,
            retain_samples=retain,
        ),
        seed=seed,
        couple_regional_draws=couple,
    )


def _inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    local, regional, params, rings = load_love_example()
    return local, regional, params["ppes"], rings


def test_complete_lra_uses_regional_draw_handoff() -> None:
    local, regional, params, rings = _inputs()
    result = run_lra(local, regional, params, rings, _config())
    assert result.regional.samples is None
    assert result.local.manifest.parameters["paired_regional_cover_draws"] is True
    assert result.manifest.parameters["regional_draw_handoff"] is True
    np.testing.assert_allclose(
        result.local.cover["mean"].dropna().sum(axis=1), 1, atol=1e-12
    )


def test_decoupled_lra_is_explicit() -> None:
    local, regional, params, rings = _inputs()
    result = run_lra(local, regional, params, rings, _config(couple=False))
    assert result.local.manifest.parameters["paired_regional_cover_draws"] is False
    assert result.manifest.parameters["regional_draw_handoff"] is False


def test_retained_samples_are_exposed() -> None:
    local, regional, params, rings = _inputs()
    result = run_lra(local, regional, params, rings, _config(retain=True))
    assert result.regional.samples is not None
    assert result.regional.samples.shape == (1, 4, 10)
    assert result.local.samples["cover"].shape == (2, 10, 10)


def test_config_requires_stage_compatibility() -> None:
    reveals = RevealsConfig("lake", 300, iterations=2)
    with pytest.raises(ValidationError, match="basin types"):
        LRAConfig(
            reveals,
            LoveConfig("analytical", "peatland", 300, 12.9, 10, repeats=2),
        )
    with pytest.raises(ValidationError, match="diameters"):
        LRAConfig(
            reveals,
            LoveConfig("analytical", "lake", 400, 12.9, 10, repeats=2),
        )
    with pytest.raises(ValidationError, match="iterations"):
        LRAConfig(
            RevealsConfig("lake", 300, iterations=1),
            LoveConfig("analytical", "lake", 300, 12.9, 10, repeats=2),
        )


def test_lra_series_pairs_exact_coordinates() -> None:
    local, regional, params, rings = _inputs()
    local_series = pd.concat([local, local], ignore_index=True)
    regional_series = pd.concat([regional, regional], ignore_index=True)
    local_series.iloc[:, 0] = [100, 200]
    regional_series.iloc[:, 0] = [200, 100]
    result = run_lra_series(
        local_series, regional_series, params, rings, _config(seed=99)
    )
    assert list(result.runs) == ["100", "200"]
    assert all(run.manifest.algorithm == "LRA" for run in result.runs.values())


def test_lra_series_rejects_missing_duplicate_or_taxon_mismatch() -> None:
    local, regional, params, rings = _inputs()
    local_series = pd.concat([local, local], ignore_index=True)
    regional_series = pd.concat([regional, regional], ignore_index=True)
    local_series.iloc[:, 0] = [100, 100]
    regional_series.iloc[:, 0] = [100, 200]
    with pytest.raises(ValidationError, match="unique"):
        run_lra_series(local_series, regional_series, params, rings, _config())

    local_series.iloc[:, 0] = [100, 300]
    with pytest.raises(ValidationError, match="do not match"):
        run_lra_series(local_series, regional_series, params, rings, _config())

    local_one = local.copy().rename(columns={local.columns[-1]: "Other"})
    with pytest.raises(ValidationError, match="identical taxon"):
        run_lra_series(local_one, regional, params, rings, _config())


def _verify_checksums(root: Path) -> None:
    manifest = json.loads((root / "checksums.json").read_text())
    for relative, record in manifest.items():
        path = root / relative
        assert path.is_file()
        assert path.stat().st_size == record["bytes"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"]
