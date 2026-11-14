"""Source-backed controls retain the existing public-host request authority."""

import hashlib
from importlib import import_module
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.bokesjon_pilot.basin_sensitivity.protocol import (
    profiles,
)


def implementation() -> Any:
    try:
        return import_module(
            "bijux_pollenomics_dev.source_completion.pollen_reconstruction."
            "bokesjon_pilot.basin_sensitivity.inputs"
        )
    except ModuleNotFoundError:
        pytest.fail("The authenticated basin request input boundary is missing")


def source_repository() -> Path:
    repository = next(
        p for p in Path(__file__).resolve().parents if (p / "uv.lock").is_file()
    )
    if not (repository / "artifacts/science/love-nonnegative-cover/cache").is_dir():
        pytest.skip("Retained source-bound BOKE baseline is not available")
    return repository


def test_profile_request_keeps_counts_and_rebinds_geometry_evidence(
    tmp_path: Path,
) -> None:
    module = implementation()
    inputs = module.load_inputs(source_repository())
    root = tmp_path / "inputs"
    request = module.materialize(inputs, profiles()[0], root)
    card_pin = next(
        row
        for row in inputs.source_pins
        if row["path"] == "data/neotoma/raw/bokesjon-core-sources/basin-sources.json"
    )
    assert card_pin["sha256"] == hashlib.sha256(inputs.basin_sources).hexdigest()
    decision = json.loads((root / "decision.json").read_text())["basin_sensitivity"]
    assert decision["basin_source_card"]["sha256"] == card_pin["sha256"]
    assert "lansstyrelsen.se" in decision["source"]
    assert request["local"]["samples"][0]["counts"] == [570, 105]
    assert request["regional"]["samples"][0]["counts"] == [506, 36]
    assert request["regional"]["basin"]["diameter_m"] == 1674.0
    assert (
        request["configuration"]["love"]["analytical_cover_policy"]
        == "clip-and-renormalize"
    )
    assert request["local"]["basin"]["diameter_m"] == pytest.approx(138.1976597885342)
    assert len(list(root.iterdir())) == 9
    from bijux_pollenomics.analysis.lra.api import validate_lra_inputs

    validate_lra_inputs(request, input_root=root)
    assert inputs.request["local"]["basin"]["diameter_m"] == 160.0


def test_changed_original_evidence_is_refused_before_profile_materialization(
    tmp_path: Path,
) -> None:
    module = implementation()
    inputs = module.load_inputs(source_repository())
    inputs.evidence["BOKE-raw.json"] = b"{}"
    with pytest.raises(ValueError, match="evidence"):
        module.materialize(inputs, profiles()[2], tmp_path / "inputs")
    assert not (tmp_path / "inputs").exists()
