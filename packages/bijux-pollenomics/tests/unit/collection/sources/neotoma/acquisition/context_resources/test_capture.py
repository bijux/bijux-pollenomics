"""Two fixed official namespaces and explicit canonical request order."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture import NeotomaMetadataResponse

from .native_products import capture_legacy_context_fixture, captured, source_response


def test_new_capture_inhibits_known_ignored_site_environment_filter(
    context_resource_inputs: Callable[..., dict[str, Any]], tmp_path: Path
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.context_resources import (
        NeotomaContextResourcePlan,
        capture_neotoma_context_resources,
    )

    inputs = context_resource_inputs()
    plan = NeotomaContextResourcePlan(
        (12,),
        inputs.pop("context_manifest_sha256"),
        inputs.pop("native_archive_manifest_sha256"),
    )
    calls = []

    def fetched(url: str, **kwargs: Any) -> Any:
        calls.append(url)
        return source_response(url, **kwargs)

    with pytest.raises(ValueError, match="siteid"):
        capture_neotoma_context_resources(
            tmp_path / "capture", plan=plan, fetch=fetched, **inputs
        )
    assert calls == [] and not (tmp_path / "capture").exists()


def test_dataset_environment_query_uses_all_authenticated_native_parents(
    context_resource_inputs: Callable[..., dict[str, Any]], tmp_path: Path
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.context_resources import (
        NeotomaContextResourcePlan,
        capture_neotoma_context_resources,
    )

    inputs = context_resource_inputs()
    plan = NeotomaContextResourcePlan(
        (13, 12),
        inputs.pop("context_manifest_sha256"),
        inputs.pop("native_archive_manifest_sha256"),
        ("dataset_depositional_environment", "lake_candidates"),
    )
    calls = []

    def fetched(url: str, **kwargs: Any) -> Any:
        calls.append(url)
        return source_response(url, **kwargs)

    result = capture_neotoma_context_resources(
        tmp_path / "capture", plan=plan, fetch=fetched, **inputs
    )
    assert calls == [
        "https://api.neotomadb.org/v2.0/apps/depenvt?datasetid=401%2C402&limit=2&offset=0",
        "https://api.neotomadb.org/v2.0/apps/depenvt?datasetid=201%2C202&limit=2&offset=0",
        "https://api.neotomadb.org/v2.0/data/spatial/lakes?siteid=13&buffer=1000&prec=0.0001&proj=4326",
        "https://api.neotomadb.org/v2.0/data/spatial/lakes?siteid=12&buffer=1000&prec=0.0001&proj=4326",
    ]
    assert result.request_count == 4


@pytest.mark.parametrize(
    "values", [None, (), (201, 201), (202, 201), (True,), (201.0,), [201, 202], (-1,)]
)
def test_dataset_query_factory_refuses_non_native_or_ambiguous_ID_tuple(
    values: Any,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.context_resources.protocol import (
        request_for,
    )

    with pytest.raises(ValueError):
        request_for("dataset_depositional_environment", 12, dataset_ids=values)


def test_lake_query_does_not_accept_dataset_filter_aliases() -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.context_resources.protocol import (
        request_for,
    )

    with pytest.raises(ValueError):
        request_for("lake_candidates", 12, dataset_ids=(201, 202))


def test_legacy_wire_routes_apps_and_data_without_qualifying_native_payloads(
    context_resource_inputs: Callable[..., dict[str, Any]], tmp_path: Path
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.context_resources import (
        NeotomaContextResourcePlan,
    )

    inputs = context_resource_inputs()
    plan = NeotomaContextResourcePlan(
        site_ids=(13, 12),
        context_manifest_sha256=inputs.pop("context_manifest_sha256"),
        native_archive_manifest_sha256=inputs.pop("native_archive_manifest_sha256"),
    )
    calls = []

    def fetch(url: str, **kwargs: Any) -> Any:
        calls.append(url)
        return source_response(url, **kwargs)

    result = capture_legacy_context_fixture(
        tmp_path / "capture", plan=plan, fetch=fetch, **inputs
    )
    assert calls == [
        "https://api.neotomadb.org/v2.0/apps/depenvt?siteid=13",
        "https://api.neotomadb.org/v2.0/apps/depenvt?siteid=12",
        "https://api.neotomadb.org/v2.0/data/spatial/lakes?siteid=13&buffer=1000&prec=0.0001&proj=4326",
        "https://api.neotomadb.org/v2.0/data/spatial/lakes?siteid=12&buffer=1000&prec=0.0001&proj=4326",
    ]
    assert result.request_count == 4
    assert result.partitions == {"received_complete_unqualified_context_resource": 4}
    assert all(row["summary"]["schema_qualified"] is False for row in result.resources)
    assert all(
        row["summary"]["dated_basin_geometry_admitted"] is False
        for row in result.resources
    )


@pytest.mark.parametrize(
    ("body", "status", "complete", "expected"),
    [
        (b"[]", 200, True, "received_complete_unqualified_context_resource"),
        (b"null", 200, True, "received_complete_unqualified_context_resource"),
        (
            b'{"status":"error"}',
            200,
            True,
            "received_complete_unqualified_context_resource",
        ),
        (b'{"depth":1,"depth":2}', 200, True, "refused_native_json"),
        (b'{"depth":1e-9999}', 200, True, "refused_native_json"),
        (b'{"depth":NaN}', 200, True, "refused_native_json"),
        (b'null,"foreign":1', 200, True, "refused_native_json"),
        (b"unavailable", 404, True, "unavailable_http"),
        (b"{", 200, False, "refused_incomplete_body"),
    ],
)
def test_literal_failures_and_generic_JSON_preserve_source_bytes(
    context_resource_inputs: Callable[..., dict[str, Any]],
    tmp_path: Path,
    body: bytes,
    status: int,
    complete: bool,
    expected: str,
) -> None:
    arguments, result = captured(
        context_resource_inputs,
        tmp_path,
        fetch=lambda url, **kwargs: NeotomaMetadataResponse(
            url, status, (), body, complete
        ),
    )
    assert result.partitions == {expected: 2}
    for row in result.resources:
        path = arguments["directory"] / row["attempts"][0]["body_file"]
        assert path.read_bytes() == body
        assert row.get("absence_certified", False) is False


def test_one_attempt_transport_failure_never_retries_or_expands_routes(
    context_resource_inputs: Callable[..., dict[str, Any]], tmp_path: Path
) -> None:
    calls = []

    def failed(url: str, **kwargs: Any) -> Any:
        calls.append((url, kwargs))
        raise OSError("Literal transport refusal")

    arguments, result = captured(context_resource_inputs, tmp_path, fetch=failed)
    assert len(calls) == result.request_count == 2
    assert result.partitions == {"transport_failure": 2}
    assert not list(arguments["directory"].glob("*.body"))


def test_incomplete_final_global_sentinel_is_retained_and_stops_next_GET(
    context_resource_inputs: Callable[..., dict[str, Any]], tmp_path: Path
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.context_resources import (
        DEFAULT_CONTEXT_LIMITS,
    )

    calls = []

    def fetched(url: str, **kwargs: Any) -> Any:
        calls.append(kwargs)
        assert kwargs["max_bytes"] == 3
        return NeotomaMetadataResponse(url, 200, (), b"null", False)

    arguments, result = captured(
        context_resource_inputs,
        tmp_path,
        fetch=fetched,
        limits=replace(DEFAULT_CONTEXT_LIMITS, max_total_bytes=3),
    )
    assert len(calls) == result.request_count == 1
    assert result.response_bytes == 4
    assert result.partitions == {
        "refused_incomplete_body": 1,
        "not_attempted_budget": 1,
    }
    assert (
        arguments["directory"] / result.resources[0]["attempts"][0]["body_file"]
    ).read_bytes() == b"null"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("max_requests", True),
        ("max_requests", 129),
        ("max_attempts", 2),
        ("max_response_bytes", 0),
        ("max_total_bytes", 1.5),
        ("wall_seconds", float("nan")),
        ("timeout_seconds", True),
        ("retry_delay_seconds", 1),
    ],
)
def test_invalid_transport_limits_refuse_before_scope_or_output(
    context_resource_inputs: Callable[..., dict[str, Any]],
    tmp_path: Path,
    field: str,
    value: Any,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.context_resources import (
        DEFAULT_CONTEXT_LIMITS,
        NeotomaContextResourcePlan,
        capture_neotoma_context_resources,
    )

    inputs = context_resource_inputs()
    plan = NeotomaContextResourcePlan(
        (12,),
        inputs.pop("context_manifest_sha256"),
        inputs.pop("native_archive_manifest_sha256"),
    )
    with pytest.raises(ValueError):
        capture_neotoma_context_resources(
            tmp_path / "capture",
            plan=plan,
            limits=replace(DEFAULT_CONTEXT_LIMITS, **{field: value}),
            fetch=lambda *args, **kwargs: pytest.fail("Invalid cap reached HTTP"),
            **inputs,
        )
    assert not (tmp_path / "capture").exists()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("site_ids", (True,)),
        ("site_ids", (12, 12)),
        ("site_ids", (12.0,)),
        ("site_ids", ()),
        ("context_manifest_sha256", None),
        ("native_archive_manifest_sha256", "bad"),
        ("resource_kinds", ("lake_candidates", "depositional_environment")),
        ("resource_kinds", ("/foreign",)),
        ("lake_buffer_m", 2000),
        ("lake_precision", 0.01),
        ("lake_projection", 3857),
    ],
)
def test_invalid_plan_cannot_rewrite_source_routes(
    context_resource_inputs: Callable[..., dict[str, Any]],
    tmp_path: Path,
    field: str,
    value: Any,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.context_resources import (
        NeotomaContextResourcePlan,
        capture_neotoma_context_resources,
    )

    inputs = context_resource_inputs()
    plan = NeotomaContextResourcePlan(
        (12,),
        inputs.pop("context_manifest_sha256"),
        inputs.pop("native_archive_manifest_sha256"),
    )
    with pytest.raises(ValueError):
        capture_neotoma_context_resources(
            tmp_path / "capture",
            plan=replace(plan, **{field: value}),
            fetch=lambda *args, **kwargs: pytest.fail("Invalid plan reached HTTP"),
            **inputs,
        )
    assert not (tmp_path / "capture").exists()


def test_existing_destination_is_preserved_without_scope_or_HTTP(
    context_resource_inputs: Callable[..., dict[str, Any]], tmp_path: Path
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.context_resources import (
        NeotomaContextResourcePlan,
        capture_neotoma_context_resources,
    )

    inputs = context_resource_inputs()
    plan = NeotomaContextResourcePlan(
        (12,),
        inputs.pop("context_manifest_sha256"),
        inputs.pop("native_archive_manifest_sha256"),
    )
    output = tmp_path / "capture"
    output.mkdir()
    (output / "foreign").write_bytes(b"preserve")
    with pytest.raises(FileExistsError):
        capture_neotoma_context_resources(
            output,
            plan=plan,
            fetch=lambda *args, **kwargs: pytest.fail(
                "Existing destination reached HTTP"
            ),
            **inputs,
        )
    assert (output / "foreign").read_bytes() == b"preserve"


def test_parent_proof_metadata_cap_is_checked_before_any_GET(
    context_resource_inputs: Callable[..., dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.context_resources import (
        NeotomaContextResourcePlan,
        capture_neotoma_context_resources,
        workflow,
    )

    inputs = context_resource_inputs()
    plan = NeotomaContextResourcePlan(
        (12,),
        inputs.pop("context_manifest_sha256"),
        inputs.pop("native_archive_manifest_sha256"),
        ("dataset_depositional_environment", "lake_candidates"),
    )
    monkeypatch.setattr(workflow, "MAX_METADATA_BYTES", 1, raising=False)
    calls = []

    def fetched(url: str, **kwargs: Any) -> Any:
        calls.append(url)
        return source_response(url, **kwargs)

    with pytest.raises(ValueError, match="metadata"):
        capture_neotoma_context_resources(
            tmp_path / "capture", plan=plan, fetch=fetched, **inputs
        )
    assert calls == []
