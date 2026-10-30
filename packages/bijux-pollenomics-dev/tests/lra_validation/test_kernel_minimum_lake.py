"""The separate minimum-lake profile retains refusal and numerical outcomes."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.atlas_media.process_execution import CompletedCommand
from bijux_pollenomics_dev.lra_validation import kernel_branches as subject
from bijux_pollenomics_lra.dispersal import kernels
from bijux_pollenomics_lra.models.errors import ValidationError

from .test_kernel_branches import ROOT, raw_rows, write_raw


def minimum_rows() -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    raw = [
        dict(row, case_id=case.case_id)
        for row, case in zip(
            raw_rows()[:3], subject.cases(subject.MINIMUM_LAKE_POPULATION), strict=True
        )
    ]
    python = [
        {"status": "returned", "value": -0.125, "warnings": "", "error": ""}
        for _ in raw
    ]
    raw[0].update(status="error", length="0", value="", error=subject.R_DOMAIN_ERROR)
    python[0].update(status="error", value="", error=subject.PYTHON_DOMAIN_ERROR)
    return raw, python


def test_minimum_lake_population_retains_refusal_and_original_schema() -> None:
    population = subject.MINIMUM_LAKE_POPULATION
    selected = subject.cases(population)
    assert [c.case_id for c in selected] == [
        f"lake-d{d}-c100000-gpm_neutral" for d in (5, 6, 7)
    ]
    for c in selected:
        assert (c.basin, c.method, c.region_cutoff_argument_m) == (
            "lake",
            "gpm neutral",
            100000,
        )
        assert (c.fall_speed_m_s, c.wind_speed_m_s) == (0.03, 3)
    raw, python = minimum_rows()
    rows = subject.comparison_rows(raw, python, population)
    assert [r["outcome"] for r in rows] == [
        "paired_refusal",
        "finite_comparison",
        "finite_comparison",
    ]
    assert all(r["passed"] for r in rows) and rows[0]["absolute_residual"] == ""
    old = subject.comparison_rows(
        raw_rows(),
        [{"status": "returned", "value": -0.125, "warnings": "", "error": ""}] * 30,
    )
    assert len(old) == 30 and all(
        "outcome" not in r and "expected_outcome" not in r for r in old
    )
    with pytest.raises(ValueError):
        subject.cases("unknown")


@pytest.mark.parametrize(
    "defect",
    [
        "R_only",
        "Python_only",
        "unexpected_return",
        "wrong_R_error",
        "wrong_Python_error",
        "all_errors",
        "nan_return",
        "wrong_length",
        "numeric_error_token",
    ],
)
def test_minimum_lake_expected_error_cannot_hide_unrelated_or_one_sided_failures(
    defect: str,
) -> None:
    raw, python = minimum_rows()
    if defect == "R_only":
        python[0].update(status="returned", value=-0.125, error="")
    elif defect == "Python_only":
        raw[0].update(status="returned", length="1", value="-.125", error="")
    elif defect == "unexpected_return":
        raw[0].update(status="returned", length="1", value="-.125", error="")
        python[0].update(status="returned", value=-0.125, error="")
    elif defect == "wrong_R_error":
        raw[0]["error"] = "unrelated source failure"
    elif defect == "wrong_Python_error":
        python[0]["error"] = "ValueError: unrelated refusal"
    elif defect == "all_errors":
        for i in (1, 2):
            raw[i].update(raw[0], case_id=raw[i]["case_id"])
            python[i].update(python[0])
    elif defect == "nan_return":
        raw[1]["value"] = "NA"
        python[1]["value"] = math.nan
    elif defect == "wrong_length":
        raw[0]["length"] = "1"
    else:
        raw[0]["value"] = "0"
    rows = subject.comparison_rows(raw, python, subject.MINIMUM_LAKE_POPULATION)
    assert any(not r["passed"] for r in rows)


def test_minimum_lake_generated_batch_and_reader_require_only_three_named_cases(
    tmp_path: Path,
) -> None:
    population = subject.MINIMUM_LAKE_POPULATION
    script = subject.r_script(
        Path("/unused"),
        Path("/unused"),
        json.loads((ROOT / subject.LOCK).read_text()),
        population,
    )
    assert (
        script.count('run_case("') == 3
        and 'identical(result$status,c("error","returned","returned"))' in script
    )
    assert (
        subject.R_DOMAIN_ERROR in script
        and "all(is.finite(as.numeric(result$value[2:3])))" in script
    )
    raw, _ = minimum_rows()
    path = tmp_path / "R.csv"
    write_raw(path, raw)
    assert subject.read_r(path, population) == raw
    with pytest.raises(ValueError):
        subject.read_r(path)


@pytest.mark.parametrize("failure", ["none", "r_exit", "source"])
def test_minimum_driver_preserves_case_refusal_but_requires_parent_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    failure: str,
) -> None:
    (tmp_path / "artifacts").mkdir()
    library = tmp_path / "library"
    library.mkdir()
    output = tmp_path / "artifacts/result"
    revisions = []
    calls = []

    def source(_: Path) -> tuple[str, dict[str, Any]]:
        revisions.append(1)
        return ("2" if failure == "source" and len(revisions) > 1 else "1") * 40, {}

    def kernel(*args: Any) -> float:
        calls.append(args)
        if args[2] == 5:
            raise ValidationError(
                "The source lake integration requires a basin diameter of at least 6 m"
            )
        return -0.125

    def native(command: tuple[str, ...], **_: Any) -> CompletedCommand:
        raw, _python = minimum_rows()
        write_raw(output / "r-values.csv", raw)
        return CompletedCommand(
            command,
            7 if failure == "r_exit" else 0,
            b"",
            b"",
            0.1,
            False,
            "not_required",
        )

    monkeypatch.setattr(subject, "_source", source)
    monkeypatch.setattr(subject, "r_script", lambda *_: "No kernel execution")
    monkeypatch.setattr(subject, "run_bounded_argv", native)
    monkeypatch.setattr(kernels, "DispersalFactorK", kernel)
    assert subject.execute(
        tmp_path, library, Path("/Rscript"), output, subject.MINIMUM_LAKE_POPULATION
    ) == (failure != "none")
    assert [c[2] for c in calls] == [5, 6, 7] and len(revisions) == 2
    log = capsys.readouterr().out
    assert "numerical_matches=2 paired_refusals=1" in log
    if failure == "source":
        assert "source_stable=false" in log
