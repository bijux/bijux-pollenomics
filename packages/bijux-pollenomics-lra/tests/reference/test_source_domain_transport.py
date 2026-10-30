"""Keep source-domain CLI transport canonical without executing an R process."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

import numpy as np
from numpy.typing import NDArray
import pytest

from .lra_oracle import run_source_domains


def test_source_domain_cli_executes_canonical_scripts_and_keeps_r_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    observed: list[list[str]] = []
    expected_cases: list[str] = []

    def own_expectation(
        case: run_source_domains.DomainCase,
    ) -> NDArray[np.float64]:
        expected_cases.append(case.id)
        return np.array([0.5], dtype=np.float64)

    monkeypatch.setattr(run_source_domains, "expectation", own_expectation)

    def blocked(
        command: list[str], **options: object
    ) -> subprocess.CompletedProcess[str]:
        observed.append(command)
        return subprocess.CompletedProcess(command, 2, "", "Controlled R refusal")

    monkeypatch.setattr(
        run_source_domains,
        "shutil",
        SimpleNamespace(which=lambda name: "/usr/bin/Rscript"),
    )
    monkeypatch.setattr(
        run_source_domains,
        "subprocess",
        SimpleNamespace(run=blocked, TimeoutExpired=subprocess.TimeoutExpired),
    )
    output = tmp_path / "domains"
    assert run_source_domains.main(["--output", str(output)]) == 2
    assert expected_cases == [case.id for case in run_source_domains.cases()]
    (command,) = observed
    owner = Path(run_source_domains.__file__).parent
    assert command[2] == str(owner / "source_domains.R")
    assert command[5] == str(owner / "r_support.R")
    assert command[3] == str(output)
    report = json.loads((output / "report.json").read_text())
    assert report["r_exit_code"] == 2
    assert report["status"] == "blocked"
    assert report["passed_cases"] == 0
    assert not list(output.glob("*.py"))
    assert not list(output.glob("*.R"))
