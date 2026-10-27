"""Exercise source identities, complete comparisons and hostile containers."""

from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import stat
import tarfile
from typing import Any, Literal
import zipfile

import pytest

from bijux_pollenomics_dev.source_completion.lra_delivery import archives
from bijux_pollenomics_dev.source_completion.lra_delivery.archives import (
    ArchiveError,
    archive_inventory,
    compare_adoption_manifest,
    compare_inventory_files,
)


def write_archive(path: Path, files: dict[str, bytes], root: str = "received") -> Path:
    """Construct portable synthetic deliveries without touching original inputs."""
    if path.suffix == ".zip":
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, body in files.items():
                archive.writestr(f"{root}/{name}", body)
    else:
        mode: Literal["w:gz", "w"] = "w:gz" if path.name.endswith(".gz") else "w"
        with tarfile.open(path, mode) as archive:
            directory = tarfile.TarInfo(root)
            directory.type = tarfile.DIRTYPE
            archive.addfile(directory)
            for name, body in files.items():
                entry = tarfile.TarInfo(f"{root}/{name}")
                entry.size = len(body)
                archive.addfile(entry, io.BytesIO(body))
    return path


@pytest.mark.parametrize("suffix", [".tar", ".tar.gz", ".zip"])
def test_complete_regular_inventory_without_extracting(
    tmp_path: Path, suffix: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("extraction is forbidden")

    monkeypatch.setattr(tarfile.TarFile, "extract", forbidden)
    monkeypatch.setattr(tarfile.TarFile, "extractall", forbidden)
    monkeypatch.setattr(zipfile.ZipFile, "extract", forbidden)
    monkeypatch.setattr(zipfile.ZipFile, "extractall", forbidden)
    files = {
        "package/model.py": b"raise RuntimeError('never import')",
        "data/sample.csv": b"uninterpreted bytes",
    }
    path = write_archive(tmp_path / ("delivery" + suffix), files)
    result = archive_inventory(path)
    assert result["source"] == {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }
    assert result["regular_file_count"] == 2
    assert result["uncompressed_bytes"] == sum(map(len, files.values()))
    actual = {
        r["path"]: (r["bytes"], r["sha256"])
        for r in result["members"]
        if r["type"] == "file"
    }
    assert actual == {
        p: (len(b), hashlib.sha256(b).hexdigest()) for p, b in files.items()
    }
    assert "never import" not in json.dumps(result)


def test_cross_format_single_root_comparison_and_manifest_differences(
    tmp_path: Path,
) -> None:
    files = {"model.py": b"original", "extra.txt": b"retained"}
    left = archive_inventory(write_archive(tmp_path / "left.tar", files, "tar_root"))
    right = archive_inventory(write_archive(tmp_path / "right.zip", files, "zip_root"))
    assert compare_inventory_files(left, right)["equal"] is True
    manifest = {
        "files": [
            {"source": "model.py", "sha256": hashlib.sha256(b"changed").hexdigest()},
            {"source": "missing.py", "sha256": "0" * 64},
        ]
    }
    difference = compare_adoption_manifest(left, manifest)
    assert difference["left_only"] == ["extra.txt"]
    assert difference["right_only"] == ["missing.py"]
    assert difference["differing"] == [
        {
            "path": "model.py",
            "left_sha256": hashlib.sha256(b"original").hexdigest(),
            "right_sha256": hashlib.sha256(b"changed").hexdigest(),
        }
    ]
    assert difference["equal_file_count"] == 0
    assert difference["equal"] is False


def test_only_selected_package_metadata_and_license_text_are_retained(
    tmp_path: Path,
) -> None:
    project = b"""[project]
name="received"
version="0.1.0"
description="must not be exported"
license={text="GPL-3.0-or-later"}
dependencies=["numpy>=1.25"]
[project.optional-dependencies]
test=["pytest>=8"]
[project.scripts]
received="received.cli:main"
[project.entry-points."example.group"]
received="received.plugin:entry"
[build-system]
requires=["setuptools>=68"]
build-backend="setuptools.build_meta"
"""
    result = archive_inventory(
        write_archive(
            tmp_path / "metadata.tar.gz",
            {
                "pyproject.toml": project,
                "LICENSE": b"license terms",
                "NOTICE.md": b"source attribution",
                "README.md": b"must not copy this document",
                "integration/host_adapter.py": b"never execute",
            },
        )
    )
    assert result["metadata"] == {
        "pyproject": {
            "pyproject.toml": {
                "name": "received",
                "version": "0.1.0",
                "license": {"text": "GPL-3.0-or-later"},
                "dependencies": ["numpy>=1.25"],
                "optional-dependencies": {"test": ["pytest>=8"]},
                "scripts": {"received": "received.cli:main"},
                "entry-points": {
                    "example.group": {"received": "received.plugin:entry"}
                },
            }
        },
        "build_system": {
            "pyproject.toml": {
                "requires": ["setuptools>=68"],
                "build-backend": "setuptools.build_meta",
            }
        },
        "license_notice": {
            "LICENSE": "license terms",
            "NOTICE.md": "source attribution",
        },
    }
    assert "must not" not in json.dumps(result)
    assert (
        next(
            r for r in result["members"] if r["path"] == "integration/host_adapter.py"
        )["role"]
        == "integration_adapter"
    )


@pytest.mark.parametrize(
    "name",
    [
        "/absolute.py",
        "received/../escape.py",
        "received/./ambiguous.py",
        "received//empty.py",
        "C:/drive.py",
        "received/back\\slash.py",
        "received/new\nline.py",
    ],
)
def test_tar_refuses_unsafe_native_paths(tmp_path: Path, name: str) -> None:
    path = tmp_path / "unsafe.tar"
    with tarfile.open(path, "w", format=tarfile.PAX_FORMAT) as archive:
        entry = tarfile.TarInfo(name)
        entry.size = 1
        archive.addfile(entry, io.BytesIO(b"x"))
    with pytest.raises(ArchiveError, match="path"):
        archive_inventory(path)


@pytest.mark.parametrize("suffix", [".tar", ".zip"])
def test_refuses_duplicate_native_members(tmp_path: Path, suffix: str) -> None:
    path = tmp_path / ("duplicate" + suffix)
    if suffix == ".tar":
        with tarfile.open(path, "w") as archive:
            for _ in range(2):
                entry = tarfile.TarInfo("received/same.py")
                archive.addfile(entry, io.BytesIO())
    else:
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("received/same.py", b"")
            with pytest.warns(UserWarning, match="Duplicate"):
                archive.writestr("received/same.py", b"")
    with pytest.raises(ArchiveError, match="duplicate"):
        archive_inventory(path)


@pytest.mark.parametrize(
    "kind", [tarfile.SYMTYPE, tarfile.LNKTYPE, tarfile.FIFOTYPE, tarfile.CHRTYPE]
)
def test_refuses_tar_links_and_special_members(tmp_path: Path, kind: bytes) -> None:
    path = tmp_path / "special.tar"
    with tarfile.open(path, "w") as archive:
        entry = tarfile.TarInfo("received/special")
        entry.type = kind
        entry.linkname = "outside"
        archive.addfile(entry)
    with pytest.raises(ArchiveError, match="special"):
        archive_inventory(path)


@pytest.mark.parametrize("kind", [stat.S_IFLNK, stat.S_IFIFO])
def test_refuses_zip_links_and_special_members(tmp_path: Path, kind: int) -> None:
    path = tmp_path / "special.zip"
    with zipfile.ZipFile(path, "w") as archive:
        entry = zipfile.ZipInfo("received/special")
        entry.create_system = 3
        entry.external_attr = (kind | 0o777) << 16
        archive.writestr(entry, b"outside")
    with pytest.raises(ArchiveError, match="special"):
        archive_inventory(path)


@pytest.mark.parametrize(
    "limit,value",
    [
        ("max_members", 1),
        ("max_uncompressed_bytes", 3),
        ("max_member_bytes", 2),
        ("max_metadata_bytes", 2),
        ("max_archive_bytes", 10),
    ],
)
def test_independent_closed_resource_limits(
    tmp_path: Path, limit: str, value: int
) -> None:
    path = write_archive(
        tmp_path / "limited.zip", {"LICENSE": b"1234", "model.py": b"5678"}
    )
    with pytest.raises(ArchiveError, match="ceiling"):
        archive_inventory(path, **{limit: value})


def test_compressed_bomb_is_rejected_before_payload_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = write_archive(tmp_path / "bomb.zip", {"large.bin": b"\0" * 1000000})

    def forbidden(*args: Any, **kwargs: Any) -> bytes:
        raise AssertionError("over-budget payload must not be read")

    monkeypatch.setattr(zipfile.ZipExtFile, "read", forbidden)
    with pytest.raises(ArchiveError, match="uncompressed"):
        archive_inventory(path, max_uncompressed_bytes=100)


@pytest.mark.parametrize("body", [b"\xff", b"[project\n"])
def test_invalid_selected_metadata_refuses(tmp_path: Path, body: bytes) -> None:
    path = write_archive(tmp_path / "metadata.zip", {"pyproject.toml": body})
    with pytest.raises(ArchiveError, match="metadata"):
        archive_inventory(path)


@pytest.mark.parametrize("files", [{"only": b""}, {"first/a": b"", "second/b": b""}])
def test_flat_or_multiple_roots_remain_literal(
    tmp_path: Path, files: dict[str, bytes]
) -> None:
    path = tmp_path / "roots.zip"
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    result = archive_inventory(path)
    assert result["root"] is None
    assert {m["path"] for m in result["members"]} == set(files)


def test_flat_adapter_has_no_invented_root(tmp_path: Path) -> None:
    files = {
        ".gitignore": b"ignored",
        "integration/host_adapter.py": b"never import",
        "integration/README.md": b"receipt",
    }
    path = tmp_path / "adapter.zip"
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    result = archive_inventory(path)
    assert result["root"] is None
    assert {m["path"] for m in result["members"]} == set(files)


def test_nested_projects_are_not_exported_as_license_text(tmp_path: Path) -> None:
    path = tmp_path / "multiple-projects.zip"
    with zipfile.ZipFile(path, "w") as archive:
        for root in ("first", "second"):
            archive.writestr(
                f"{root}/pyproject.toml",
                '[project]\nname="nested"\ndescription="not exported"',
            )
    result = archive_inventory(path)
    assert result["root"] is None
    assert result["regular_file_count"] == 2
    assert result["metadata"] == {
        "pyproject": {},
        "build_system": {},
        "license_notice": {},
    }
    assert "not exported" not in json.dumps(result)


def test_regular_file_cannot_be_another_members_parent(tmp_path: Path) -> None:
    path = write_archive(
        tmp_path / "conflict.zip", {"parent": b"x", "parent/child": b"y"}
    )
    with pytest.raises(ArchiveError, match="ancestor"):
        archive_inventory(path)


def test_nul_path_is_not_admitted_by_path_validator() -> None:
    with pytest.raises(ArchiveError, match="control"):
        archives._path("received/nul\x00.py")


@pytest.mark.parametrize("value", [True, 0, -1, 1.5])
def test_limit_types_are_strict(tmp_path: Path, value: Any) -> None:
    path = write_archive(tmp_path / "limits.zip", {"f": b""})
    with pytest.raises(ArchiveError, match="positive integer"):
        archive_inventory(path, max_members=value)


def test_source_before_after_identity_is_mandatory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = write_archive(tmp_path / "changing.zip", {"f": b"unchanged"})
    values = iter(["1" * 64, "2" * 64])
    monkeypatch.setattr(archives, "_sha", lambda *_: next(values))
    with pytest.raises(ArchiveError, match="changed"):
        archive_inventory(path)


def test_duplicate_adoption_rows_are_not_silently_collapsed(tmp_path: Path) -> None:
    result = archive_inventory(write_archive(tmp_path / "source.zip", {"f": b""}))
    row = {"source": "f", "sha256": hashlib.sha256(b"").hexdigest()}
    with pytest.raises(ArchiveError, match="duplicate"):
        compare_adoption_manifest(result, {"files": [row, row]})


@pytest.mark.parametrize(
    "body",
    [
        b"[project]\nname=1",
        b'[project]\ndependencies="not a list"',
        b"[project.optional-dependencies]\ntest=[1]",
        b"[project.scripts]\nentry=1",
        b'[project.entry-points]\ngroup="not a table"',
        b"[project]\nlicense=1979-05-27",
        b"[build-system]\nrequires=[1]",
        b"[build-system]\nbuild-backend=true",
    ],
)
def test_selected_metadata_has_closed_serializable_types(
    tmp_path: Path, body: bytes
) -> None:
    path = write_archive(tmp_path / "typed.zip", {"pyproject.toml": body})
    with pytest.raises(ArchiveError, match="metadata"):
        archive_inventory(path)
