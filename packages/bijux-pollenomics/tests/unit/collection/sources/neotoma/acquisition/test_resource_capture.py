"""Numerical source capture has explicit roles, versions and failure populations."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture import NeotomaMetadataResponse
from bijux_pollenomics.collection.sources.neotoma.capture.resources import (
    NeotomaResourceLimits,
    NeotomaResourcePlan,
    NeotomaResourceSpec,
    NeotomaRetainedSource,
    capture_neotoma_resources,
    replay_neotoma_resource_capture,
)


def spec(
    identity: int = 201,
    kind: str = "pollen",
    role: str = "development_resource_discovery",
    database: str | None = "source database",
    versions: tuple[str, ...] = ("current",),
) -> NeotomaResourceSpec:
    return NeotomaResourceSpec(
        identity,
        12,
        100,
        kind,
        database,
        role,
        "a" * 64,
        "/data/0/site/datasets/0",
        versions,
    )


def plan(*resources: NeotomaResourceSpec) -> NeotomaResourcePlan:
    return NeotomaResourcePlan(resources, "b" * 64)


def body(resource: NeotomaResourceSpec) -> bytes:
    dataset = {
        "datasetid": resource.dataset_id,
        "datasettype": resource.dataset_type,
        "database": resource.database,
    }
    samples = [
        {
            "sampleid": None if resource.dataset_type == "geochronologic" else 2001,
            "datum": [
                {
                    "taxonid": None if resource.dataset_type == "geochronologic" else 1,
                    "value": None if resource.dataset_type == "geochronologic" else 3.5,
                    "units": "%"
                    if resource.dataset_type == "loss-on-ignition"
                    else "NISP",
                }
            ],
        }
    ]
    return json.dumps(
        {
            "status": "success",
            "data": [
                {
                    "site": {
                        "siteid": 12,
                        "dataset": dict(dataset),
                        "collectionunit": {
                            "collectionunitid": 100,
                            "dataset": {**dataset, "samples": samples},
                            "chronologies": [],
                        },
                    }
                }
            ],
        }
    ).encode()


def response(url: str, content: bytes, status: int = 200) -> NeotomaMetadataResponse:
    return NeotomaMetadataResponse(
        url, status, (("Content-Length", str(len(content))),), content
    )


@pytest.mark.parametrize(
    "kind",
    [
        "pollen",
        "geochronologic",
        "loss-on-ignition",
        "charcoal",
        "microcharcoal",
        "plant macrofossil",
        "pollen trap",
        "testate amoebae",
    ],
)
def test_each_current_native_type_preserves_bytes_without_pollen_recasting(
    tmp_path: Path, kind: str
) -> None:
    resource = spec(kind=kind, database=None)
    content = body(resource)
    result = capture_neotoma_resources(
        tmp_path / "capture",
        plan=plan(resource),
        fetch=lambda url, **_: response(url, content),
    )
    row = result.resources[0]
    assert row["terminal_status"] == "parsed_native"
    assert row["summary"]["dataset_type"] == kind and row["summary"]["database"] is None
    assert row["summary"]["sample_rows"] == 1
    assert row["summary"]["identified_samples"] == int(kind != "geochronologic")
    assert (
        tmp_path / "capture" / row["attempts"][0]["body_file"]
    ).read_bytes() == content
    assert row["scientific_admission"] == "not_asserted"
    assert (
        replay_neotoma_resource_capture(
            tmp_path / "capture", expected_manifest_sha256=result.manifest_sha256
        ).resources
        == result.resources
    )


@pytest.mark.parametrize(
    "role", ["reserved_candidate_confirmation", "heldout_no_numerical_access"]
)
def test_reserved_roles_are_accounted_without_any_numerical_get(
    tmp_path: Path, role: str
) -> None:
    result = capture_neotoma_resources(
        tmp_path / "capture",
        plan=plan(spec(role=role)),
        fetch=lambda *_a, **_k: pytest.fail("reserved numerical GET"),
    )
    assert result.request_count == 0
    assert result.resources[0]["terminal_status"] == "not_attempted_exposure_role"


def test_current_and_frozen_have_distinct_identity_and_unknown_frozen_refuses_promotion(
    tmp_path: Path,
) -> None:
    resource = spec(versions=("current", "doi_frozen"))
    content = body(resource)
    urls = []

    def fetch(url: str, **_: object) -> NeotomaMetadataResponse:
        urls.append(url)
        return response(url, content)

    result = capture_neotoma_resources(
        tmp_path / "capture", plan=plan(resource), fetch=fetch
    )
    assert urls == [
        "https://api.neotomadb.org/v2.0/data/downloads/201",
        "https://api.neotomadb.org/v2.0/data/frozen/201",
    ]
    assert [r["terminal_status"] for r in result.resources] == [
        "parsed_native",
        "unresolved_frozen_schema",
    ]
    assert len({r["resource_key"] for r in result.resources}) == 2


def test_failure_populations_do_not_abort_other_declared_resources(
    tmp_path: Path,
) -> None:
    first, second = spec(), spec(202)
    content = body(second)

    def fetch(url: str, **_: object) -> NeotomaMetadataResponse:
        return (
            response(url, b'{"status":"error"}', 404)
            if url.endswith("/201")
            else response(url, content)
        )

    result = capture_neotoma_resources(
        tmp_path / "capture", plan=plan(first, second), fetch=fetch
    )
    assert [r["terminal_status"] for r in result.resources] == [
        "unavailable_http",
        "parsed_native",
    ]
    assert result.request_count == 2


def test_transient_failure_keeps_original_receipt_when_retry_succeeds(
    tmp_path: Path,
) -> None:
    resource = spec()
    calls = []

    def fetch(url: str, **_: object) -> NeotomaMetadataResponse:
        calls.append(url)
        if len(calls) == 1:
            raise TimeoutError("source timeout")
        return response(url, body(resource))

    result = capture_neotoma_resources(
        tmp_path / "capture",
        plan=plan(resource),
        limits=NeotomaResourceLimits(retry_delay_seconds=0),
        fetch=fetch,
    )
    attempts = result.resources[0]["attempts"]
    assert result.request_count == len(attempts) == 2
    assert (
        json.loads((tmp_path / "capture" / attempts[0]["receipt_file"]).read_bytes())[
            "terminal_status"
        ]
        == "transport_failure"
    )
    assert result.resources[0]["terminal_status"] == "parsed_native"
    assert "reason" not in result.resources[0]


@pytest.mark.parametrize("mutation", ["dataset", "site", "unit", "type", "database"])
def test_current_download_cannot_borrow_a_different_native_owner(
    tmp_path: Path, mutation: str
) -> None:
    resource = spec()
    document = json.loads(body(resource))
    site = document["data"][0]["site"]
    unit = site["collectionunit"]
    if mutation == "dataset":
        unit["dataset"]["datasetid"] = 999
    elif mutation == "site":
        site["siteid"] = 999
    elif mutation == "unit":
        unit["collectionunitid"] = 999
    elif mutation == "type":
        unit["dataset"]["datasettype"] = "charcoal"
    else:
        site["dataset"]["database"] = None
    result = capture_neotoma_resources(
        tmp_path / "capture",
        plan=plan(resource),
        fetch=lambda url, **_: response(url, json.dumps(document).encode()),
    )
    assert result.resources[0]["terminal_status"] == "refused_native_protocol"


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


def test_request_budget_accounts_for_unattempted_resources(tmp_path: Path) -> None:
    first = spec()
    result = capture_neotoma_resources(
        tmp_path / "capture",
        plan=plan(first, spec(202)),
        limits=NeotomaResourceLimits(max_requests=1),
        fetch=lambda url, **_: response(url, body(first)),
    )
    assert [r["terminal_status"] for r in result.resources] == [
        "parsed_native",
        "not_attempted_budget",
    ]
    assert result.request_count == 1


def test_resource_capture_does_not_replace_prior_output(tmp_path: Path) -> None:
    output = tmp_path / "capture"
    output.mkdir()
    (output / "original").write_bytes(b"keep")
    with pytest.raises(FileExistsError):
        capture_neotoma_resources(
            output,
            plan=plan(spec()),
            fetch=lambda *_a, **_k: pytest.fail("unexpected GET"),
        )
    assert (output / "original").read_bytes() == b"keep"


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
    "content,status",
    [
        (b"not JSON", "refused_native_protocol"),
        (b'{"status":"error","data":[]}', "refused_native_protocol"),
        (b'{"status":"success"}', "refused_native_protocol"),
        (b'{"status":"success","data":[]}', "unavailable_api_empty"),
    ],
)
def test_native_empty_error_and_malformed_have_distinct_retained_results(
    tmp_path: Path, content: bytes, status: str
) -> None:
    result = capture_neotoma_resources(
        tmp_path / "capture",
        plan=plan(spec()),
        fetch=lambda url, **_: response(url, content),
    )
    assert result.resources[0]["terminal_status"] == status
    assert (
        tmp_path / "capture" / result.resources[0]["attempts"][0]["body_file"]
    ).read_bytes() == content


def test_duplicate_native_dataset_rows_are_refused(tmp_path: Path) -> None:
    resource = spec()
    document = json.loads(body(resource))
    document["data"] *= 2
    result = capture_neotoma_resources(
        tmp_path / "capture",
        plan=plan(resource),
        fetch=lambda url, **_: response(url, json.dumps(document).encode()),
    )
    assert result.resources[0]["terminal_status"] == "refused_native_protocol"


def test_partial_body_is_retained_and_cannot_be_promoted(tmp_path: Path) -> None:
    content = b'{"sta'
    result = capture_neotoma_resources(
        tmp_path / "capture",
        plan=plan(spec()),
        limits=NeotomaResourceLimits(max_response_bytes=4),
        fetch=lambda url, **_: replace(response(url, content), body_complete=False),
    )
    assert result.resources[0]["terminal_status"] == "refused_incomplete_body"
    assert result.response_bytes == 5
    body_path = tmp_path / "capture" / result.resources[0]["attempts"][0]["body_file"]
    body_path.write_bytes(b"other")
    with pytest.raises(ValueError, match="identity"):
        replay_neotoma_resource_capture(tmp_path / "capture")


@pytest.mark.parametrize("invalid", [True, 0, -1, 201.9, "201"])
def test_invalid_native_request_id_refuses_before_http(
    tmp_path: Path, invalid: object
) -> None:
    with pytest.raises(ValueError):
        capture_neotoma_resources(
            tmp_path / "capture",
            plan=plan(replace(spec(), dataset_id=invalid)),  # type: ignore[arg-type]
            fetch=lambda *_a, **_k: pytest.fail("invalid identity GET"),
        )
    assert not (tmp_path / "capture").exists()


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
