"""The Atlas receives pinned download references, never captured numerical buffers."""

from __future__ import annotations

from pathlib import Path
from typing import IO, Any

import pytest

from bijux_pollenomics.reporting.map_document.source_resources import (
    load_atlas_resource_catalogue,
    models,
)
from tests.unit.collection.sources.neotoma.reading_observation import (
    capture_opening,
    observe_opening,
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
    read = capture_opening()
    opened = []
    read_limits = {}
    expected_limits = {
        member: (archive / member).stat().st_size + 1
        for member in ("manifest.json", "downloads/index.json")
    }

    class ObservedMetadata:
        def __init__(self, stream: IO[bytes], member: str) -> None:
            self.stream, self.member = stream, member

        def __enter__(self) -> ObservedMetadata:
            self.stream.__enter__()
            return self

        def __exit__(self, *args: Any) -> Any:
            return self.stream.__exit__(*args)

        def fileno(self) -> int:
            return self.stream.fileno()

        def read(self, size: int = -1) -> bytes:
            read_limits[self.member] = size
            return self.stream.read(size)

    def observe(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.is_relative_to(archive):
            opened.append(path.relative_to(archive).as_posix())
            assert (
                path.name == "manifest.json" or path == archive / "downloads/index.json"
            )
        assert path.suffix != ".body"
        stream = read(path, *args, **kwargs)
        return (
            ObservedMetadata(stream, path.relative_to(archive).as_posix())
            if path.is_relative_to(archive)
            else stream
        )

    observe_opening(monkeypatch, observe)
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
    assert read_limits == expected_limits
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
