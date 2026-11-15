"""Numerical source capture has explicit roles, versions and failure populations."""

from __future__ import annotations

from dataclasses import replace
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


@pytest.mark.parametrize("metadata_path", ["site", "unit", "both"])
def test_current_missing_database_is_not_borrowed_from_declared_null(
    tmp_path: Path, metadata_path: str
) -> None:
    resource = spec(database=None)
    native = json.loads(body(resource))
    site = native["data"][0]["site"]
    if metadata_path in {"site", "both"}:
        del site["dataset"]["database"]
    if metadata_path in {"unit", "both"}:
        del site["collectionunit"]["dataset"]["database"]
    content = json.dumps(native).encode()
    capture = capture_neotoma_resources(
        tmp_path / "capture",
        plan=plan(resource),
        fetch=lambda url, **_: response(url, content),
    )
    assert capture.resources[0]["terminal_status"] == "refused_native_protocol"
    assert (
        capture.resources[0]["summary"]["reason"]
        == "Native dataset type/database differs"
    )
    assert (
        tmp_path / "capture/dataset-201-current-attempt-1.body"
    ).read_bytes() == content
    replayed = replay_neotoma_resource_capture(
        tmp_path / "capture", expected_manifest_sha256=capture.manifest_sha256
    )
    assert replayed.resources == capture.resources
