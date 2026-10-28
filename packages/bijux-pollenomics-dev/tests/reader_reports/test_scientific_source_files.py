"""The public source attachment owner exports one finite metadata/code population."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.source_completion.scientific_readers import (
    source_files as source,
)


def _fixture(root: Path) -> dict[str, Any]:
    rows = []
    for index, (name, destination) in enumerate(source.ROUTES):
        data = f"first-party source {index}\n".encode()
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        rows.append(
            {
                "source": name,
                "destination": destination,
                "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data),
                "git_blob": hashlib.sha1(
                    b"blob " + str(len(data)).encode() + b"\0" + data,
                    usedforsecurity=False,
                ).hexdigest(),
            }
        )
    payload = {
        "schema_version": "scientific-source-files.v1",
        "scope": "First-party fixture metadata only",
        "files": rows,
    }
    _manifest(root, payload)
    (root / "artifacts").mkdir()
    return payload


def _manifest(root: Path, payload: dict[str, Any]) -> None:
    path = root / source.MANIFEST
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload))


def test_finite_attachments_preserve_all_source_bytes(tmp_path: Path) -> None:
    _fixture(tmp_path)
    output = tmp_path / "artifacts/attachments"
    paths = source.export_source_files(tmp_path, output)
    assert len(paths) == 15
    assert len(list(output.rglob("*.*"))) == 15
    for name, destination in source.ROUTES:
        assert (output / destination.removeprefix("docs/report/")).read_bytes() == (
            tmp_path / name
        ).read_bytes()


@pytest.mark.parametrize(
    "field,value",
    [
        ("source", "data/private/native-counts.json"),
        ("destination", "docs/report/unowned/raw.json"),
        ("sha256", "0" * 64),
        ("git_blob", "0" * 40),
        ("bytes", 1),
        ("bytes", True),
        ("source_revision", "0" * 40),
    ],
)
def test_manifest_cannot_change_scope_or_source_identity(
    tmp_path: Path, field: str, value: object
) -> None:
    payload = _fixture(tmp_path)
    payload["files"][0][field] = value
    _manifest(tmp_path, payload)
    with pytest.raises(source.ScientificSourceFileError):
        source.export_source_files(tmp_path, tmp_path / "artifacts/attachments")
    assert not (tmp_path / "artifacts/attachments").exists()


def test_missing_population_refuses_before_output(tmp_path: Path) -> None:
    payload = _fixture(tmp_path)
    payload["files"].pop()
    _manifest(tmp_path, payload)
    with pytest.raises(source.ScientificSourceFileError):
        source.export_source_files(tmp_path, tmp_path / "artifacts/attachments")
    assert not (tmp_path / "artifacts/attachments").exists()


def test_changed_source_refuses_before_output(tmp_path: Path) -> None:
    _fixture(tmp_path)
    (tmp_path / source.ROUTES[-1][0]).write_bytes(b"changed")
    with pytest.raises(source.ScientificSourceFileError, match="byte identity"):
        source.export_source_files(tmp_path, tmp_path / "artifacts/attachments")
    assert not (tmp_path / "artifacts/attachments").exists()


@pytest.mark.parametrize("kind", ["leaf_symlink", "parent_symlink", "hardlink"])
def test_aliased_source_refuses(tmp_path: Path, kind: str) -> None:
    _fixture(tmp_path)
    path = tmp_path / source.ROUTES[0][0]
    if kind == "parent_symlink":
        parent = path.parent
        actual = parent.with_name("actual-source")
        parent.rename(actual)
        parent.symlink_to(actual, target_is_directory=True)
    else:
        actual = path.with_name("actual-source.json")
        path.rename(actual)
        if kind == "leaf_symlink":
            path.symlink_to(actual)
        else:
            os.link(actual, path)
    with pytest.raises(source.ScientificSourceFileError):
        source.export_source_files(tmp_path, tmp_path / "artifacts/attachments")
    assert not (tmp_path / "artifacts/attachments").exists()


@pytest.mark.parametrize("kind", ["outside", "existing", "symlink_ancestor", "dotdot"])
def test_output_boundary_refuses(tmp_path: Path, kind: str) -> None:
    _fixture(tmp_path)
    output = tmp_path / "artifacts/attachments"
    if kind == "outside":
        output = tmp_path / "unowned"
    elif kind == "existing":
        output.mkdir()
    elif kind == "symlink_ancestor":
        actual = tmp_path / "artifacts/actual"
        actual.mkdir()
        alias = tmp_path / "artifacts/alias"
        alias.symlink_to(actual, target_is_directory=True)
        output = alias / "attachments"
    else:
        output = tmp_path / "artifacts/../artifacts/attachments"
    with pytest.raises(ReportRebuildError):
        source.export_source_files(tmp_path, output)
