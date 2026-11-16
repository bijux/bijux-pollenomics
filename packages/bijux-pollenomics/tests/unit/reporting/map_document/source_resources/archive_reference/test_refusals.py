"""A rehashed archive descriptor cannot authorize a wrong native source link."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from typing import IO, Any

import pytest

from bijux_pollenomics.reporting.map_document.source_resources import (
    AtlasResourceArchiveInput,
    AtlasResourceCatalogueInput,
    load_atlas_resource_catalogue,
)
from tests.unit.collection.sources.neotoma.reading_observation import (
    capture_opening,
    observe_opening,
)


def reseal(root: Path, manifest: dict[str, object]) -> str:
    path = root / "manifest.json"
    path.write_text(json.dumps(manifest))
    return sha256(path.read_bytes()).hexdigest()


@pytest.mark.parametrize(
    "damage",
    [
        "dataset",
        "version",
        "status",
        "protected_href",
        "duplicate",
        "schema",
        "body_digest",
        "body_size",
        "undeclared_body",
        "catalogue_pin",
        "boolean_size",
    ],
)
def test_rehashed_manifest_and_index_cannot_change_resource_authority(
    archive_inputs: tuple[Path, str, Path, str], damage: str
) -> None:
    catalogue, digest, archive, _ = archive_inputs
    index_path = archive / "downloads/index.json"
    index = json.loads(index_path.read_bytes())
    manifest = json.loads((archive / "manifest.json").read_bytes())
    available = next(row for row in index["resources"] if "download_path" in row)
    if damage == "dataset":
        available["dataset_id"] = "999"
    elif damage == "version":
        available["version"] = "original_paper"
    elif damage == "status":
        available["statuses"]["qualification_status"] = "invented_authority"
    elif damage == "protected_href":
        blocked = next(
            row for row in index["resources"] if row["state"] == "blocked_exposure_role"
        )
        blocked["download_path"] = available["download_path"]
    elif damage == "duplicate":
        index["resources"].append(deepcopy(available))
    elif damage == "schema":
        index["schema_version"] = "unowned-download-index.v1"
    elif damage == "body_digest":
        manifest["files"][available["download_path"]]["sha256"] = "0" * 64
    elif damage == "body_size":
        manifest["files"][available["download_path"]]["bytes"] += 1
        manifest["source_bytes"] += 1
    elif damage == "undeclared_body":
        removed = manifest["files"].pop(available["download_path"])
        manifest["source_bytes"] -= removed["bytes"]
    elif damage == "catalogue_pin":
        manifest["catalogue_manifest_sha256"] = "0" * 64
    else:
        manifest["source_bytes"] -= (
            manifest["files"]["downloads/index.json"]["bytes"] - 1
        )
        manifest["files"]["downloads/index.json"]["bytes"] = True
    if damage in {
        "dataset",
        "version",
        "status",
        "protected_href",
        "duplicate",
        "schema",
    }:
        old_size = manifest["files"]["downloads/index.json"]["bytes"]
        index_path.write_text(json.dumps(index))
        data = index_path.read_bytes()
        manifest["files"]["downloads/index.json"] = {
            "bytes": len(data),
            "sha256": sha256(data).hexdigest(),
        }
        manifest["source_bytes"] += len(data) - old_size
    pin = reseal(archive, manifest)
    with pytest.raises(ValueError):
        load_atlas_resource_catalogue(
            AtlasResourceCatalogueInput(
                catalogue,
                digest,
                archive=AtlasResourceArchiveInput(
                    archive, pin, "/data/neotoma/source-resources/"
                ),
            )
        )


@pytest.mark.parametrize("member", ["manifest.json", "downloads/index.json"])
@pytest.mark.parametrize("alias", ["symlink", "hardlink"])
def test_archive_metadata_aliases_refuse_before_any_entity_access(
    archive_inputs: tuple[Path, str, Path, str], tmp_path: Path, member: str, alias: str
) -> None:
    import os

    catalogue, digest, archive, pin = archive_inputs
    target = archive / member
    backing = tmp_path / "aliased-metadata"
    target.rename(backing)
    if alias == "symlink":
        target.symlink_to(backing)
    else:
        os.link(backing, target)
    with pytest.raises(ValueError):
        load_atlas_resource_catalogue(
            AtlasResourceCatalogueInput(
                catalogue,
                digest,
                archive=AtlasResourceArchiveInput(
                    archive, pin, "/data/neotoma/source-resources/"
                ),
            )
        )


def test_declared_index_size_mismatch_refuses_before_buffering_index(
    archive_inputs: tuple[Path, str, Path, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    catalogue, digest, archive, _ = archive_inputs
    manifest = json.loads((archive / "manifest.json").read_bytes())
    old_size = manifest["files"]["downloads/index.json"]["bytes"]
    assert old_size > 1
    manifest["files"]["downloads/index.json"]["bytes"] = 1
    manifest["source_bytes"] -= old_size - 1
    pin = reseal(archive, manifest)
    actual_open = capture_opening()
    buffered = []
    index_opened = []

    class ObservedIndex:
        def __init__(self, stream: IO[bytes]) -> None:
            self.stream = stream

        def __enter__(self) -> ObservedIndex:
            self.stream.__enter__()
            return self

        def __exit__(self, *args: Any) -> Any:
            return self.stream.__exit__(*args)

        def fileno(self) -> int:
            return self.stream.fileno()

        def read(self, size: int = -1) -> bytes:
            buffered.append(size)
            return self.stream.read(size)

    def observed_open(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path == archive / "downloads/index.json":
            index_opened.append(path)
        stream = actual_open(path, *args, **kwargs)
        return (
            ObservedIndex(stream)
            if path == archive / "downloads/index.json"
            else stream
        )

    observe_opening(monkeypatch, observed_open)
    with pytest.raises(ValueError):
        load_atlas_resource_catalogue(
            AtlasResourceCatalogueInput(
                catalogue,
                digest,
                archive=AtlasResourceArchiveInput(
                    archive, pin, "/data/neotoma/source-resources/"
                ),
            )
        )
    assert buffered == []
    assert index_opened == []
