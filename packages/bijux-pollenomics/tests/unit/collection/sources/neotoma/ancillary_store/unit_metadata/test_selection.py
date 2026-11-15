"""Metadata inventory opens no units; selected typed/forensic access opens one buffer."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from .native_products import observe_units, payload, pin


def test_unit_inventory_authenticates_metadata_without_unit_bodies(
    unit_products: Callable[..., dict[str, Any]], tmp_path: Path, monkeypatch: Any
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.unit_metadata import (
        read_neotoma_unit_metadata_inventory,
        write_neotoma_unit_metadata_archive,
    )

    inputs = unit_products()
    output = tmp_path / "archive"
    write_neotoma_unit_metadata_archive(output, **inputs["writer"])
    opened = observe_units(monkeypatch, set())
    inventory = read_neotoma_unit_metadata_inventory(
        output,
        expected_manifest_sha256=pin(output / "manifest.json"),
        **inputs["reader"],
    )
    assert len(inventory.index["units"]) == 2
    assert inventory.source_entity_bodies_verified is False
    assert opened == []


def test_typed_unit_selection_preserves_nulls_opaque_references_and_source_rows(
    unit_products: Callable[..., dict[str, Any]], tmp_path: Path, monkeypatch: Any
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.unit_metadata import (
        read_neotoma_unit_metadata,
        write_neotoma_unit_metadata_archive,
    )

    inputs = unit_products()
    output = tmp_path / "archive"
    write_neotoma_unit_metadata_archive(output, **inputs["writer"])
    body = output / "capture/speleothem-unit-100-current-attempt-1.body"
    opened = observe_units(monkeypatch, {body})
    result = read_neotoma_unit_metadata(
        output,
        expected_manifest_sha256=pin(output / "manifest.json"),
        collection_unit_id=100,
        **inputs["reader"],
    )
    assert result["source_payload"] == payload(100)
    assert result["summary"]["unit_reference_label_resolution"] == "not_established"
    assert result["summary"]["units_interpreted"] is False
    assert result["summary"]["independent_vegetation_reference"] == "not_established"
    assert result["scientific_admission"] == "not_asserted"
    assert result["unselected_source_bodies_verified"] is False
    assert opened == [body]


def test_forensic_body_does_not_claim_native_owner_qualification(
    unit_products: Callable[..., dict[str, Any]], tmp_path: Path
) -> None:

    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.unit_metadata import (
        read_neotoma_unit_metadata,
        read_neotoma_unit_metadata_entity,
        write_neotoma_unit_metadata_archive,
    )

    inputs = unit_products(foreign_payload=True)
    output = tmp_path / "archive"
    write_neotoma_unit_metadata_archive(output, **inputs["writer"])
    kwargs = {
        "expected_manifest_sha256": pin(output / "manifest.json"),
        "collection_unit_id": 100,
        **inputs["reader"],
    }
    raw = read_neotoma_unit_metadata_entity(output, **kwargs)
    assert raw["terminal_status"] == "received_complete_unqualified_unit_resource"
    assert raw["scientific_admission"] == "not_asserted"
    with pytest.raises(ValueError, match="owner"):
        read_neotoma_unit_metadata(output, **kwargs)


@pytest.mark.parametrize(
    "budget", ["request", "zero_remaining", "insufficient_remaining", "caller"]
)
def test_selected_unit_request_ordinal_and_remaining_budget_refuse_before_body(
    unit_products: Callable[..., dict[str, Any]],
    tmp_path: Path,
    monkeypatch: Any,
    budget: str,
) -> None:
    from dataclasses import replace

    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.unit_metadata import (
        load_neotoma_unit_metadata_archive,
        read_neotoma_unit_metadata_entity,
        write_neotoma_unit_metadata_archive,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.resources.models import (
        DEFAULT_RESOURCE_LIMITS,
    )

    from .native_products import rewrite_archive_source

    inputs = unit_products()
    output = tmp_path / "archive"
    write_neotoma_unit_metadata_archive(output, **inputs["writer"])
    first = output / "capture/speleothem-unit-100-current-attempt-1.body"
    second = output / "capture/speleothem-unit-200-current-attempt-1.body"

    def mutate(_: Any, control: dict[str, Any], __: Any) -> None:
        if budget == "request":
            control["limits"]["max_requests"] = 1
        elif budget == "zero_remaining":
            control["limits"]["max_total_bytes"] = first.stat().st_size
        elif budget == "insufficient_remaining":
            control["limits"]["max_total_bytes"] = (
                first.stat().st_size + second.stat().st_size - 1
            )

    digest = rewrite_archive_source(output, mutate)
    options: dict[str, Any] = (
        {"limits": replace(DEFAULT_RESOURCE_LIMITS, max_requests=1)}
        if budget == "caller"
        else {}
    )
    opened = observe_units(monkeypatch, set())
    with pytest.raises(ValueError, match="budget"):
        read_neotoma_unit_metadata_entity(
            output,
            expected_manifest_sha256=digest,
            collection_unit_id=200,
            **inputs["reader"],
            **options,
        )
    with pytest.raises(ValueError, match="budget"):
        load_neotoma_unit_metadata_archive(
            output, expected_manifest_sha256=digest, **inputs["reader"], **options
        )
    assert opened == []


def test_valid_earlier_unit_does_not_admit_or_replay_later_over_budget_request(
    unit_products: Callable[..., dict[str, Any]], tmp_path: Path, monkeypatch: Any
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.unit_metadata import (
        read_neotoma_unit_metadata_entity,
        write_neotoma_unit_metadata_archive,
    )

    from .native_products import rewrite_archive_source

    inputs = unit_products()
    output = tmp_path / "archive"
    write_neotoma_unit_metadata_archive(output, **inputs["writer"])

    def mutate(_: Any, control: dict[str, Any], __: Any) -> None:
        control["limits"]["max_requests"] = 1

    digest = rewrite_archive_source(output, mutate)
    body = output / "capture/speleothem-unit-100-current-attempt-1.body"
    opened = observe_units(monkeypatch, {body})
    result = read_neotoma_unit_metadata_entity(
        output,
        expected_manifest_sha256=digest,
        collection_unit_id=100,
        **inputs["reader"],
    )
    assert result["terminal_status"] == "received_complete_unqualified_unit_resource"
    assert result["source_capture_history_replayed"] is False
    assert opened == [body]


@pytest.mark.parametrize("extra", [1, 2])
def test_incomplete_selected_unit_retains_only_legal_final_sentinel(
    unit_products: Callable[..., dict[str, Any]],
    tmp_path: Path,
    monkeypatch: Any,
    extra: int,
) -> None:
    import json

    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.unit_metadata import (
        read_neotoma_unit_metadata_entity,
        write_neotoma_unit_metadata_archive,
    )
    from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive.files import (
        encoded_json,
    )

    from .native_products import rewrite_archive_source

    inputs = unit_products()
    output = tmp_path / "archive"
    write_neotoma_unit_metadata_archive(output, **inputs["writer"])
    first = output / "capture/speleothem-unit-100-current-attempt-1.body"
    second = output / "capture/speleothem-unit-200-current-attempt-1.body"

    def mutate(document: dict[str, Any], control: dict[str, Any], root: Path) -> None:
        entry = document["units"][1]
        ref = entry["attempts"][0]
        receipt = root / ref["receipt_file"]
        record = json.loads(receipt.read_bytes())
        record.update(body_complete=False, terminal_status="refused_http_response")
        receipt.write_bytes(encoded_json(record))
        ref["receipt_sha256"] = pin(receipt)
        entry.pop("summary")
        entry.update(
            terminal_status="refused_incomplete_body",
            reason="Incomplete or bounded HTTP entity",
        )
        document["partitions"] = {
            "received_complete_unqualified_unit_resource": 1,
            "refused_incomplete_body": 1,
        }
        control["limits"]["max_total_bytes"] = (
            first.stat().st_size + second.stat().st_size - extra
        )

    digest = rewrite_archive_source(output, mutate)
    opened = observe_units(monkeypatch, {second})
    if extra == 1:
        result = read_neotoma_unit_metadata_entity(
            output,
            expected_manifest_sha256=digest,
            collection_unit_id=200,
            **inputs["reader"],
        )
        assert (
            result["terminal_status"] == "refused_incomplete_body"
            and result["body_complete"] is False
        )
        assert opened == [second]
    else:
        with pytest.raises(ValueError, match="budget"):
            read_neotoma_unit_metadata_entity(
                output,
                expected_manifest_sha256=digest,
                collection_unit_id=200,
                **inputs["reader"],
            )
        assert opened == []


def test_malformed_limit_object_refuses_before_any_unit_body(
    unit_products: Callable[..., dict[str, Any]], tmp_path: Path, monkeypatch: Any
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.unit_metadata import (
        read_neotoma_unit_metadata_entity,
        write_neotoma_unit_metadata_archive,
    )

    inputs = unit_products()
    output = tmp_path / "archive"
    write_neotoma_unit_metadata_archive(output, **inputs["writer"])
    malformed: Any = None
    opened = observe_units(monkeypatch, set())
    with pytest.raises(ValueError, match="limit"):
        read_neotoma_unit_metadata_entity(
            output,
            expected_manifest_sha256=pin(output / "manifest.json"),
            collection_unit_id=100,
            limits=malformed,
            **inputs["reader"],
        )
    assert opened == []
