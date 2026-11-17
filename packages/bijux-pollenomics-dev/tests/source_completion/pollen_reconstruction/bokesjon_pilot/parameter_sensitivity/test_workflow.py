"""The maintained consumer runs the real host and publishes derived results only."""

from dataclasses import replace
import json

import pytest

from bijux_pollenomics.analysis.lra.api import read_source_lra_cases, run_lra_request
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.bokesjon_pilot.parameter_sensitivity import (
    preparation,
    workflow,
)

from .test_buffer_ownership import generated


def test_generated_plan_executes_and_exports_derived_only(tmp_path):
    inputs, reference, buffers, scope = generated(tmp_path)
    baseline = run_lra_request(
        inputs.request,
        input_root=inputs.directory,
        destination=tmp_path / "retained-baseline",
    )
    inputs = replace(inputs, directory=baseline.directory)
    prepared = preparation.prepare(inputs, reference, buffers=buffers, scope=scope)
    destination = tmp_path / "comparison"
    report = workflow.execute_prepared(
        prepared,
        inputs,
        destination=destination,
        source_revision="generated-source-control",
    )
    assert report["status"] == "complete_conditional_nominal_comparison"
    assert report["mean"] is report["covariance"] is None
    public = read_source_lra_cases(
        destination / "source-cases",
        expected_manifest_sha256=report["source_case_manifest_sha256"],
    )
    assert public.manifest()["source_inputs_embedded"] is False
    assert json.loads((destination / "report.json").read_bytes()) == report
    assert (destination / "README.md").is_file()
    assert {
        p.relative_to(destination).as_posix()
        for p in destination.rglob("*")
        if p.is_file()
    } == {"source-cases/manifest.json", "README.md", "report.json"}
    assert all(
        r["native_full_pollen_N"] is None for r in public.manifest()["source_coverage"]
    )
    assert report["baseline_exact_numeric_match"] is True
    assert all(
        "counts" not in r
        for role in report["support"]["records"]
        for r in role["pooled_records"]
    )
    assert report["source_request_sha256"]


def test_callback_failure_preserves_prior_and_original_error(tmp_path, monkeypatch):
    inputs, reference, buffers, scope = generated(tmp_path)
    prepared = preparation.prepare(inputs, reference, buffers=buffers, scope=scope)
    destination = tmp_path / "comparison"
    destination.mkdir()
    (destination / "previous.txt").write_text("PRIOR COMPLETE")
    failure = RuntimeError("generated primary execution failure")

    def broken(*args, **kwargs):
        raise failure

    monkeypatch.setattr(workflow, "run_source_lra_cases", broken)
    with pytest.raises(RuntimeError) as caught:
        workflow.execute_prepared(
            prepared,
            inputs,
            destination=destination,
            source_revision="generated-source-control",
        )
    assert caught.value is failure
    assert (destination / "previous.txt").read_text() == "PRIOR COMPLETE"


def test_source_revision_refuses_before_opening_actual_inputs(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(workflow, "load_inputs", lambda *a, **k: calls.append(True))
    with pytest.raises(ValueError):
        workflow.run(
            tmp_path,
            tmp_path / "artifacts/science/comparison",
            source_revision="not-a-code-revision",
        )
    assert not calls
