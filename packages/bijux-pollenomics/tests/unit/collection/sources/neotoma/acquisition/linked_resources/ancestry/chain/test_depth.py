"""Newly received parents never reset baseline-relative traversal distance."""

from pathlib import Path
from typing import Any

from .native_products import capture_parent, publish_chain


def test_two_layers_keep_original_seeds_and_parent_hops(
    chain_products: dict[str, Any], tmp_path: Path
) -> None:
    sources, first_capture = capture_parent(chain_products, tmp_path / "detail-15")
    sources, first_pin, first = publish_chain(
        tmp_path / "parent-chain", sources=sources, captures=(first_capture,)
    )
    sources, second_capture = capture_parent(
        chain_products,
        tmp_path / "detail-16",
        identity=16,
        parent=None,
        parent_pin=first_pin,
        sources=sources,
    )
    _, _, second = publish_chain(
        tmp_path / "child-chain",
        sources=sources,
        parent=first_pin,
        captures=(second_capture,),
    )
    assert first["baseline"] == second["baseline"]
    assert second["baseline"]["seed_taxon_ids"] == [11, 12]
    node = next(row for row in second["taxa"] if row["native_id"] == 16)
    assert node["declared_seed"] is False
    assert node["additional_parent_hops_from_seed"] == 2
    assert node["source_result"]["recorded_hop"] == 2
    assert second["frontier"] == []
    assert any(row["status"] == "explicit_null" for row in second["edges"])


def test_self_edge_preserves_recorded_pointer_and_stops_refetch(
    chain_products: dict[str, Any], tmp_path: Path
) -> None:
    sources, capture = capture_parent(
        chain_products, tmp_path / "self-detail", parent=15
    )
    _, _, document = publish_chain(
        tmp_path / "self-chain", sources=sources, captures=(capture,)
    )
    assert any(row["status"] == "self_edge" for row in document["edges"])
    assert document["summary"]["declared_seed_taxa"] == 2
    assert document["frontier"] == []


def test_successful_empty_is_retained_result_and_not_refetched(
    chain_products: dict[str, Any], tmp_path: Path
) -> None:
    sources, capture = capture_parent(
        chain_products, tmp_path / "empty-detail", rows=[]
    )
    _, _, document = publish_chain(
        tmp_path / "empty-chain", sources=sources, captures=(capture,)
    )
    assert (
        document["known_entity_results"]["taxon-15"]["qualification_status"]
        == "successful_empty_not_absence"
    )
    assert document["edges"] == [] and document["frontier"] == []


def test_exact_depth32_preserves_depth33_edge_but_blocks_new_body(
    chain_products: dict[str, Any], tmp_path: Path, monkeypatch: Any
) -> None:
    import pytest

    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain import (
        derive_neotoma_taxon_ancestry_chain,
    )

    from .native_products import observe_native_body_opens, retain_chain

    sources, parent_pin = None, None
    for identity in range(15, 47):
        sources, capture = capture_parent(
            chain_products,
            tmp_path / f"detail-{identity}",
            identity=identity,
            parent=identity + 1,
            parent_pin=parent_pin,
            sources=sources,
        )
        sources, parent_pin, document = retain_chain(
            tmp_path / f"graph-{identity}",
            sources=sources,
            parent=parent_pin,
            captures=(capture,),
        )
    frontier = next(
        row for row in document["frontier"] if row["target_key"] == "taxon-47"
    )
    assert frontier["additional_parent_hops_from_seed"] == 33
    assert frontier["status"] == "not_attempted_depth_bound"
    assert document["baseline"]["seed_taxon_ids"] == [11, 12]
    sources, forbidden = capture_parent(
        chain_products,
        tmp_path / "bounded-detail",
        identity=47,
        parent=None,
        parent_pin=parent_pin,
        sources=sources,
    )
    opened = observe_native_body_opens(monkeypatch, None)
    with pytest.raises(ValueError, match="bounded"):
        derive_neotoma_taxon_ancestry_chain(
            sources=sources,
            parent_chain_sha256=parent_pin,
            new_capture_manifest_sha256s=(forbidden,),
        )
    assert opened == []


def test_restricting_initial_depth_records_changed_frontier(
    chain_products: dict[str, Any],
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain import (
        NeotomaTaxonAncestryChainLimits,
        derive_neotoma_taxon_ancestry_chain,
    )

    from .native_products import bindings

    result = derive_neotoma_taxon_ancestry_chain(
        sources=bindings(chain_products),
        parent_chain_sha256=None,
        new_capture_manifest_sha256s=(),
        limits=NeotomaTaxonAncestryChainLimits(max_additional_parent_hops=0),
    )
    assert result["frontier"]
    assert all(
        row["status"] == "not_attempted_depth_bound" for row in result["frontier"]
    )
