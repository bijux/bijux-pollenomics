"""Changes during computation invalidate the completed numerical result."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from bijux_pollenomics.analysis.lra.engine.discovery import (
    OPTIMIZED_RING_TAXON_CAPABILITY,
)
from bijux_pollenomics.analysis.lra.engine.errors import LRARefusal
from bijux_pollenomics.analysis.lra.execution import service

from ..outputs.test_publication import Result, binding
from ..support import request_fixture


@pytest.mark.parametrize("change", ["code", "source"])
def test_run_binds_inputs_before_and_after_computation(
    tmp_path: Path, change: str
) -> None:
    engine = binding(tmp_path)
    payload = request_fixture(tmp_path)
    destination = tmp_path / "output"

    def changed_result(*args: object) -> Result:
        target = tmp_path / (
            "installed/api.py" if change == "code" else "raw_snapshot.txt"
        )
        target.write_text("changed during computation")
        return Result()

    with (
        patch.object(service, "load_engine", return_value=engine),
        patch.object(service, "reconstruct", side_effect=changed_result),
        pytest.raises(LRARefusal) as error,
    ):
        service.run_lra_request(payload, input_root=tmp_path, destination=destination)
    expected = (
        "lra_code_changed_during_run"
        if change == "code"
        else "evidence_digest_mismatch"
    )
    assert error.value.reason_code == expected
    assert not destination.exists()


def test_revised_profile_selects_optional_engine_before_validation(
    tmp_path: Path,
) -> None:
    payload = request_fixture(tmp_path, "love")
    payload["method_profile"] = "ring-taxon-preserving"
    payload["configuration"]["love"].update(
        method="optimized", optimized_profile="ring-taxon-preserving"
    )
    payload["rings"].append(
        {
            **payload["rings"][0],
            "inner_m": 200,
            "outer_m": 400,
            "mean_m": 300,
        }
    )
    with (
        patch.object(service, "load_engine") as loader,
        patch.object(service, "validate_engine_configuration"),
    ):
        service.validate_lra_inputs(payload, input_root=tmp_path)
    loader.assert_called_once_with(required_capability=OPTIMIZED_RING_TAXON_CAPABILITY)


def test_installed_revised_profile_validates_through_host(tmp_path: Path) -> None:
    payload = request_fixture(tmp_path, "love")
    payload["method_profile"] = "ring-taxon-preserving"
    payload["configuration"]["love"].update(
        method="optimized",
        optimized_profile="ring-taxon-preserving",
        repeats=1,
        optimizer_iterations=2,
        stochastic=False,
    )
    payload["rings"].append(
        {
            **payload["rings"][0],
            "inner_m": 200,
            "outer_m": 400,
            "mean_m": 300,
        }
    )
    request = service.validate_lra_inputs(payload, input_root=tmp_path)
    assert request.payload()["method_profile"] == "ring-taxon-preserving"
