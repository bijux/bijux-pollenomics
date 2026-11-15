"""Numerical source capture has explicit roles, versions and failure populations."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture import NeotomaMetadataResponse
from bijux_pollenomics.collection.sources.neotoma.capture.resources import (
    NeotomaRetainedSource,
    capture_neotoma_resources,
    replay_neotoma_resource_capture,
)

from .native_payloads import body, plan, response, spec


def test_resume_authenticates_failed_capture_and_preserves_original_times(
    tmp_path: Path,
) -> None:
    first = tmp_path / "first"
    resource = spec()
    captured = capture_neotoma_resources(
        first, plan=plan(resource), fetch=lambda url, **_: response(url, b"{}", 404)
    )
    before = {p.name: p.read_bytes() for p in first.iterdir() if p.is_file()}
    result = capture_neotoma_resources(
        tmp_path / "resumed",
        plan=plan(resource),
        reuse_from={captured.manifest_sha256: first},
        fetch=lambda *_a, **_k: pytest.fail("repeated unavailable source"),
    )
    assert result.request_count == 0
    assert result.resources[0]["terminal_status"] == "unavailable_http"
    assert (
        result.resources[0]["reused_from"]["manifest_sha256"]
        == captured.manifest_sha256
    )
    assert before == {p.name: p.read_bytes() for p in first.iterdir() if p.is_file()}
    assert (
        replay_neotoma_resource_capture(
            tmp_path / "resumed", source_captures={captured.manifest_sha256: first}
        ).resources
        == result.resources
    )
    resumed_manifest = tmp_path / "resumed" / "capture-manifest.json"
    original_manifest = resumed_manifest.read_bytes()
    altered = json.loads(original_manifest)
    altered["resources"][0]["retained_source"] = {
        "body_sha256": "0" * 64,
        "provenance_sha256": "f" * 64,
        "retrieved_at": "1900-01-01T00:00:00+00:00",
    }
    resumed_manifest.write_text(json.dumps(altered))
    with pytest.raises(ValueError, match="relabelled"):
        replay_neotoma_resource_capture(
            tmp_path / "resumed", source_captures={captured.manifest_sha256: first}
        )
    resumed_manifest.write_bytes(original_manifest)
    receipt = first / captured.resources[0]["attempts"][0]["receipt_file"]
    receipt.write_bytes(b"{}")
    with pytest.raises(ValueError, match="identity"):
        replay_neotoma_resource_capture(
            tmp_path / "resumed", source_captures={captured.manifest_sha256: first}
        )


def test_retry_failed_reuses_success_and_retries_only_previous_failure(
    tmp_path: Path,
) -> None:
    first, second = spec(), spec(202)
    original = tmp_path / "original"
    captured = capture_neotoma_resources(
        original,
        plan=plan(first, second),
        fetch=lambda url, **_: (
            response(url, body(first))
            if url.endswith("/201")
            else response(url, b"{}", 404)
        ),
    )
    urls = []

    def fetch(url: str, **_: object) -> NeotomaMetadataResponse:
        urls.append(url)
        return response(url, body(second))

    result = capture_neotoma_resources(
        tmp_path / "retry",
        plan=plan(first, second),
        reuse_from={captured.manifest_sha256: original},
        retry_failed=True,
        fetch=fetch,
    )
    assert urls == ["https://api.neotomadb.org/v2.0/data/downloads/202"]
    assert [row["terminal_status"] for row in result.resources] == [
        "parsed_native",
        "parsed_native",
    ]
    assert "reused_from" in result.resources[0]
    assert (
        result.resources[1]["predecessor_result"]["terminal_status"]
        == "unavailable_http"
    )


def test_qualified_prior_source_keeps_original_provenance_without_new_get(
    tmp_path: Path,
) -> None:
    resource = spec(kind="geochronologic")
    content = body(resource)
    source = tmp_path / "dating-source.json"
    source.write_bytes(content)
    provenance = tmp_path / "source.json"
    provenance.write_text(
        json.dumps(
            {
                "schema_version": "bokesjon-public-core-sources.v1",
                "sources": [
                    {
                        "source_url": "https://api.neotomadb.org/v2.0/data/downloads/201",
                        "final_url": "https://api.neotomadb.org/v2.0/data/downloads/201",
                        "status": 200,
                        "retrieved_at": "2026-11-14T17:32:38+00:00",
                        "bytes": len(content),
                        "sha256": sha256(content).hexdigest(),
                    }
                ],
            }
        )
    )
    old = NeotomaRetainedSource(
        source,
        provenance,
        sha256(provenance.read_bytes()).hexdigest(),
        sha256(content).hexdigest(),
    )
    inputs = {"dataset-201-current": old}
    result = capture_neotoma_resources(
        tmp_path / "capture",
        plan=plan(resource),
        retained_sources=inputs,
        fetch=lambda *_a, **_k: pytest.fail("existing dating source refetched"),
    )
    row = result.resources[0]
    assert (
        result.request_count == 0
        and row["terminal_status"] == "reused_qualified_native"
    )
    assert row["retained_source"]["retrieved_at"] == "2026-11-14T17:32:38+00:00"
    assert row["retained_source"]["provenance_sha256"] == old.provenance_sha256
    assert not list((tmp_path / "capture").glob("*.body"))
    assert (
        replay_neotoma_resource_capture(
            tmp_path / "capture", retained_sources=inputs
        ).resources
        == result.resources
    )
    source.write_bytes(b"{}")
    with pytest.raises(ValueError, match="identity"):
        replay_neotoma_resource_capture(tmp_path / "capture", retained_sources=inputs)


@pytest.mark.parametrize(
    "mutation", ["digest", "key", "status", "missing", "retry_disabled"]
)
def test_retry_predecessor_must_match_authenticated_selected_input(
    tmp_path: Path, mutation: str
) -> None:
    resource = spec()
    original = tmp_path / "original"
    first = capture_neotoma_resources(
        original, plan=plan(resource), fetch=lambda url, **_: response(url, b"{}", 404)
    )
    output = tmp_path / "retry"
    capture_neotoma_resources(
        output,
        plan=plan(resource),
        reuse_from={first.manifest_sha256: original},
        retry_failed=True,
        fetch=lambda url, **_: response(url, body(resource)),
    )
    manifest_path = output / "capture-manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    predecessor = manifest["resources"][0]["predecessor_result"]
    if mutation == "digest":
        predecessor["manifest_sha256"] = "0" * 64
    elif mutation == "key":
        predecessor["resource_key"] = "dataset-999-doi_frozen"
    elif mutation == "status":
        predecessor["terminal_status"] = "parsed_native"
    elif mutation == "missing":
        del manifest["resources"][0]["predecessor_result"]
    else:
        control_path = output / "request-plan.json"
        control = json.loads(control_path.read_bytes())
        control["retry_failed"] = False
        control_path.write_text(json.dumps(control))
        manifest["plan_sha256"] = sha256(control_path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="predecessor|retry"):
        replay_neotoma_resource_capture(
            output, source_captures={first.manifest_sha256: original}
        )


def test_fresh_attempt_cannot_invent_a_predecessor(tmp_path: Path) -> None:
    resource = spec()
    output = tmp_path / "capture"
    capture_neotoma_resources(
        output,
        plan=plan(resource),
        fetch=lambda url, **_: response(url, body(resource)),
    )
    path = output / "capture-manifest.json"
    manifest = json.loads(path.read_bytes())
    manifest["resources"][0]["predecessor_result"] = {
        "manifest_sha256": "0" * 64,
        "resource_key": "dataset-201-current",
        "terminal_status": "unavailable_http",
    }
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="predecessor"):
        replay_neotoma_resource_capture(output)


@pytest.mark.parametrize("retry_second", [False, True])
def test_reuse_chain_separates_selected_capture_from_ancestor_resolvers(
    tmp_path: Path, retry_second: bool
) -> None:
    resource = spec()
    first_path, second_path, third_path = (
        tmp_path / name for name in ("first", "second", "third")
    )
    first = capture_neotoma_resources(
        first_path,
        plan=plan(resource),
        fetch=lambda url, **_: response(url, b"{}", 404),
    )
    second = capture_neotoma_resources(
        second_path,
        plan=plan(resource),
        reuse_from={first.manifest_sha256: first_path},
        retry_failed=retry_second,
        fetch=(lambda url, **_: response(url, body(resource)))
        if retry_second
        else (lambda *_a, **_k: pytest.fail("reuse GET")),
    )
    third = capture_neotoma_resources(
        third_path,
        plan=plan(resource),
        reuse_from={second.manifest_sha256: second_path},
        source_captures={first.manifest_sha256: first_path},
        fetch=lambda *_a, **_k: pytest.fail("chained reuse GET"),
    )
    assert third.request_count == 0
    assert third.resources[0].get("predecessor_result") == second.resources[0].get(
        "predecessor_result"
    )
    assert (
        third.resources[0]["reused_from"]["manifest_sha256"] == second.manifest_sha256
    )
    assert json.loads((third_path / "request-plan.json").read_bytes())[
        "input_captures"
    ] == [second.manifest_sha256]
    assert (
        replay_neotoma_resource_capture(
            third_path,
            source_captures={
                first.manifest_sha256: first_path,
                second.manifest_sha256: second_path,
            },
        ).resources
        == third.resources
    )


def test_competing_direct_roots_refuse_before_new_get(tmp_path: Path) -> None:
    resource = spec()
    first_path, second_path = tmp_path / "first", tmp_path / "second"
    first = capture_neotoma_resources(
        first_path,
        plan=plan(resource),
        fetch=lambda url, **_: response(url, b"{}", 404),
    )
    second = capture_neotoma_resources(
        second_path,
        plan=plan(resource),
        fetch=lambda url, **_: response(url, body(resource)),
    )
    with pytest.raises(ValueError, match="Ambiguous"):
        capture_neotoma_resources(
            tmp_path / "ambiguous",
            plan=plan(resource),
            reuse_from={
                first.manifest_sha256: first_path,
                second.manifest_sha256: second_path,
            },
            fetch=lambda *_a, **_k: pytest.fail("competing input GET"),
        )


def test_unrelated_selected_input_refuses_before_new_get(tmp_path: Path) -> None:
    original = tmp_path / "original"
    first = capture_neotoma_resources(
        original, plan=plan(spec()), fetch=lambda url, **_: response(url, b"{}", 404)
    )
    with pytest.raises(ValueError, match="no requested resource"):
        capture_neotoma_resources(
            tmp_path / "unrelated",
            plan=plan(spec(202)),
            reuse_from={first.manifest_sha256: original},
            fetch=lambda *_a, **_k: pytest.fail("unrelated input GET"),
        )
