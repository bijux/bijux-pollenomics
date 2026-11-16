"""Source-backed synthetic baseline products without provider access."""

from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def chain_products(ancestry_products: dict[str, Any], tmp_path: Path) -> dict[str, Any]:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry import (
        derive_neotoma_taxon_ancestry,
        publish_neotoma_taxon_ancestry,
    )

    sources = ancestry_products["sources"]
    baseline = tmp_path / "baseline"
    document = derive_neotoma_taxon_ancestry(sources)
    publish_neotoma_taxon_ancestry(baseline, document=document, sources=sources)
    return {
        **ancestry_products,
        "baseline": baseline,
        "baseline_document": document,
        "baseline_sha256": sha256(
            (baseline / "manifest.json").read_bytes()
        ).hexdigest(),
    }


def bindings(products: dict[str, Any], **changes: Any) -> Any:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain import (
        NeotomaTaxonAncestryChainSources,
    )

    original = products["sources"]
    values = {
        "recorded_baseline_sources": original,
        "baseline_projection_directory": products["baseline"],
        "expected_baseline_projection_sha256": products["baseline_sha256"],
        "chain_sources": {},
        "ancestry_capture_sources": {},
        "current_context_directory": original.context_directory,
        "expected_current_context_sha256": original.expected_context_sha256,
        "current_native_archive_directory": original.native_archive_directory,
        "expected_current_native_archive_sha256": original.expected_native_archive_sha256,
    }
    return NeotomaTaxonAncestryChainSources(**{**values, **changes})


def capture_parent(
    products: dict[str, Any],
    directory: Path,
    *,
    identity: int = 15,
    parent: int | None = 16,
    parent_pin: str | None = None,
    sources: Any = None,
    rows: list[dict[str, Any]] | None = None,
) -> tuple[Any, str]:
    """Retain generated HTTP bytes and real receipts without invoking transport."""
    from dataclasses import replace

    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain.authority import (
        ChainOperation,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain.models import (
        CAPTURE_SCHEMA,
        DEFAULT_LIMITS,
        MAX_ENTITY_BYTES,
        SCHEMA,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.protocol import (
        request_for,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.receipts import (
        _retain_http_response,
    )
    from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive.files import (
        encoded_json,
    )

    from ....resources.native_payloads import response

    sources = sources or bindings(products)
    with ChainOperation(sources) as operation:
        state, graph = operation.resolve(parent_pin, DEFAULT_LIMITS)
    key = f"taxon-{identity}"
    node = next(row for row in graph["frontier"] if row["target_key"] == key)
    witness = next(
        edge
        for edge in state["edges"].values()
        if edge["target_kind"] == "taxon"
        and edge["native_id"] == identity
        and edge["child_taxon_id"] != identity
    )
    import copy
    import json

    native = copy.deepcopy(products["native"]["taxon-11"])
    record = native["data"][0]
    record.update(taxonid=identity, highertaxonid=parent)
    native["data"] = rows if rows is not None else [record]
    directory.mkdir()
    target = {"target_key": key, "kind": "taxon", "native_id": identity}
    request = request_for(target, 1)
    attempt, receipt = _retain_http_response(
        directory,
        request,
        response(request.url, json.dumps(native).encode()),
        "2026-11-15T10:00:00+00:00",
    )
    entry = {
        **target,
        "root_dataset_ids": node["current_root_dataset_ids"],
        "recorded_role": node["current_use_role"],
        "recorded_hop": node["additional_parent_hops_from_seed"],
        "witness_edge_id": witness["edge_id"],
        "terminal_status": "received_complete_unqualified_linked_resource",
        "attempts": [attempt],
    }
    plan = {
        "schema_version": CAPTURE_SCHEMA,
        "source_ancestry": {
            "schema_version": SCHEMA
            if parent_pin
            else products["baseline_document"]["schema_version"],
            "manifest_sha256": parent_pin or products["baseline_sha256"],
        },
        "current_context_manifest_sha256": sources.expected_current_context_sha256,
        "current_native_archive_manifest_sha256": sources.expected_current_native_archive_sha256,
        "frontier_target_keys": [key],
        "limits": {"max_response_bytes": MAX_ENTITY_BYTES, "max_attempts": 1},
    }
    plan_raw = encoded_json(plan)
    (directory / "request-plan.json").write_bytes(plan_raw)
    manifest = {
        "schema_version": CAPTURE_SCHEMA,
        "status": "closed",
        "plan_sha256": sha256(plan_raw).hexdigest(),
        "resources": [entry],
        "request_count": 1,
        "response_bytes": receipt["retained_body_bytes"],
        "scientific_admission": "not_asserted",
    }
    raw = encoded_json(manifest)
    (directory / "capture-manifest.json").write_bytes(raw)
    pin = sha256(raw).hexdigest()
    return replace(
        sources,
        ancestry_capture_sources={**sources.ancestry_capture_sources, pin: directory},
    ), pin


def publish_chain(
    directory: Path,
    *,
    sources: Any,
    parent: str | None = None,
    captures: tuple[str, ...] = (),
) -> tuple[Any, str, dict[str, Any]]:
    """Publish synthetic source-derived deltas with a fresh portable resolver."""
    from dataclasses import replace

    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain import (
        derive_neotoma_taxon_ancestry_chain,
        publish_neotoma_taxon_ancestry_chain,
    )

    document = derive_neotoma_taxon_ancestry_chain(
        sources=sources,
        parent_chain_sha256=parent,
        new_capture_manifest_sha256s=captures,
    )
    publish_neotoma_taxon_ancestry_chain(directory, document=document, sources=sources)
    pin = sha256((directory / "manifest.json").read_bytes()).hexdigest()
    return (
        replace(sources, chain_sources={**sources.chain_sources, pin: directory}),
        pin,
        document,
    )


def retain_chain(
    directory: Path, *, sources: Any, parent: str | None, captures: tuple[str, ...]
) -> tuple[Any, str, dict[str, Any]]:
    """Retain generated chain bytes to exercise long source closures economically."""
    from dataclasses import replace

    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry import (
        storage,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain import (
        derive_neotoma_taxon_ancestry_chain,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain.models import (
        COLLECTIONS,
        SCHEMA,
    )
    from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive.files import (
        encoded_json,
    )

    document = derive_neotoma_taxon_ancestry_chain(
        sources=sources,
        parent_chain_sha256=parent,
        new_capture_manifest_sha256s=captures,
    )
    manifest, buffers = storage._pack(document, collections=COLLECTIONS, schema=SCHEMA)
    directory.mkdir()
    for name, raw in buffers.items():
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    raw = encoded_json(manifest)
    (directory / "manifest.json").write_bytes(raw)
    pin = sha256(raw).hexdigest()
    return (
        replace(sources, chain_sources={**sources.chain_sources, pin: directory}),
        pin,
        document,
    )


def new_context(products: dict[str, Any], directory: Path) -> tuple[Path, str]:
    """Publish a genuine distinct metadata context against the same native owner."""
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store import (
        write_neotoma_ancillary_context,
    )
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context import (
        load_neotoma_ancillary_context,
    )

    original = products["sources"]
    context = load_neotoma_ancillary_context(
        original.context_directory,
        expected_manifest_sha256=original.expected_context_sha256,
        native_archive_directory=original.native_archive_directory,
    )
    exposure = directory.with_suffix(".json")
    exposure.write_text('{"status":"independent_synthetic_source_review"}')
    write_neotoma_ancillary_context(
        directory,
        native_archive_directory=original.native_archive_directory,
        expected_native_archive_sha256=original.expected_native_archive_sha256,
        legacy_rosters=context.legacy_rosters,
        exposure_authority=exposure,
        expected_exposure_authority_sha256=sha256(exposure.read_bytes()).hexdigest(),
    )
    return directory, sha256((directory / "manifest.json").read_bytes()).hexdigest()


def observe_native_body_opens(monkeypatch: Any, name: str | None) -> list[int]:
    """Observe the real descriptor boundary for both legacy and tree readers."""
    import os

    original = os.open
    opened: list[int] = []

    def observe(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        descriptor = original(path, flags, *args, **kwargs)
        leaf = Path(path).name
        selected = (
            leaf == name
            if name is not None
            else leaf.startswith(("taxon-", "publication-", "contact-"))
            and leaf.endswith(".body")
        )
        if selected and not flags & os.O_DIRECTORY:
            opened.append(descriptor)
        return descriptor

    monkeypatch.setattr(os, "open", observe)
    return opened


def change_capture(sources: Any, old: str, change: Any) -> tuple[Any, str]:
    """Change synthetic controls and update only their explicitly supplied pin."""
    from dataclasses import replace
    import json

    from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive.files import (
        encoded_json,
    )

    root = sources.ancestry_capture_sources[old]
    manifest = json.loads((root / "capture-manifest.json").read_bytes())
    plan = json.loads((root / "request-plan.json").read_bytes())
    change(manifest, plan)
    plan_raw = encoded_json(plan)
    (root / "request-plan.json").write_bytes(plan_raw)
    manifest["plan_sha256"] = sha256(plan_raw).hexdigest()
    raw = encoded_json(manifest)
    (root / "capture-manifest.json").write_bytes(raw)
    pin = sha256(raw).hexdigest()
    captures = dict(sources.ancestry_capture_sources)
    captures.pop(old)
    return replace(sources, ancestry_capture_sources={**captures, pin: root}), pin


def current_epoch(
    products: dict[str, Any], directory: Path, change: str
) -> tuple[Path, str, Path, str]:
    """Construct independent receipt-backed current roster/owner changes."""
    from dataclasses import replace

    from bijux_pollenomics.collection.sources.neotoma import (
        resource_catalogue as catalogue,
    )
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store import (
        write_neotoma_ancillary_context,
    )
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context import (
        load_neotoma_ancillary_context,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.authority import (
        authenticate_linked_root_metadata,
    )
    from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive import (
        write_neotoma_source_archive,
    )

    from ....facets.parent_scope.native_sources import source_inputs

    original = products["sources"]
    context = load_neotoma_ancillary_context(
        original.context_directory,
        expected_manifest_sha256=original.expected_context_sha256,
        native_archive_directory=original.native_archive_directory,
    )
    roster, scope = next(iter(context.current_scope_inputs.items()))
    roots = authenticate_linked_root_metadata(
        expected_roster_sha256=roster, scope=scope
    )["resources"]
    resources = tuple(
        replace(
            row,
            exposure_role="heldout_no_numerical_access"
            if change == "strengthen"
            else "development_resource_discovery",
        )
        if row.dataset_id == 203 and change in {"strengthen", "weaken"}
        else replace(row, site_id=15)
        if row.dataset_id == 203 and change == "owner"
        else row
        for row in roots
        if not (row.dataset_id == 202 and change == "population")
    )
    directory.mkdir()
    plan, fresh = source_inputs(directory / "source-inputs", resources)
    public = directory / "catalogue"
    logical = catalogue.build_neotoma_resource_catalogue(
        roster_path=fresh.roster_path,
        expected_roster_sha256=plan.roster_sha256,
        metadata_captures=fresh.metadata_captures,
        resource_captures={},
    )
    catalogue.write_neotoma_resource_catalogue(
        public,
        catalogue=logical,
        capture_sources=fresh.metadata_captures,
        roster_path=fresh.roster_path,
    )
    native = directory / "native"
    write_neotoma_source_archive(
        native,
        catalogue_directory=public,
        expected_catalogue_manifest_sha256=sha256(
            (public / "manifest.json").read_bytes()
        ).hexdigest(),
        capture_sources=fresh.metadata_captures,
    )
    native_pin = sha256((native / "manifest.json").read_bytes()).hexdigest()
    authority = directory / "authority.json"
    authority.write_text('{"status":"independent_synthetic_review"}')
    target = directory / "context"
    write_neotoma_ancillary_context(
        target,
        native_archive_directory=native,
        expected_native_archive_sha256=native_pin,
        legacy_rosters=context.legacy_rosters,
        exposure_authority=authority,
        expected_exposure_authority_sha256=sha256(authority.read_bytes()).hexdigest(),
    )
    return (
        target,
        sha256((target / "manifest.json").read_bytes()).hexdigest(),
        native,
        native_pin,
    )
