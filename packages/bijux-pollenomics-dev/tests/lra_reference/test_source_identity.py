"""Challenge actual-byte/Git binding and literal-only generated metadata separation."""

from __future__ import annotations

import hashlib
from importlib import metadata
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.lra_reference import source_identity as identity
from bijux_pollenomics_dev.ci.lra_reference.contracts import ReferenceRefusal
from bijux_pollenomics_dev.ci.lra_reference.sources import (
    SOURCE_DIRECTORIES,
    SOURCE_METADATA,
    source_inventory,
)

TEMPLATE = b"""from __future__ import annotations
__all__ = ["__version__", "version", "__version_tuple__", "version_tuple", "__commit_id__", "commit_id"]
version: str
__version__: str
__version_tuple__: tuple[int | str, ...]
version_tuple: tuple[int | str, ...]
commit_id: str | None
__commit_id__: str | None
__version__ = version = '0.1.9.dev4+dirty'
__version_tuple__ = version_tuple = (0, 1, 9, 'dev4', 'dirty')
__commit_id__ = commit_id = None
"""


def fixture_tree(root: Path) -> bytes:
    for path in SOURCE_DIRECTORIES:
        target = root / path / "module.py"
        target.parent.mkdir(parents=True)
        target.write_bytes(b"value = 1\n")
    for path in SOURCE_METADATA:
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"synthetic metadata")
    (root / identity.DECLARATION_PATH).write_text(
        '[tool.hatch.build.hooks.vcs]\nversion-file = "src/bijux_pollenomics_lra/_build_version.py"\n'
    )
    result = []
    for path in source_inventory(root):
        data = (root / path).read_bytes()
        blob = hashlib.sha1(
            b"blob " + str(len(data)).encode() + b"\0" + data
        ).hexdigest()
        result.append(b"100644 blob " + blob.encode() + b"\t" + path.encode() + b"\0")
    return b"".join(result)


def add_generated(root: Path) -> None:
    target = root / identity.GENERATED_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(TEMPLATE)


def test_source_only_and_governed_generated_have_same_static_identity(
    tmp_path: Path,
) -> None:
    tree = fixture_tree(tmp_path)
    before = identity.inspect_source_identity(tmp_path, tree)
    assert before.generated_files == {}
    add_generated(tmp_path)
    after = identity.inspect_source_identity(tmp_path, tree)
    assert before.tracked_files == after.tracked_files
    assert before.tracked_git_blobs == after.tracked_git_blobs
    assert after.generated_files[identity.GENERATED_PATH]["committed_source"] is False
    assert (
        after.generated_files[identity.GENERATED_PATH]["literals"]["version"]
        == "0.1.9.dev4+dirty"
    )


@pytest.mark.parametrize(
    "mutation", ["hidden_tracked_change", "ignored_executable", "missing_tracked"]
)
def test_status_cannot_hide_actual_executed_source_changes(
    tmp_path: Path, mutation: str
) -> None:
    tree = fixture_tree(tmp_path)
    target = tmp_path / SOURCE_DIRECTORIES[0] / "module.py"
    if mutation == "hidden_tracked_change":
        target.write_bytes(b"value = 2\n")
    elif mutation == "ignored_executable":
        target.with_name("ignored_payload.py").write_bytes(b"value = 2\n")
    else:
        target.unlink()
    # No status output participates: even an empty/assume-unchanged status cannot
    # turn altered blobs or ignored ungoverned executable extras into committed code.
    with pytest.raises(ReferenceRefusal):
        identity.inspect_source_identity(tmp_path, tree)


@pytest.mark.parametrize(
    "suffix",
    [b"\nimport os\n", b'\nraise RuntimeError("executed")\n', b"\nversion = str(1)\n"],
)
def test_generated_file_is_parsed_without_execution(
    tmp_path: Path, suffix: bytes
) -> None:
    tree = fixture_tree(tmp_path)
    add_generated(tmp_path)
    (tmp_path / identity.GENERATED_PATH).write_bytes(TEMPLATE + suffix)
    with pytest.raises(ReferenceRefusal):
        identity.inspect_source_identity(tmp_path, tree)


def test_generated_path_requires_committed_package_declaration(tmp_path: Path) -> None:
    fixture_tree(tmp_path)
    (tmp_path / identity.DECLARATION_PATH).write_text(
        '[tool.hatch.build.hooks.vcs]\nversion-file = "different.py"\n'
    )
    data = (tmp_path / identity.DECLARATION_PATH).read_bytes()
    # Rebuild the synthetic tree to describe the altered committed declaration.
    tree = b"".join(
        b"100644 blob "
        + hashlib.sha1(
            b"blob "
            + str(len((tmp_path / path).read_bytes())).encode()
            + b"\0"
            + (tmp_path / path).read_bytes()
        )
        .hexdigest()
        .encode()
        + b"\t"
        + path.encode()
        + b"\0"
        for path in source_inventory(tmp_path)
    )
    assert data
    add_generated(tmp_path)
    with pytest.raises(ReferenceRefusal, match="not declared"):
        identity.inspect_source_identity(tmp_path, tree)


@pytest.mark.parametrize("installed", [False, True])
def test_selected_runtime_version_origin_is_distinct_from_stale_generated(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, installed: bool
) -> None:
    tree = fixture_tree(tmp_path)
    add_generated(tmp_path)
    captured = identity.inspect_source_identity(tmp_path, tree)

    class Distribution:
        version = "0.2.0"

        def locate_file(self, _path: str) -> Path:
            return tmp_path / "installed"

        def read_text(self, _name: str) -> str:
            return "Name: bijux-pollenomics-lra\nVersion: 0.2.0\n"

    def distribution(_name: str) -> Any:
        if installed:
            return Distribution()
        raise metadata.PackageNotFoundError("synthetic missing")

    monkeypatch.setattr(
        "bijux_pollenomics_dev.ci.lra_reference.source_identity.metadata.distribution",
        distribution,
    )
    selected = identity.selected_engine_version(captured)
    assert selected["origin"] == (
        "installed-distribution-metadata"
        if installed
        else "governed-generated-fallback"
    )
    assert selected["version"] == ("0.2.0" if installed else "0.1.9.dev4+dirty")


def test_source_only_without_distribution_has_explicit_unknown_origin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tree = fixture_tree(tmp_path)

    def missing(_name: str) -> Any:
        raise metadata.PackageNotFoundError("synthetic missing")

    monkeypatch.setattr(
        "bijux_pollenomics_dev.ci.lra_reference.source_identity.metadata.distribution",
        missing,
    )
    assert identity.selected_engine_version(
        identity.inspect_source_identity(tmp_path, tree)
    ) == {"origin": "source-only-unknown-fallback", "version": "0+unknown"}


def test_ignored_directory_symlink_cannot_hide_external_code(tmp_path: Path) -> None:
    tree = fixture_tree(tmp_path)
    external = tmp_path / "external"
    external.mkdir()
    (external / "payload.py").write_text("value = 2\n")
    (tmp_path / SOURCE_DIRECTORIES[0] / "ignored_external_package").symlink_to(
        external, target_is_directory=True
    )
    with pytest.raises(ReferenceRefusal, match="symlinks"):
        identity.inspect_source_identity(tmp_path, tree)
