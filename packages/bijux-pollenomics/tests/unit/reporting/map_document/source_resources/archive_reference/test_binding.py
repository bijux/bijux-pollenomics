"""The Atlas receives pinned download references, never captured numerical buffers."""

from __future__ import annotations

import fcntl
import os
from pathlib import Path
import stat
from typing import Any

import pytest

from bijux_pollenomics.reporting.map_document.source_resources import (
    load_atlas_resource_catalogue,
    models,
)


def test_reference_reads_only_manifest_and_index_without_native_entities(
    archive_inputs: tuple[Path, str, Path, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    catalogue, digest, archive, archive_pin = archive_inputs
    source = models.AtlasResourceCatalogueInput(
        catalogue,
        digest,
        archive=models.AtlasResourceArchiveInput(
            archive, archive_pin, "/data/neotoma/source-resources/"
        ),
    )
    original_open, original_read, original_close = os.open, os.read, os.close
    original_scandir = os.scandir
    opened: list[str] = []
    descriptors: dict[int, str] = {}
    read_limits: dict[str, list[int]] = {}
    byte_counts: dict[str, int] = {}
    sizes = {
        member: (archive / member).stat().st_size
        for member in ("manifest.json", "downloads/index.json")
    }

    def descriptor_path(descriptor: int) -> Path:
        try:
            return Path(
                os.fsdecode(fcntl.fcntl(descriptor, 50, bytes(1024)).split(b"\0", 1)[0])
            )
        except OSError:
            return Path(os.readlink(f"/proc/self/fd/{descriptor}"))

    def observe(value: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        descriptor = original_open(value, flags, *args, **kwargs)
        path = descriptor_path(descriptor)
        if path.is_relative_to(archive) and stat.S_ISREG(os.fstat(descriptor).st_mode):
            member = path.relative_to(archive).as_posix()
            assert member in sizes, "Metadata-only reference opened a sibling entity"
            opened.append(member)
            descriptors[descriptor] = member
        return descriptor

    def read(descriptor: int, size: int) -> bytes:
        member = descriptors.get(descriptor)
        if member is not None:
            remaining = sizes[member] - byte_counts.get(member, 0)
            assert 0 < size <= min(1024 * 1024, remaining + 1)
            read_limits.setdefault(member, []).append(size)
        content = original_read(descriptor, size)
        if member is not None:
            byte_counts[member] = byte_counts.get(member, 0) + len(content)
            assert byte_counts[member] <= sizes[member]
        return content

    def close(descriptor: int) -> None:
        descriptors.pop(descriptor, None)
        original_close(descriptor)

    def scandir(value: Any) -> Any:
        path = descriptor_path(value) if isinstance(value, int) else Path(value)
        assert not path.is_relative_to(archive), (
            "Selected metadata reader inventoried sibling entities"
        )
        return original_scandir(value)

    monkeypatch.setattr(os, "open", observe)
    monkeypatch.setattr(os, "read", read)
    monkeypatch.setattr(os, "close", close)
    monkeypatch.setattr(os, "scandir", scandir)
    monkeypatch.setattr(os, "supports_dir_fd", os.supports_dir_fd | {observe})
    projected = load_atlas_resource_catalogue(source)
    reference = projected.provenance["source_archive"]
    assert reference["manifest_sha256"] == archive_pin
    assert reference["catalogue_manifest_sha256"] == digest
    assert reference["published_base_url"] == "/data/neotoma/source-resources/"
    assert reference["index"]["path"] == "downloads/index.json"
    assert reference["validation_scope"] == "manifest_and_download_index_only"
    assert reference["file_protocol_downloads"] == "unavailable_requires_local_http"
    assert reference["scientific_admission"] == "not_asserted"
    assert sorted(opened) == ["downloads/index.json", "manifest.json"]
    assert set(read_limits) == set(sizes)
    assert byte_counts == sizes
    assert all(
        limits[0] == min(1024 * 1024, sizes[member] + 1) and limits[-1] == 1
        for member, limits in read_limits.items()
    )
    assert not descriptors
    assert "resources" not in reference and "files" not in reference


@pytest.mark.parametrize(
    "base",
    [
        "https://api.neotomadb.org/data/",
        "//host/data/",
        "data/",
        "/data",
        "/data//sources/",
        "/data/../sources/",
        "/data/./sources/",
        "/data/%2e%2e/",
        "/data/%2f/",
        "/data\\sources/",
        "/data/?query=1",
        "/data/#fragment",
        "/data/\n",
        "/artifacts/source-resources/",
        None,
        True,
    ],
)
def test_archive_public_prefix_refuses_nonportable_or_ambiguous_routes(
    base: Any,
) -> None:
    with pytest.raises(ValueError):
        models.AtlasResourceArchiveInput(Path("unopened"), "a" * 64, base)
