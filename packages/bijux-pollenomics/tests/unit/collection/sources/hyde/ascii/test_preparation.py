"""Real ZIP source preparation retains spelling and refuses changed custody."""

from dataclasses import replace
from pathlib import Path
import zipfile

import pytest

from bijux_pollenomics.collection.sources.hyde.ascii import (
    AsciiWindowLimits,
    AsciiWindowSelection,
    preparation,
    prepare_hyde_ascii_window,
)
from bijux_pollenomics.collection.sources.hyde.ascii.streaming import (
    StreamedWindow,
    stream_window,
)
from bijux_pollenomics.collection.sources.hyde.local import (
    BoundArchiveMember,
    LocalHydeInventory,
    prepare_local_hyde_inventory,
)
from bijux_pollenomics.collection.sources.quarantine import IntakeRefusal

HEADER = b"ncols 3\r\nnrows 2\r\nxllcorner -180\r\nyllcorner -90\r\ncellsize 0.0833333\r\nNODATA_value -9999\r\n"
BODY = b"-9999 0 1.2500\n2e-1 -0 -9999.0\n"


def fixture(
    root: Path, content: bytes = HEADER + BODY
) -> tuple[Path, LocalHydeInventory, AsciiWindowSelection]:
    source = root / "raw"
    source.mkdir()
    with zipfile.ZipFile(
        source / "base-2000AD.zip", "w", compression=zipfile.ZIP_DEFLATED
    ) as archive:
        archive.writestr("cropland2000AD.asc", content)
    custody = prepare_local_hyde_inventory(source, root / "custody")
    selection = AsciiWindowSelection(
        "base-2000AD.zip",
        0,
        "cropland2000AD.asc",
        0,
        2,
        0,
        3,
        (("scenario", "base"), ("time", "2000AD"), ("variable", "cropland")),
    )
    return source, custody, selection


def test_actual_source_preserves_tokens_missingness_and_native_header(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, custody, selection = fixture(tmp_path)

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("ZIP extraction is forbidden")

    monkeypatch.setattr(zipfile.ZipFile, "extract", forbidden)
    monkeypatch.setattr(zipfile.ZipFile, "extractall", forbidden)
    product = prepare_hyde_ascii_window(
        custody.directory,
        expected_custody_manifest_sha256=custody.manifest_sha256,
        source_root=source,
        selection=selection,
        destination=tmp_path / "result",
    )
    assert product.source_tokens == ("-9999", "0", "1.2500", "2e-1", "-0", "-9999.0")
    assert product.missing_mask == (True, False, False, False, False, True)
    assert product.header.value("cellsize") == "0.0833333"
    assert {p.name for p in product.directory.iterdir()} == {
        "manifest.json",
        "window.json",
    }
    assert {p.name for p in source.iterdir()} == {"base-2000AD.zip"}


@pytest.mark.parametrize(
    "mutation",
    [
        "changed_archive",
        "changed_after_stream",
        "producer",
        "existing_destination",
        "wrong_member",
    ],
)
def test_publication_refuses_real_source_or_identity_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    source, custody, selection = fixture(tmp_path)
    destination = tmp_path / "result"
    if mutation == "changed_archive":
        with (source / selection.archive_path).open("ab") as stream:
            stream.write(b"changed")
    elif mutation == "changed_after_stream":
        original = stream_window

        def changed(
            source_root: Path,
            selected: BoundArchiveMember,
            request: AsciiWindowSelection,
            limits: AsciiWindowLimits,
        ) -> StreamedWindow:
            value = original(source_root, selected, request, limits)
            with (source / selection.archive_path).open("ab") as stream:
                stream.write(b"changed after complete stream")
            return value

        monkeypatch.setattr(preparation, "stream_window", changed)
    elif mutation == "producer":
        original_identity = preparation.producer_identity
        calls = 0

        def changed_identity() -> dict[str, str]:
            nonlocal calls
            calls += 1
            value = original_identity()
            if calls > 1:
                value["collection/sources/hyde/ascii/parsing.py"] = "0" * 64
            return value

        monkeypatch.setattr(preparation, "producer_identity", changed_identity)
    elif mutation == "existing_destination":
        destination.mkdir()
        (destination / "owned-before").write_text("keep")
    else:
        selection = replace(selection, expected_member_name="cropland2000AD-other.asc")
    with pytest.raises(IntakeRefusal):
        prepare_hyde_ascii_window(
            custody.directory,
            expected_custody_manifest_sha256=custody.manifest_sha256,
            source_root=source,
            selection=selection,
            destination=destination,
        )
    assert (
        not destination.exists() or (destination / "owned-before").read_text() == "keep"
    )
