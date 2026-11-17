"""A separately supplied context cannot relabel already prepared scientific inputs."""

from dataclasses import replace
import json

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.bokesjon_pilot.parameter_sensitivity import (
    preparation,
    workflow,
)

from .test_buffer_ownership import generated


@pytest.mark.parametrize(
    "damage", ["request", "evidence", "provenance", "normalization"]
)
def test_context_substitution_refuses_before_workspace_or_executor(
    tmp_path, monkeypatch, damage
):
    inputs, reference, buffers, scope = generated(tmp_path)
    pins = ({"path": "generated-source-reference.json", "sha256": "a" * 64},)
    inputs = replace(inputs, source_pins=pins)
    prepared = preparation.prepare(inputs, reference, buffers=buffers, scope=scope)
    if damage == "request":
        request = inputs.request
        request["local"]["samples"][0]["sample_id"] = "unrelated-pooled-record"
        request["regional"]["samples"][0]["age_support_bp"] = [4500, 5000]
        inputs = replace(inputs, request_bytes=json.dumps(request).encode())
    elif damage == "evidence":
        inputs.evidence[next(iter(inputs.evidence))] = b"changed evidence"
    elif damage == "provenance":
        pins[0]["sha256"] = "b" * 64
        assert (
            json.loads(prepared.members["parameter-basis.json"])["source_input_pins"][
                0
            ]["sha256"]
            == "a" * 64
        )
    else:
        prepared = replace(prepared, normalization_json="{}")
    calls = []

    def forbidden(*args, **kwargs):
        calls.append(True)
        raise AssertionError("Substituted context reached workspace or executor")

    monkeypatch.setattr(workflow, "resolve_publication_workspace_parent", forbidden)
    monkeypatch.setattr(workflow, "run_source_lra_cases", forbidden)
    target = tmp_path / "must-not-publish"
    with pytest.raises(ValueError):
        workflow.execute_prepared(
            prepared,
            inputs,
            destination=target,
            source_revision="generated-source-control",
        )
    assert not calls and not target.exists()
