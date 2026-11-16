"""A capture-local proof selection refuses physical drift before returning authority."""

from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.ancillary_store.linked_evidence import (
    metadata,
)
from bijux_pollenomics.collection.sources.neotoma.ancillary_store.linked_evidence.occurrences import (
    verify_scoped_metadata_sources,
)
from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources import (
    evidence as evidence_owner,
)

from .test_metadata_selection import observe_metadata, prepared


@pytest.mark.parametrize(
    "change", ["header_inode", "header_write", "part_inode", "extra", "ancestor_alias"]
)
def test_batch_refuses_namespace_drift_after_authenticated_header_before_proofs(
    ancestry_products: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    change: str,
) -> None:
    document, control, context, sources = prepared(ancestry_products)
    root = ancestry_products["sources"].evidence.directory
    real = evidence_owner._index

    def changed(*args: Any, **kwargs: Any) -> Any:
        result = real(*args, **kwargs)
        member = root / "evidence-manifest.json"
        if change == "part_inode":
            member = next((root / "proofs").iterdir())
        if change in {"header_inode", "part_inode"}:
            replacement = root.parent / "replacement.json"
            replacement.write_bytes(member.read_bytes())
            replacement.replace(member)
        elif change == "header_write":
            member.write_bytes(member.read_bytes())
        elif change == "extra":
            (root / "unowned.json").write_bytes(b"{}")
        else:
            moved = root.with_name("displaced-evidence")
            root.rename(moved)
            root.symlink_to(moved, target_is_directory=True)
        return result

    monkeypatch.setattr(metadata, "_index", changed)
    counts, _ = observe_metadata(monkeypatch, root, ())
    with pytest.raises(ValueError):
        verify_scoped_metadata_sources(document, control, context, sources)
    assert not [name for name in counts if name.startswith("proofs/")]


def test_batch_refuses_equal_bytes_proof_replacement_after_final_part_read(
    ancestry_products: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    document, control, context, sources = prepared(ancestry_products)
    root = ancestry_products["sources"].evidence.directory
    real = evidence_owner._part

    def changed(*args: Any, **kwargs: Any) -> Any:
        result = real(*args, **kwargs)
        member = next((root / "proofs").iterdir())
        replacement = root.parent / "replacement-proof.json"
        replacement.write_bytes(member.read_bytes())
        replacement.replace(member)
        return result

    monkeypatch.setattr(evidence_owner, "_part", changed)
    with pytest.raises(ValueError, match="changed"):
        verify_scoped_metadata_sources(document, control, context, sources)


@pytest.mark.parametrize("alias", ["leaf", "ancestor", "hardlink"])
def test_batch_rejects_metadata_alias_before_header_read(
    ancestry_products: dict[str, Any], monkeypatch: pytest.MonkeyPatch, alias: str
) -> None:
    import os

    document, control, context, sources = prepared(ancestry_products)
    root = ancestry_products["sources"].evidence.directory
    member = root / "evidence-manifest.json"
    if alias == "ancestor":
        moved = root.with_name("aliased-evidence")
        root.rename(moved)
        root.symlink_to(moved, target_is_directory=True)
    else:
        moved = root.parent / "aliased-manifest.json"
        member.rename(moved)
        if alias == "leaf":
            member.symlink_to(moved)
        else:
            os.link(moved, member)
    counts, _ = observe_metadata(monkeypatch, root, ())
    with pytest.raises(ValueError):
        verify_scoped_metadata_sources(document, control, context, sources)
    assert not counts


def test_batch_corrupt_selected_part_cannot_grant_metadata_authority(
    ancestry_products: dict[str, Any],
) -> None:
    document, control, context, sources = prepared(ancestry_products)
    part = next((ancestry_products["sources"].evidence.directory / "proofs").iterdir())
    part.write_bytes(b"x" * part.stat().st_size)
    with pytest.raises(ValueError, match="identity"):
        verify_scoped_metadata_sources(document, control, context, sources)


def test_target_refusal_remains_primary_when_evidence_also_changes(
    ancestry_products: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    from copy import deepcopy

    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.linked_evidence.sources import (
        _restrict_scoped_target,
    )

    document, control, context, sources = prepared(ancestry_products)
    control = deepcopy(control)
    control["targets"][0]["metadata_dependency_count"] += 1
    root = ancestry_products["sources"].evidence.directory
    real = _restrict_scoped_target

    def changed(*args: Any, **kwargs: Any) -> Any:
        try:
            return real(*args, **kwargs)
        finally:
            member = root / "evidence-manifest.json"
            member.write_bytes(member.read_bytes())

    monkeypatch.setattr(metadata, "_restrict_scoped_target", changed)
    with pytest.raises(ValueError, match="correspondence differs"):
        verify_scoped_metadata_sources(document, control, context, sources)
