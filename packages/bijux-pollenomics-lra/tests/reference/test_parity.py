from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from lra_oracle.cases import build_cases, r_literal
from lra_oracle.prospective import (
    EXPECTED_DECLARATION_SHA256,
    load_prospective_optimized_declaration,
)
from lra_oracle.scope import R_COMPATIBLE_API
from lra_oracle.stored import run_stored_parity

from bijux_pollenomics_lra.dispersal.rounding import r_round


@pytest.mark.parametrize("digits", [0, 2, 3, 4])
def test_r_round_handles_sign_and_nonfinite(digits: int) -> None:
    values = np.array([0.015, 0.025, 2.675, np.inf, np.nan, 0.0])
    result = np.asarray(r_round(values, digits))
    np.testing.assert_allclose(r_round(-values, digits), -result, equal_nan=True)
    assert np.isinf(result[3]) and np.isnan(result[4])


def test_r_round_is_not_numpy_shortcut() -> None:
    assert r_round(0.015, 2) == 0.01
    assert np.round(0.015, 2) == 0.02


def test_stored_parity_passes_and_reports_scope(tmp_path: Path) -> None:
    report = run_stored_parity()
    assert report.status == "passed"
    assert report.models == 45
    assert report.evaluation_points == 5760
    assert report.refit_points == 5760
    assert report.evaluation_max_abs_error <= report.tolerance
    assert report.refit_max_abs_error <= report.tolerance
    path = report.write(tmp_path / "stored.json")
    assert json.loads(path.read_text())["status"] == "passed"


def test_live_oracle_preparation_covers_all_apis(tmp_path: Path) -> None:
    setup, cases = build_cases(tmp_path)
    assert set(R_COMPATIBLE_API) == {case.api for case in cases}
    assert len({case.name for case in cases}) == len(cases)
    assert all(len(case.expected) > 0 for case in cases)
    assert any(case.mode == "supplied_random_draws" for case in cases)
    assert any(case.mode == "sampler_and_optimizer_replay" for case in cases)
    assert setup


def test_prospective_optimized_declaration_is_frozen_and_covered(
    tmp_path: Path,
) -> None:
    declaration = load_prospective_optimized_declaration()
    assert declaration.declaration_sha256 == EXPECTED_DECLARATION_SHA256
    assert len(declaration.cases) == 3
    assert declaration.rtol == declaration.atol == 1e-10
    assert len({case.input_sha256 for case in declaration.cases}) == 3
    _, cases = build_cases(tmp_path)
    prepared = {case.name: case for case in cases}
    for declared in declaration.cases:
        assert f"{declared.case_id}_intermediates" in prepared
        assert f"{declared.case_id}_taxon_axis" in prepared
        ring_axis = prepared[f"{declared.case_id}_ring_axis"]
        assert ring_axis.exact_indices == tuple(range(len(ring_axis.expected)))
        wrapper = prepared[f"{declared.case_id}_wrapper_replay"]
        assert wrapper.exact_indices
        assert f"{declared.case_id}_nonfinite_objective" in prepared
        assert f"{declared.case_id}_all_nonfinite_refusal" in prepared


def test_r_literals_escape_and_encode_arrays() -> None:
    assert r_literal('a"b') == '"a\\"b"'
    assert r_literal(np.nan) == "NA_real_"
    matrix = r_literal(np.array([[1, 2], [3, 4]]))
    assert matrix.startswith("array(c(") and "dim=c(2,2)" in matrix


def test_prepare_only_writes_explicit_nonexecution_report(
    project_root: Path, tmp_path: Path
) -> None:
    output = tmp_path / "live"
    completed = subprocess.run(
        [
            sys.executable,
            str(project_root / "tests/reference/lra_oracle" / "run_live_r.py"),
            "--prepare-only",
            "--output",
            str(output),
        ],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    report = json.loads((output / "report.json").read_text())
    assert report["status"] == "prepared_not_executed"
    assert report["live_R_executed"] is False
    assert (output / "python_expected_not_R_goldens.npz").is_file()
    assert (output / "oracle.R").is_file()
