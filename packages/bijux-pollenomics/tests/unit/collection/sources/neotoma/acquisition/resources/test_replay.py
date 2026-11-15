"""Numerical source capture has explicit roles, versions and failure populations."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture import NeotomaMetadataResponse
from bijux_pollenomics.collection.sources.neotoma.capture.resources import (
    NeotomaResourceLimits,
    capture_neotoma_resources,
    replay_neotoma_resource_capture,
)

from .native_payloads import body, plan, response, spec


@pytest.mark.parametrize(
    "field,value",
    [("reason", "invented"), ("http_status", 503), ("absence_certified", True)],
)
def test_replay_rejects_assessment_fields_not_supported_by_final_attempt(
    tmp_path: Path, field: str, value: object
) -> None:
    resource = spec()
    output = tmp_path / "capture"
    capture_neotoma_resources(
        output,
        plan=plan(resource),
        fetch=lambda url, **_: response(url, body(resource)),
    )
    manifest_path = output / "capture-manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest["resources"][0][field] = value
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="assessment"):
        replay_neotoma_resource_capture(output)


def test_replay_rejects_global_parsed_claim_in_partial_capture(tmp_path: Path) -> None:
    output = tmp_path / "capture"
    capture_neotoma_resources(
        output, plan=plan(spec()), fetch=lambda url, **_: response(url, b"{}", 404)
    )
    path = output / "capture-manifest.json"
    manifest = json.loads(path.read_bytes())
    manifest["all_resources_parsed"] = True
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="ledger"):
        replay_neotoma_resource_capture(output)


def test_replay_observes_stricter_caller_attempt_limit(tmp_path: Path) -> None:
    resource = spec()
    calls = []

    def fetch(url: str, **_: object) -> NeotomaMetadataResponse:
        calls.append(url)
        if len(calls) == 1:
            raise TimeoutError("transient")
        return response(url, body(resource))

    output = tmp_path / "capture"
    capture_neotoma_resources(
        output,
        plan=plan(resource),
        limits=NeotomaResourceLimits(retry_delay_seconds=0),
        fetch=fetch,
    )
    with pytest.raises(ValueError, match="attempt budget"):
        replay_neotoma_resource_capture(
            output, limits=NeotomaResourceLimits(max_attempts=1)
        )


@pytest.mark.parametrize("mutation", ["extra", "scalar_kind", "reference_extra"])
def test_reused_result_must_be_the_exact_authenticated_copy(
    tmp_path: Path, mutation: str
) -> None:
    original = tmp_path / "original"
    resource = spec()
    captured = capture_neotoma_resources(
        original, plan=plan(resource), fetch=lambda url, **_: response(url, b"{}", 404)
    )
    reused = tmp_path / "reused"
    capture_neotoma_resources(
        reused,
        plan=plan(resource),
        reuse_from={captured.manifest_sha256: original},
        fetch=lambda *_a, **_k: pytest.fail("reuse GET"),
    )
    path = reused / "capture-manifest.json"
    manifest = json.loads(path.read_bytes())
    entry = manifest["resources"][0]
    if mutation == "extra":
        entry["invented_source_claim"] = "scientifically approved"
    elif mutation == "scalar_kind":
        entry["http_status"] = 404.0
    else:
        entry["reused_from"]["invented_source_claim"] = True
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="relabelled|reference"):
        replay_neotoma_resource_capture(
            reused, source_captures={captured.manifest_sha256: original}
        )


@pytest.mark.parametrize("scope", ["entry", "manifest", "control", "attempt_reference"])
def test_new_attempt_rejects_unowned_result_fields(tmp_path: Path, scope: str) -> None:
    resource = spec()
    output = tmp_path / "capture"
    capture_neotoma_resources(
        output,
        plan=plan(resource),
        fetch=lambda url, **_: response(url, body(resource)),
    )
    path = output / "capture-manifest.json"
    manifest = json.loads(path.read_bytes())
    if scope == "entry":
        manifest["resources"][0]["invented_source_claim"] = "scientifically approved"
    elif scope == "manifest":
        manifest["invented_source_claim"] = "scientifically approved"
    elif scope == "attempt_reference":
        manifest["resources"][0]["attempts"][0]["invented_source_claim"] = (
            "scientifically approved"
        )
    else:
        control_path = output / "request-plan.json"
        control = json.loads(control_path.read_bytes())
        control["invented_source_claim"] = "scientifically approved"
        control_path.write_text(json.dumps(control))
        manifest["plan_sha256"] = sha256(control_path.read_bytes()).hexdigest()
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="fields|assessment"):
        replay_neotoma_resource_capture(output)
