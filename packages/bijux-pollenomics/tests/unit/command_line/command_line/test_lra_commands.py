"""Installed-command contracts for structured exploratory LRA operations."""

from __future__ import annotations

import hashlib
from importlib import metadata
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from bijux_pollenomics.cli import main

from ...analysis.lra.support import request_fixture


@pytest.mark.parametrize("refused", [False, True])
@pytest.mark.parametrize("profile", [None, "calendar-bp1950-signed.v1"])
def test_saved_report_command_pins_both_inputs_without_running_engine(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    refused: bool,
    profile: str | None,
) -> None:
    from bijux_pollenomics.command_line.runtime import lra
    from bijux_pollenomics.reporting.lra_products import api
    from bijux_pollenomics.reporting.lra_products.api import (
        LRAPresentation,
        LRAPresentationRefusal,
    )

    product, geometry, destination = (
        tmp_path / "product",
        tmp_path / "geometry.json",
        tmp_path / "report",
    )
    result = LRAPresentation(destination, "0" * 64, "1" * 64, "2" * 64, 1, 1)
    with (
        patch.object(
            api,
            "render_lra_report",
            return_value=result,
            side_effect=LRAPresentationRefusal(
                "changed_presentation_input", "geometry.json"
            )
            if refused
            else None,
        ) as render,
        patch.object(lra, "run_lra_request") as compute,
    ):
        code = main(
            [
                "render-lra-report",
                str(product),
                "--expected-manifest-sha256",
                "1" * 64,
                "--geometry",
                str(geometry),
                "--expected-geometry-sha256",
                "2" * 64,
                "--output",
                str(destination),
                *([] if profile is None else ["--temporal-profile", profile]),
            ]
        )
    assert code == (2 if refused else 0)
    assert not compute.called
    render.assert_called_once_with(
        product,
        expected_manifest_sha256="1" * 64,
        geometry_path=geometry,
        expected_geometry_sha256="2" * 64,
        destination=destination,
        temporal_profile=profile,
    )
    payload = json.loads(capsys.readouterr().out)
    if refused:
        assert payload["status"] == "refused"
        assert payload["reason_code"] == "changed_presentation_input"
    else:
        assert payload["status"] == "generated_exploratory"
        assert payload["product_manifest_sha256"] == "1" * 64
        assert payload["geometry_sha256"] == "2" * 64
        assert payload["mapped_site_count"] == payload["refused_site_count"] == 1
        assert payload["scientific_acceptance"] == "not_evaluated"


@pytest.mark.parametrize(
    "interrupted,completed,expected_code",
    [(False, True, 0), (False, False, 2), (True, False, 130)],
)
def test_batch_cli_preserves_item_outcomes_and_exit_status(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    interrupted: bool,
    completed: bool,
    expected_code: int,
) -> None:
    from bijux_pollenomics.analysis.lra.api import LRABatchItemResult, LRABatchResult
    from bijux_pollenomics.command_line.runtime import lra

    path = tmp_path / "batch.json"
    request = request_fixture(tmp_path)
    path.write_text(
        json.dumps(
            {
                "schema_version": "lra-batch-request.v1",
                "items": [{"item_id": "one", "request": request}],
            }
        )
    )
    result = LRABatchResult(
        "0" * 64,
        tmp_path / "attempt",
        (
            LRABatchItemResult(
                0, "one", "1" * 64, "completed" if completed else "not_run"
            ),
        ),
        interrupted,
    )
    with patch.object(lra, "run_lra_batch", return_value=result) as run:
        code = main(
            [
                "run-lra-batch",
                str(path),
                "--input-root",
                str(tmp_path),
                "--cache-root",
                str(tmp_path / "cache"),
                "--report-root",
                str(tmp_path / "attempt"),
                "--max-workers",
                "2",
            ]
        )
    assert code == expected_code
    output = json.loads(capsys.readouterr().out)
    assert output == result.as_dict()
    assert run.call_args.args[0][0].payload() == request
    assert run.call_args.kwargs["limits"].max_workers == 2


@pytest.mark.parametrize(
    "payload",
    [
        {"schema_version": "lra-batch-request.v1", "items": "invalid"},
        {
            "schema_version": "lra-batch-request.v1",
            "items": [{"item_id": "one", "request": None}],
        },
        {"schema_version": "unversioned", "items": []},
    ],
)
def test_batch_cli_refuses_invalid_envelope_before_spawning(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    payload: object,
) -> None:
    from bijux_pollenomics.command_line.runtime import lra

    path = tmp_path / "batch.json"
    path.write_text(json.dumps(payload))
    with patch.object(lra, "run_lra_batch") as run:
        code = main(
            [
                "run-lra-batch",
                str(path),
                "--input-root",
                str(tmp_path),
                "--cache-root",
                str(tmp_path / "cache"),
                "--report-root",
                str(tmp_path / "attempt"),
            ]
        )
    assert code == 2 and not run.called
    assert (
        json.loads(capsys.readouterr().out)["reason_code"] == "invalid_lra_batch_json"
    )


def test_valid_request_reports_missing_extra_without_creating_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    request = tmp_path / "request.json"
    request.write_text(json.dumps(request_fixture(tmp_path)))
    destination = tmp_path / "product"
    with patch.object(
        metadata, "distribution", side_effect=metadata.PackageNotFoundError
    ):
        code = main(
            [
                "run-lra",
                str(request),
                "--input-root",
                str(tmp_path),
                "--output",
                str(destination),
            ]
        )
    result = json.loads(capsys.readouterr().out)
    assert code == 2
    assert result["reason_code"] == "lra_extension_missing"
    assert not destination.exists()


def test_duplicate_json_key_is_not_silently_overwritten(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    request = tmp_path / "request.json"
    request.write_text('{"operation":"reveals","operation":"love"}')
    code = main(["validate-lra-input", str(request), "--input-root", str(tmp_path)])
    result = json.loads(capsys.readouterr().out)
    assert code == 2
    assert result["reason_code"] == "lra_request_io_or_encoding"
    assert "Duplicate JSON key" in result["detail"]


def test_nonobject_request_is_a_structured_refusal(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    request = tmp_path / "request.json"
    request.write_text("[]")
    code = main(["validate-lra-input", str(request), "--input-root", str(tmp_path)])
    assert code == 2
    assert json.loads(capsys.readouterr().out)["reason_code"] == "invalid_lra_json"


def test_optimizer_diagnostics_survive_command_boundary(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from bijux_pollenomics.analysis.lra.engine.errors import LRARefusal
    from bijux_pollenomics.command_line.runtime import lra

    request = tmp_path / "request.json"
    request.write_text(json.dumps(request_fixture(tmp_path)))
    diagnostics = [
        {"reason": "maximum_iterations", "evaluations": 5, "best_objective": 0.125}
    ]
    refusal = LRARefusal(
        "optimizer_nonconvergence",
        "Iteration budget exhausted",
        diagnostics=diagnostics,
    )
    with patch.object(lra, "run_lra_request", side_effect=refusal):
        code = main(
            [
                "run-lra",
                str(request),
                "--input-root",
                str(tmp_path),
                "--output",
                str(tmp_path / "product"),
            ]
        )
    envelope = json.loads(capsys.readouterr().out)
    assert code == 2
    assert envelope["reason_code"] == "optimizer_nonconvergence"
    assert envelope["diagnostics"] == diagnostics


@pytest.mark.parametrize(
    ("status", "interrupted", "expected_code"),
    [("complete", False, 0), ("incomplete", False, 2), ("incomplete", True, 130)],
)
def test_joint_command_preserves_computation_status_and_denominators(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    status: str,
    interrupted: bool,
    expected_code: int,
) -> None:
    from bijux_pollenomics.analysis.lra.uncertainty import api

    path = tmp_path / "joint.json"
    payload = {"test_input": "routing only"}
    path.write_text(json.dumps(payload))
    target, cache = tmp_path / "ensemble", tmp_path / "cache"
    denominators = {
        "requested_draw_bins": 4,
        "successful_draw_bins": 4 if status == "complete" else 3,
        "refused_draw_bins": int(status != "complete" and not interrupted),
        "not_run_draw_bins": int(interrupted),
    }
    manifest = {
        "status": status,
        "interrupted": interrupted,
        "denominators": denominators,
    }
    encoded = json.dumps(manifest)
    checksum = hashlib.sha256(encoded.encode()).hexdigest()
    product = api.JointLRAProduct(target, checksum, encoded)
    sentinel = object()
    with (
        patch.object(api.JointLRAPlan, "from_dict", return_value=sentinel) as parse,
        patch.object(api, "run_joint_lra_ensemble", return_value=product) as run,
    ):
        code = main(
            [
                "run-joint-lra",
                str(path),
                "--input-root",
                str(tmp_path),
                "--output",
                str(target),
                "--cache-root",
                str(cache),
            ]
        )
    assert code == expected_code
    parse.assert_called_once_with(payload)
    run.assert_called_once_with(
        sentinel,
        input_root=tmp_path,
        destination=target,
        cache_directory=cache,
    )
    output = json.loads(capsys.readouterr().out)
    assert output == {
        "status": "generated_exploratory",
        "scientific_acceptance": "not_evaluated",
        "computation_status": status,
        "interrupted": interrupted,
        "denominators": denominators,
        "directory": str(target),
        "manifest_sha256": checksum,
    }


@pytest.mark.parametrize("encoded", ["{}", '{"bins":[],"bins":[]}', "[]"])
def test_joint_command_refuses_malformed_plan_before_execution(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    encoded: str,
) -> None:
    from bijux_pollenomics.analysis.lra.uncertainty import api

    path = tmp_path / "joint.json"
    path.write_text(encoded)
    target = tmp_path / "ensemble"
    with patch.object(api, "run_joint_lra_ensemble") as run:
        code = main(
            [
                "run-joint-lra",
                str(path),
                "--input-root",
                str(tmp_path),
                "--output",
                str(target),
            ]
        )
    assert code == 2 and not run.called and not target.exists()
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "refused"
    assert output["reason_code"] in {
        "invalid_joint_plan",
        "invalid_lra_json",
        "lra_request_io_or_encoding",
    }
