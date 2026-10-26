"""Exercise the source-native curve directory boundary without MCMC proposals."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess

import pytest

from bijux_pollenomics_dev.source_completion.pollen_age_support.abborrtjarnen_bacon.inputs import (
    read_inputs,
)


def test_prepared_curve_directory_opens_in_native_zero_proposal_call(
    tmp_path: Path,
) -> None:
    repository = Path(__file__).resolve().parents[6]
    library = repository / "artifacts/qualification/native-reference/library"
    source_root = repository.parent / "-bijux-pollenomics-data"
    rscript = shutil.which("Rscript")
    if (
        rscript is None
        or not (library / "rbacon/DESCRIPTION").is_file()
        or not (source_root / "legacyage/zenodo-5815192").is_dir()
    ):
        pytest.skip(
            "Qualified native R runtime and original source inputs are unavailable"
        )
    if "Version: 4.0.2\n" not in (library / "rbacon/DESCRIPTION").read_text():
        pytest.skip("The declared rbacon 4.0.2 runtime is not installed")
    case = read_inputs(repository, source_root)
    case_path = tmp_path / "input.json"
    case_path.write_text(
        json.dumps(
            {
                "protocol": case.protocol,
                "controls": case.controls,
                "sample_ids": case.sample_ids,
                "depths": case.depths.tolist(),
            }
        )
    )
    script = (
        repository
        / "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/pollen_age_support/abborrtjarnen_bacon/fit.R"
    )
    prepared = subprocess.run(
        [
            rscript,
            "--vanilla",
            str(script),
            str(library),
            str(case_path),
            str(tmp_path),
            "prepare-only",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    (tmp_path / "source-prepare.log").write_text(prepared.stdout + prepared.stderr)
    assert prepared.returncode == 0, prepared.stderr
    contract = tmp_path / "prepared-contract.json"
    metadata = json.loads(contract.read_text())
    assert metadata["native_calibration_directory"].endswith("/")
    # Native 4.0.2 calculates signed it=25*Dim*(3000+ssize). -3000
    # makes it exactly zero before unsigned conversion; the loop is not entered.
    probe = """
args <- commandArgs(trailingOnly=TRUE)
suppressPackageStartupMessages(library(rbacon, lib.loc=args[1]))
prepared <- jsonlite::read_json(args[2], simplifyVector=TRUE)
rbacon:::bacon(prepared$native_input, args[3], -3000L,
  prepared$native_calibration_directory)
stopifnot(nrow(read.table(args[3])) == 1L)
cat("native_proposals=0 initialization_states=1 posterior_draws=0\\n")
"""
    checked = subprocess.run(
        [
            rscript,
            "--vanilla",
            "-e",
            probe,
            str(library),
            str(contract),
            str(tmp_path / "initial-state.out"),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    (tmp_path / "native-input-probe.log").write_text(checked.stdout + checked.stderr)
    assert checked.returncode == 0, checked.stderr
    assert (
        "native_proposals=0 initialization_states=1 posterior_draws=0" in checked.stdout
    )
