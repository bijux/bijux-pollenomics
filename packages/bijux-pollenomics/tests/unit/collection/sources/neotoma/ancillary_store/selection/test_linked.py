"""Named linked occurrences authenticate one predecessor and one detail entity."""

from __future__ import annotations

from typing import Any

import pytest

from .native_products import observe_entities, rewrite_index_row


def test_linked_selection_authenticates_only_named_predecessor_and_detail_once(
    selected_products: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        read_neotoma_ancillary_linked_entity,
    )

    row = next(
        row for row in selected_products["view"].observations if row["kind"] == "linked"
    )
    occurrence = selected_products["view"].linked_occurrences[0]
    proof = occurrence["source_proof"]
    predecessor = next(
        row
        for row in selected_products["view"].observations
        if row["source_capture_manifest_sha256"]
        == proof["source_capture_manifest_sha256"]
        and row.get("facet_key") == proof["source_facet_key"]
    )
    body = selected_products["capsule"] / row["forensic_locator"]["body_relative_path"]
    parent_body = (
        selected_products["capsule"]
        / predecessor["forensic_locator"]["body_relative_path"]
    )
    opened = observe_entities(monkeypatch, selected_products, {parent_body, body})
    result = read_neotoma_ancillary_linked_entity(
        selected_products["directory"],
        **selected_products["kwargs"],
        observation_id=row["observation_id"],
        occurrence_id=occurrence["occurrence_id"],
        kind="taxon",
        native_id=1,
    )
    assert opened == [parent_body, body]
    assert result["body"] == b'{"status":"success","data":[{"taxonid":1}]}'
    assert result["source_proof"] == proof
    assert result["selected_occurrence_native_field_verified"] is True
    assert result["all_recorded_proof_root_metadata_verified"] is True
    assert result["unselected_occurrence_native_fields_verified"] is False
    assert result["related_resource_graph_complete"] is False


def test_typed_linked_refuses_unqualified_native_layout(
    selected_products: dict[str, Any],
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        read_neotoma_ancillary_linked,
    )

    row = next(
        row for row in selected_products["view"].observations if row["kind"] == "linked"
    )
    occurrence = selected_products["view"].linked_occurrences[0]
    with pytest.raises(ValueError, match="envelope|fields|schema"):
        read_neotoma_ancillary_linked(
            selected_products["directory"],
            **selected_products["kwargs"],
            observation_id=row["observation_id"],
            occurrence_id=occurrence["occurrence_id"],
            kind="taxon",
            native_id=1,
        )


@pytest.mark.parametrize(
    "changes",
    [
        {"native_id": True},
        {"native_id": 2},
        {"kind": "contact"},
        {"occurrence_id": None},
        {"occurrence_id": "latest"},
    ],
)
def test_wrong_linked_target_or_occurrence_refuses_without_entities(
    selected_products: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    changes: dict[str, Any],
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        read_neotoma_ancillary_linked_entity,
    )

    row = next(
        row for row in selected_products["view"].observations if row["kind"] == "linked"
    )
    occurrence = selected_products["view"].linked_occurrences[0]
    opened = observe_entities(monkeypatch, selected_products, set())
    options = {
        "observation_id": row["observation_id"],
        "occurrence_id": occurrence["occurrence_id"],
        "kind": "taxon",
        "native_id": 1,
        **changes,
    }
    with pytest.raises(ValueError):
        read_neotoma_ancillary_linked_entity(
            selected_products["directory"], **selected_products["kwargs"], **options
        )
    assert opened == []


def test_rehashed_occurrence_cannot_claim_another_native_field(
    selected_products: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        read_neotoma_ancillary_linked_entity,
    )

    row = next(
        row for row in selected_products["view"].observations if row["kind"] == "linked"
    )
    occurrence = selected_products["view"].linked_occurrences[0]
    rewrite_index_row(
        selected_products,
        "linked_occurrences",
        occurrence["occurrence_id"],
        lambda value: value["source_proof"].update(
            json_pointer="/data/0/highertaxonid"
        ),
    )
    opened = observe_entities(monkeypatch, selected_products, set())
    with pytest.raises(ValueError, match="occurrence"):
        read_neotoma_ancillary_linked_entity(
            selected_products["directory"],
            **selected_products["kwargs"],
            observation_id=row["observation_id"],
            occurrence_id=occurrence["occurrence_id"],
            kind="taxon",
            native_id=1,
        )
    assert opened == []


@pytest.mark.parametrize(
    "restriction", ["protected", "unmatched", "same_id_foreign_database"]
)
def test_all_recorded_roots_are_checked_before_any_predecessor_or_detail_body(
    selected_products: dict[str, Any], monkeypatch: pytest.MonkeyPatch, restriction: str
) -> None:
    from copy import deepcopy

    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        read_neotoma_ancillary_linked_entity,
    )

    from .native_products import facet_row, rewrite_capture

    row = next(
        row for row in selected_products["view"].observations if row["kind"] == "linked"
    )
    occurrence = selected_products["view"].linked_occurrences[0]

    def mutate(document: dict[str, Any], control: dict[str, Any], _: Any) -> None:
        target = document["resources"][0]["identity"]
        proof = deepcopy(target["source_proofs"][0])
        if restriction == "protected":
            proof["root_identity"] = deepcopy(
                facet_row(selected_products, dataset=203)["root_identity"]
            )
            proof["root_dataset_id"] = 203
        elif restriction == "unmatched":
            proof["root_identity"]["dataset_id"] = 999
            proof["root_dataset_id"] = 999
        else:
            proof["root_identity"]["database"] = "foreign source database"
        # The requested development occurrence stays first. No later proof may be erased.
        target["source_proofs"].append(proof)
        control["targets"][0] = deepcopy(target)

    old = row["source_capture_manifest_sha256"]
    new = rewrite_capture(selected_products, old, mutate)
    opened = observe_entities(monkeypatch, selected_products, set())
    with pytest.raises(ValueError, match="owner|role|scope"):
        read_neotoma_ancillary_linked_entity(
            selected_products["directory"],
            **selected_products["kwargs"],
            observation_id=row["observation_id"].replace(old, new),
            occurrence_id=occurrence["occurrence_id"].replace(old, new),
            kind="taxon",
            native_id=1,
        )
    assert opened == []


def test_native_pointer_relation_is_not_implied_by_rehashed_source_metadata(
    selected_products: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    from copy import deepcopy

    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        read_neotoma_ancillary_linked_entity,
    )

    from .native_products import facet_row, rewrite_capture

    row = next(
        row for row in selected_products["view"].observations if row["kind"] == "linked"
    )
    occurrence = selected_products["view"].linked_occurrences[0]

    def mutate(document: dict[str, Any], control: dict[str, Any], _: Any) -> None:
        target = document["resources"][0]["identity"]
        # A valid native pointer cannot stand in for another registered relationship.
        target["source_proofs"][0]["json_pointer"] = "/data/0/highertaxonid"
        control["targets"][0] = deepcopy(target)

    old = row["source_capture_manifest_sha256"]
    new = rewrite_capture(selected_products, old, mutate)
    selected_id = row["observation_id"].replace(old, new)
    selected_occurrence = occurrence["occurrence_id"].replace(old, new)
    rewrite_index_row(
        selected_products,
        "linked_occurrences",
        selected_occurrence,
        lambda value: value["source_proof"].update(
            json_pointer="/data/0/highertaxonid"
        ),
    )
    predecessor = facet_row(selected_products)
    body = (
        selected_products["capsule"]
        / predecessor["forensic_locator"]["body_relative_path"]
    )
    opened = observe_entities(monkeypatch, selected_products, {body})
    with pytest.raises(ValueError, match="pointer"):
        read_neotoma_ancillary_linked_entity(
            selected_products["directory"],
            **selected_products["kwargs"],
            observation_id=selected_id,
            occurrence_id=selected_occurrence,
            kind="taxon",
            native_id=1,
        )
    assert opened == [body]


@pytest.mark.parametrize("http_status", [200, 404])
def test_typed_and_forensic_linked_access_retain_native_identity_and_http_status(
    selected_products: dict[str, Any], monkeypatch: pytest.MonkeyPatch, http_status: int
) -> None:
    from hashlib import sha256
    import json

    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        read_neotoma_ancillary_linked,
        read_neotoma_ancillary_linked_entity,
    )
    from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive.files import (
        encoded_json,
    )

    from .native_products import rewrite_capture, sync_observation

    row = next(
        row for row in selected_products["view"].observations if row["kind"] == "linked"
    )
    original = row["source_capture_manifest_sha256"]
    record = dict.fromkeys(("author", "highertaxonid", "publicationid", "publication"))
    record.update(
        taxonid=1,
        taxonname="Native taxon",
        taxoncode="NATIVE",
        ecolgroup="UPHE",
        status="source status",
        taxagroupid="Vascular plants",
    )
    expected = (
        encoded_json(
            {"status": "success", "data": [record], "message": "Source message"}
        )
        if http_status == 200
        else b"Literal unavailable source body"
    )

    def mutate(document: dict[str, Any], _: Any, directory: Any) -> None:
        entry = document["resources"][0]
        reference = entry["attempts"][-1]
        (directory / reference["body_file"]).write_bytes(expected)
        path = directory / reference["receipt_file"]
        receipt = json.loads(path.read_bytes())
        receipt.update(
            retained_body_bytes=len(expected),
            retained_body_sha256=sha256(expected).hexdigest(),
            http_status=http_status,
            terminal_status="complete_http_200"
            if http_status == 200
            else "refused_http_response",
        )
        path.write_bytes(encoded_json(receipt))
        reference["receipt_sha256"] = sha256(path.read_bytes()).hexdigest()
        if http_status == 404:
            entry.pop("summary")
            entry.update(
                terminal_status="unavailable_http",
                http_status=404,
                absence_certified=False,
            )
        document["response_bytes"] = len(expected)
        document["partitions"] = {entry["terminal_status"]: 1}

    capture = rewrite_capture(selected_products, original, mutate)
    selected = sync_observation(selected_products, capture, "linked")
    options = {
        "observation_id": selected["observation_id"],
        "occurrence_id": selected["observation_id"] + ":proof:0",
        "kind": "taxon",
        "native_id": 1,
    }
    predecessor = selected_products["view"].linked_occurrences[0]["source_proof"][
        "source_capture_manifest_sha256"
    ]
    parent = next(
        value
        for value in selected_products["view"].observations
        if value.get("facet") == "taxa"
        and value["source_capture_manifest_sha256"] == predecessor
    )
    parent_body = (
        selected_products["capsule"] / parent["forensic_locator"]["body_relative_path"]
    )
    linked_body = selected["directory"] / selected["entry"]["attempts"][-1]["body_file"]
    opened = observe_entities(
        monkeypatch, selected_products, {parent_body, linked_body}
    )
    if http_status == 200:
        result = read_neotoma_ancillary_linked(
            selected_products["directory"], **selected_products["kwargs"], **options
        )
        assert result["source_records"] == [record]
    else:
        result = read_neotoma_ancillary_linked_entity(
            selected_products["directory"], **selected_products["kwargs"], **options
        )
        assert result["terminal_status"] == "unavailable_http"
    assert result["body"] == expected
    assert result["http_status"] == http_status
    assert opened == [parent_body, linked_body]


@pytest.mark.parametrize("field", ["max_total_bytes", "max_response_bytes"])
def test_linked_request_budget_refuses_before_predecessor_entity_access(
    selected_products: dict[str, Any], monkeypatch: pytest.MonkeyPatch, field: str
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        read_neotoma_ancillary_linked_entity,
    )

    from .native_products import rewrite_capture

    row = next(
        row for row in selected_products["view"].observations if row["kind"] == "linked"
    )
    old = row["source_capture_manifest_sha256"]

    def mutate(_: Any, control: dict[str, Any], __: Any) -> None:
        control["limits"][field] = 1

    digest = rewrite_capture(selected_products, old, mutate)
    selected_id = row["observation_id"].replace(old, digest)
    opened = observe_entities(monkeypatch, selected_products, set())
    with pytest.raises(ValueError, match="budget|bound|limit"):
        read_neotoma_ancillary_linked_entity(
            selected_products["directory"],
            **selected_products["kwargs"],
            observation_id=selected_id,
            occurrence_id=selected_id + ":proof:0",
            kind="taxon",
            native_id=1,
        )
    assert opened == []
