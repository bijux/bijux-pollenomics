"""Dataset facets inherit source roles without inventing native schema or versions."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture.resources import (
    NeotomaResourceLimits,
)

from ..resources.native_payloads import response, spec
from .native_payloads import BODY, FACETS, owner, plan


def test_exact_five_dataset_facets_keep_raw_bytes_and_unqualified_payload_owners(
    tmp_path: Path,
) -> None:
    urls = []

    def fetch(url: str, **_kwargs: Any) -> Any:
        urls.append(url)
        return response(url, BODY)

    directory = tmp_path / "facets"
    result = owner().capture_neotoma_dataset_facets(
        directory, plan=plan(spec(versions=("doi_frozen",))), fetch=fetch
    )
    assert urls == [
        f"https://api.neotomadb.org/v2.0/data/datasets/201/{facet}" for facet in FACETS
    ]
    assert result.request_count == 5
    assert result.response_bytes == 5 * len(BODY)
    assert result.partitions == {"received_complete_unqualified_facet": 5}
    assert len(result.facets) == 5
    for row, facet in zip(result.facets, FACETS, strict=True):
        assert row["facet"] == facet and row["content_version"] == "current"
        assert row["api_version"] == "v2.0"
        assert row["summary"]["payload_owner_status"] == "not_established"
        assert row["summary"]["schema_qualified"] is False
        assert row["scientific_admission"] == "not_asserted"
        admitted = owner().read_neotoma_facet_body(
            directory,
            expected_manifest_sha256=result.manifest_sha256,
            facet_key=row["facet_key"],
        )
        assert admitted.body == BODY
        assert admitted.root_identity["dataset_id"] == 201
    replay = owner().replay_neotoma_facet_capture(
        directory, expected_manifest_sha256=result.manifest_sha256
    )
    assert replay == result


@pytest.mark.parametrize(
    "role", ["reserved_candidate_confirmation", "heldout_no_numerical_access"]
)
def test_every_facet_is_role_gated_before_fetch_or_body_access(
    tmp_path: Path, role: str
) -> None:
    def never(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("Blocked numerical facet accessed transport")

    result = owner().capture_neotoma_dataset_facets(
        tmp_path / "blocked", plan=plan(spec(role=role)), fetch=never
    )
    assert result.request_count == 0 and result.response_bytes == 0
    assert result.partitions == {"not_attempted_exposure_role": 5}
    assert not list((tmp_path / "blocked").glob("*.body"))
    with pytest.raises(ValueError, match="exposure role"):
        owner().read_neotoma_facet_body(
            tmp_path / "blocked",
            expected_manifest_sha256=result.manifest_sha256,
            facet_key=result.facets[0]["facet_key"],
        )


@pytest.mark.parametrize("damage", ["unknown", "duplicate", "empty", "role", "id"])
def test_malformed_plan_refuses_before_any_request(tmp_path: Path, damage: str) -> None:
    resource = spec()
    facets: tuple[str, ...] = FACETS
    if damage == "unknown":
        facets = ("unsupported_facet",)
    elif damage == "duplicate":
        facets = ("chronologies", "chronologies")
    elif damage == "empty":
        facets = ()
    elif damage == "role":
        resource = replace(resource, exposure_role="metadata_only")
    else:
        resource = replace(resource, dataset_id=True)

    def never(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("Malformed plan reached transport")

    with pytest.raises(ValueError):
        owner().capture_neotoma_dataset_facets(
            tmp_path / "invalid", plan=plan(resource, facets=facets), fetch=never
        )
    assert not (tmp_path / "invalid").exists()


@pytest.mark.parametrize("facet", ["contacts", "doi", "sites"])
def test_explicit_association_facets_keep_native_entities_unqualified(
    tmp_path: Path, facet: str
) -> None:
    from hashlib import sha256

    from bijux_pollenomics.collection.sources.neotoma.capture.facets.profiles import (
        qualify_neotoma_facet_body,
    )

    # This observed projects shape must never qualify a different endpoint.
    content = (
        b'{"status":"success","data":{"datasetid":201,"projects":[]},'
        b'"message":"Retrieved"}'
    )
    urls = []

    def fetch(url: str, **_kwargs: Any) -> Any:
        urls.append(url)
        return response(url, content)

    directory = tmp_path / facet
    result = owner().capture_neotoma_dataset_facets(
        directory, plan=plan(spec(), facets=(facet,)), fetch=fetch
    )
    assert urls == [f"https://api.neotomadb.org/v2.0/data/datasets/201/{facet}"]
    assert result.request_count == 1
    assert result.partitions == {"received_complete_unqualified_facet": 1}
    assert (
        owner().replay_neotoma_facet_capture(
            directory, expected_manifest_sha256=result.manifest_sha256
        )
        == result
    )
    body = owner().read_neotoma_facet_body(
        directory,
        expected_manifest_sha256=result.manifest_sha256,
        facet_key=result.facets[0]["facet_key"],
    )
    assert body.body == content
    qualified = qualify_neotoma_facet_body(
        spec(), facet, content, expected_body_sha256=sha256(content).hexdigest()
    )
    assert qualified["qualification_status"] == "unqualified_source_schema"
    assert qualified["source_payload"]["data"] == {"datasetid": 201, "projects": []}
    assert "not registered" in qualified["reason"]
    assert owner().NeotomaFacetPlan((spec(),), "b" * 64).facets == FACETS


@pytest.mark.parametrize("facet", ["contacts", "doi", "sites"])
@pytest.mark.parametrize(
    "role", ["reserved_candidate_confirmation", "heldout_no_numerical_access"]
)
def test_association_facets_obey_parent_exposure_before_fetch(
    tmp_path: Path, facet: str, role: str
) -> None:
    def never(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("Protected association reached transport")

    result = owner().capture_neotoma_dataset_facets(
        tmp_path / "blocked", plan=plan(spec(role=role), facets=(facet,)), fetch=never
    )
    assert result.request_count == 0
    assert result.partitions == {"not_attempted_exposure_role": 1}
    with pytest.raises(ValueError, match="exposure role"):
        owner().read_neotoma_facet_body(
            tmp_path / "blocked",
            expected_manifest_sha256=result.manifest_sha256,
            facet_key=result.facets[0]["facet_key"],
        )


def test_exposed_root_does_not_promote_another_roots_reserved_facets(
    tmp_path: Path,
) -> None:
    directory = tmp_path / "mixed"
    result = owner().capture_neotoma_dataset_facets(
        directory,
        plan=plan(spec(), spec(202, role="reserved_candidate_confirmation")),
        fetch=lambda url, **_: response(url, BODY),
    )
    assert result.request_count == 5
    assert result.partitions == {
        "received_complete_unqualified_facet": 5,
        "not_attempted_exposure_role": 5,
    }
    assert not list(directory.glob("dataset-202-*.body"))
    blocked = next(
        row for row in result.facets if row["root_identity"]["dataset_id"] == 202
    )
    with pytest.raises(ValueError, match="exposure role"):
        owner().read_neotoma_facet_body(
            directory,
            expected_manifest_sha256=result.manifest_sha256,
            facet_key=blocked["facet_key"],
        )


@pytest.mark.parametrize(
    ("kind", "status"),
    [
        ("http", "unavailable_http"),
        ("incomplete", "refused_incomplete_body"),
        ("duplicate", "refused_native_json"),
        ("underflow", "refused_native_json"),
        ("transport", "transport_failure"),
    ],
)
def test_failures_remain_reasoned_retained_entities(
    tmp_path: Path, kind: str, status: str
) -> None:
    content = {
        "duplicate": b'{"datasetid":999,"datasetid":201}',
        "underflow": b'{"age":1e-9999}',
    }.get(kind, BODY)

    def fetch(url: str, **_kwargs: Any) -> Any:
        if kind == "transport":
            raise TimeoutError("synthetic timeout")
        result = response(url, content, 404 if kind == "http" else 200)
        return replace(
            result,
            body_complete=kind != "incomplete",
        )

    directory = tmp_path / "failure"
    result = owner().capture_neotoma_dataset_facets(
        directory,
        plan=plan(spec(), facets=("chronologies",)),
        limits=NeotomaResourceLimits(max_attempts=1),
        fetch=fetch,
    )
    assert result.facets[0]["terminal_status"] == status
    assert result.request_count == 1
    if kind != "transport":
        body_path = directory / result.facets[0]["attempts"][0]["body_file"]
        assert body_path.read_bytes() == content
    with pytest.raises(ValueError):
        owner().read_neotoma_facet_body(
            directory,
            expected_manifest_sha256=result.manifest_sha256,
            facet_key=result.facets[0]["facet_key"],
        )


def test_request_budget_closes_unattempted_facets_without_claiming_absence(
    tmp_path: Path,
) -> None:
    result = owner().capture_neotoma_dataset_facets(
        tmp_path / "bounded",
        plan=plan(spec()),
        limits=NeotomaResourceLimits(max_requests=2),
        fetch=lambda url, **_: response(url, BODY),
    )
    assert result.request_count == 2
    assert result.partitions == {
        "received_complete_unqualified_facet": 2,
        "not_attempted_budget": 3,
    }


def test_foreign_response_owner_refuses_capture_without_discarding_raw_entity(
    tmp_path: Path,
) -> None:
    from bijux_pollenomics.core.owned_tree import build_staging_output_dir

    output = tmp_path / "foreign"
    with pytest.raises(ValueError, match="final_url"):
        owner().capture_neotoma_dataset_facets(
            output,
            plan=plan(spec(), facets=("chronologies",)),
            fetch=lambda url, **_: response(url + "/foreign", BODY),
        )
    stage = build_staging_output_dir(output)
    assert not output.exists()
    assert (stage / "refusal.json").is_file()
    assert [path.read_bytes() for path in stage.glob("*.body")] == [BODY]


def test_retry_keeps_original_failed_http_entity(tmp_path: Path) -> None:
    attempts = []

    def fetch(url: str, **_kwargs: Any) -> Any:
        attempts.append(url)
        return response(url, BODY, 503 if len(attempts) == 1 else 200)

    result = owner().capture_neotoma_dataset_facets(
        tmp_path / "retry",
        plan=plan(spec(), facets=("lithology",)),
        limits=NeotomaResourceLimits(retry_delay_seconds=0),
        fetch=fetch,
    )
    assert result.request_count == 2
    assert len(result.facets[0]["attempts"]) == 2
    assert result.partitions == {"received_complete_unqualified_facet": 1}


def test_existing_output_is_preserved_before_transport(tmp_path: Path) -> None:
    output = tmp_path / "existing"
    output.mkdir()
    sentinel = output / "untouched"
    sentinel.write_bytes(b"original")
    with pytest.raises(FileExistsError):
        owner().capture_neotoma_dataset_facets(
            output,
            plan=plan(spec()),
            fetch=lambda *_args, **_kwargs: pytest.fail("Existing output reached GET"),
        )
    assert sentinel.read_bytes() == b"original"
