"""Batch lifetime and independent source bindings cannot be supplied by callers."""

from pathlib import Path
from typing import Any

import pytest

from ..native_products import selected_products as selected_products
from .native_inputs import (
    api,
    facet_row,
    observe,
    scoped_arguments,
)
from .native_inputs import (
    scoped_inputs as scoped_inputs,
)
from .native_inputs import (
    scoped_selection_products as scoped_selection_products,
)


def test_closed_operation_cannot_reopen_or_reuse_authority(
    selected_products: dict[str, Any],
) -> None:
    source = selected_products
    row = facet_row(source)
    operation = api().prepare_neotoma_preflight_batch(
        source["directory"], **source["kwargs"]
    )
    with pytest.raises(ValueError, match="open|entered"):
        operation.facet(
            observation_id=row["observation_id"], dataset_id=201, facet="taxa"
        )
    with operation:
        operation.facet(
            observation_id=row["observation_id"], dataset_id=201, facet="taxa"
        )
    with pytest.raises(ValueError, match="closed|open"):
        operation.facet(
            observation_id=row["observation_id"], dataset_id=201, facet="taxa"
        )
    with pytest.raises(ValueError, match="closed|reopen"):
        operation.__enter__()


def test_member_drift_refuses_close_and_next_operation_uses_new_reads(
    selected_products: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    source = selected_products
    observe(monkeypatch, source)
    row = facet_row(source)
    operation = api().prepare_neotoma_preflight_batch(
        source["directory"], **source["kwargs"]
    )
    operation.__enter__()
    operation.facet(observation_id=row["observation_id"], dataset_id=201, facet="taxa")
    path = source["directory"] / "scope/current-parent-proof.json"
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="changed|drift|identity|size"):
        operation.close()
    with (
        pytest.raises(ValueError),
        api().prepare_neotoma_preflight_batch(source["directory"], **source["kwargs"]),
    ):
        pass


def test_input_root_alias_refuses_and_no_scope_object_can_be_injected(
    selected_products: dict[str, Any], tmp_path: Path
) -> None:
    source = selected_products
    alias = tmp_path / "source-alias"
    alias.symlink_to(source["directory"], target_is_directory=True)
    with (
        pytest.raises(ValueError, match="symlink|redirect|physical"),
        api().prepare_neotoma_preflight_batch(alias, **source["kwargs"]),
    ):
        pass
    with pytest.raises(TypeError):
        api().prepare_neotoma_preflight_batch(
            source["directory"],
            **source["kwargs"],
            scope={"role": "development_resource_discovery"},
        )


def test_known_protected_contact_remains_blocked_with_cached_current_facts(
    scoped_selection_products: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    source = scoped_selection_products
    observe(monkeypatch, source)
    row = next(
        row
        for row in source["view"].observations
        if row["kind"] == "linked" and row["identity"]["kind"] == "contact"
    )
    occurrence = next(
        row2
        for row2 in source["view"].linked_occurrences
        if row2["observation_id"] == row["observation_id"]
    )
    with (
        api().prepare_neotoma_preflight_batch(
            source["directory"], **scoped_arguments(source)
        ) as batch,
        pytest.raises(ValueError, match="protected|role|scope"),
    ):
        batch.linked(
            observation_id=row["observation_id"],
            occurrence_id=occurrence["occurrence_id"],
            kind="contact",
            native_id=row["identity"]["native_id"],
        )


@pytest.mark.parametrize("restriction", ["protected", "unmatched", "foreign_database"])
def test_cached_global_facts_still_check_every_recorded_target_owner(
    selected_products: dict[str, Any], monkeypatch: pytest.MonkeyPatch, restriction: str
) -> None:
    from copy import deepcopy

    from ..native_products import rewrite_capture

    source = selected_products
    row = next(row for row in source["view"].observations if row["kind"] == "linked")
    occurrence = source["view"].linked_occurrences[0]

    def mutate(
        document: dict[str, Any], control: dict[str, Any], _directory: Any
    ) -> None:
        target = document["resources"][0]["identity"]
        proof = deepcopy(target["source_proofs"][0])
        if restriction == "protected":
            proof["root_identity"] = deepcopy(
                facet_row(source, dataset=203)["root_identity"]
            )
            proof["root_dataset_id"] = 203
        elif restriction == "unmatched":
            proof["root_identity"]["dataset_id"] = proof["root_dataset_id"] = 999
        else:
            proof["root_identity"]["database"] = "foreign source database"
        target["source_proofs"].append(proof)
        control["targets"][0] = deepcopy(target)

    old = row["source_capture_manifest_sha256"]
    digest = rewrite_capture(source, old, mutate)
    observe(monkeypatch, source)
    with (
        api().prepare_neotoma_preflight_batch(
            source["directory"], **source["kwargs"]
        ) as batch,
        pytest.raises(ValueError, match="owner|role|scope"),
    ):
        batch.linked(
            observation_id=row["observation_id"].replace(old, digest),
            occurrence_id=occurrence["occurrence_id"].replace(old, digest),
            kind="taxon",
            native_id=1,
        )
