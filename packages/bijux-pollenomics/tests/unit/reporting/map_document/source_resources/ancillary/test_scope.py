"""Independent source anchors and literal native owners precede Atlas metadata joins."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.resource_catalogue import (
    load_neotoma_resource_catalogue,
)
from bijux_pollenomics.reporting.map_document import source_resources as owner
from bijux_pollenomics.reporting.map_document.source_resources.ancillary.projection import (
    load_atlas_ancillary_metadata,
)
from tests.unit.collection.sources.neotoma.reading_observation import (
    capture_opening,
    observe_opening,
)

from .native_federations import (
    ancillary_sources as ancillary_sources,
)
from .native_federations import (
    capsule_inputs as capsule_inputs,
)
from .native_federations import (
    scoped_ancillary_sources as scoped_ancillary_sources,
)
from .native_federations import (
    scoped_inputs as scoped_inputs,
)
from .native_federations import (
    scoped_selection_products as scoped_selection_products,
)
from .native_federations import (
    source_input,
)


@pytest.mark.parametrize("anchor", ["federation", "context", "native", "catalogue"])
def test_independent_anchor_mismatch_refuses(
    ancillary_sources: dict[str, Any], anchor: str
) -> None:
    source = source_input(ancillary_sources)
    dependency, archive = source.ancillary, source.archive
    assert dependency is not None and archive is not None
    if anchor == "federation":
        source = replace(
            source,
            ancillary=replace(dependency, expected_manifest_sha256="0" * 64),
        )
    elif anchor == "context":
        source = replace(
            source,
            ancillary=replace(dependency, expected_context_sha256="0" * 64),
        )
    elif anchor == "native":
        source = replace(
            source, archive=replace(archive, expected_manifest_sha256="0" * 64)
        )
    else:
        source = replace(source, expected_manifest_sha256="0" * 64)
    with pytest.raises(ValueError, match="identity|anchor|SHA|digest"):
        owner.load_atlas_resource_catalogue(source)


@pytest.mark.parametrize(
    "field",
    ["site_id", "collection_unit_id", "dataset_type", "database", "missing_resource"],
)
def test_exact_five_field_native_owner_is_required(
    ancillary_sources: dict[str, Any], field: str
) -> None:
    source = source_input(ancillary_sources)
    raw = load_neotoma_resource_catalogue(
        source.directory, expected_manifest_sha256=source.expected_manifest_sha256
    )
    changed = deepcopy(raw)
    if field == "missing_resource":
        changed["resources"].pop()
    else:
        changed["resources"][0][field] = "different literal owner"
    with pytest.raises(ValueError, match="owner|resource|membership"):
        load_atlas_ancillary_metadata(source, catalogue=changed)


def test_only_outcome_free_native_metadata_bodies_are_opened(
    ancillary_sources: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    source = source_input(ancillary_sources)
    raw = load_neotoma_resource_catalogue(
        source.directory, expected_manifest_sha256=source.expected_manifest_sha256
    )
    native = ancillary_sources["native_archive_directory"]
    allowed = {
        native / "captures" / digest / member["name"]
        for digest, descriptor in raw["capture_descriptors"].items()
        if descriptor["capture_kind"] == "metadata"
        for member in descriptor["files"]
        if member["source_entity"] is True
    }
    opened = []
    original = capture_opening()

    def guarded(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.suffix == ".body":
            assert path in allowed, path
            opened.append(path.name)
        return original(path, *args, **kwargs)

    observe_opening(monkeypatch, guarded)
    view = owner.load_atlas_resource_catalogue(source)
    assert view.ancillary is not None
    assert view.ancillary.entity_body_hashes_verified is False
    assert view.ancillary.source_assessments_replayed is False
    assert opened, (
        "Current owner scope must authenticate native metadata, not trust role text"
    )


@pytest.mark.parametrize(
    "resolver", ["missing", "unknown_anchor", "wrong_directory", "redirected"]
)
def test_scoped_evidence_requires_its_explicit_exact_physical_anchor(
    scoped_ancillary_sources: dict[str, Any], tmp_path: Path, resolver: str
) -> None:
    source = source_input(scoped_ancillary_sources)
    assert owner.load_atlas_resource_catalogue(source).ancillary is not None
    dependency = source.ancillary
    assert dependency is not None and dependency.evidence_sources is not None
    digest, directory = next(iter(dependency.evidence_sources.items()))
    evidence: dict[str, Path] | None = None
    if resolver == "unknown_anchor":
        evidence = {"0" * 64: directory}
    elif resolver == "wrong_directory":
        evidence = {digest: next(iter(dependency.capsule_sources.values()))}
    elif resolver == "redirected":
        alias = tmp_path / "redirected-evidence"
        alias.symlink_to(directory, target_is_directory=True)
        evidence = {digest: alias}
    source = replace(source, ancillary=replace(dependency, evidence_sources=evidence))
    with pytest.raises(
        ValueError, match="evidence|identity|source|anchor|redirect|symlink"
    ):
        owner.load_atlas_resource_catalogue(source)


def test_scoped_projection_opens_zero_facet_linked_or_numerical_entities(
    scoped_ancillary_sources: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    source = source_input(scoped_ancillary_sources)
    raw = load_neotoma_resource_catalogue(
        source.directory, expected_manifest_sha256=source.expected_manifest_sha256
    )
    native = scoped_ancillary_sources["native_archive_directory"]
    allowed = {
        native / "captures" / digest / member["name"]
        for digest, descriptor in raw["capture_descriptors"].items()
        if descriptor["capture_kind"] == "metadata"
        for member in descriptor["files"]
        if member["source_entity"] is True
    }
    opened = []
    original = capture_opening()

    def guarded(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.suffix == ".body":
            assert path in allowed, path
            opened.append(path)
        return original(path, *args, **kwargs)

    observe_opening(monkeypatch, guarded)
    projected = owner.load_atlas_resource_catalogue(source).ancillary
    assert projected is not None and projected.linked_occurrences
    assert projected.entity_body_hashes_verified is False
    assert projected.source_assessments_replayed is False
    assert opened
