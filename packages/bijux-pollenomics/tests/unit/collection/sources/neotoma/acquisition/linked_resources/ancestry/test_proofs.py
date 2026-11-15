"""Native child ownership and exact source pointers precede parent claims."""

from typing import Any

import pytest


def test_complete_seed_inventory_retains_both_parent_steps(
    ancestry_products: dict[str, Any],
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry import (
        derive_neotoma_taxon_ancestry,
    )

    document = derive_neotoma_taxon_ancestry(ancestry_products["sources"])
    assert document["authority"]["declared_seed_taxon_ids"] == [11, 12]
    parents = [edge for edge in document["edges"] if edge["relation"] == "taxon_parent"]
    assert [(edge["child_taxon_id"], edge["native_id"]) for edge in parents] == [
        (11, 12),
        (12, 15),
    ]
    assert [edge["json_pointer"] for edge in parents] == ["/data/0/highertaxonid"] * 2
    assert all(edge["native_field_value_verified"] is True for edge in parents)
    frontier = next(
        row for row in document["frontier"] if row["target_key"] == "taxon-15"
    )
    assert frontier["additional_parent_hops_from_seed"] == 1
    assert frontier["GET_authorized"] is False


def test_blocked_slot_is_not_a_received_entity(
    ancestry_products: dict[str, Any],
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry import (
        derive_neotoma_taxon_ancestry,
    )

    document = derive_neotoma_taxon_ancestry(ancestry_products["sources"])
    assert document["source_entity_slot_count"] == 4
    assert document["source_capture_entry_count"] == 4
    assert document["source_entity_attempted_target_count"] == 3
    assert document["source_received_HTTP_entity_count"] == 3


def test_wrong_scoped_evidence_refuses_before_any_detail_body(
    ancestry_products: dict[str, Any], monkeypatch: Any
) -> None:
    from dataclasses import replace
    from hashlib import sha256
    import json
    from pathlib import Path

    import pytest

    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry import (
        derive_neotoma_taxon_ancestry,
    )

    products = ancestry_products
    root = products["capture"]
    control = json.loads((root / "request-plan.json").read_bytes())
    control["source_evidence"]["manifest_sha256"] = "0" * 64
    (root / "request-plan.json").write_text(json.dumps(control))
    manifest = json.loads((root / "capture-manifest.json").read_bytes())
    manifest["source_evidence"]["manifest_sha256"] = "0" * 64
    manifest["plan_sha256"] = sha256(
        (root / "request-plan.json").read_bytes()
    ).hexdigest()
    (root / "capture-manifest.json").write_text(json.dumps(manifest))
    sources = replace(
        products["sources"],
        capture_sources={
            sha256((root / "capture-manifest.json").read_bytes()).hexdigest(): root
        },
    )
    original = Path.open
    opened = []

    def observe(path: Path, *args: Any, **kwargs: Any) -> Any:
        if root in path.parents and path.suffix == ".body":
            opened.append(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observe)
    with pytest.raises(ValueError, match="evidence"):
        derive_neotoma_taxon_ancestry(sources)
    assert opened == []


@pytest.mark.parametrize("ancestry_products", [{"parent11": None}], indirect=True)
def test_explicit_null_is_literal_not_zero_or_biological_root(
    ancestry_products: dict[str, Any],
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry import (
        derive_neotoma_taxon_ancestry,
    )

    document = derive_neotoma_taxon_ancestry(ancestry_products["sources"])
    edge = next(
        edge
        for edge in document["edges"]
        if edge["child_taxon_id"] == 11 and edge["relation"] == "taxon_parent"
    )
    assert edge["native_id"] is None and edge["status"] == "explicit_null"
    assert edge["native_field_value_verified"] is True
    assert all(row["native_id"] != 0 for row in document["taxa"])
    assert all(row["biological_rank_asserted"] is False for row in document["taxa"])


@pytest.mark.parametrize(
    "ancestry_products",
    [
        {"child11": 999},
        {"parent11": True},
        {"parent11": 0},
        {"parent11": "12"},
        {"missing_parent": 11},
    ],
    indirect=True,
)
def test_unqualified_native_seed_cannot_create_parent_edges(
    ancestry_products: dict[str, Any],
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry import (
        derive_neotoma_taxon_ancestry,
    )

    document = derive_neotoma_taxon_ancestry(ancestry_products["sources"])
    seed = next(row for row in document["seeds"] if row["native_id"] == 11)
    assert seed["qualification_status"] == "refused_source_profile"
    assert seed["literal_record_count"] is None
    assert not any(edge["child_taxon_id"] == 11 for edge in document["edges"])
    assert document["summary"]["qualified_seed_sources"] == 1


@pytest.mark.parametrize("ancestry_products", [{"ecological_rows": 12}], indirect=True)
def test_repeated_ecological_records_retain_every_native_pointer(
    ancestry_products: dict[str, Any],
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry import (
        derive_neotoma_taxon_ancestry,
    )

    document = derive_neotoma_taxon_ancestry(ancestry_products["sources"])
    rows = [edge for edge in document["edges"] if edge["child_taxon_id"] == 12]
    assert len(rows) == 4 and len({row["edge_id"] for row in rows}) == 4
    assert {row["json_pointer"] for row in rows} == {
        "/data/0/highertaxonid",
        "/data/0/publicationid",
        "/data/1/highertaxonid",
        "/data/1/publicationid",
    }
    assert document["summary"]["declared_seed_taxa"] == 2
    assert document["summary"]["qualified_literal_taxon_records"] == 3


def test_omitted_eligible_source_target_refuses_before_detail_body(
    ancestry_products: dict[str, Any], monkeypatch: Any
) -> None:
    from dataclasses import replace
    from hashlib import sha256
    import json
    from pathlib import Path

    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry import (
        derive_neotoma_taxon_ancestry,
    )

    root = ancestry_products["capture"]
    control = json.loads((root / "request-plan.json").read_bytes())
    control["targets"] = [
        row for row in control["targets"] if row["target_key"] != "taxon-12"
    ]
    (root / "request-plan.json").write_text(json.dumps(control))
    manifest = json.loads((root / "capture-manifest.json").read_bytes())
    manifest["resources"] = [
        row for row in manifest["resources"] if row["target_key"] != "taxon-12"
    ]
    manifest["plan_sha256"] = sha256(
        (root / "request-plan.json").read_bytes()
    ).hexdigest()
    (root / "capture-manifest.json").write_text(json.dumps(manifest))
    sources = replace(
        ancestry_products["sources"],
        capture_sources={
            sha256((root / "capture-manifest.json").read_bytes()).hexdigest(): root
        },
    )
    original = Path.open
    opened = []

    def observe(path: Path, *args: Any, **kwargs: Any) -> Any:
        if root in path.parents and path.suffix == ".body":
            opened.append(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observe)
    with pytest.raises(ValueError, match="complete eligible source target coverage"):
        derive_neotoma_taxon_ancestry(sources)
    assert opened == []


@pytest.mark.parametrize("member", ["receipt", "body"])
def test_source_byte_drift_cannot_produce_a_derived_layer(
    ancestry_products: dict[str, Any], member: str
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry import (
        derive_neotoma_taxon_ancestry,
    )

    root = ancestry_products["capture"]
    path = root / (
        "taxon-12-current-attempt-1.receipt.json"
        if member == "receipt"
        else "taxon-12-current-attempt-1.body"
    )
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="identity|digest|SHA|receipt"):
        derive_neotoma_taxon_ancestry(ancestry_products["sources"])
