"""Refuse dishonest source identities and overlapping private outputs."""

import io
import json
from pathlib import Path
import tarfile

import pytest

from bijux_pollenomics_dev.ci.lra_reference.contracts import ReferenceRefusal, load_lock
from bijux_pollenomics_dev.ci.lra_reference.paths import exclusive_outputs, local_path
from bijux_pollenomics_dev.ci.lra_reference.sources import (
    verify_archive,
    verify_sources,
)

from .support import LOCK


@pytest.mark.parametrize(
    "mutation",
    [
        "duplicate",
        "missing",
        "order",
        "runtime",
        "reference",
        "url",
        "boolean_size",
        "nul",
    ],
)
def test_invalid_lock(tmp_path: Path, mutation: str) -> None:
    data = json.loads(LOCK.read_text())
    if mutation == "missing":
        del data["packages"]
    elif mutation == "order":
        data["install_order"].reverse()
    elif mutation == "runtime":
        data["runtime_policy"]["r_version"] = "4.6.1"
    elif mutation == "reference":
        data["reference"]["sha256"] = "a" * 64
    elif mutation == "url":
        data["packages"][0]["url"] = "https://example.com/a.tar.gz"
    elif mutation == "boolean_size":
        data["packages"][0]["byte_count"] = True
    elif mutation == "nul":
        data["packages"][0]["archive_filename"] = "a\0.tar.gz"
    encoded = json.dumps(data)
    if mutation == "duplicate":
        encoded = encoded[:-1] + ',"schema_version":"lra-r-source-lock.v1"}'
    path = tmp_path / "lock.json"
    path.write_text(encoded)
    with pytest.raises(ReferenceRefusal):
        load_lock(path)


@pytest.mark.parametrize("layout", ["same", "child", "parent", "existing"])
def test_output_boundaries(tmp_path: Path, layout: str) -> None:
    source = tmp_path / "source"
    source.mkdir()
    output = {
        "same": source,
        "child": source / "nested",
        "parent": tmp_path,
        "existing": tmp_path / "exists",
    }[layout]
    if layout == "existing":
        output.mkdir()
    with pytest.raises(ReferenceRefusal):
        exclusive_outputs((output,), (source,))


def test_symlink_ancestor_and_lexical_escape(tmp_path: Path) -> None:
    actual = tmp_path / "actual"
    actual.mkdir()
    link = tmp_path / "link"
    link.symlink_to(actual, target_is_directory=True)
    with pytest.raises(ReferenceRefusal):
        local_path(link / "missing")
    with pytest.raises(ReferenceRefusal):
        local_path(link / ".." / "elsewhere")


@pytest.mark.parametrize("kind", ["link", "escape", "version"])
def test_source_archive_refusals(tmp_path: Path, kind: str) -> None:
    path = tmp_path / "source.tar.gz"
    with tarfile.open(path, "w:gz") as archive:
        item = tarfile.TarInfo(
            "abc/DESCRIPTION"
            if kind == "version"
            else "../escape"
            if kind == "escape"
            else "abc/link"
        )
        data = b"Package: abc\nVersion: 2\n"
        if kind == "link":
            item.type = tarfile.SYMTYPE
            item.linkname = "/outside"
            archive.addfile(item)
        else:
            item.size = len(data)
            archive.addfile(item, io.BytesIO(data))
    with pytest.raises(ReferenceRefusal):
        verify_archive(path, "abc", "1")


def test_all_source_bytes_required_before_provision(tmp_path: Path) -> None:
    with pytest.raises(ReferenceRefusal, match="Source bytes missing"):
        verify_sources(load_lock(LOCK), tmp_path, tmp_path)
