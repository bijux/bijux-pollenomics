"""Selected metadata and fresh current-context contradictions refuse before entities."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive.files import (
    encoded_json,
)
from tests.unit.collection.sources.neotoma.reading_observation import (
    capture_opening,
    observe_opening,
)

from .native_products import (
    facet_row,
    observe_entities,
    rewrite_federation_member,
    rewrite_index_row,
)


@pytest.mark.parametrize(
    "field",
    [
        "expected_context_sha256",
        "expected_native_archive_sha256",
        "expected_manifest_sha256",
    ],
)
def test_independently_expected_anchor_mismatch_opens_no_entity(
    selected_products: dict[str, Any], monkeypatch: pytest.MonkeyPatch, field: str
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        read_neotoma_ancillary_facet_entity,
    )

    row = facet_row(selected_products)
    opened = observe_entities(monkeypatch, selected_products, set())
    options = {**selected_products["kwargs"], field: "0" * 64}
    with pytest.raises(ValueError):
        read_neotoma_ancillary_facet_entity(
            selected_products["directory"],
            **options,
            observation_id=row["observation_id"],
            dataset_id=201,
            facet="taxa",
        )
    assert opened == []


@pytest.mark.parametrize("mutation", ["role", "metadata", "alias_header"])
def test_rehashed_stale_parent_proof_does_not_authorize_entity(
    selected_products: dict[str, Any], monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        read_neotoma_ancillary_facet_entity,
    )

    row = facet_row(selected_products)
    relative = "scope/current-parent-proof.json"
    proof = json.loads((selected_products["directory"] / relative).read_bytes())
    if mutation == "alias_header":
        proof["unknown_model_sharing"] = "all_known"
    else:
        parent = next(
            parent for parent in proof["parents"] if parent["dataset_id"] == 201
        )
        if mutation == "role":
            parent["effective_scope_role"] = "exposed_development"
        else:
            parent["metadata_sources"] = []
    rewrite_federation_member(selected_products, relative, proof)
    opened = observe_entities(monkeypatch, selected_products, set())
    with pytest.raises(ValueError, match="parent|scope"):
        read_neotoma_ancillary_facet_entity(
            selected_products["directory"],
            **selected_products["kwargs"],
            observation_id=row["observation_id"],
            dataset_id=201,
            facet="taxa",
        )
    assert opened == []


@pytest.mark.parametrize(
    "field,value",
    [("database", None), ("dataset_type", "speleothem"), ("collection_unit_id", 999)],
)
def test_rehashed_same_dataset_foreign_context_refuses_before_body(
    selected_products: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: Any,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        read_neotoma_ancillary_facet_entity,
    )

    row = facet_row(selected_products)
    rewrite_index_row(
        selected_products,
        "observations",
        row["observation_id"],
        lambda record: record["root_identity"].update({field: value}),
    )
    opened = observe_entities(monkeypatch, selected_products, set())
    with pytest.raises(ValueError, match="owner|correspondence"):
        read_neotoma_ancillary_facet_entity(
            selected_products["directory"],
            **selected_products["kwargs"],
            observation_id=row["observation_id"],
            dataset_id=201,
            facet="taxa",
        )
    assert opened == []


def test_metadata_header_duplicate_capture_owner_refuses_before_entities(
    selected_products: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        read_neotoma_ancillary_facet_entity,
    )

    row = facet_row(selected_products)
    path = selected_products["directory"] / "manifest.json"
    manifest = json.loads(path.read_bytes())
    existing = next(iter(manifest["capsule_captures"].values()))
    manifest["capsule_captures"]["0" * 64] = existing
    manifest["capsule_manifest_sha256s"] = sorted(manifest["capsule_captures"])
    path.write_bytes(encoded_json(manifest))
    selected_products["kwargs"]["expected_manifest_sha256"] = sha256(
        path.read_bytes()
    ).hexdigest()
    opened = observe_entities(monkeypatch, selected_products, set())
    with pytest.raises(ValueError, match="ownership|duplicated"):
        read_neotoma_ancillary_facet_entity(
            selected_products["directory"],
            **selected_products["kwargs"],
            observation_id=row["observation_id"],
            dataset_id=201,
            facet="taxa",
        )
    assert opened == []


@pytest.mark.parametrize("member", ["body", "receipt", "plan", "source_manifest"])
def test_source_corruption_refuses_with_only_selected_body_permitted(
    selected_products: dict[str, Any], monkeypatch: pytest.MonkeyPatch, member: str
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        read_neotoma_ancillary_facet_entity,
    )

    row = facet_row(selected_products)
    body = selected_products["capsule"] / row["forensic_locator"]["body_relative_path"]
    if member == "body":
        path = body
    elif member == "receipt":
        path = body.parent / row["attempts"][-1]["receipt_file"]
    else:
        path = body.parent / (
            "request-plan.json" if member == "plan" else "capture-manifest.json"
        )
    path.write_bytes(path.read_bytes() + b" ")
    opened = observe_entities(monkeypatch, selected_products, set())
    with pytest.raises(ValueError):
        read_neotoma_ancillary_facet_entity(
            selected_products["directory"],
            **selected_products["kwargs"],
            observation_id=row["observation_id"],
            dataset_id=201,
            facet="taxa",
        )
    assert opened == []


def test_unselected_source_body_and_index_parts_remain_unopened(
    selected_products: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        read_neotoma_ancillary_facet_entity,
    )

    row = facet_row(selected_products)
    root = selected_products["directory"]
    index = json.loads((root / "index.json").read_bytes())
    allowed_parts = {
        part["path"]
        for part in index["parts"]
        if part["population"] == "slots"
        or part["population"] == "observations"
        and part["group"] == row["source_capture_manifest_sha256"]
    }
    unselected = {
        root / part["path"]
        for part in index["parts"]
        if part["path"] not in allowed_parts
    }
    original = capture_opening()

    def observe(path: Path, *args: Any, **kwargs: Any) -> Any:
        assert path not in unselected, "Unselected federation part opened"
        return original(path, *args, **kwargs)

    observe_opening(monkeypatch, observe)
    body = selected_products["capsule"] / row["forensic_locator"]["body_relative_path"]
    opened = observe_entities(monkeypatch, selected_products, {body})
    read_neotoma_ancillary_facet_entity(
        root,
        **selected_products["kwargs"],
        observation_id=row["observation_id"],
        dataset_id=201,
        facet="taxa",
    )
    assert opened == [body]


def test_rehashed_original_source_locator_must_match_frozen_roster_before_body(
    selected_products: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        read_neotoma_ancillary_facet_entity,
    )

    from .native_products import rewrite_capture

    row = facet_row(selected_products)

    def mutate(document: dict[str, Any], control: dict[str, Any], _: Any) -> None:
        for resource in control["plan"]["resources"]:
            if resource["dataset_id"] == 201:
                resource["metadata_sha256"] = "0" * 64
        for entry in document["facets"]:
            if entry["root_identity"]["dataset_id"] == 201:
                entry["root_identity"]["metadata_sha256"] = "0" * 64

    old = row["source_capture_manifest_sha256"]
    new = rewrite_capture(selected_products, old, mutate)
    selected_id = row["observation_id"].replace(old, new)
    rewrite_index_row(
        selected_products,
        "observations",
        selected_id,
        lambda value: value["root_identity"].update(metadata_sha256="0" * 64),
    )
    body = selected_products["capsule"] / row["forensic_locator"][
        "body_relative_path"
    ].replace(old, new)
    opened = observe_entities(monkeypatch, selected_products, {body})
    with pytest.raises(ValueError, match="locator|roster|identity"):
        read_neotoma_ancillary_facet_entity(
            selected_products["directory"],
            **selected_products["kwargs"],
            observation_id=selected_id,
            dataset_id=201,
            facet="taxa",
        )
    assert opened == []


@pytest.mark.parametrize(
    "mutation",
    ["observation_string", "api_version", "preselected_epoch", "false_pending"],
)
def test_selected_slot_cannot_contradict_its_exact_source_binding(
    selected_products: dict[str, Any], monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        read_neotoma_ancillary_facet_entity,
    )

    row = facet_row(selected_products)

    def mutate(slot: dict[str, Any]) -> None:
        if mutation == "observation_string":
            slot["observation_ids"] = row["observation_id"]
        elif mutation == "api_version":
            slot["api_version"] = "v1.0"
        elif mutation == "preselected_epoch":
            slot["selected_observation_id"] = row["observation_id"]
        else:
            slot["coverage_status"] = "pending_capture"

    rewrite_index_row(
        selected_products, "slots", "dataset-201-facet-taxa-current", mutate
    )
    body = selected_products["capsule"] / row["forensic_locator"]["body_relative_path"]
    opened = observe_entities(monkeypatch, selected_products, {body})
    with pytest.raises(ValueError, match="slot"):
        read_neotoma_ancillary_facet_entity(
            selected_products["directory"],
            **selected_products["kwargs"],
            observation_id=row["observation_id"],
            dataset_id=201,
            facet="taxa",
        )
    assert opened == []


@pytest.mark.parametrize(
    "budget",
    ["request_ordinal", "total_exhausted", "total_remaining", "response_bytes"],
)
def test_selected_attempt_obeys_original_request_and_prefix_byte_budget(
    selected_products: dict[str, Any], monkeypatch: pytest.MonkeyPatch, budget: str
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        read_neotoma_ancillary_facet_entity,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.facets import (
        replay_neotoma_facet_capture,
    )

    from .native_products import rewrite_capture

    row = next(
        row
        for row in selected_products["view"].observations
        if row.get("facet") == "doi"
        and row["root_identity"]["dataset_id"] == 201
        and row["capture_parent_scope_verification"] == "not_recorded_legacy_capture"
    )
    positive = read_neotoma_ancillary_facet_entity(
        selected_products["directory"],
        **selected_products["kwargs"],
        observation_id=row["observation_id"],
        dataset_id=201,
        facet="doi",
    )
    assert positive["terminal_status"] == "received_complete_unqualified_facet"

    def mutate(
        document: dict[str, Any], control: dict[str, Any], directory: Path
    ) -> None:
        preceding = document["facets"][0]["attempts"][0]["body_file"]
        prefix = (directory / preceding).stat().st_size
        selected_size = len(positive["body"])
        field, value = {
            "request_ordinal": ("max_requests", 1),
            "total_exhausted": ("max_total_bytes", prefix),
            "total_remaining": ("max_total_bytes", prefix + selected_size - 1),
            "response_bytes": ("max_response_bytes", selected_size - 1),
        }[budget]
        control["limits"][field] = value

    old = row["source_capture_manifest_sha256"]
    new = rewrite_capture(selected_products, old, mutate)
    with pytest.raises(ValueError):
        replay_neotoma_facet_capture(
            selected_products["capsule"] / "captures" / new,
            expected_manifest_sha256=new,
        )
    body = selected_products["capsule"] / row["forensic_locator"][
        "body_relative_path"
    ].replace(old, new)
    opened = observe_entities(monkeypatch, selected_products, {body})
    with pytest.raises(ValueError, match="budget|bound|limit"):
        read_neotoma_ancillary_facet_entity(
            selected_products["directory"],
            **selected_products["kwargs"],
            observation_id=row["observation_id"].replace(old, new),
            dataset_id=201,
            facet="doi",
        )
    assert opened == []


@pytest.mark.parametrize(
    "field,value",
    [
        ("max_requests", 1),
        ("max_requests", True),
        ("max_total_bytes", 1),
        ("max_response_bytes", 1),
        ("max_attempts", False),
    ],
)
def test_stricter_or_malformed_caller_limits_refuse_before_entities(
    selected_products: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: Any,
) -> None:
    from dataclasses import replace

    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        read_neotoma_ancillary_facet_entity,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.resources.models import (
        DEFAULT_RESOURCE_LIMITS,
    )

    row = next(
        row
        for row in selected_products["view"].observations
        if row.get("facet") == "doi"
        and row["root_identity"]["dataset_id"] == 201
        and row["capture_parent_scope_verification"] == "not_recorded_legacy_capture"
    )
    body = selected_products["capsule"] / row["forensic_locator"]["body_relative_path"]
    opened = observe_entities(monkeypatch, selected_products, {body})
    with pytest.raises(ValueError, match="budget|bound|limit"):
        read_neotoma_ancillary_facet_entity(
            selected_products["directory"],
            **selected_products["kwargs"],
            observation_id=row["observation_id"],
            dataset_id=201,
            facet="doi",
            limits=replace(DEFAULT_RESOURCE_LIMITS, **{field: value}),
        )
    assert opened == []
