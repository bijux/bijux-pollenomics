"""Supporting metadata preserves independent authority without opening source entities."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, fields, replace
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context_resources import (
    read_neotoma_context_resource_inventory,
)
from bijux_pollenomics.collection.sources.neotoma.ancillary_store.reference_tables import (
    read_neotoma_reference_archive_inventory,
)
from bijux_pollenomics.collection.sources.neotoma.ancillary_store.unit_metadata import (
    read_neotoma_unit_metadata_inventory,
)
from bijux_pollenomics.reporting.map_document import source_resources as owner
from bijux_pollenomics.reporting.map_document.static_assets.source_resources import (
    build_source_resource_payloads,
)

from .native_archives import (
    reference_archive as reference_archive,
)
from .native_archives import (
    reference_source as reference_source,
)
from .native_archives import (
    second_reference_archive as second_reference_archive,
)
from .native_archives import (
    site_context_products as site_context_products,
)
from .native_archives import (
    supporting_sources as supporting_sources,
)
from .native_archives import (
    unit_products as unit_products,
)

KINDS = ("unit_metadata", "reference_tables", "context_resources")


def encoded(value: Any) -> str:
    return json.dumps(asdict(value), sort_keys=True, separators=(",", ":"))


def inventory(inputs: dict[str, Any]) -> Any:
    source, reference, kind = inputs["source"], inputs["reference"], inputs["kind"]
    assert source.ancillary is not None and source.archive is not None
    kwargs = {"expected_manifest_sha256": reference.expected_manifest_sha256}
    if kind == "reference_tables":
        return read_neotoma_reference_archive_inventory(reference.directory, **kwargs)
    if kind == "unit_metadata":
        return read_neotoma_unit_metadata_inventory(
            reference.directory,
            **kwargs,
            context_directory=source.ancillary.context_directory,
            expected_context_sha256=source.ancillary.expected_context_sha256,
            native_archive_directory=source.archive.directory,
            expected_native_archive_sha256=source.archive.expected_manifest_sha256,
        )
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context_resources import (
        NeotomaContextArchiveBindings,
    )

    return read_neotoma_context_resource_inventory(
        reference.directory,
        **kwargs,
        original=reference.original,
        current=NeotomaContextArchiveBindings(
            source.ancillary.context_directory,
            source.ancillary.expected_context_sha256,
            source.archive.directory,
            source.archive.expected_manifest_sha256,
        ),
    )


@pytest.mark.parametrize("kind", KINDS)
def test_supporting_inventory_is_exact_detached_metadata_with_no_entity_reads(
    supporting_sources: Callable[..., dict[str, Any]],
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
) -> None:
    inputs = supporting_sources(kind)
    source = inputs["source"]
    expected = inventory(inputs)
    # Native catalogue metadata is the only source body allowed by the federation.
    native = source.archive.directory
    from bijux_pollenomics.collection.sources.neotoma.resource_catalogue import (
        load_neotoma_resource_catalogue,
    )

    compact = load_neotoma_resource_catalogue(
        source.directory, expected_manifest_sha256=source.expected_manifest_sha256
    )
    allowed = {
        native / "captures" / digest / member["name"]
        for digest, descriptor in compact["capture_descriptors"].items()
        if descriptor["capture_kind"] == "metadata"
        for member in descriptor["files"]
        if member["source_entity"] is True
    }
    original_open = Path.open
    opened: list[Path] = []

    def guarded(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.suffix == ".body":
            assert path in allowed, path
            opened.append(path)
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded)
    projected = owner.load_atlas_resource_catalogue(source).ancillary
    assert isinstance(projected, owner.AtlasAncillarySupportingMetadata)
    assert len(projected.supporting_archives) == 1
    assert isinstance(projected, owner.AtlasAncillarySupportingMetadata)
    record = projected.supporting_archives[0]
    assert record["archive_kind"] == kind
    assert record["manifest"] == expected.manifest
    assert record["index"] == expected.index
    assert (
        record["archive_manifest_sha256"]
        == inputs["reference"].expected_manifest_sha256
    )
    for key in (
        "entity_body_hashes_verified",
        "native_profiles_verified",
        "source_assessments_replayed",
    ):
        assert record[key] is False
    assert record["scientific_admission"] == "not_asserted"
    assert record["selected_source_authority"] == "not_provided_by_metadata_projection"
    assert "href" not in encoded(projected)
    assert str(inputs["directory"]) not in encoded(projected)
    assert str(source.ancillary.context_directory) not in encoded(projected)
    assert opened
    record["index"]["detached"] = True
    assert "detached" not in expected.index


@pytest.mark.parametrize("kind", KINDS)
def test_supporting_archives_preserve_all_native_populations_and_legacy_bytes(
    supporting_sources: Callable[..., dict[str, Any]], kind: str
) -> None:
    source = supporting_sources(kind)["source"]
    assert source.ancillary is not None
    plain = replace(source, ancillary=replace(source.ancillary, archives=None))
    baseline = owner.load_atlas_resource_catalogue(plain)
    configured = owner.load_atlas_resource_catalogue(source)
    assert type(baseline.ancillary) is owner.AtlasAncillaryMetadata
    assert "supporting_archives" not in asdict(baseline.ancillary)
    assert baseline.ancillary is not None and configured.ancillary is not None
    for field in fields(baseline.ancillary):
        assert getattr(baseline.ancillary, field.name) == getattr(
            configured.ancillary, field.name
        )
    for field in fields(baseline):
        if field.name != "ancillary":
            assert getattr(baseline, field.name) == getattr(configured, field.name)
    assert build_source_resource_payloads(baseline) == build_source_resource_payloads(
        configured
    )
    empty = replace(
        source,
        ancillary=replace(
            source.ancillary, archives=owner.AtlasAncillaryArchivesInput()
        ),
    )
    assert encoded(owner.load_atlas_resource_catalogue(empty)) == encoded(baseline)


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("defect", ["digest", "redirected"])
def test_supporting_independent_archive_anchor_refuses_after_real_precondition(
    supporting_sources: Callable[..., dict[str, Any]],
    tmp_path: Path,
    kind: str,
    defect: str,
) -> None:
    inputs = supporting_sources(kind)
    source, reference = inputs["source"], inputs["reference"]
    assert owner.load_atlas_resource_catalogue(source).ancillary is not None
    if defect == "digest":
        reference = replace(reference, expected_manifest_sha256="0" * 64)
    else:
        alias = tmp_path / "redirected-support"
        alias.symlink_to(reference.directory, target_is_directory=True)
        reference = replace(reference, directory=alias)
    dependency = replace(
        source.ancillary,
        archives=owner.AtlasAncillaryArchivesInput(**{kind: (reference,)}),
    )
    with pytest.raises(
        ValueError, match="anchor|digest|identity|physical|symlink|redirect"
    ):
        owner.load_atlas_resource_catalogue(replace(source, ancillary=dependency))


def test_original_and_changed_current_scope_are_preserved_without_admission(
    supporting_sources: Callable[..., dict[str, Any]],
) -> None:
    inputs = supporting_sources("context_resources", changed=True)
    projected = owner.load_atlas_resource_catalogue(inputs["source"]).ancillary
    assert isinstance(projected, owner.AtlasAncillarySupportingMetadata)
    record = projected.supporting_archives[0]
    scopes = record["scope_accounts"]
    assert any(row["original_role"] != row["current_role"] for row in scopes)
    assert any("blocked" in row["current_access"] for row in scopes)
    assert record["entity_body_hashes_verified"] is False


@pytest.mark.parametrize("reference_source", ["incomplete"], indirect=True)
def test_incomplete_global_reference_prefix_stays_forensic_and_unrelated_to_sites(
    supporting_sources: Callable[..., dict[str, Any]],
) -> None:
    inputs = supporting_sources("reference_tables")
    projected = owner.load_atlas_resource_catalogue(inputs["source"]).ancillary
    assert isinstance(projected, owner.AtlasAncillarySupportingMetadata)
    record = projected.supporting_archives[0]
    assert record["manifest"]["table_population_complete"] is False
    assert any(
        row["terminal_status"] == "refused_incomplete_body"
        for row in record["index"]["tables"]
    )
    assert record["scope_accounts"] == []
    assert record["entity_body_hashes_verified"] is False


@pytest.mark.parametrize("invalid", [True, "1" * 63, "A" * 64, None])
def test_supporting_input_requires_literal_independent_anchor(
    tmp_path: Path, invalid: Any
) -> None:
    with pytest.raises(ValueError):
        owner.AtlasSourceArchiveInput(tmp_path, invalid)


def test_supporting_families_require_exact_typed_archive_owners(tmp_path: Path) -> None:
    invalid: Any = {}
    with pytest.raises(ValueError):
        owner.AtlasAncillaryArchivesInput(unit_metadata=invalid)
    reference = owner.AtlasSourceArchiveInput(tmp_path, "1" * 64)
    invalid = reference
    with pytest.raises(ValueError):
        owner.AtlasAncillaryArchivesInput(context_resources=(invalid,))


def test_all_reference_epochs_are_preserved_without_deduplicating_source_history(
    supporting_sources: Callable[..., dict[str, Any]],
    second_reference_archive: dict[str, Any],
) -> None:
    inputs = supporting_sources("reference_tables")
    source, first = inputs["source"], inputs["reference"]
    second = owner.AtlasSourceArchiveInput(
        second_reference_archive["directory"], second_reference_archive["sha256"]
    )
    assert first.expected_manifest_sha256 != second.expected_manifest_sha256
    configured = replace(
        source,
        ancillary=replace(
            source.ancillary,
            archives=owner.AtlasAncillaryArchivesInput(
                reference_tables=(first, second)
            ),
        ),
    )
    projected = owner.load_atlas_resource_catalogue(configured).ancillary
    assert isinstance(projected, owner.AtlasAncillarySupportingMetadata)
    assert [
        row["archive_manifest_sha256"] for row in projected.supporting_archives
    ] == [first.expected_manifest_sha256, second.expected_manifest_sha256]
    assert all(
        row["entity_body_hashes_verified"] is False
        for row in projected.supporting_archives
    )
    assert (
        projected.supporting_archives[0]["index"]
        != projected.supporting_archives[1]["index"]
    )


@pytest.mark.parametrize("kind", KINDS)
def test_duplicate_archive_anchors_and_mutable_populations_are_refused(
    tmp_path: Path, kind: str
) -> None:
    reference = owner.AtlasSourceArchiveInput(tmp_path, "1" * 64)
    if kind == "context_resources":
        from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context_resources import (
            NeotomaContextArchiveBindings,
        )

        reference = owner.AtlasContextArchiveInput(
            tmp_path,
            "1" * 64,
            NeotomaContextArchiveBindings(tmp_path, "2" * 64, tmp_path, "3" * 64),
        )
    values: dict[str, Any] = {kind: (reference, reference)}
    with pytest.raises(ValueError, match="unique"):
        owner.AtlasAncillaryArchivesInput(**values)
    values = {kind: [reference]}
    with pytest.raises(ValueError, match="tuple"):
        owner.AtlasAncillaryArchivesInput(**values)


@pytest.mark.parametrize("defect", ["owner", "path", "digest"])
def test_original_context_authority_is_explicit_and_not_coerced(
    tmp_path: Path, defect: str
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context_resources import (
        NeotomaContextArchiveBindings,
    )

    original: Any = NeotomaContextArchiveBindings(
        tmp_path, "2" * 64, tmp_path, "3" * 64
    )
    if defect == "owner":
        original = {}
    elif defect == "path":
        original = replace(original, context_directory=str(tmp_path))
    else:
        original = replace(original, expected_context_sha256="A" * 64)
    with pytest.raises(ValueError, match="original"):
        owner.AtlasContextArchiveInput(tmp_path, "1" * 64, original)


def test_context_input_annotation_resolves_to_the_native_binding_owner() -> None:
    from typing import get_type_hints

    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context_resources import (
        NeotomaContextArchiveBindings,
    )

    assert (
        get_type_hints(owner.AtlasContextArchiveInput)["original"]
        is NeotomaContextArchiveBindings
    )
