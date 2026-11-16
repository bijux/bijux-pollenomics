"""Default pilot limits remain bounded; explicit callers use protocol ceilings."""

from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context_resources import (
    load_neotoma_context_resource_archive,
    read_neotoma_context_resource,
    read_neotoma_context_resource_entity,
    write_neotoma_context_resource_archive,
)
from bijux_pollenomics.collection.sources.neotoma.capture.context_resources.models import (
    DEFAULT_CONTEXT_LIMITS,
)

from ..native_products import observe_context_bodies
from .native_products import publish, source_products


@pytest.fixture(scope="module")
def raw_products(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    return source_products(tmp_path_factory.mktemp("explicit-caller") / "products")


def test_explicit_nine_request_limits_publish_and_replay_all_nine_source_buffers(
    raw_products: dict[str, Any], tmp_path: Path
) -> None:
    reader = publish(tmp_path / "portable", raw_products)
    full = load_neotoma_context_resource_archive(
        tmp_path / "portable", **reader, limits=raw_products["limits"]
    )
    assert full["native_profile_partitions"] == {"qualified_native_environment_rows": 9}


def test_default_limits_do_not_expand_to_match_recorded_capture(
    raw_products: dict[str, Any], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert DEFAULT_CONTEXT_LIMITS.max_requests == 8
    assert DEFAULT_CONTEXT_LIMITS.max_total_bytes == 8 * 1024 * 1024
    opened = observe_context_bodies(monkeypatch, set())
    with pytest.raises(ValueError, match="capture budget"):
        write_neotoma_context_resource_archive(
            tmp_path / "default", **{**raw_products, "limits": DEFAULT_CONTEXT_LIMITS}
        )
    assert opened == []


@pytest.mark.parametrize(
    "field,value",
    [
        ("max_requests", True),
        ("max_attempts", True),
        ("max_response_bytes", True),
        ("max_total_bytes", True),
        ("max_requests", 129),
        ("max_attempts", 2),
        ("max_response_bytes", 2097153),
        ("max_total_bytes", 256 * 1024 * 1024 + 1),
        ("timeout_seconds", float("nan")),
        ("wall_seconds", float("inf")),
        ("retry_delay_seconds", float("nan")),
        ("timeout_seconds", 46),
        ("wall_seconds", 121),
        ("retry_delay_seconds", 1),
    ],
)
def test_invalid_or_over_ceiling_caller_limits_refuse_before_any_context_body(
    raw_products: dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: Any,
) -> None:
    opened = observe_context_bodies(monkeypatch, set())
    with pytest.raises(ValueError):
        write_neotoma_context_resource_archive(
            tmp_path / "refused",
            **{
                **raw_products,
                "limits": replace(raw_products["limits"], **{field: value}),
            },
        )
    assert opened == []


def test_ninth_selection_requires_optin_but_earlier_selection_keeps_default_access(
    raw_products: dict[str, Any], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "portable"
    reader = publish(output, raw_products)
    first = (
        output
        / "capture/site-12-dataset_depositional_environment-current-attempt-1.body"
    )
    ninth = (
        output
        / "capture/site-20-dataset_depositional_environment-current-attempt-1.body"
    )
    opened = observe_context_bodies(monkeypatch, {first})
    read_neotoma_context_resource(
        output, site_id=12, resource_kind="dataset_depositional_environment", **reader
    )
    assert opened == [first]
    opened.clear()
    with pytest.raises(ValueError, match="capture budget"):
        read_neotoma_context_resource_entity(
            output,
            site_id=20,
            resource_kind="dataset_depositional_environment",
            **reader,
        )
    assert opened == []
    monkeypatch.undo()
    opened = observe_context_bodies(monkeypatch, {ninth})
    selected = read_neotoma_context_resource(
        output,
        site_id=20,
        resource_kind="dataset_depositional_environment",
        **reader,
        limits=raw_products["limits"],
    )
    assert opened == [ninth]
    assert selected["source_payload"]["data"][0]["datasetid"] == 209
    assert selected["unselected_source_bodies_verified"] is False


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("max_requests", 8, "capture budget"),
        ("max_total_bytes", 8 * 1024 * 1024, "capture budget"),
        ("max_total_bytes", 9 * 1024 * 1024 - 1, "remaining byte budget"),
        ("max_response_bytes", 1024 * 1024 - 1, "remaining byte budget"),
    ],
)
def test_restrictive_caller_ordinal_prefix_and_remaining_bytes_refuse_before_selected_body(
    raw_products: dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: int,
    reason: str,
) -> None:
    output = tmp_path / "portable"
    reader = publish(output, raw_products)
    opened = observe_context_bodies(monkeypatch, set())
    with pytest.raises(ValueError, match=reason):
        read_neotoma_context_resource_entity(
            output,
            site_id=20,
            resource_kind="dataset_depositional_environment",
            **reader,
            limits=replace(raw_products["limits"], **{field: value}),
        )
    assert opened == []


def test_last_incomplete_sentinel_remains_available_only_under_admitted_prefix_bound(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    raw = source_products(tmp_path / "source-products", incomplete_last=True)
    output = tmp_path / "portable"
    reader = publish(output, raw)
    own = (
        output
        / "capture/site-20-dataset_depositional_environment-current-attempt-1.body"
    )
    opened = observe_context_bodies(monkeypatch, {own})
    result = read_neotoma_context_resource_entity(
        output,
        site_id=20,
        resource_kind="dataset_depositional_environment",
        **reader,
        limits=raw["limits"],
    )
    assert opened == [own] and result["body_complete"] is False
    assert len(result["body"]) == 1024 * 1024
    monkeypatch.undo()
    opened = observe_context_bodies(monkeypatch, set())
    with pytest.raises(ValueError, match="remaining byte budget"):
        read_neotoma_context_resource_entity(
            output,
            site_id=20,
            resource_kind="dataset_depositional_environment",
            **reader,
            limits=replace(
                raw["limits"], max_total_bytes=raw["limits"].max_total_bytes - 1
            ),
        )
    assert opened == []
