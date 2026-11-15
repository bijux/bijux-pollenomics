"""One batch reuses authenticated metadata without granting native entity access."""

from typing import Any

import pytest

from ..native_products import selected_products as selected_products
from .native_inputs import (
    api,
    facet_row,
    linked_rows,
    observe,
    scoped_arguments,
)
from .native_inputs import (
    scoped_inputs as scoped_inputs,
)
from .native_inputs import (
    scoped_selection_products as scoped_selection_products,
)


def test_actual_guards_return_immutable_metadata_without_any_entity(
    selected_products: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    source = selected_products
    row = facet_row(source)
    observe(monkeypatch, source)
    with api().prepare_neotoma_preflight_batch(
        source["directory"], **source["kwargs"]
    ) as batch:
        prepared = batch.facet(
            observation_id=row["observation_id"], dataset_id=201, facet="taxa"
        )
        assert prepared.to_dict()["row"] == row
        assert prepared.parents[201]["effective_scope_role"] in {
            "development_resource_discovery",
            "exposed_development",
        }
        assert (
            prepared.source["response_bound"]
            >= prepared.source["receipt"]["retained_body_bytes"]
        )
        assert prepared.entity_bodies_verified is False
        assert prepared.native_field_value_verified is False
        with pytest.raises(TypeError):
            prepared.row["current_use_role"] = "invented role"
        with pytest.raises(TypeError):
            prepared.source["receipt"]["retained_body_bytes"] = 0
        detached = prepared.to_dict()
        detached["row"]["current_use_role"] = "invented role"
        again = batch.facet(
            observation_id=row["observation_id"], dataset_id=201, facet="taxa"
        )
        assert again.to_dict()["row"] == row
        assert "body" not in again.to_dict()
        assert str(source["directory"]) not in str(again.to_dict())


def test_many_facets_reuse_real_current_metadata_but_second_operation_is_fresh(
    selected_products: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    source = selected_products
    counts = observe(monkeypatch, source)
    rows = [
        row
        for row in source["view"].observations
        if row["kind"] == "facet"
        and row["root_identity"]["dataset_id"] == 201
        and row["capture_parent_scope_verification"] != "not_recorded_legacy_capture"
    ]
    assert len(rows) >= 2
    native = source["kwargs"]["native_archive_directory"]
    with api().prepare_neotoma_preflight_batch(
        source["directory"], **source["kwargs"]
    ) as batch:
        initial = {
            path: count
            for path, count in counts.items()
            if path.suffix == ".body" and native in path.parents
        }
        assert initial
        for _ in range(10):
            for row in rows:
                batch.facet(
                    observation_id=row["observation_id"],
                    dataset_id=201,
                    facet=row["facet"],
                )
        assert {
            path: count
            for path, count in counts.items()
            if path.suffix == ".body" and native in path.parents
        } == initial
        assert all(
            count == 1
            for path, count in counts.items()
            if source["directory"] in path.parents and path.name != "manifest.json"
        )
    before = dict(counts)
    with api().prepare_neotoma_preflight_batch(
        source["directory"], **source["kwargs"]
    ) as another:
        another.facet(
            observation_id=rows[0]["observation_id"],
            dataset_id=201,
            facet=rows[0]["facet"],
        )
    assert all(counts[path] > before[path] for path in initial)


def test_distinct_targets_share_each_same_verified_evidence_part_once(
    scoped_selection_products: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    source = scoped_selection_products
    counts = observe(monkeypatch, source)
    with api().prepare_neotoma_preflight_batch(
        source["directory"], **scoped_arguments(source)
    ) as batch:
        for native in (11, 12):
            row, occurrences = linked_rows(source, native)
            assert occurrences
            for occurrence in occurrences:
                prepared = batch.linked(
                    observation_id=row["observation_id"],
                    occurrence_id=occurrence["occurrence_id"],
                    kind="taxon",
                    native_id=native,
                )
                assert (
                    prepared.witness["evidence_locator"]
                    == occurrence["evidence_locator"]
                )
                assert prepared.native_field_value_verified is False
                assert (
                    prepared.source["response_bound"]
                    >= prepared.source["receipt"]["retained_body_bytes"]
                )
        proof_reads = {
            path: count
            for path, count in counts.items()
            if path.parent.name == "proofs"
        }
        assert proof_reads and all(count == 1 for count in proof_reads.values())
