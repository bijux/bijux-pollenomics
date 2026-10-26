"""Preserve completed and active chain populations when the native job fails."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from bijux_pollenomics_dev.ci.atlas_media.process_execution import CompletedCommand
from bijux_pollenomics_dev.source_completion.pollen_age_support.abborrtjarnen_bacon import (
    workflow,
)
from bijux_pollenomics_dev.source_completion.pollen_age_support.abborrtjarnen_bacon.inputs import (
    CoreInputs,
)


def test_failed_second_chain_keeps_actual_partial_population(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    library = tmp_path / "library"
    curves = library / "rintcal/extdata"
    curves.mkdir(parents=True)
    for name in ("3Col_intcal20.14C", "intcal20.14c"):
        (curves / name).write_bytes(b"source-curve")
    digest = hashlib.sha256(b"source-curve").hexdigest()
    monkeypatch.setattr(workflow, "CURVE_SHA256", digest)
    monkeypatch.setattr(workflow, "FULL_CURVE_SHA256", digest)
    monkeypatch.setattr(workflow, "_revision", lambda repository: "committed")
    case = CoreInputs(
        {"source_inputs": {}, "execution": {"seeds": [314159, 271828]}},
        (),
        ("sample",),
        np.asarray([0.0]),
        np.asarray([[1]], dtype=np.int64),
        np.asarray([[[1.0]]]),
        [],
    )
    monkeypatch.setattr(workflow, "read_inputs", lambda repository, source_root: case)
    oracle = tmp_path / "oracle.json"
    oracle.write_text(
        json.dumps(
            {
                "passed": True,
                "source_version": "4.0.2",
                "model_fits": 0,
                "absolute_tolerance": 1e-8,
                "source_support_refusals": 4,
                "fixture_cases": 6,
                "comparison_rows": 64,
                "relative_tolerance": 0,
                "maximum_native_corrected_helper_gap": 0.0,
            }
        )
    )

    def failed(
        command: tuple[str, ...],
        *,
        cwd: Path,
        timeout_seconds: float,
        max_output_bytes: int,
    ) -> CompletedCommand:
        (cwd / "fit-summary.json").write_text(
            json.dumps(
                {
                    "chains": [{"seed": 314159}],
                    "active_seed": 271828,
                    "active_stage": "native_sampling",
                }
            )
        )
        return CompletedCommand(
            command,
            9,
            b"native failure",
            b"123456 maximum resident set size\n",
            0.1,
            False,
            "not_required",
        )

    monkeypatch.setattr(workflow, "run_bounded_argv", failed)
    result = workflow.run(tmp_path, tmp_path, library, oracle, artifacts / "failure")
    assert result["scientific_status"] == "refused_native_execution"
    assert result["requested_chain_seeds"] == [314159, 271828]
    assert result["chain_accounting"] == [
        {"seed": 314159, "status": "saved_states_and_ages_produced"},
        {"seed": 271828, "status": "active_incomplete_execution"},
    ]
    assert result["partial_fit_account"]["active_stage"] == "native_sampling"
    assert result["measured_peak_rss_bytes"] == 123456
    assert (
        json.loads((artifacts / "failure/report.json").read_text())["exit_status"] == 9
    )
