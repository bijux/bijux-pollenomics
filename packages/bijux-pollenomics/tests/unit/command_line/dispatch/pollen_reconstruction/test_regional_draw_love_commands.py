"""Normal LRA commands expose the existing authenticated draw-fed LOVE route."""

from __future__ import annotations

from importlib import metadata
import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from bijux_pollenomics.analysis.lra import publication_draws
from bijux_pollenomics.analysis.lra.engine.discovery import EngineBinding, load_engine
from bijux_pollenomics.analysis.lra.execution import regional_draw_love, service
from bijux_pollenomics.analysis.lra.outputs.reading import read_lra_product
from bijux_pollenomics.cli import main
from bijux_pollenomics.command_line.runtime import lra
from bijux_pollenomics_lra import api as engine_api

from ....analysis.lra.support import regional_draw_love_fixture, request_fixture
from ....analysis.lra.test_publication_draws import _bundle, _pin


@pytest.fixture
def draw_request(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[dict[str, Any], Path]:
    bundle, _ = _bundle(tmp_path)
    payload = regional_draw_love_fixture(
        tmp_path, bundle=bundle, checksums_sha256=_pin(bundle)
    )
    binding = EngineBinding(
        "bijux-pollenomics-lra", "0.2.0", "python-numpy-scipy", engine_api
    )
    for owner in (regional_draw_love, publication_draws, service):
        monkeypatch.setattr(owner, "load_engine", lambda **_: binding)
    request = tmp_path / "request.json"
    request.write_text(json.dumps(payload))
    return payload, request


def command_arguments(command: str, request: Path, root: Path) -> list[str]:
    arguments = [command, str(request), "--input-root", str(root)]
    if command == "run-lra":
        arguments.extend(["--output", str(root / "product")])
    return arguments


def test_validation_authenticates_source_without_running_either_reconstruction(
    tmp_path: Path,
    draw_request: tuple[dict[str, Any], Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, request = draw_request
    with (
        patch.object(engine_api, "run_love_from_regional_draws") as compute,
        patch.object(lra, "validate_lra_inputs") as generic,
    ):
        code = main(command_arguments("validate-lra-input", request, tmp_path))
    assert code == 0
    compute.assert_not_called()
    generic.assert_not_called()
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "validated_exploratory_input"
    assert result["scientific_acceptance"] == "not_evaluated"
    assert len(result["request_sha256"]) == 64
    assert not (tmp_path / "product").exists()


def test_run_registers_and_reopens_real_draw_fed_product(
    tmp_path: Path,
    draw_request: tuple[dict[str, Any], Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    payload, request = draw_request
    with patch.object(lra, "run_lra_request") as generic:
        code = main(command_arguments("run-lra", request, tmp_path))
    assert code == 0
    generic.assert_not_called()
    result = json.loads(capsys.readouterr().out)
    product = read_lra_product(
        tmp_path / "product", expected_manifest_sha256=result["manifest_sha256"]
    )
    manifest = product.manifest()
    assert (
        result["scientific_content_sha256"] == product.product.scientific_content_sha256
    )
    assert manifest["scientific_acceptance"] == "not_evaluated"
    assert manifest["units"]["regional_cover_draws"] == "fraction"
    assert "regional_cover" not in manifest["units"]
    saved = json.loads((tmp_path / "product/request.json").read_bytes())
    assert saved == payload and "regional" not in saved
    scientific = manifest["scientific_identity"]["engine_scientific_manifest"]
    assert scientific["inputs"].get("regional_pollen") is None
    assert (tmp_path / "product/numerical/cover_mean.csv").is_file()


@pytest.mark.parametrize("command", ["validate-lra-input", "run-lra"])
@pytest.mark.parametrize("schema", ["unknown.v1", None, True, ["lra-request.v1"]])
def test_unknown_or_malformed_schema_cannot_select_draw_route(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    command: str,
    schema: object,
) -> None:
    request = tmp_path / "request.json"
    request.write_text(json.dumps({"schema_version": schema}))
    with (
        patch.object(lra, "validate_regional_draw_love_inputs") as validate,
        patch.object(lra, "run_regional_draw_love_request") as run,
    ):
        code = main(command_arguments(command, request, tmp_path))
    assert code == 2
    assert json.loads(capsys.readouterr().out)["reason_code"] == "invalid_lra_schema"
    validate.assert_not_called()
    run.assert_not_called()
    assert not (tmp_path / "product").exists()


@pytest.mark.parametrize("command", ["validate-lra-input", "run-lra"])
@pytest.mark.parametrize(
    "change", ["missing_source", "wrong_operation", "changed_member"]
)
def test_draw_route_preserves_schema_and_authentication_refusals(
    tmp_path: Path,
    draw_request: tuple[dict[str, Any], Path],
    capsys: pytest.CaptureFixture[str],
    command: str,
    change: str,
) -> None:
    payload, request = draw_request
    if change == "missing_source":
        del payload["regional_draw_source"]
    elif change == "wrong_operation":
        payload["operation"] = "reveals"
    else:
        member = tmp_path / "regional/regional-cover-draws/bin-0.csv"
        member.write_text(member.read_text() + "changed\n")
    request.write_text(json.dumps(payload))
    code = main(command_arguments(command, request, tmp_path))
    assert code == 2
    result = json.loads(capsys.readouterr().out)
    assert result["reason_code"] == (
        "invalid_multisite_regional_draw_source"
        if change == "changed_member"
        else "invalid_lra_schema"
    )
    assert not (tmp_path / "product").exists()


@pytest.mark.parametrize("command", ["validate-lra-input", "run-lra"])
def test_duplicate_schema_is_refused_before_either_route(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], command: str
) -> None:
    request = tmp_path / "request.json"
    request.write_text(
        '{"schema_version":"lra-request.v1",'
        '"schema_version":"lra-regional-draw-love-request.v1"}'
    )
    code = main(command_arguments(command, request, tmp_path))
    assert code == 2
    result = json.loads(capsys.readouterr().out)
    assert result["reason_code"] == "lra_request_io_or_encoding"
    assert "Duplicate JSON key" in result["detail"]
    assert not (tmp_path / "product").exists()


@pytest.mark.parametrize("command", ["validate-lra-input", "run-lra"])
def test_generic_request_keeps_its_original_production_route(
    tmp_path: Path,
    draw_request: tuple[dict[str, Any], Path],
    capsys: pytest.CaptureFixture[str],
    command: str,
) -> None:
    _, request = draw_request
    request.write_text(json.dumps(request_fixture(tmp_path)))
    with (
        patch.object(lra, "validate_regional_draw_love_inputs") as validate,
        patch.object(lra, "run_regional_draw_love_request") as run,
    ):
        code = main(command_arguments(command, request, tmp_path))
    assert code == 0
    validate.assert_not_called()
    run.assert_not_called()
    assert json.loads(capsys.readouterr().out)["status"] == (
        "validated_exploratory_input"
        if command == "validate-lra-input"
        else "generated_exploratory"
    )


def test_draw_route_retains_numerical_failure_without_partial_product(
    tmp_path: Path,
    draw_request: tuple[dict[str, Any], Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, request = draw_request
    with patch.object(
        engine_api,
        "run_love_from_regional_draws",
        side_effect=engine_api.ValidationError(
            "Controlled numerical refusal", reason_code="controlled_numerical_refusal"
        ),
    ):
        code = main(command_arguments("run-lra", request, tmp_path))
    assert code == 2
    assert (
        json.loads(capsys.readouterr().out)["reason_code"]
        == "controlled_numerical_refusal"
    )
    assert not (tmp_path / "product").exists()


@pytest.mark.parametrize("command", ["validate-lra-input", "run-lra"])
def test_missing_optional_engine_remains_actionable_without_output(
    tmp_path: Path,
    draw_request: tuple[dict[str, Any], Path],
    capsys: pytest.CaptureFixture[str],
    command: str,
) -> None:
    _, request = draw_request
    with (
        patch.object(regional_draw_love, "load_engine", load_engine),
        patch.object(
            metadata, "distribution", side_effect=metadata.PackageNotFoundError
        ),
    ):
        code = main(command_arguments(command, request, tmp_path))
    assert code == 2
    assert json.loads(capsys.readouterr().out)["reason_code"] == "lra_extension_missing"
    assert not (tmp_path / "product").exists()


def test_benchmark_does_not_acquire_the_additional_request_schema(
    tmp_path: Path,
    draw_request: tuple[dict[str, Any], Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, request = draw_request
    with patch.object(engine_api, "run_love_from_regional_draws") as compute:
        code = main(
            [
                "benchmark-lra",
                str(request),
                "--input-root",
                str(tmp_path),
                "--output",
                str(tmp_path / "product"),
            ]
        )
    assert code == 2
    assert json.loads(capsys.readouterr().out)["reason_code"] == "invalid_lra_schema"
    compute.assert_not_called()
    assert not (tmp_path / "product").exists()


@pytest.mark.parametrize("command", ["validate-lra-input", "run-lra", "benchmark-lra"])
def test_help_limits_the_additional_schema_to_normal_validation_and_run(
    capsys: pytest.CaptureFixture[str], command: str
) -> None:
    with pytest.raises(SystemExit) as stopped:
        main([command, "--help"])
    assert stopped.value.code == 0
    help_text = capsys.readouterr().out
    assert ("lra-regional-draw-love-request.v1" in help_text) == (
        command != "benchmark-lra"
    )
