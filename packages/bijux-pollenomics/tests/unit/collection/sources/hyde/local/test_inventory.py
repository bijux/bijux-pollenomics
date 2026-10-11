"""Filesystem and source identity boundaries preserve missingness and ancillary separation."""

from pathlib import Path
import zipfile

import pytest

from bijux_pollenomics.collection.sources.hyde.local import LocalInventoryLimits
from bijux_pollenomics.collection.sources.hyde.local.inventory import (
    hash_file,
    source_snapshot,
)
from bijux_pollenomics.collection.sources.quarantine import IntakeRefusal


def source_fixture(root: Path) -> Path:
    root.mkdir()
    (root / "zero.bin").write_bytes(b"")
    (root / "native.nc").write_bytes(b"not interpreted as NetCDF metadata")
    (root / ".DS_Store").write_bytes(b"ancillary")
    (root / "License.txt").write_bytes(b"CC BY-NC4\r\n")
    (root / "README-3.5.txt").write_bytes(
        b"release3.5; CC BY3; native version unresolved\r\n"
    )
    with zipfile.ZipFile(
        root / "native.zip", "w", compression=zipfile.ZIP_DEFLATED
    ) as archive:
        archive.comment = b"native archive comment"
        archive.writestr("folder/", b"")
        archive.writestr("taxon-\u00e4.asc", b"-9999 0 1\n")
        with pytest.warns(UserWarning, match="Duplicate name"):
            archive.writestr("taxon-\u00e4.asc", b"-9999 2 3\n")
        archive.writestr("../unsafe.asc", b"custody only")
    return root


def test_regular_zero_and_hidden_files_are_hash_owned(tmp_path: Path) -> None:
    root = source_fixture(tmp_path / "raw")
    limits = LocalInventoryLimits(chunk_bytes=1)
    snapshot = source_snapshot(root, limits)
    assert len(snapshot) == 6 and snapshot["zero.bin"].size == 0
    assert ".DS_Store" in snapshot and "missing.bin" not in snapshot
    assert (
        hash_file(root / "zero.bin", snapshot["zero.bin"], limits)
        == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )


@pytest.mark.parametrize(
    "kind", ["file_link", "directory_link", "root_link", "empty", "limit"]
)
def test_unsupported_source_ownership_refuses(tmp_path: Path, kind: str) -> None:
    root = source_fixture(tmp_path / "raw")
    limits = LocalInventoryLimits()
    if kind == "file_link":
        (root / "link").symlink_to(root / "zero.bin")
    elif kind == "directory_link":
        (root / "link").symlink_to(tmp_path, target_is_directory=True)
    elif kind == "root_link":
        alias = tmp_path / "alias"
        alias.symlink_to(root, target_is_directory=True)
        root = alias
    elif kind == "empty":
        root = tmp_path / "empty"
        root.mkdir()
    else:
        limits = LocalInventoryLimits(maximum_files=1)
    with pytest.raises(IntakeRefusal):
        source_snapshot(root, limits)


def test_replaced_descriptor_identity_refuses(tmp_path: Path) -> None:
    root = source_fixture(tmp_path / "raw")
    limits = LocalInventoryLimits()
    stamp = source_snapshot(root, limits)["zero.bin"]
    (root / "zero.bin").write_bytes(b"changed")
    with pytest.raises(IntakeRefusal, match="hyde_source_changed"):
        hash_file(root / "zero.bin", stamp, limits)
