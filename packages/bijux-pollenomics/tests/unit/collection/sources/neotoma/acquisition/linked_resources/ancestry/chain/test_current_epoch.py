"""Current epoch duties remain live throughout replay of an older baseline."""

from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry import (
    layers,
    proofs,
)
from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain import (
    derive_neotoma_taxon_ancestry_chain,
)
from bijux_pollenomics.collection.sources.neotoma.capture.receipts import _read

from .native_products import bindings, new_context, observe_native_body_opens


@pytest.mark.parametrize("stage", ["before_baseline", "during_baseline"])
def test_new_current_context_remains_live_inside_recorded_baseline(
    chain_products: dict[str, Any], tmp_path: Path, monkeypatch: Any, stage: str
) -> None:
    context, pin = new_context(chain_products, tmp_path / "current-context")
    sources = bindings(
        chain_products,
        current_context_directory=context,
        expected_current_context_sha256=pin,
    )
    permission = context / "manifest.json"
    changed = False
    original_facts = proofs.source_facts
    opened = observe_native_body_opens(monkeypatch, None)

    def revoke() -> None:
        nonlocal changed
        permission.write_bytes(permission.read_bytes())
        changed = True

    def facts(*args: Any, **kwargs: Any) -> Any:
        if stage == "before_baseline" and not changed:
            revoke()
        return original_facts(*args, **kwargs)

    def read(path: Path, bound: int) -> bytes:
        raw = _read(path, bound)
        if stage == "during_baseline" and path.suffix == ".body" and not changed:
            revoke()
        return raw

    monkeypatch.setattr(layers, "source_facts", facts)
    monkeypatch.setattr(proofs, "_read", read)
    with pytest.raises(ValueError, match="changed"):
        derive_neotoma_taxon_ancestry_chain(
            sources=sources, parent_chain_sha256=None, new_capture_manifest_sha256s=()
        )
    assert changed
    assert len(opened) == int(stage == "during_baseline")


def test_unchanged_distinct_current_context_keeps_original_baseline(
    chain_products: dict[str, Any], tmp_path: Path
) -> None:
    context, pin = new_context(chain_products, tmp_path / "current-context")
    result = derive_neotoma_taxon_ancestry_chain(
        sources=bindings(
            chain_products,
            current_context_directory=context,
            expected_current_context_sha256=pin,
        ),
        parent_chain_sha256=None,
        new_capture_manifest_sha256s=(),
    )
    assert result["baseline"]["seed_taxon_ids"] == [11, 12]
    assert result["summary"]["new_HTTP_requests"] == 0


def test_permission_seals_preserve_the_existing_ancestry_source_profile(
    chain_products: dict[str, Any], tmp_path: Path, monkeypatch: Any
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context.seals import (
        _CurrentContextSeals,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain.models import (
        MAX_FILES,
        MAX_SOURCE_BYTES,
    )
    from bijux_pollenomics.core.filesystem import BoundedInputTree

    source = chain_products["sources"]
    guard = _CurrentContextSeals(
        context_directory=source.context_directory,
        expected_context_sha256=source.expected_context_sha256,
        native_archive_directory=source.native_archive_directory,
        expected_native_archive_sha256=source.expected_native_archive_sha256,
        _max_files=MAX_FILES,
        _max_bytes=MAX_SOURCE_BYTES,
    )
    monkeypatch.setattr(
        BoundedInputTree, "read", lambda *args, **kwargs: pytest.fail("Body opened")
    )
    try:
        for name in ("first", "second"):
            root = tmp_path / name
            root.mkdir()
            with (root / "member.bin").open("wb") as stream:
                stream.truncate(320 * 1024 * 1024)
            guard._seal(root)
        assert sum(guard._members.values()) == 640 * 1024 * 1024
        assert guard._max_files == MAX_FILES
    finally:
        guard._close()


def test_legacy_recorded_limits_keep_outer_epoch_guard(
    chain_products: dict[str, Any], tmp_path: Path, monkeypatch: Any
) -> None:
    from dataclasses import replace
    from inspect import unwrap
    import json
    import os

    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context import (
        load_neotoma_ancillary_context,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources import (
        NeotomaLinkedResourcePlan,
        NeotomaLinkedTarget,
        replay,
    )

    from ....resources.native_payloads import response
    from ...evidence.native_products import capture_legacy_linked_fixture
    from .native_products import chain_products as rebuild_chain

    owner = chain_products["sources"]
    context = load_neotoma_ancillary_context(
        owner.context_directory,
        expected_manifest_sha256=owner.expected_context_sha256,
        native_archive_directory=owner.native_archive_directory,
    )
    work = tmp_path / "legacy-source"
    work.mkdir()

    def fetch(url: str, **_: Any) -> Any:
        route, identity = url.rsplit("/", 2)[-2:]
        key = ("taxon" if route == "taxa" else "publication") + "-" + identity
        return response(url, json.dumps(chain_products["native"][key]).encode())

    legacy = work / "details"
    result = capture_legacy_linked_fixture(
        legacy,
        plan=NeotomaLinkedResourcePlan(
            tuple(sorted(owner.source_facets)),
            (
                NeotomaLinkedTarget("taxon", 11),
                NeotomaLinkedTarget("taxon", 12),
                NeotomaLinkedTarget("publication", 13),
            ),
            include_higher_taxa=True,
        ),
        source_facets=owner.source_facets,
        scope_inputs=context.current_scope_inputs,
        fetch=fetch,
    )
    products = unwrap(rebuild_chain)(
        {
            **chain_products,
            "sources": replace(owner, capture_sources={result.manifest_sha256: legacy}),
        },
        work,
    )
    current, pin = new_context(products, work / "current")
    sources = bindings(
        products, current_context_directory=current, expected_current_context_sha256=pin
    )
    permission = current / "manifest.json"
    original_targets, original_open = replay._targets_for_control, os.open
    changed = False
    late: list[str] = []

    def revoke_after_targets(*args: Any, **kwargs: Any) -> Any:
        nonlocal changed
        value = original_targets(*args, **kwargs)
        permission.write_bytes(permission.read_bytes())
        changed = True
        return value

    def opened(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        descriptor = original_open(path, flags, *args, **kwargs)
        if changed and not flags & os.O_DIRECTORY and str(path).endswith(".body"):
            late.append(str(path))
        return descriptor

    monkeypatch.setattr(replay, "_targets_for_control", revoke_after_targets)
    monkeypatch.setattr(os, "open", opened)
    monkeypatch.setattr(os, "supports_dir_fd", os.supports_dir_fd | {opened})
    with pytest.raises(ValueError, match="changed"):
        derive_neotoma_taxon_ancestry_chain(
            sources=sources, parent_chain_sha256=None, new_capture_manifest_sha256s=()
        )
    assert changed
    assert late == []
