"""The supported host command exposes bounded fresh calls and one reference."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from bijux_pollenomics.analysis.lra.engine.errors import LRARefusal
from bijux_pollenomics.cli import main
from bijux_pollenomics.command_line.runtime import lra

from ....analysis.lra.support import request_fixture


def test_actual_cli_benchmarks_seeded_request_and_writes_only_one_reference(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    payload = request_fixture(tmp_path)
    payload["configuration"]["reveals"]["stochastic"] = True
    request = tmp_path / "request.json"
    request.write_text(json.dumps(payload))
    code = main(
        [
            "benchmark-lra",
            str(request),
            "--input-root",
            str(tmp_path),
            "--output",
            str(tmp_path / "reference"),
            "--repeats",
            "2",
        ]
    )
    result = json.loads(capsys.readouterr().out)
    assert code == 0 and result["status"] == "benchmarked_exploratory"
    assert result["seed"] == 7 and result["repeats"] == 2
    assert len(result["repeated_call_seconds"]) == 1
    assert result["engine"]["numerical_backend"] == "python-numpy-scipy"
    assert sorted(p.name for p in tmp_path.iterdir() if p.is_dir()) == ["reference"]


@pytest.mark.parametrize(
    "reason,expected_code",
    [("lra_extension_missing", 2), ("lra_benchmark_interrupted", 130)],
)
def test_cli_preserves_refusal_diagnostics_and_never_reports_timings_as_success(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], reason: str, expected_code: int
) -> None:
    request = tmp_path / "request.json"
    request.write_text(json.dumps(request_fixture(tmp_path)))
    with patch.object(
        lra,
        "benchmark_lra_request",
        side_effect=LRARefusal(
            reason,
            "Install bijux-pollenomics[lra]",
            diagnostics={"attempted_calls": 0},
        ),
    ):
        code = main(
            [
                "benchmark-lra",
                str(request),
                "--input-root",
                str(tmp_path),
                "--output",
                str(tmp_path / "reference"),
            ]
        )
    result = json.loads(capsys.readouterr().out)
    assert code == expected_code and result["status"] == "refused"
    assert result["reason_code"] == reason
    assert result["diagnostics"] == {"attempted_calls": 0}
    assert "first_call_seconds" not in result and not (tmp_path / "reference").exists()


def test_cli_default_and_help_come_from_registered_parser(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from bijux_pollenomics.command_line.parsing import build_parser

    parsed = build_parser().parse_args(
        [
            "benchmark-lra",
            "request.json",
            "--input-root",
            "inputs",
            "--output",
            "reference",
        ]
    )
    assert parsed.repeats == 3
    with pytest.raises(SystemExit) as raised:
        main(["benchmark-lra", "--help"])
    assert raised.value.code == 0
    text = capsys.readouterr().out
    assert "lra-request.v1" in text and "single reference product" in text
    assert "2 to 10" in text and "default: 3" in text
