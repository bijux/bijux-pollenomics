"""Rehashed occurrence metadata cannot replace an authenticated native pointer."""

from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
    read_neotoma_ancillary_linked_entity,
)

from ..selection.native_products import rewrite_index_row
from .native_products import selected


@pytest.mark.parametrize("field", ["locator", "role", "root"])
def test_forged_scoped_occurrence_refuses_before_pointed_entity_access(
    scoped_selection_products: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    field: str,
) -> None:
    products = scoped_selection_products
    row, occurrence = selected(products)

    def mutate(value: dict[str, Any]) -> None:
        if field == "locator":
            value["evidence_locator"]["row_offset"] += 1
        elif field == "role":
            value["current_use_role"] = "heldout_no_numerical_access"
        else:
            value["root_dataset_id"] = 202

    rewrite_index_row(
        products, "linked_occurrences", occurrence["occurrence_id"], mutate
    )
    opened = []
    original = Path.open

    def observe(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.suffix == ".body" and any(
            root in path.parents
            for root in (products["capsule"], products["facet_capsule"])
        ):
            opened.append(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observe)
    with pytest.raises(ValueError):
        read_neotoma_ancillary_linked_entity(
            products["directory"],
            **products["kwargs"],
            evidence_sources=products["evidence_sources"],
            observation_id=row["observation_id"],
            occurrence_id=occurrence["occurrence_id"],
            kind="taxon",
            native_id=11,
        )
    assert opened == []


def test_legacy_contact_rechecks_protected_pi_outside_all_recorded_roots(
    scoped_selection_products: dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from .native_products import legacy_contact_products

    products = legacy_contact_products(scoped_selection_products, tmp_path)
    row = next(row for row in products["view"].observations if row["kind"] == "linked")
    occurrence = next(
        value
        for value in products["view"].linked_occurrences
        if value["observation_id"] == row["observation_id"]
    )
    assert row["current_use_role"] == "heldout_no_numerical_access"
    assert all(
        value["source_proof"]["root_dataset_id"] in (201, 203)
        for value in products["view"].linked_occurrences
    )

    def weaken(value: dict[str, Any]) -> None:
        value["current_use_role"] = "exposed_development"
        value["access_restrictions"] = []
        value["entity_access_status"] = "requires_selected_source_guard"

    rewrite_index_row(products, "observations", row["observation_id"], weaken)
    opened = []
    original = Path.open

    def observed(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.suffix == ".body" and any(
            root in path.parents
            for root in (products["capsule"], products["facet_capsule"])
        ):
            opened.append(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observed)
    with pytest.raises(ValueError, match="protected current metadata"):
        read_neotoma_ancillary_linked_entity(
            products["directory"],
            **products["kwargs"],
            observation_id=row["observation_id"],
            occurrence_id=occurrence["occurrence_id"],
            kind="contact",
            native_id=900,
        )
    assert opened == []


def test_authenticated_scoped_metadata_cannot_replace_pointed_native_value(
    scoped_selection_products: dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from hashlib import sha256
    import json
    import shutil

    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule import (
        write_neotoma_ancillary_capsule,
    )
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context.validation import (
        load_neotoma_ancillary_context,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources import (
        NeotomaLinkedResourcePlan,
        NeotomaLinkedTarget,
        capture_neotoma_linked_resources,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.models import (
        NeotomaLinkedEvidence,
    )

    from ...acquisition.resources.native_payloads import response
    from .native_products import federation_products, pin

    products = scoped_selection_products
    _, original_state = next(iter(products["evidence_sources"].items()))
    state = tmp_path / "false-native-pointer-state"
    shutil.copytree(original_state, state)
    header = json.loads((state / "evidence-manifest.json").read_bytes())
    for descriptor in header["parts"]:
        old_pin = descriptor["sha256"]
        path = state / "proofs" / f"{old_pin}.json"
        document = json.loads(path.read_bytes())
        changed = False
        for proof in document["proofs"]:
            if proof["target_kind"] == "taxon" and proof["native_id"] == 11:
                proof.update(
                    relation="source_reported_higher_taxon",
                    optional_higher_taxon=True,
                    json_pointer="/data/0/highertaxonid",
                )
                changed = True
        if not changed:
            continue
        raw = json.dumps(document).encode()
        new_pin = sha256(raw).hexdigest()
        path.unlink()
        (state / "proofs" / f"{new_pin}.json").write_bytes(raw)
        descriptor.update(sha256=new_pin, bytes=len(raw))
        for target in header["targets"].values():
            for span in target["proof_ranges"]:
                if span["part_sha256"] == old_pin:
                    span["part_sha256"] = new_pin
    header["targets"]["taxon-11"]["has_direct_proof"] = False
    (state / "evidence-manifest.json").write_text(json.dumps(header))
    state_pin = pin(state / "evidence-manifest.json")
    context = load_neotoma_ancillary_context(
        products["kwargs"]["context_directory"],
        expected_manifest_sha256=products["kwargs"]["expected_context_sha256"],
        native_archive_directory=products["kwargs"]["native_archive_directory"],
    )
    original_row, _ = selected(products)
    native_body = (
        products["capsule"] / original_row["forensic_locator"]["body_relative_path"]
    ).read_bytes()
    capture = tmp_path / "native-pointer-detail-capture"
    captured = capture_neotoma_linked_resources(
        capture,
        plan=NeotomaLinkedResourcePlan(
            tuple(sorted(products["sources"])),
            (NeotomaLinkedTarget("taxon", 11),),
            include_higher_taxa=True,
        ),
        evidence=NeotomaLinkedEvidence(state, state_pin),
        source_facets=products["sources"],
        scope_inputs=context.current_scope_inputs,
        fetch=lambda url, **_: response(url, native_body),
    )
    capsule = tmp_path / "native-pointer-detail-capsule"
    evidence_sources = {state_pin: state}
    write_neotoma_ancillary_capsule(
        capsule,
        facet_captures={},
        linked_captures={captured.manifest_sha256: capture},
        predecessor_facets=products["sources"],
        evidence_sources=evidence_sources,
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
        {**products, "evidence_sources": evidence_sources},
        tmp_path / "native-pointer-federation",
        {
            pin(products["facet_capsule"] / "manifest.json"): products["facet_capsule"],
            pin(capsule / "manifest.json"): capsule,
        },
        scoped=True,
    )
    products["capsule"] = capsule
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
    with pytest.raises(ValueError, match="native field target differs"):
        read_neotoma_ancillary_linked_entity(
            products["directory"],
            **products["kwargs"],
            evidence_sources=evidence_sources,
            observation_id=row["observation_id"],
            occurrence_id=occurrence["occurrence_id"],
            kind="taxon",
            native_id=11,
        )
    assert len(opened) == 1
    assert products["facet_capsule"] in opened[0].parents


@pytest.mark.parametrize(
    "descriptor", [[], None, {"not-a-state-digest": {"schema_version": "invented"}}]
)
def test_malformed_state_metadata_refuses_without_resolving_unselected_parts(
    scoped_selection_products: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    descriptor: Any,
) -> None:
    import json

    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        read_neotoma_ancillary_facet_entity,
    )

    from .native_products import pin

    products = scoped_selection_products
    path = products["directory"] / "manifest.json"
    manifest = json.loads(path.read_bytes())
    manifest["linked_evidence"] = descriptor
    path.write_text(json.dumps(manifest))
    products["kwargs"]["expected_manifest_sha256"] = pin(path)
    row = next(
        value
        for value in products["view"].observations
        if value["kind"] == "facet"
        and value["facet"] == "taxa"
        and value["root_identity"]["dataset_id"] == 201
    )
    original = Path.open
    opened = []

    def observed(source: Path, *args: Any, **kwargs: Any) -> Any:
        assert source.parent.name != "proofs"
        if source.suffix == ".body" and products["facet_capsule"] in source.parents:
            opened.append(source)
        return original(source, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observed)
    with pytest.raises(ValueError, match="evidence|state|descriptor"):
        read_neotoma_ancillary_facet_entity(
            products["directory"],
            **products["kwargs"],
            observation_id=row["observation_id"],
            dataset_id=201,
            facet="taxa",
        )
    assert opened == []


def test_typed_detail_checks_its_native_owner_after_forensic_byte_access(
    scoped_selection_products: dict[str, Any],
    tmp_path: Path,
) -> None:
    import json

    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule import (
        write_neotoma_ancillary_capsule,
    )
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context.validation import (
        load_neotoma_ancillary_context,
    )
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        read_neotoma_ancillary_linked,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources import (
        NeotomaLinkedResourcePlan,
        NeotomaLinkedTarget,
        capture_neotoma_linked_resources,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.models import (
        NeotomaLinkedEvidence,
    )

    from ...acquisition.resources.native_payloads import response
    from .native_products import federation_products, pin

    products = scoped_selection_products
    state_pin, state = next(iter(products["evidence_sources"].items()))
    original_row, _ = selected(products)
    payload = json.loads(
        (
            products["capsule"] / original_row["forensic_locator"]["body_relative_path"]
        ).read_bytes()
    )
    payload["data"][0]["taxonid"] = 99
    native_body = json.dumps(payload).encode()
    context = load_neotoma_ancillary_context(
        products["kwargs"]["context_directory"],
        expected_manifest_sha256=products["kwargs"]["expected_context_sha256"],
        native_archive_directory=products["kwargs"]["native_archive_directory"],
    )
    root = tmp_path / "foreign-native-owner-capture"
    captured = capture_neotoma_linked_resources(
        root,
        plan=NeotomaLinkedResourcePlan(
            tuple(sorted(products["sources"])), (NeotomaLinkedTarget("taxon", 11),)
        ),
        evidence=NeotomaLinkedEvidence(state, state_pin),
        source_facets=products["sources"],
        scope_inputs=context.current_scope_inputs,
        fetch=lambda url, **_: response(url, native_body),
    )
    capsule = tmp_path / "foreign-native-owner-capsule"
    write_neotoma_ancillary_capsule(
        capsule,
        facet_captures={},
        linked_captures={captured.manifest_sha256: root},
        predecessor_facets=products["sources"],
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
        tmp_path / "foreign-native-owner-federation",
        {
            pin(products["facet_capsule"] / "manifest.json"): products["facet_capsule"],
            pin(capsule / "manifest.json"): capsule,
        },
        scoped=True,
    )
    products["capsule"] = capsule
    row, occurrence = selected(products)
    options = {
        **products["kwargs"],
        "evidence_sources": products["evidence_sources"],
        "observation_id": row["observation_id"],
        "occurrence_id": occurrence["occurrence_id"],
        "kind": "taxon",
        "native_id": 11,
    }
    forensic = read_neotoma_ancillary_linked_entity(products["directory"], **options)
    assert forensic["body"] == native_body
    assert "source_payload" not in forensic
    with pytest.raises(ValueError, match="owner differs"):
        read_neotoma_ancillary_linked(products["directory"], **options)
