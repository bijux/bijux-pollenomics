"""One native baseline execution proves the maintained host boundary is usable."""

from importlib import import_module
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.bokesjon_pilot.basin_sensitivity.inputs import (
    load_inputs,
    materialize,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.bokesjon_pilot.basin_sensitivity.protocol import (
    profiles,
)


def implementation() -> Any:
    try:
        return import_module(
            "bijux_pollenomics_dev.source_completion.pollen_reconstruction."
            "bokesjon_pilot.basin_sensitivity.calculation"
        )
    except ModuleNotFoundError:
        pytest.fail("The maintained native calculation boundary is missing")


def test_single_native_baseline_matches_saved_signed_and_clipped_rings(
    tmp_path: Path,
) -> None:
    module = implementation()
    repository = next(
        p for p in Path(__file__).resolve().parents if (p / "uv.lock").is_file()
    )
    if not (repository / "artifacts/science/love-nonnegative-cover/cache").is_dir():
        pytest.skip("Retained source-bound BOKE baseline is not available")
    baseline = load_inputs(repository)
    request = materialize(baseline, profiles()[2], tmp_path / "inputs")
    result = module.calculate(request, tmp_path / "inputs", tmp_path / "native")
    assert result["signed_cover"] == [
        [-0.15419144652611294, 1.154191446526113],
        [0.1797901525758312, 0.8202098474241688],
    ]
    assert result["clipped_cover"] == [
        [0.0, 1.0],
        [0.1797901525758312, 0.8202098474241688],
    ]
    assert result["ring_midpoints_m"] == [290.5, 750.0]
    assert result["Kloc"][0] == [0.05126155086212125, 0.045528407092411904]
    assert result["regional_cover_percent"] == [72.17, 27.83]
    assert (tmp_path / "native/request.json").is_file()
