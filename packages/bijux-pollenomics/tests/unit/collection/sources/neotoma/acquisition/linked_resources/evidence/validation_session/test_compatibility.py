"""Public replay remains fresh and publication uses independent derivation sessions."""

from pathlib import Path
from typing import Any

from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources import (
    ancestry,
    replay_neotoma_linked_resources,
)
from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry import (
    derive_neotoma_taxon_ancestry,
    publish_neotoma_taxon_ancestry,
)

from .native_products import observe_work, session_arguments


def test_public_replays_authenticate_fresh_evidence_every_call(
    session_products: dict[str, Any], monkeypatch: Any
) -> None:
    arguments = session_arguments(session_products)
    owner = arguments["source_owner"]
    pin, directory = next(iter(owner.capture_sources.items()))
    work = observe_work(monkeypatch)
    for _ in range(2):
        replay_neotoma_linked_resources(
            directory,
            expected_manifest_sha256=pin,
            source_facets=owner.source_facets,
            evidence=owner.evidence,
            scope_inputs=arguments["scope_inputs"],
            legacy_rosters=arguments["legacy_rosters"],
        )
    assert work["loader_calls"] == 2
    assert work["native_detail_opens"] == 2


def test_session_and_fresh_replay_derivations_are_exactly_equal(
    session_products: dict[str, Any], monkeypatch: Any
) -> None:
    owner = session_products["sources"]
    batched = derive_neotoma_taxon_ancestry(owner)
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.replay import (
        _replay_linked_resources,
    )

    original = _replay_linked_resources

    def fresh(*args: Any, **kwargs: Any) -> Any:
        kwargs.pop("_session")
        kwargs.pop("_operation")
        return original(*args, **kwargs)

    monkeypatch.setattr(ancestry.proofs, "_replay_linked_resources", fresh)
    assert derive_neotoma_taxon_ancestry(owner) == batched


def test_publisher_uses_three_independent_full_validation_sessions(
    session_products: dict[str, Any], tmp_path: Path, monkeypatch: Any
) -> None:
    owner = session_products["sources"]
    document = derive_neotoma_taxon_ancestry(owner)
    work = observe_work(monkeypatch)
    publish_neotoma_taxon_ancestry(
        tmp_path / "published-ancestry", document=document, sources=owner
    )
    assert work["loader_calls"] == 3
    assert work["native_detail_opens"] == 33
