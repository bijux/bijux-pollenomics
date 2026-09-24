"""The host publishes draw-fed LOVE without a regional pollen placeholder."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from bijux_pollenomics.analysis.lra import publication_draws
from bijux_pollenomics.analysis.lra.engine.discovery import EngineBinding
from bijux_pollenomics.analysis.lra.engine.errors import LRARefusal
from bijux_pollenomics.analysis.lra.execution import regional_draw_love
from bijux_pollenomics.analysis.lra.outputs.reading import read_lra_product
from bijux_pollenomics_lra import api as engine_api

from ..support import regional_draw_love_fixture
from ..test_publication_draws import _bundle, _pin


def _binding() -> EngineBinding:
    return EngineBinding(
        "bijux-pollenomics-lra",
        "0.2.0",
        "python-numpy-scipy",
        engine_api,
    )


def test_installed_host_publishes_and_reopens_draw_fed_love(tmp_path: Path) -> None:
    bundle, _ = _bundle(tmp_path)
    payload = regional_draw_love_fixture(
        tmp_path,
        bundle=bundle,
        checksums_sha256=_pin(bundle),
        local_site_id="small",
        cohort_disposition="included_method_control",
    )
    binding = _binding()
    destination = tmp_path / "local-product"
    with (
        patch.object(regional_draw_love, "load_engine", return_value=binding),
        patch.object(publication_draws, "load_engine", return_value=binding),
    ):
        product = regional_draw_love.run_regional_draw_love_request(
            payload,
            input_root=tmp_path,
            destination=destination,
        )
    verified = read_lra_product(
        destination, expected_manifest_sha256=product.manifest_sha256
    )
    manifest = verified.manifest()
    request = json.loads((destination / "request.json").read_text())
    scientific = manifest["scientific_identity"]["engine_scientific_manifest"]
    assert request["schema_version"] == "lra-regional-draw-love-request.v1"
    assert "regional" not in request
    assert request["regional_draw_source"]["cohort_disposition"] == (
        "included_method_control"
    )
    assert manifest["scientific_acceptance"] == "not_evaluated"
    assert manifest["units"]["regional_cover_draws"] == "fraction"
    assert "regional_cover" not in manifest["units"]
    assert scientific["inputs"].get("regional_pollen") is None
    assert scientific["parameters"]["configuration_kind"] == ("regional-cover-draws")
    assert "regional_basin_type" not in scientific["parameters"]
    assert "regional_basin_diameter_m" not in scientific["parameters"]
    assert scientific["parameters"]["regional_cohort_overlap"] is True
    assert (destination / "numerical/cover_mean.csv").is_file()


def test_source_change_during_calculation_refuses_before_publication(
    tmp_path: Path,
) -> None:
    bundle, _ = _bundle(tmp_path)
    payload = regional_draw_love_fixture(
        tmp_path,
        bundle=bundle,
        checksums_sha256=_pin(bundle),
    )
    binding = _binding()
    original = engine_api.run_love_from_regional_draws

    def mutate_source(*args: object, **kwargs: object) -> object:
        result = original(*args, **kwargs)
        member = bundle / "regional-cover-draws/bin-0.csv"
        member.write_text(member.read_text() + "changed\n")
        return result

    destination = tmp_path / "local-product"
    with (
        patch.object(regional_draw_love, "load_engine", return_value=binding),
        patch.object(publication_draws, "load_engine", return_value=binding),
        patch.object(engine_api, "run_love_from_regional_draws", mutate_source),
        pytest.raises(LRARefusal) as raised,
    ):
        regional_draw_love.run_regional_draw_love_request(
            payload,
            input_root=tmp_path,
            destination=destination,
        )
    assert raised.value.reason_code == "invalid_multisite_regional_draw_source"
    assert not destination.exists()


def test_source_change_during_result_serialization_refuses_publication(
    tmp_path: Path,
) -> None:
    bundle, _ = _bundle(tmp_path)
    payload = regional_draw_love_fixture(
        tmp_path,
        bundle=bundle,
        checksums_sha256=_pin(bundle),
    )
    binding = _binding()
    original_write = engine_api.LoveResult.write

    def mutate_source_during_write(
        result: engine_api.LoveResult, directory: str | Path
    ) -> Path:
        written = original_write(result, directory)
        member = bundle / "regional-cover-draws/bin-0.csv"
        member.write_text(member.read_text() + "changed\n")
        return written

    destination = tmp_path / "local-product"
    with (
        patch.object(regional_draw_love, "load_engine", return_value=binding),
        patch.object(publication_draws, "load_engine", return_value=binding),
        patch.object(engine_api.LoveResult, "write", mutate_source_during_write),
        pytest.raises(LRARefusal) as raised,
    ):
        regional_draw_love.run_regional_draw_love_request(
            payload,
            input_root=tmp_path,
            destination=destination,
        )
    assert raised.value.reason_code == "invalid_multisite_regional_draw_source"
    assert not destination.exists()
