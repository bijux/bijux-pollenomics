"""Prospective kernel-branch contracts without executing source kernels or R."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
import shutil
import subprocess
from typing import Any
import warnings

import numpy as np
import pytest

from bijux_pollenomics_dev.ci.atlas_media.process_execution import CompletedCommand
from bijux_pollenomics_dev.lra_validation import kernel_branches as subject
from bijux_pollenomics_lra.dispersal import kernels

ROOT = Path(__file__).resolve().parents[4]


def test_exact_source_branch_matrix_and_original_tolerances_are_frozen() -> None:
    cases = subject.cases()
    assert len(cases) == len({case.case_id for case in cases}) == 30
    assert {case.method for case in cases} == set(kernels.METHODS)
    assert all(
        case.fall_speed_m_s == 0.03 and case.wind_speed_m_s == 3 for case in cases
    )
    for method in kernels.METHODS:
        selected = [case for case in cases if case.method == method]
        assert [(c.diameter_m, c.region_cutoff_argument_m) for c in selected[:3]] == [
            (1999, 100000),
            (2000, 100000),
            (2001, 100000),
        ]
        assert [(c.diameter_m, c.region_cutoff_argument_m) for c in selected[3:]] == [
            (100, 999999),
            (100, 1000000),
            (100, 1000001),
        ]
    assert subject.RTOL == 1e-10 and subject.ATOL == 3e-10


@pytest.mark.parametrize(
    "token,value,passed,kind",
    [
        ("-0.25", -0.25, True, "finite"),
        ("1.0842021724855044e-17", 1.0842021724855044e-17, True, "finite"),
        ("0", 0.0, True, "finite"),
        ("-0", -0.0, True, "finite"),
        ("NaN", math.nan, True, "nan"),
        ("NA", math.nan, True, "nan"),
        ("Inf", math.inf, True, "+inf"),
        ("-Inf", -math.inf, True, "-inf"),
        ("Inf", -math.inf, False, "+inf"),
        ("NaN", 0.0, False, "nan"),
        ("0", math.nan, False, "finite"),
    ],
)
def test_literal_nonfinite_masks_negative_and_correctly_rounded_values(
    token: str,
    value: float,
    passed: bool,
    kind: str,
) -> None:
    result = subject.compare(token, value)
    assert result["passed"] is passed and result["r_kind"] == kind
    if math.isfinite(value) and kind == "finite":
        assert result["absolute_residual"] == 0


@pytest.mark.parametrize(
    "token", ["", " 1", "1 ", "nan", "None", "1junk", "1e9999", "NA_real_"]
)
def test_malformed_or_overflowing_source_token_is_not_a_missing_value(
    token: str,
) -> None:
    with pytest.raises(ValueError):
        subject.compare(token, 0.0)


def test_inherited_absolute_plus_relative_threshold_uses_python_reference() -> None:
    assert subject.compare("0.0000000003", 0.0)["passed"] is True
    assert subject.compare("0.0000000003000001", 0.0)["passed"] is False
    value = 10_000.0
    for delta in (1e-6, 1.001e-6):
        token = repr(value + delta)
        assert subject.compare(token, value)["passed"] is (
            abs(float(token) - value) <= 3e-10 + 1e-10 * abs(value)
        )


@pytest.mark.parametrize("value", [np.array([1.0]), True, "1", np.array(1 + 1j)])
def test_python_non_scalar_or_nonnumeric_return_is_a_retained_error(
    monkeypatch: pytest.MonkeyPatch,
    value: Any,
) -> None:
    monkeypatch.setattr(kernels, "DispersalFactorK", lambda *_: value)
    rows = subject.python_values(math.inf)
    assert len(rows) == 30 and all(row["status"] == "error" for row in rows)
    assert all("numeric scalar" in row["error"] for row in rows)


def test_python_source_warning_and_negative_return_are_not_clipped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = []

    def kernel(*args: Any) -> float:
        calls.append(args)
        warnings.warn("ignored outer value", RuntimeWarning, stacklevel=2)
        return -0.125

    monkeypatch.setattr(kernels, "DispersalFactorK", kernel)
    rows = subject.python_values(math.inf)
    assert len(calls) == 30 and calls[0] == (
        0.03,
        "lake",
        1999,
        "lsm unstable",
        100000,
        3,
    )
    assert all(row["status"] == "returned" and row["value"] == -0.125 for row in rows)
    assert all(row["warnings"] == "ignored outer value" for row in rows)
    with pytest.raises(TimeoutError):
        subject.python_values(-math.inf)


def raw_rows() -> list[dict[str, str]]:
    return [
        {
            "case_id": c.case_id,
            "status": "returned",
            "length": "1",
            "value": "-0.125",
            "warnings": "",
            "error": "",
        }
        for c in subject.cases()
    ]


def write_raw(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(raw_rows()[0]), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


@pytest.mark.parametrize(
    "defect", ["missing", "duplicate", "order", "extra_column", "shape", "error"]
)
def test_source_population_shape_and_error_cannot_be_excluded(
    tmp_path: Path,
    defect: str,
) -> None:
    rows = raw_rows()
    if defect == "missing":
        rows.pop()
    elif defect == "duplicate":
        rows[-1] = rows[0].copy()
    elif defect == "order":
        rows.reverse()
    elif defect == "extra_column":
        for row in rows:
            row["extra"] = "1"
    elif defect == "shape":
        rows[0]["length"] = "2"
    else:
        rows[0].update(status="error", error="original failure", value="", length="0")
    path = tmp_path / "r.csv"
    if defect == "extra_column":
        with path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    else:
        write_raw(path, rows)
    if defect in {"shape", "error"}:
        result = subject.comparison_rows(
            subject.read_r(path),
            [{"status": "returned", "value": -0.125, "warnings": "", "error": ""}] * 30,
        )
        assert not result[0]["passed"] and len(result) == 30
        assert all(row["passed"] for row in result[1:])
    else:
        with pytest.raises(ValueError):
            subject.read_r(path)


def test_native_script_uses_original_namespace_and_exact_runtime_source_guards() -> (
    None
):
    lock = json.loads((ROOT / subject.LOCK).read_text())
    script = subject.r_script(Path("/shared/library"), Path("/owned/output"), lock)
    assert script.count('run_case("') == 30
    assert "disqover::DispersalFactorK(.03,basin,diameter,method,cutoff,3)" in script
    assert 'getNamespaceInfo(asNamespace("disqover"),"path")' in script
    assert 'normalizePath(file.path(library_path,"disqover"))' in script
    assert lock["reference"]["sha256"] in script and '"4.6.0"' in script
    assert "is.nan(value)" in script and "is.na(value)" in script
    assert 'invokeRestart("muffleWarning")' in script
    assert "source(" not in script and "install.packages" not in script


def test_generated_r_admission_accepts_only_real_scalars_without_calling_kernels() -> (
    None
):
    rscript = shutil.which("Rscript")
    if rscript is None:
        pytest.skip(
            "R primitive scalar-guard check needs Rscript; no parity is inferred"
        )
    lock = json.loads((ROOT / subject.LOCK).read_text())
    source = subject.r_script(Path("/unused"), Path("/unused"), lock)
    expression = next(
        line.split(" <- ", 1)[1]
        for line in source.splitlines()
        if line.startswith("  ok <- ")
    )
    control = f"""guard <- function(value){{error <- "";{expression}}}
values <- list(.25,1L,NA_real_,NaN,Inf,-.25,matrix(1,1,1),array(1,c(1,1,1)),1+1i,TRUE,"1",list(1),numeric(0))
stopifnot(identical(vapply(values,guard,logical(1)),c(rep(TRUE,6),rep(FALSE,7))))
cat("Real scalar guard passed; no source package or kernel was invoked.\\n")"""
    result = subprocess.run(
        [rscript, "--vanilla", "-e", control],
        check=True,
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert "Real scalar guard passed" in result.stdout


@pytest.mark.parametrize(
    "failure", ["none", "r_exit", "timeout", "source", "missing", "budget"]
)
def test_actual_execution_contract_preserves_failures_without_retry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    failure: str,
) -> None:
    (tmp_path / "artifacts").mkdir()
    library = tmp_path / "library"
    library.mkdir()
    output = tmp_path / "artifacts/result"
    sources = []
    calls = []

    def source(_: Path) -> tuple[str, dict[str, Any]]:
        sources.append(1)
        return ("2" if failure == "source" and len(sources) > 1 else "1") * 40, {}

    def run(command: tuple[str, ...], **kwargs: Any) -> CompletedCommand:
        calls.append((command, kwargs))
        if failure != "missing":
            write_raw(output / "r-values.csv", raw_rows())
        return CompletedCommand(
            command,
            7 if failure == "r_exit" else 0,
            b"actual R metadata\n",
            b"warning preserved\n",
            0.1,
            failure == "timeout",
            "terminated" if failure == "timeout" else "not_required",
        )

    monkeypatch.setattr(subject, "_source", source)
    monkeypatch.setattr(subject, "r_script", lambda *_: "original function invocation")
    monkeypatch.setattr(subject, "run_bounded_argv", run)
    monkeypatch.setattr(kernels, "DispersalFactorK", lambda *_: -0.125)
    if failure == "budget":
        monkeypatch.setattr(subject, "OUTPUT_LIMIT", 1)
    assert subject.execute(tmp_path, library, Path("/Rscript"), output) == (
        failure != "none"
    )
    assert len(calls) == 1 and len(sources) == 2
    assert calls[0][1]["timeout_seconds"] <= 60
    assert (output / "r-stderr.txt").read_bytes() == b"warning preserved\n"
    if failure != "missing":
        with (output / "comparison.csv").open() as handle:
            result = list(csv.DictReader(handle))
        assert len(result) == 30 and all(
            row["python_value"] == "-0.125" for row in result
        )
    else:
        assert not (output / "comparison.csv").exists()
    log = capsys.readouterr().out
    assert "source_commit=" in log and "exit_code=" in log
    if failure == "r_exit":
        assert "r_exit=7" in log
    if failure == "source":
        assert "source_stable=false" in log


def test_source_guard_keeps_actual_equations_resource_and_raw_archive_in_scope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = []
    monkeypatch.setattr(subprocess, "check_output", lambda *_, **__: "1" * 40)
    monkeypatch.setattr(
        subprocess, "check_call", lambda command, **_: calls.append(command)
    )
    revision, lock = subject._source(ROOT)
    assert revision == "1" * 40 and lock["reference"]["version"] == "0.9.14"
    for path in (
        "dispersal/kernels.py",
        "dispersal/loess.py",
        "dispersal/rounding.py",
        "models/validation.py",
        "resources/data/lsm_models.npz",
    ):
        assert any(str(p).endswith(path) for p in calls[-1])
    monkeypatch.setattr(kernels, "__file__", "/foreign/kernels.py")
    with pytest.raises(ValueError, match="Canonical"):
        subject._source(ROOT)
