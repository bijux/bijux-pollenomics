"""A chain never promotes an added parent to the frozen seed inventory."""

from pathlib import Path
from typing import Any

import pytest

from .native_products import bindings


def test_empty_chain_preserves_frozen_baseline_and_uncaptured_parent(
    chain_products: dict[str, Any],
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain import (
        derive_neotoma_taxon_ancestry_chain,
    )

    result = derive_neotoma_taxon_ancestry_chain(
        sources=bindings(chain_products),
        parent_chain_sha256=None,
        new_capture_manifest_sha256s=(),
    )
    assert result["baseline"]["seed_taxon_ids"] == [11, 12]
    assert (
        result["baseline"]["seed_projection_manifest_sha256"]
        == chain_products["baseline_sha256"]
    )
    assert result["summary"]["known_taxon_nodes"] == 3
    assert result["summary"]["declared_seed_taxa"] == 2
    assert result["taxa"] == [] and result["edges"] == []
    assert result["native_body_copies"] == 0


def test_historical_context_is_not_reinterpreted_as_current(
    chain_products: dict[str, Any], tmp_path: Any
) -> None:
    from dataclasses import replace

    import pytest

    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain import (
        derive_neotoma_taxon_ancestry_chain,
    )

    from .native_products import capture_parent, new_context, retain_chain

    historical, historical_pin = new_context(
        chain_products, tmp_path / "historical-context"
    )
    sources = replace(
        bindings(chain_products),
        current_context_directory=historical,
        expected_current_context_sha256=historical_pin,
    )
    sources, capture = capture_parent(
        chain_products, tmp_path / "historical-detail", sources=sources
    )
    sources, parent_pin, parent = retain_chain(
        tmp_path / "historical-graph", sources=sources, parent=None, captures=(capture,)
    )
    original = chain_products["sources"]
    current = replace(
        sources,
        current_context_directory=original.context_directory,
        expected_current_context_sha256=original.expected_context_sha256,
    )
    with pytest.raises(ValueError, match="historical source epoch resolver is missing"):
        derive_neotoma_taxon_ancestry_chain(
            sources=current,
            parent_chain_sha256=parent_pin,
            new_capture_manifest_sha256s=(),
        )
    current = replace(current, context_sources={historical_pin: historical})
    derived = derive_neotoma_taxon_ancestry_chain(
        sources=current, parent_chain_sha256=parent_pin, new_capture_manifest_sha256s=()
    )
    assert (
        derived["current_context_manifest_sha256"] == original.expected_context_sha256
    )
    assert parent["current_context_manifest_sha256"] == historical_pin
    assert (
        parent["known_entity_results"]["taxon-15"]["source"]["utc_start"]
        == "2026-11-15T10:00:00+00:00"
    )
    wrong = replace(
        current, context_sources={historical_pin: original.context_directory}
    )
    with pytest.raises(ValueError, match="identity"):
        derive_neotoma_taxon_ancestry_chain(
            sources=wrong,
            parent_chain_sha256=parent_pin,
            new_capture_manifest_sha256s=(),
        )


@pytest.mark.parametrize("change", ["strengthen", "owner", "population"])
def test_changed_current_roster_refuses_before_any_native_detail(
    chain_products: dict[str, Any], tmp_path: Path, monkeypatch: Any, change: str
) -> None:
    from dataclasses import replace
    import os

    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain import (
        derive_neotoma_taxon_ancestry_chain,
    )

    from .native_products import current_epoch

    context, context_pin, native, native_pin = current_epoch(
        chain_products, tmp_path / "current", change
    )
    sources = replace(
        bindings(chain_products),
        current_context_directory=context,
        expected_current_context_sha256=context_pin,
        current_native_archive_directory=native,
        expected_current_native_archive_sha256=native_pin,
    )
    real_open, opened = os.open, []

    def observe(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        descriptor = real_open(path, flags, *args, **kwargs)
        if str(path).endswith(".body") and Path(path).name.startswith(
            ("taxon-", "publication-")
        ):
            opened.append(path)
        return descriptor

    monkeypatch.setattr(os, "open", observe)
    with pytest.raises(ValueError, match="protected|owner population"):
        derive_neotoma_taxon_ancestry_chain(
            sources=sources, parent_chain_sha256=None, new_capture_manifest_sha256s=()
        )
    assert opened == []


def test_weaker_current_role_keeps_original_stronger_duties(
    chain_products: dict[str, Any], tmp_path: Path
) -> None:
    from dataclasses import replace

    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain import (
        derive_neotoma_taxon_ancestry_chain,
    )

    from .native_products import current_epoch

    context, context_pin, native, native_pin = current_epoch(
        chain_products, tmp_path / "current", "weaken"
    )
    sources = replace(
        bindings(chain_products),
        current_context_directory=context,
        expected_current_context_sha256=context_pin,
        current_native_archive_directory=native,
        expected_current_native_archive_sha256=native_pin,
    )
    document = derive_neotoma_taxon_ancestry_chain(
        sources=sources, parent_chain_sha256=None, new_capture_manifest_sha256s=()
    )
    assert not document["taxa"]
    assert document["summary"]["declared_seed_taxa"] == 2


def test_distinct_historical_native_epoch_requires_both_explicit_resolvers(
    chain_products: dict[str, Any], tmp_path: Path
) -> None:
    from dataclasses import replace

    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain import (
        derive_neotoma_taxon_ancestry_chain,
    )

    from .native_products import capture_parent, current_epoch, retain_chain

    context, context_pin, native, native_pin = current_epoch(
        chain_products, tmp_path / "historical", "weaken"
    )
    sources = replace(
        bindings(chain_products),
        current_context_directory=context,
        expected_current_context_sha256=context_pin,
        current_native_archive_directory=native,
        expected_current_native_archive_sha256=native_pin,
    )
    sources, capture = capture_parent(
        chain_products, tmp_path / "historical-detail", sources=sources
    )
    sources, parent, _ = retain_chain(
        tmp_path / "historical-chain", sources=sources, parent=None, captures=(capture,)
    )
    original = chain_products["sources"]
    current = replace(
        sources,
        current_context_directory=original.context_directory,
        expected_current_context_sha256=original.expected_context_sha256,
        current_native_archive_directory=original.native_archive_directory,
        expected_current_native_archive_sha256=original.expected_native_archive_sha256,
        context_sources={context_pin: context},
    )
    with pytest.raises(ValueError, match="historical source epoch resolver"):
        derive_neotoma_taxon_ancestry_chain(
            sources=current, parent_chain_sha256=parent, new_capture_manifest_sha256s=()
        )
    complete = replace(current, native_archive_sources={native_pin: native})
    result = derive_neotoma_taxon_ancestry_chain(
        sources=complete, parent_chain_sha256=parent, new_capture_manifest_sha256s=()
    )
    assert result["baseline"]["seed_taxon_ids"] == [11, 12]
