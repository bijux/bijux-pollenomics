"""Multiple native captures share one complete source-evidence foundation."""

from dataclasses import replace
import json
import os
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context import (
    load_neotoma_ancillary_context,
)
from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources import (
    NeotomaLinkedResourcePlan,
    NeotomaLinkedTarget,
    capture_neotoma_linked_resources,
)

from ....resources.native_payloads import response


@pytest.fixture
def session_products(
    ancestry_products: dict[str, Any], tmp_path: Path
) -> dict[str, Any]:
    """Capture real synthetic receipts for separate native target groups."""
    original = ancestry_products["sources"]
    context = load_neotoma_ancillary_context(
        original.context_directory,
        expected_manifest_sha256=original.expected_context_sha256,
        native_archive_directory=original.native_archive_directory,
    )
    captures = {}
    for name, targets in [
        ("first-details", (NeotomaLinkedTarget("taxon", 11),)),
        (
            "later-details",
            (NeotomaLinkedTarget("taxon", 12), NeotomaLinkedTarget("publication", 13)),
        ),
    ]:
        directory = tmp_path / name

        def fetch(url: str, **_: Any) -> Any:
            route, identity = url.rsplit("/", 2)[-2:]
            key = ("taxon" if route == "taxa" else "publication") + "-" + identity
            return response(url, json.dumps(ancestry_products["native"][key]).encode())

        result = capture_neotoma_linked_resources(
            directory,
            plan=NeotomaLinkedResourcePlan(
                tuple(sorted(original.source_facets)), targets, include_higher_taxa=True
            ),
            source_facets=original.source_facets,
            scope_inputs=context.current_scope_inputs,
            evidence=original.evidence,
            fetch=fetch,
        )
        captures[result.manifest_sha256] = directory
    return {
        **ancestry_products,
        "sources": replace(original, capture_sources=captures),
        "context": context,
    }


def observe_work(monkeypatch: Any) -> dict[str, Any]:
    """Count real loader invocations, file descriptors and metadata stat operations."""
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources import (
        evidence,
        protocol,
    )

    result: dict[str, Any] = {
        "loader_calls": 0,
        "native_detail_opens": 0,
        "provider_metadata_opens": 0,
        "stat_calls": 0,
        "scandir_calls": 0,
    }
    loader = evidence.load_neotoma_linked_evidence
    opened, stat_call, scanned = os.open, os.stat, os.scandir

    def validate(*args: Any, **kwargs: Any) -> Any:
        result["loader_calls"] += 1
        return loader(*args, **kwargs)

    def open_file(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        descriptor = opened(path, flags, *args, **kwargs)
        name = Path(path).name
        if not flags & os.O_DIRECTORY and name.endswith(".body"):
            field = (
                "native_detail_opens"
                if name.startswith(("taxon-", "publication-", "contact-"))
                else "provider_metadata_opens"
            )
            result[field] += 1
        return descriptor

    def stat_file(*args: Any, **kwargs: Any) -> Any:
        result["stat_calls"] += 1
        return stat_call(*args, **kwargs)

    def scan(*args: Any, **kwargs: Any) -> Any:
        result["scandir_calls"] += 1
        return scanned(*args, **kwargs)

    monkeypatch.setattr(evidence, "load_neotoma_linked_evidence", validate)
    monkeypatch.setattr(protocol, "load_neotoma_linked_evidence", validate)
    monkeypatch.setattr(os, "open", open_file)
    monkeypatch.setattr(os, "stat", stat_file)
    monkeypatch.setattr(os, "scandir", scan)
    monkeypatch.setattr(
        os, "supports_dir_fd", os.supports_dir_fd | {open_file, stat_file}
    )
    return result


def session_arguments(products: dict[str, Any]) -> dict[str, Any]:
    """Select exactly the immutable legacy authority declared by the evidence."""
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.evidence_parts.ownership import (
        _LinkedEvidenceSources,
    )

    original = products["sources"]
    sources = _LinkedEvidenceSources(
        evidence=original.evidence,
        source_facets=original.source_facets,
        capture_sources=original.capture_sources,
        context_directory=original.context_directory,
        expected_context_sha256=original.expected_context_sha256,
        native_archive_directory=original.native_archive_directory,
        expected_native_archive_sha256=original.expected_native_archive_sha256,
    )
    header = json.loads(
        (sources.evidence.directory / "evidence-manifest.json").read_bytes()
    )
    legacy = {
        pin: products["context"].legacy_rosters[pin]
        for pin in header["authority"]["legacy_roster_sha256s"]
    }
    return {
        "source_owner": sources,
        "_max_source_files": 40960,
        "scope_inputs": products["context"].current_scope_inputs,
        "legacy_rosters": legacy,
        "operation": object(),
    }
