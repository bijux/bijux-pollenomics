"""Capture preflight authenticates shared proof metadata once per selection."""

from collections import Counter
from copy import deepcopy
import fcntl
import os
from pathlib import Path
import sys
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule.inventory import (
    _capture,
)
from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context import (
    load_neotoma_ancillary_context,
)
from bijux_pollenomics.collection.sources.neotoma.ancillary_store.linked_evidence.occurrences import (
    verify_scoped_metadata_sources,
)


def prepared(products: dict[str, Any]) -> tuple[Any, Any, Any, dict[str, Path]]:
    """Load the real generated capture and independent current metadata inputs."""
    sources = products["sources"]
    pin, root = next(iter(sources.capture_sources.items()))
    _, document, control = _capture(root, pin, "linked")
    context = load_neotoma_ancillary_context(
        sources.context_directory,
        expected_manifest_sha256=sources.expected_context_sha256,
        native_archive_directory=sources.native_archive_directory,
    )
    assert len(control["targets"]) == 4
    return (
        document,
        control,
        context,
        {sources.evidence.manifest_sha256: sources.evidence.directory},
    )


def observe_metadata(
    monkeypatch: pytest.MonkeyPatch, root: Path, entity_roots: tuple[Path, ...]
) -> tuple[Counter[str], list[int]]:
    """Observe actual descriptor opens, including descriptor-relative tree reads."""
    original = os.open
    counts: Counter[str] = Counter()
    descriptors: list[int] = []

    def opened(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        descriptor = original(path, flags, *args, **kwargs)
        try:
            physical = Path(
                fcntl.fcntl(descriptor, 50, bytes(1024))
                .split(bytes([0]), 1)[0]
                .decode()
                if sys.platform == "darwin"
                else os.readlink(f"/proc/self/fd/{descriptor}")
            )
        except BaseException:
            os.close(descriptor)
            raise
        if not flags & os.O_DIRECTORY and physical.is_relative_to(root):
            counts[physical.relative_to(root).as_posix()] += 1
            descriptors.append(descriptor)
        if str(physical).endswith(".body") and any(
            physical.is_relative_to(parent) for parent in entity_roots
        ):
            os.close(descriptor)
            raise AssertionError("Metadata selection opened a native entity body")
        return descriptor

    monkeypatch.setattr(os, "open", opened)
    monkeypatch.setattr(os, "supports_dir_fd", os.supports_dir_fd | {opened})
    return counts, descriptors


@pytest.mark.parametrize("member", ["evidence-manifest.json", "proof-part"])
def test_multi_target_preflight_reads_each_authenticated_metadata_member_once(
    ancestry_products: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    member: str,
) -> None:
    document, control, context, evidence = prepared(ancestry_products)
    root = ancestry_products["sources"].evidence.directory
    sources = ancestry_products["sources"]
    counts, descriptors = observe_metadata(
        monkeypatch,
        root,
        (*sources.capture_sources.values(), *sources.source_facets.values()),
    )
    assert verify_scoped_metadata_sources(document, control, context, evidence) == next(
        iter(evidence)
    )
    if member == "evidence-manifest.json":
        assert counts[member] == 1
    else:
        assert [
            count for path, count in counts.items() if path.startswith("proofs/")
        ] == [1]
    assert descriptors
    for descriptor in descriptors:
        with pytest.raises(OSError):
            os.fstat(descriptor)


def test_default_selected_reader_reopens_metadata_and_refuses_later_corruption(
    ancestry_products: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.linked_evidence.sources import (
        read_scoped_target,
        scoped_metadata,
    )

    _, control, context, evidence = prepared(ancestry_products)
    source, _, current = scoped_metadata(control, context, evidence)
    target = next(row for row in control["targets"] if row["kind"] == "taxon")
    root = source.directory
    counts, _ = observe_metadata(monkeypatch, root, ())
    first = read_scoped_target(source, target, current, attempted=True)
    assert first["current_use_role"] == "exposed_development"
    assert read_scoped_target(source, target, current, attempted=True) == first
    assert counts["evidence-manifest.json"] == 2
    part = next((root / "proofs").iterdir())
    part.write_bytes(b"x" * part.stat().st_size)
    with pytest.raises(ValueError, match="identity"):
        read_scoped_target(source, target, current, attempted=True)


@pytest.mark.parametrize("change", ["identity", "owner", "protected", "direct"])
def test_batch_keeps_shared_selected_target_restrictions(
    ancestry_products: dict[str, Any], change: str
) -> None:
    document, control, context, evidence = prepared(ancestry_products)
    document, control = deepcopy(document), deepcopy(control)
    if change == "identity":
        control["targets"][0]["metadata_dependency_count"] += 1
    elif change == "owner":
        control["plan"]["source_facet_manifest_sha256s"] = []
    elif change == "protected":
        offset = next(
            i for i, row in enumerate(control["targets"]) if row["kind"] == "contact"
        )
        assert not document["resources"][offset]["attempts"]
        document["resources"][offset]["attempts"] = [{"forbidden": True}]
    else:
        control["plan"]["include_higher_taxa"] = False
    with pytest.raises(ValueError):
        verify_scoped_metadata_sources(document, control, context, evidence)


def test_capture_metadata_preflight_streams_multiple_selected_parts_once(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule.inventory import (
        prepare_capsule_metadata,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources import (
        evidence as owner,
    )

    monkeypatch.setattr(owner, "PART_TARGET_BYTES", 1)
    products = request.getfixturevalue("ancestry_products")
    sources = products["sources"]
    root = sources.evidence.directory
    parts = list((root / "proofs").iterdir())
    assert len(parts) > 1
    counts, _ = observe_metadata(
        monkeypatch,
        root,
        (*sources.capture_sources.values(), *sources.source_facets.values()),
    )
    result = prepare_capsule_metadata(
        context_directory=sources.context_directory,
        expected_context_sha256=sources.expected_context_sha256,
        native_archive_directory=sources.native_archive_directory,
        facet_captures={},
        linked_captures=sources.capture_sources,
        predecessor_facets=sources.source_facets,
        evidence_sources={sources.evidence.manifest_sha256: root},
    )
    assert len(result.linked_sources) == 1
    assert counts["evidence-manifest.json"] == 1
    assert len([key for key in counts if key.startswith("proofs/")]) == len(parts)
    assert all(value == 1 for value in counts.values())
