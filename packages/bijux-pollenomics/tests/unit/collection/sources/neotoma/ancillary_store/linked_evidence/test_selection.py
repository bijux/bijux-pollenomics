"""Scoped selection authenticates only its named native field and detail buffer."""

from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
    read_neotoma_ancillary_facet_entity,
    read_neotoma_ancillary_linked,
    read_neotoma_ancillary_linked_entity,
)

from .native_products import selected


def test_scoped_typed_detail_and_selected_native_pointer_open_once(
    scoped_selection_products: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    products = scoped_selection_products
    row, occurrence = selected(products)
    locator = occurrence["evidence_locator"]
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources import (
        read_neotoma_linked_evidence_target,
    )

    state_pin, state = next(iter(products["evidence_sources"].items()))
    known = read_neotoma_linked_evidence_target(
        state, expected_manifest_sha256=state_pin, kind="taxon", native_id=11
    )
    offset = list(known["proof_locators"]).index(locator)
    proof = known["source_proofs"][offset]
    source_manifest = proof["source_capture_manifest_sha256"]
    source = next(
        value
        for value in products["view"].observations
        if value["kind"] == "facet"
        and value["source_capture_manifest_sha256"] == source_manifest
        and value["facet_key"] == proof["source_facet_key"]
    )
    parent = (
        products["facet_capsule"] / source["forensic_locator"]["body_relative_path"]
    )
    body = products["capsule"] / row["forensic_locator"]["body_relative_path"]
    expected = body.read_bytes()
    opened = []
    original = Path.open

    def observe(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.suffix == ".body" and (
            products["capsule"] in path.parents
            or products["facet_capsule"] in path.parents
        ):
            assert path in {parent, body}
            opened.append(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observe)
    result = read_neotoma_ancillary_linked(
        products["directory"],
        **products["kwargs"],
        evidence_sources=products["evidence_sources"],
        observation_id=row["observation_id"],
        occurrence_id=occurrence["occurrence_id"],
        kind="taxon",
        native_id=11,
    )
    assert opened == [parent, body]
    assert result["body"] == expected
    assert result["source_payload"]["data"][0]["taxonid"] == 11
    assert result["evidence_locator"] == locator
    assert result["source_proof"] == proof
    assert result["unselected_entity_bodies_verified"] is False


def test_facet_selection_needs_no_unrelated_state_resolver_or_proof_parts(
    scoped_selection_products: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    products = scoped_selection_products
    row = next(
        value
        for value in products["view"].observations
        if value["kind"] == "facet"
        and value["facet"] == "taxa"
        and value["root_identity"]["dataset_id"] == 201
    )
    body = products["facet_capsule"] / row["forensic_locator"]["body_relative_path"]
    original = Path.open
    opened = []

    def observe(path: Path, *args: Any, **kwargs: Any) -> Any:
        assert path.parent.name != "proofs"
        if path.suffix == ".body" and products["facet_capsule"] in path.parents:
            assert path == body
            opened.append(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observe)
    value = read_neotoma_ancillary_facet_entity(
        products["directory"],
        **products["kwargs"],
        observation_id=row["observation_id"],
        dataset_id=201,
        facet="taxa",
    )
    assert opened == [body]
    assert value["scientific_admission"] == "not_asserted"


def test_scoped_linked_selection_refuses_missing_state_without_entity_access(
    scoped_selection_products: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    products = scoped_selection_products
    row, occurrence = selected(products)
    original = Path.open
    opened = []

    def observe(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.suffix == ".body" and any(
            root in path.parents
            for root in (products["capsule"], products["facet_capsule"])
        ):
            opened.append(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observe)
    with pytest.raises(ValueError, match="evidence|resolver"):
        read_neotoma_ancillary_linked_entity(
            products["directory"],
            **products["kwargs"],
            observation_id=row["observation_id"],
            occurrence_id=occurrence["occurrence_id"],
            kind="taxon",
            native_id=11,
        )
    assert opened == []


@pytest.mark.parametrize("budget", ["requests", "entity", "total"])
def test_scoped_request_and_remaining_budget_refuses_before_any_entity(
    scoped_selection_products: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    budget: str,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.resources.models import (
        NeotomaResourceLimits,
    )

    products = scoped_selection_products
    row, occurrence = selected(products, 12)
    members = [
        value
        for value in products["view"].observations
        if value["kind"] == "linked" and value["attempts"]
    ]
    sizes = [value["attempts"][-1]["body_bytes"] for value in members]
    changes = (
        {"max_requests": 1}
        if budget == "requests"
        else {"max_response_bytes": row["attempts"][-1]["body_bytes"] - 1}
        if budget == "entity"
        else {"max_total_bytes": sum(sizes) - 1}
    )
    original = Path.open
    opened = []

    def observe(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.suffix == ".body" and any(
            root in path.parents
            for root in (products["capsule"], products["facet_capsule"])
        ):
            opened.append(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observe)
    options = {**products["kwargs"], "limits": NeotomaResourceLimits(**changes)}
    with pytest.raises(ValueError, match="budget"):
        read_neotoma_ancillary_linked_entity(
            products["directory"],
            **options,
            evidence_sources=products["evidence_sources"],
            observation_id=row["observation_id"],
            occurrence_id=occurrence["occurrence_id"],
            kind="taxon",
            native_id=12,
        )
    assert opened == []


def test_scoped_incomplete_entity_retains_sentinel_without_typed_admission(
    scoped_selection_products: dict[str, Any],
    tmp_path: Path,
) -> None:
    from .native_products import sentinel_products

    products = sentinel_products(scoped_selection_products, tmp_path)
    row, occurrence = selected(products)
    options = {
        **products["kwargs"],
        "evidence_sources": products["evidence_sources"],
        "observation_id": row["observation_id"],
        "occurrence_id": occurrence["occurrence_id"],
        "kind": "taxon",
        "native_id": 11,
    }
    result = read_neotoma_ancillary_linked_entity(products["directory"], **options)
    assert result["body"] == b"x" * 33
    assert result["body_complete"] is False
    assert result["terminal_status"] == "refused_incomplete_body"
    with pytest.raises(ValueError, match="complete"):
        read_neotoma_ancillary_linked(products["directory"], **options)


def test_facet_owned_by_scoped_capsule_needs_no_global_evidence_resolver(
    scoped_selection_products: dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule import (
        write_neotoma_ancillary_capsule,
    )

    from .native_products import federation_products, pin

    products = scoped_selection_products
    capture_pin = next(
        value["source_capture_manifest_sha256"]
        for value in products["view"].observations
        if value["kind"] == "linked"
    )
    joint = tmp_path / "joint-scoped-capsule"
    write_neotoma_ancillary_capsule(
        joint,
        facet_captures=products["sources"],
        linked_captures={capture_pin: products["capsule"] / "captures" / capture_pin},
        evidence_sources=products["evidence_sources"],
        **{
            key: products["kwargs"][key]
            for key in (
                "context_directory",
                "expected_context_sha256",
                "native_archive_directory",
            )
        },
    )
    products = federation_products(
        products,
        tmp_path / "joint-scoped-federation",
        {pin(joint / "manifest.json"): joint},
        scoped=True,
    )
    row = next(
        value
        for value in products["view"].observations
        if value["kind"] == "facet"
        and value["facet"] == "taxa"
        and value["root_identity"]["dataset_id"] == 201
    )
    body = joint / row["forensic_locator"]["body_relative_path"]
    original = Path.open
    opened = []

    def observe(path: Path, *args: Any, **kwargs: Any) -> Any:
        assert path.parent.name != "proofs"
        if path.suffix == ".body" and joint in path.parents:
            assert path == body
            opened.append(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observe)
    read_neotoma_ancillary_facet_entity(
        products["directory"],
        **products["kwargs"],
        observation_id=row["observation_id"],
        dataset_id=201,
        facet="taxa",
    )
    assert opened == [body]


@pytest.mark.parametrize(
    "changes",
    [
        {"native_id": True},
        {"native_id": 12},
        {"kind": "contact"},
        {"occurrence_id": "latest"},
    ],
)
def test_scoped_requested_identity_refuses_before_any_entity(
    scoped_selection_products: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    changes: dict[str, Any],
) -> None:
    products = scoped_selection_products
    row, occurrence = selected(products)
    options = {
        **products["kwargs"],
        "evidence_sources": products["evidence_sources"],
        "observation_id": row["observation_id"],
        "occurrence_id": occurrence["occurrence_id"],
        "kind": "taxon",
        "native_id": 11,
        **changes,
    }
    original = Path.open
    opened = []

    def observed(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.suffix == ".body" and any(
            root in path.parents
            for root in (products["capsule"], products["facet_capsule"])
        ):
            opened.append(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observed)
    with pytest.raises(ValueError):
        read_neotoma_ancillary_linked_entity(products["directory"], **options)
    assert opened == []


def test_original_scope_uses_one_authenticated_buffer_and_no_cross_call_cache(
    scoped_selection_products: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    products = scoped_selection_products
    row, occurrence = selected(products)
    original = Path.open
    scope_opens = []

    def observed(path: Path, *args: Any, **kwargs: Any) -> Any:
        if (
            path.name == "parent-scope.json"
            and products["facet_capsule"] in path.parents
        ):
            scope_opens.append(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observed)
    options = {
        **products["kwargs"],
        "evidence_sources": products["evidence_sources"],
        "observation_id": row["observation_id"],
        "occurrence_id": occurrence["occurrence_id"],
        "kind": "taxon",
        "native_id": 11,
    }
    read_neotoma_ancillary_linked_entity(products["directory"], **options)
    assert len(scope_opens) == 1
    path = scope_opens[0]
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="bounded|digest|identity"):
        read_neotoma_ancillary_linked_entity(products["directory"], **options)
