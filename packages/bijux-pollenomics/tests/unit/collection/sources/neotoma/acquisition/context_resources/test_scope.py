"""Whole-site protected/unknown/alias scopes never become numerical metadata loopholes."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from .native_products import rebuild_context, source_response


@pytest.mark.parametrize("constraint", ["protected", "alias"])
def test_protected_parent_or_alias_is_indexed_zero_GET_for_both_resource_kinds(
    context_resource_inputs: Callable[..., dict[str, Any]],
    tmp_path: Path,
    constraint: str,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.context_resources import (
        NeotomaContextResourcePlan,
        capture_neotoma_context_resources,
    )

    inputs = context_resource_inputs(**{constraint: True})
    plan = NeotomaContextResourcePlan(
        site_ids=(12,),
        context_manifest_sha256=inputs.pop("context_manifest_sha256"),
        native_archive_manifest_sha256=inputs.pop("native_archive_manifest_sha256"),
        resource_kinds=("dataset_depositional_environment", "lake_candidates"),
    )
    calls = []

    def fetch(url: str, **kwargs: Any) -> Any:
        calls.append(url)
        return source_response(url, **kwargs)

    result = capture_neotoma_context_resources(
        tmp_path / "capture", plan=plan, fetch=fetch, **inputs
    )
    assert calls == [] and result.request_count == 0
    assert result.partitions == {"not_attempted_parent_scope": 2}
    assert all(
        row["scope_status"] == "protected_current_scope" for row in result.resources
    )


def test_missing_roster_site_is_explicit_unestablished_scope_with_zero_GET(
    context_resource_inputs: Callable[..., dict[str, Any]], tmp_path: Path
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.context_resources import (
        NeotomaContextResourcePlan,
        capture_neotoma_context_resources,
    )

    inputs = context_resource_inputs()
    plan = NeotomaContextResourcePlan(
        site_ids=(999,),
        context_manifest_sha256=inputs.pop("context_manifest_sha256"),
        native_archive_manifest_sha256=inputs.pop("native_archive_manifest_sha256"),
        resource_kinds=("dataset_depositional_environment", "lake_candidates"),
    )

    def fetch(*_: Any, **__: Any) -> Any:
        pytest.fail("Unknown whole-site scope reached transport")

    result = capture_neotoma_context_resources(
        tmp_path / "capture", plan=plan, fetch=fetch, **inputs
    )
    assert result.partitions == {"not_attempted_parent_scope": 2}
    assert all(
        row["scope_status"] == "unestablished_current_parent_scope"
        for row in result.resources
    )


def test_unrostered_current_native_sibling_cannot_authorize_known_subset(
    context_resource_inputs: Callable[..., dict[str, Any]], tmp_path: Path
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.context_resources import (
        NeotomaContextResourcePlan,
        capture_neotoma_context_resources,
    )

    inputs = context_resource_inputs(owner_change="span")

    def omit(roster: dict[str, Any]) -> None:
        roster["resources"] = [
            row for row in roster["resources"] if row["dataset_id"] != 203
        ]
        roster["resource_count"] = len(roster["resources"])

    inputs = rebuild_context(inputs, tmp_path / "unclassified", omit)
    plan = NeotomaContextResourcePlan(
        (12,),
        inputs.pop("context_manifest_sha256"),
        inputs.pop("native_archive_manifest_sha256"),
        ("dataset_depositional_environment", "lake_candidates"),
    )
    result = capture_neotoma_context_resources(
        tmp_path / "context-capture",
        plan=plan,
        fetch=lambda *args, **kwargs: pytest.fail(
            "Unclassified sibling authorized GET"
        ),
        **inputs,
    )
    assert result.request_count == 0
    assert all(
        row["scope_status"] == "unestablished_current_parent_scope"
        for row in result.resources
    )
    import json

    scope = json.loads((tmp_path / "context-capture/parent-scope.json").read_bytes())
    assert scope["unclassified_native_parents"] == [
        {"dataset_id": 203, "site_id": 12, "collection_unit_id": 100}
    ]


def test_scope_metadata_never_opens_native_numerical_bodies(
    context_resource_inputs: Callable[..., dict[str, Any]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.context_resources import (
        NeotomaContextResourcePlan,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.context_resources.scope import (
        prepare_scope,
    )

    inputs = context_resource_inputs()
    plan = NeotomaContextResourcePlan(
        (12,),
        inputs.pop("context_manifest_sha256"),
        inputs.pop("native_archive_manifest_sha256"),
    )
    original = Path.open
    opened = []

    def observe(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.suffix == ".body":
            assert "inventory" in path.name, f"Numerical source entity opened: {path}"
            opened.append(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observe)
    scope = prepare_scope(plan, **inputs)
    assert opened
    assert scope["site_count"] == 3
    assert scope["site_partitions"] == {
        "eligible_current_scope": 2,
        "protected_current_scope": 1,
    }
    assert scope["numerical_source_entities_inspected"] is False
