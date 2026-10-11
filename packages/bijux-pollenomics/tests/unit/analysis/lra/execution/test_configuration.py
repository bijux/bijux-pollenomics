"""Method-specific input checks must run before numerical reconstruction."""

from __future__ import annotations

from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

from bijux_pollenomics.analysis.lra.engine.discovery import EngineBinding
from bijux_pollenomics.analysis.lra.engine.errors import LRARefusal
from bijux_pollenomics.analysis.lra.execution.adapter import (
    validate_engine_configuration,
)
from bijux_pollenomics.analysis.lra.inputs.validation import validate_request

from ..support import request_fixture


def _binding() -> EngineBinding:
    api = ModuleType("configuration_stub")

    def configuration(**values: object) -> SimpleNamespace:
        return SimpleNamespace(**values)

    for name in ("RevealsConfig", "LoveConfig"):
        setattr(api, name, configuration)
    return EngineBinding("synthetic", "0", "configuration_only", api)


@pytest.mark.parametrize(
    "case,reason",
    [
        ("edge", "invalid_analytical_ring_support"),
        ("mask", "unsupported_analytical_land_mask"),
        ("regional_rings", "invalid_local_ring_limit"),
    ],
)
def test_unsupported_geometry_fails_during_input_validation(
    tmp_path: Path, case: str, reason: str
) -> None:
    payload = request_fixture(tmp_path, "love")
    if case == "edge":
        payload["rings"][0]["inner_m"] = 10
    elif case == "mask":
        payload["rings"][0]["terrestrial_area_m2"] *= 0.5
    else:
        payload["configuration"]["love"]["method"] = "optimized"
    request = validate_request(payload, input_root=tmp_path)
    with pytest.raises(LRARefusal) as error:
        validate_engine_configuration(_binding(), request)
    assert error.value.reason_code == reason


def test_analytical_geometry_has_positive_land_support_beyond_basin(
    tmp_path: Path,
) -> None:
    request = validate_request(request_fixture(tmp_path, "love"), input_root=tmp_path)
    validate_engine_configuration(_binding(), request)
