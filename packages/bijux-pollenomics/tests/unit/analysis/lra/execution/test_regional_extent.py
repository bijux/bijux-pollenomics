"""The real optional engine refuses incompatible paired extents at validation."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path

import pytest

from bijux_pollenomics.analysis.lra.engine.discovery import EngineBinding
from bijux_pollenomics.analysis.lra.engine.errors import LRARefusal
from bijux_pollenomics.analysis.lra.execution import service
from bijux_pollenomics.analysis.lra.execution.adapter import reconstruct
from bijux_pollenomics_lra import api

from ..support import request_fixture

validate_lra_inputs = import_module(
    "pollenomics.analysis.lra.execution.service"
).validate_lra_inputs


def _binding() -> EngineBinding:
    return EngineBinding("bijux-pollenomics-lra", "generated-source", "native", api)


@pytest.mark.parametrize(
    "method,coupled",
    [("analytical", False), ("analytical", True), ("optimized", False)],
)
def test_public_validation_refuses_mismatched_extent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, method: str, coupled: bool
) -> None:
    payload = request_fixture(tmp_path, "lra")
    payload["configuration"]["reveals"].update(
        region_cutoff_m=50_000, distance_weighting="gpm neutral"
    )
    payload["configuration"]["love"].update(
        method=method,
        distance_weighting="gpm neutral",
        analytical_cover_policy="source-raw",
    )
    payload["configuration"]["couple_regional_draws"] = coupled
    if method == "optimized":
        payload["rings"].append(
            {**payload["rings"][0], "inner_m": 200, "outer_m": 1000, "mean_m": 600}
        )
    monkeypatch.setattr(service, "load_engine", lambda **_: _binding())
    # The facade resolves the actual host service; only installed metadata
    # discovery is supplied for this source-only engine binding.
    assert validate_lra_inputs is service.validate_lra_inputs
    with pytest.raises(LRARefusal, match="100000") as error:
        validate_lra_inputs(payload, input_root=tmp_path)
    assert error.value.reason_code == "invalid_engine_configuration"


@pytest.mark.parametrize("coupled", [False, True])
def test_actual_host_adapter_preserves_default_raw_control(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, coupled: bool
) -> None:
    payload = request_fixture(tmp_path, "lra")
    payload["configuration"]["couple_regional_draws"] = coupled
    for stage in ("reveals", "love"):
        payload["configuration"][stage]["distance_weighting"] = "gpm neutral"
    payload["configuration"]["love"]["analytical_cover_policy"] = "source-raw"
    monkeypatch.setattr(service, "load_engine", lambda **_: _binding())
    request = validate_lra_inputs(payload, input_root=tmp_path)
    result = reconstruct(_binding(), request)
    assert (
        result.manifest.parameters["effective_regional_extent"][
            "love_background_cutoff_m"
        ]
        == 100_000
    )
    ratio = (
        result.local.auxiliary["Kreg"].iloc[0, 0]
        / result.local.auxiliary["Kloc"].iloc[0, 0]
    )
    expected = [0.7 * (1 + ratio) - 0.6 * ratio, 0.3 * (1 + ratio) - 0.4 * ratio]
    assert result.local.cover["mean"].iloc[0].tolist() == pytest.approx(expected)
    assert result.local.manifest.parameters["analytical_cover_policy"] == "source-raw"


def test_public_standalone_nondefault_extent_is_validated(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload = request_fixture(tmp_path, "reveals")
    payload["configuration"]["reveals"].update(
        region_cutoff_m=50_000, distance_weighting="gpm neutral"
    )
    monkeypatch.setattr(service, "load_engine", lambda **_: _binding())
    request = validate_lra_inputs(payload, input_root=tmp_path)
    result = reconstruct(_binding(), request)
    assert result.manifest.parameters["region_cutoff_m"] == 50_000


def test_public_coupled_optimizer_keeps_nondefault_background(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload = request_fixture(tmp_path, "lra")
    payload["method_profile"] = "ring-taxon-preserving"
    payload["configuration"]["reveals"].update(
        region_cutoff_m=50_000, distance_weighting="gpm neutral"
    )
    payload["configuration"]["love"].update(
        method="optimized",
        optimized_profile="ring-taxon-preserving",
        distance_weighting="gpm neutral",
    )
    payload["configuration"]["couple_regional_draws"] = True
    payload["rings"].append(
        {**payload["rings"][0], "inner_m": 200, "outer_m": 1000, "mean_m": 600}
    )
    monkeypatch.setattr(service, "load_engine", lambda **_: _binding())
    request = validate_lra_inputs(payload, input_root=tmp_path)
    assert request.payload()["configuration"]["reveals"]["region_cutoff_m"] == 50_000
