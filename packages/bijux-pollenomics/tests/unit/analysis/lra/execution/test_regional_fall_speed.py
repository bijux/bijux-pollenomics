"""The host preserves explicit expanded regional admission and provenance."""

from pathlib import Path

import pytest

from bijux_pollenomics.analysis.lra.engine.discovery import EngineBinding
from bijux_pollenomics.analysis.lra.execution import service
from bijux_pollenomics.analysis.lra.execution.adapter import reconstruct
from bijux_pollenomics_lra import api
from bijux_pollenomics_lra.models.validation import (
    LANDCLIM_II_GPM_ANALYTICAL_FALL_SPEED_PROFILE,
)

from ..support import request_fixture


@pytest.mark.parametrize("basin", ["lake", "peatland"])
def test_host_retains_expanded_regional_fall_speed_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, basin: str
) -> None:
    payload = request_fixture(tmp_path, "reveals")
    payload["regional"]["basin"]["site_type"] = basin
    payload["parameters"][0]["fallspeed_m_s"] = 0.006
    payload["configuration"]["reveals"].update(
        distance_weighting="gpm neutral",
        fall_speed_profile=LANDCLIM_II_GPM_ANALYTICAL_FALL_SPEED_PROFILE,
    )
    binding = EngineBinding("bijux-pollenomics-lra", "generated-source", "native", api)
    monkeypatch.setattr(service, "load_engine", lambda **_: binding)
    request = service.validate_lra_inputs(payload, input_root=tmp_path)
    result = reconstruct(binding, request)
    assert (
        result.manifest.compatibility_mode
        == "landclimii-gpm-neutral-expanded-regional-v1"
    )
    assert result.manifest.parameters["fall_speed_contract"]["domain_m_s"] == [
        0.006,
        0.15,
    ]
    assert (
        result.manifest.parameters["fall_speed_contract"]["wrapper_admission"]
        == "expanded-python-domain"
    )
    assert payload["parameters"][0]["fallspeed_m_s"] == 0.006
