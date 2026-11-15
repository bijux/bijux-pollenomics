"""Exact source epochs, current role gates and same-buffer facet selection."""

from __future__ import annotations

from hashlib import sha256
from typing import Any

import pytest

from .native_products import facet_row, observe_entities


def test_selected_facet_reads_only_its_entity_once(
    selected_products: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        read_neotoma_ancillary_facet_entity,
    )

    row = facet_row(selected_products)
    body = selected_products["capsule"] / row["forensic_locator"]["body_relative_path"]
    expected = body.read_bytes()
    opened = observe_entities(monkeypatch, selected_products, {body})
    result = read_neotoma_ancillary_facet_entity(
        selected_products["directory"],
        **selected_products["kwargs"],
        observation_id=row["observation_id"],
        dataset_id=201,
        facet="taxa",
    )
    assert result["body"] == expected
    assert result["body_sha256"] == sha256(expected).hexdigest()
    assert opened == [body]
    assert result["scientific_admission"] == "not_asserted"
    assert result["unselected_entity_bodies_verified"] is False
    assert result["unselected_role_obligations_verified"] is False
    assert result["related_resource_graph_complete"] is False
    assert result["selected_occurrence_native_field_verified"] is False


def test_typed_facet_qualifies_same_buffer_without_scientific_admission(
    selected_products: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        read_neotoma_ancillary_facet,
    )

    row = facet_row(selected_products)
    body = selected_products["capsule"] / row["forensic_locator"]["body_relative_path"]
    opened = observe_entities(monkeypatch, selected_products, {body})
    result = read_neotoma_ancillary_facet(
        selected_products["directory"],
        **selected_products["kwargs"],
        observation_id=row["observation_id"],
        dataset_id=201,
        facet="taxa",
    )
    assert (
        result["source_qualification"]["qualification_status"]
        == "qualified_source_schema"
    )
    assert result["source_qualification"]["source_payload"]["data"][0]["taxonid"] == 1
    assert opened == [body]
    assert result["scientific_admission"] == "not_asserted"


def test_legacy_capture_does_not_manufacture_preget_proof(
    selected_products: dict[str, Any],
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        read_neotoma_ancillary_facet_entity,
    )

    row = facet_row(selected_products, legacy=True)
    result = read_neotoma_ancillary_facet_entity(
        selected_products["directory"],
        **selected_products["kwargs"],
        observation_id=row["observation_id"],
        dataset_id=201,
        facet="taxa",
    )
    assert result["capture_parent_scope_verification"] == "not_recorded_legacy_capture"
    assert result["original_preget_scope_reconstructed"] is False


@pytest.mark.parametrize(
    "changes",
    [
        {"dataset_id": True},
        {"dataset_id": 203},
        {"facet": "sites"},
        {"observation_id": None},
        {"observation_id": "latest"},
    ],
)
def test_wrong_or_ambiguous_selection_refuses_before_entity(
    selected_products: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    changes: dict[str, Any],
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        read_neotoma_ancillary_facet_entity,
    )

    row = facet_row(selected_products)
    opened = observe_entities(monkeypatch, selected_products, set())
    selection = {
        "observation_id": row["observation_id"],
        "dataset_id": 201,
        "facet": "taxa",
        **changes,
    }
    with pytest.raises(ValueError):
        read_neotoma_ancillary_facet_entity(
            selected_products["directory"], **selected_products["kwargs"], **selection
        )
    assert opened == []


def test_protected_root_refuses_before_entity(
    selected_products: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        read_neotoma_ancillary_facet_entity,
    )

    row = facet_row(selected_products, dataset=203)
    opened = observe_entities(monkeypatch, selected_products, set())
    with pytest.raises(ValueError, match="role|scope|protected"):
        read_neotoma_ancillary_facet_entity(
            selected_products["directory"],
            **selected_products["kwargs"],
            observation_id=row["observation_id"],
            dataset_id=203,
            facet="taxa",
        )
    assert opened == []


@pytest.mark.parametrize("later_limit", ["max_requests", "max_total_bytes"])
def test_valid_earlier_selection_does_not_replay_or_reject_later_budget_overrun(
    selected_products: dict[str, Any], monkeypatch: pytest.MonkeyPatch, later_limit: str
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        read_neotoma_ancillary_facet_entity,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.facets import (
        replay_neotoma_facet_capture,
    )

    from .native_products import rewrite_capture

    row = facet_row(selected_products, legacy=True)
    original = row["source_capture_manifest_sha256"]

    def mutate(
        document: dict[str, Any], control: dict[str, Any], directory: Any
    ) -> None:
        first = document["facets"][0]["attempts"][0]["body_file"]
        control["limits"][later_limit] = (
            1 if later_limit == "max_requests" else (directory / first).stat().st_size
        )

    digest = rewrite_capture(selected_products, original, mutate)
    with pytest.raises(ValueError):
        replay_neotoma_facet_capture(
            selected_products["capsule"] / "captures" / digest,
            expected_manifest_sha256=digest,
        )
    body = selected_products["capsule"] / row["forensic_locator"][
        "body_relative_path"
    ].replace(original, digest)
    opened = observe_entities(monkeypatch, selected_products, {body})
    result = read_neotoma_ancillary_facet_entity(
        selected_products["directory"],
        **selected_products["kwargs"],
        observation_id=row["observation_id"].replace(original, digest),
        dataset_id=201,
        facet="taxa",
    )
    assert result["terminal_status"] == "received_complete_unqualified_facet"
    assert result["capture_history_replayed"] is False
    assert opened == [body]


@pytest.mark.parametrize("sentinel_extra", [1, 2])
def test_final_incomplete_entity_has_exact_remaining_budget_sentinel(
    selected_products: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    sentinel_extra: int,
) -> None:
    import json

    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        read_neotoma_ancillary_facet_entity,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.facets import (
        replay_neotoma_facet_capture,
    )
    from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive.files import (
        encoded_json,
    )

    from .native_products import rewrite_capture, sync_observation

    row = next(
        row
        for row in selected_products["view"].observations
        if row.get("facet") == "doi"
        and row["root_identity"]["dataset_id"] == 201
        and row["capture_parent_scope_verification"] == "not_recorded_legacy_capture"
    )
    original = row["source_capture_manifest_sha256"]

    def mutate(
        document: dict[str, Any], control: dict[str, Any], directory: Any
    ) -> None:
        first = document["facets"][0]["attempts"][0]["body_file"]
        entry = document["facets"][1]
        reference = entry["attempts"][-1]
        selected_size = (directory / reference["body_file"]).stat().st_size
        control["limits"]["max_total_bytes"] = (
            (directory / first).stat().st_size + selected_size - sentinel_extra
        )
        receipt_path = directory / reference["receipt_file"]
        receipt = json.loads(receipt_path.read_bytes())
        receipt.update(body_complete=False, terminal_status="refused_http_response")
        receipt_path.write_bytes(encoded_json(receipt))
        reference["receipt_sha256"] = sha256(receipt_path.read_bytes()).hexdigest()
        entry.pop("summary")
        entry.update(
            terminal_status="refused_incomplete_body",
            reason="Incomplete or bounded HTTP entity",
        )
        document["partitions"] = {
            "received_complete_unqualified_facet": 1,
            "refused_incomplete_body": 1,
            "not_attempted_exposure_role": 2,
        }

    digest = rewrite_capture(selected_products, original, mutate)
    selected = sync_observation(selected_products, digest, "facet", 1)
    source = selected["directory"]
    if sentinel_extra == 1:
        replay_neotoma_facet_capture(source, expected_manifest_sha256=digest)
    else:
        with pytest.raises(ValueError):
            replay_neotoma_facet_capture(source, expected_manifest_sha256=digest)
    body = source / selected["entry"]["attempts"][-1]["body_file"]
    opened = observe_entities(monkeypatch, selected_products, {body})
    options = {
        "observation_id": selected["observation_id"],
        "dataset_id": 201,
        "facet": "doi",
    }
    if sentinel_extra == 1:
        result = read_neotoma_ancillary_facet_entity(
            selected_products["directory"], **selected_products["kwargs"], **options
        )
        assert result["terminal_status"] == "refused_incomplete_body"
        assert result["body_complete"] is False
        assert opened == [body]
    else:
        with pytest.raises(ValueError, match="budget|bound|limit"):
            read_neotoma_ancillary_facet_entity(
                selected_products["directory"], **selected_products["kwargs"], **options
            )
        assert opened == []


@pytest.mark.parametrize("attempt_limit", [1, 2])
def test_selected_retry_uses_its_per_entry_attempt_ordinal(
    selected_products: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    attempt_limit: int,
) -> None:
    import json

    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        read_neotoma_ancillary_facet_entity,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.facets import (
        replay_neotoma_facet_capture,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.facets.protocol import (
        plan_from_json,
        request_for,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.receipts import (
        _request_record,
    )
    from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive.files import (
        encoded_json,
    )

    from .native_products import rewrite_capture, sync_observation

    row = next(
        row
        for row in selected_products["view"].observations
        if row.get("facet") == "doi"
        and row["root_identity"]["dataset_id"] == 201
        and row["capture_parent_scope_verification"] == "not_recorded_legacy_capture"
    )
    original = row["source_capture_manifest_sha256"]

    def mutate(
        document: dict[str, Any], control: dict[str, Any], directory: Any
    ) -> None:
        resource = next(
            root
            for root in plan_from_json(control)[0].resources
            if root.dataset_id == 201
        )
        entry = document["facets"][1]
        reference = entry["attempts"][0]
        receipt_path = directory / reference["receipt_file"]
        record = json.loads(receipt_path.read_bytes())
        request = request_for(resource, "doi", 2)
        record.update(_request_record(request, record["utc_start"]))
        record["body_file"] = request.name + ".body"
        (directory / reference["body_file"]).rename(directory / record["body_file"])
        final_receipt = directory / (request.name + ".receipt.json")
        final_receipt.write_bytes(encoded_json(record))
        failure = {
            **_request_record(request_for(resource, "doi", 1), record["utc_start"]),
            "utc_end": record["utc_start"],
            "terminal_status": "transport_failure",
            "body_complete": False,
            "error": "Literal source transport failure",
        }
        receipt_path.write_bytes(encoded_json(failure))
        first = {key: reference[key] for key in ("request_name", "receipt_file")}
        first["receipt_sha256"] = sha256(receipt_path.read_bytes()).hexdigest()
        final = {
            "request_name": request.name,
            "receipt_file": final_receipt.name,
            "receipt_sha256": sha256(final_receipt.read_bytes()).hexdigest(),
            "body_file": record["body_file"],
        }
        entry["attempts"] = [first, final]
        document["request_count"] += 1
        control["limits"]["max_attempts"] = attempt_limit

    digest = rewrite_capture(selected_products, original, mutate)
    selected = sync_observation(selected_products, digest, "facet", 1)
    source = selected["directory"]
    if attempt_limit == 2:
        replay_neotoma_facet_capture(source, expected_manifest_sha256=digest)
    else:
        with pytest.raises(ValueError):
            replay_neotoma_facet_capture(source, expected_manifest_sha256=digest)
    body = source / selected["entry"]["attempts"][-1]["body_file"]
    opened = observe_entities(monkeypatch, selected_products, {body})
    if attempt_limit == 2:
        result = read_neotoma_ancillary_facet_entity(
            selected_products["directory"],
            **selected_products["kwargs"],
            observation_id=selected["observation_id"],
            dataset_id=201,
            facet="doi",
        )
        assert result["terminal_status"] == "received_complete_unqualified_facet"
        assert opened == [body]
    else:
        with pytest.raises(ValueError, match="budget|bound|limit"):
            read_neotoma_ancillary_facet_entity(
                selected_products["directory"],
                **selected_products["kwargs"],
                observation_id=selected["observation_id"],
                dataset_id=201,
                facet="doi",
            )
        assert opened == []
