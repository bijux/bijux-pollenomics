"""Bounded catalogue storage retains the complete logical source projection."""

from __future__ import annotations

from collections.abc import Callable
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma import resource_catalogue as api


def _publish(
    inputs: dict[str, Any], output: Path
) -> tuple[dict[str, Any], str, dict[str, Path]]:
    catalogue = api.build_neotoma_resource_catalogue(**inputs)
    sources = {**inputs["metadata_captures"], **inputs["resource_captures"]}
    api.write_neotoma_resource_catalogue(
        output,
        catalogue=catalogue,
        capture_sources=sources,
        roster_path=inputs["roster_path"],
        partition_collections=True,
    )
    return (
        catalogue,
        sha256((output / "manifest.json").read_bytes()).hexdigest(),
        sources,
    )


def test_partitioned_catalogue_roundtrip_native_readers_and_shared_archive(
    catalogue_sources: Callable[..., dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.resource_catalogue import storage
    from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive import (
        write_neotoma_source_archive,
    )

    monkeypatch.setattr(storage, "TARGET_PART_BYTES", 1000)
    output = tmp_path / "partitioned"
    original, digest, sources = _publish(
        catalogue_sources(auxiliary_type="unregistered native proxy"), output
    )
    assert (
        api.load_neotoma_resource_catalogue(
            output,
            expected_manifest_sha256=digest,
            capture_sources=sources,
            require_source_bodies=True,
        )
        == original
    )
    document = json.loads((output / "catalogue.json").read_bytes())
    assert "resources" not in document
    assert len(document["collections"]["resources"]["parts"]) == 4
    assert all(
        path.stat().st_size <= 3 * 1024 * 1024
        for path in (output / "parts").rglob("*.json")
    )
    result = api.read_neotoma_catalogue_source_entity(
        output,
        expected_manifest_sha256=digest,
        dataset_id=202,
        version="current",
        capture_sources=sources,
    )
    assert result["acquisition_status"] == "unsupported_dataset_type"
    qualified = api.read_neotoma_catalogue_resource(
        output,
        expected_manifest_sha256=digest,
        dataset_id=201,
        version="current",
        capture_sources=sources,
    )
    assert qualified["qualification_status"] == "parsed_native"
    archive = write_neotoma_source_archive(
        tmp_path / "portable",
        catalogue_directory=output,
        expected_catalogue_manifest_sha256=digest,
        capture_sources=sources,
    )
    assert archive["catalogue_manifest_sha256"] == digest


@pytest.mark.parametrize(
    "mutation",
    ["boolean_count", "duplicate_part", "unknown_collection", "outside_part"],
)
def test_rehashed_partition_index_cannot_forge_closed_collection_membership(
    catalogue_sources: Callable[..., dict[str, Any]],
    tmp_path: Path,
    mutation: str,
) -> None:
    output = tmp_path / "partitioned"
    _, _, _ = _publish(catalogue_sources(), output)
    path = output / "catalogue.json"
    document = json.loads(path.read_bytes())
    collection = document["collections"]["resources"]
    if mutation == "boolean_count":
        collection["row_count"] = True
    elif mutation == "duplicate_part":
        collection["parts"].append(collection["parts"][0])
        collection["row_count"] *= 2
    elif mutation == "unknown_collection":
        document["collections"]["invented"] = collection
    else:
        collection["parts"][0]["path"] = "../catalogue.json"
    path.write_text(json.dumps(document))
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest["files"]["catalogue.json"] = sha256(path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="partition|collection|part"):
        api.load_neotoma_resource_catalogue(
            output,
            expected_manifest_sha256=sha256(manifest_path.read_bytes()).hexdigest(),
        )


@pytest.mark.parametrize("flag", [1, None, "yes"])
def test_partition_selection_is_literal_before_output_access(
    tmp_path: Path, flag: Any
) -> None:
    with pytest.raises(ValueError, match="literal boolean"):
        api.write_neotoma_resource_catalogue(
            tmp_path / "absent",
            catalogue={},
            capture_sources={},
            roster_path=tmp_path / "missing",
            partition_collections=flag,
        )


@pytest.mark.parametrize("owner", ["writer", "reader"])
def test_partitioned_collections_have_a_cumulative_byte_bound(
    catalogue_sources: Callable[..., dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    owner: str,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.resource_catalogue import storage

    inputs = catalogue_sources()
    output = tmp_path / "partitioned"
    if owner == "reader":
        _, digest, _ = _publish(inputs, output)
    monkeypatch.setattr(storage, "MAX_COLLECTION_BYTES", 1000, raising=False)
    with pytest.raises(ValueError, match="cumulative"):
        if owner == "writer":
            _publish(inputs, output)
        else:
            api.load_neotoma_resource_catalogue(output, expected_manifest_sha256=digest)


def test_descriptor_mapping_insertion_order_cannot_change_storage_bytes(
    catalogue_sources: Callable[..., dict[str, Any]],
    tmp_path: Path,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.resource_catalogue import storage

    catalogue = api.build_neotoma_resource_catalogue(**catalogue_sources())
    first = tmp_path / "first-catalogue"
    second = tmp_path / "second-catalogue"
    first.mkdir()
    second.mkdir()
    expected = storage.write_partitioned_catalogue(first, catalogue)
    catalogue["capture_descriptors"] = dict(
        reversed(list(catalogue["capture_descriptors"].items()))
    )
    assert storage.write_partitioned_catalogue(second, catalogue) == expected


def test_underdeclared_part_is_never_read_beyond_its_bounded_length(
    catalogue_sources: Callable[..., dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.receipts import _read
    from bijux_pollenomics.collection.sources.neotoma.resource_catalogue import storage

    catalogue = api.build_neotoma_resource_catalogue(**catalogue_sources())
    output = tmp_path / "parts"
    output.mkdir()
    files = storage.write_partitioned_catalogue(output, catalogue)
    index = json.loads((output / "catalogue.json").read_bytes())
    index["collections"]["resources"]["parts"][0]["bytes"] = 1
    bounds = []

    def read(path: Path, bound: int) -> bytes:
        bounds.append(bound)
        return _read(path, bound)

    monkeypatch.setattr(storage, "_read", read)
    with pytest.raises(ValueError):
        storage.load_partitioned_catalogue(output, index, files)
    assert bounds == [1]
