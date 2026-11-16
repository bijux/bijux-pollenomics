"""Atlas metadata pins retain physical ancestors through the actual open boundary."""

from hashlib import sha256
import os
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.reporting.map_document.source_resources.archive_reference import (
    _pinned,
)


@pytest.mark.parametrize("change", ["stable", "initial_alias", "alias_during_open"])
def test_metadata_namespace_remains_physical_through_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    root = tmp_path / "archive"
    root.mkdir()
    path = root / "manifest.json"
    raw = b'{"scope":"generated metadata"}'
    path.write_bytes(raw)
    pin = sha256(raw).hexdigest()
    original_path_open, original_os_open = Path.open, os.open
    opens: list[str] = []

    def boundary(kind: str) -> None:
        opens.append(kind)
        if change == "alias_during_open":
            retained = tmp_path / "retained-archive"
            root.rename(retained)
            root.symlink_to(retained, target_is_directory=True)

    def path_open(value: Path, *args: Any, **kwargs: Any) -> Any:
        if value == path and args and args[0] == "rb":
            boundary("path")
        return original_path_open(value, *args, **kwargs)

    def descriptor_open(value: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        if (
            value == path.name
            and not flags & os.O_DIRECTORY
            and kwargs.get("dir_fd") is not None
        ):
            boundary("descriptor")
        return original_os_open(value, flags, *args, **kwargs)

    if change == "initial_alias":
        root.rename(tmp_path / "retained-archive")
        root.symlink_to(tmp_path / "retained-archive", target_is_directory=True)
    monkeypatch.setattr(Path, "open", path_open)
    monkeypatch.setattr(os, "open", descriptor_open)
    monkeypatch.setattr(os, "supports_dir_fd", os.supports_dir_fd | {descriptor_open})
    if change == "stable":
        assert _pinned(root, path.name, pin, expected_size=len(raw)) == (
            {"scope": "generated metadata"},
            len(raw),
        )
        assert len(opens) == 1
    else:
        with pytest.raises(ValueError):
            _pinned(root, path.name, pin, expected_size=len(raw))
        assert len(opens) == (0 if change == "initial_alias" else 1)


def test_declared_size_mismatch_refuses_before_metadata_file_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "manifest.json"
    raw = b"{}"
    path.write_bytes(raw)
    original = os.open

    def opened(value: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        if value == path.name and not flags & os.O_DIRECTORY:
            pytest.fail("Declared-size mismatch reached the metadata file open")
        return original(value, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", opened)
    with pytest.raises(ValueError, match="declared byte count"):
        _pinned(tmp_path, path.name, sha256(raw).hexdigest(), expected_size=3)


@pytest.mark.parametrize("alias", ["symlink", "hardlink", "during_open"])
def test_selected_metadata_leaf_cannot_be_aliased_or_substituted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, alias: str
) -> None:
    """The selected file keeps its independently inventoried physical identity."""
    path, retained = tmp_path / "manifest.json", tmp_path / "retained.json"
    raw = b"{}"
    path.write_bytes(raw)
    original = os.open
    opened: list[int] = []

    def open_file(value: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        if value == path.name and not flags & os.O_DIRECTORY:
            opened.append(1)
            if alias == "during_open":
                path.rename(retained)
                path.write_bytes(raw)
        return original(value, flags, *args, **kwargs)

    if alias != "during_open":
        path.rename(retained)
        if alias == "symlink":
            path.symlink_to(retained)
        else:
            os.link(retained, path)
    monkeypatch.setattr(os, "open", open_file)
    monkeypatch.setattr(os, "supports_dir_fd", os.supports_dir_fd | {open_file})
    with pytest.raises(ValueError):
        _pinned(tmp_path, path.name, sha256(raw).hexdigest(), expected_size=len(raw))
    assert len(opened) == (1 if alias == "during_open" else 0)
    assert retained.read_bytes() == raw


def test_selected_metadata_nested_ancestor_alias_refuses_without_file_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A physical archive root does not authorize a redirected downloads parent."""
    downloads = tmp_path / "downloads"
    downloads.mkdir()
    (downloads / "index.json").write_bytes(b"{}")
    retained = tmp_path / "retained-downloads"
    downloads.rename(retained)
    downloads.symlink_to(retained, target_is_directory=True)
    original = os.open

    def opened(value: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        assert value != "index.json", "Alias reached the selected metadata file FD"
        return original(value, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", opened)
    with pytest.raises(ValueError):
        _pinned(tmp_path, "downloads/index.json", sha256(b"{}").hexdigest())


def test_selected_metadata_growth_stops_at_one_sentinel_byte(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Growth after the first real read cannot consume beyond the captured bound."""
    path = tmp_path / "manifest.json"
    path.write_bytes(b"{}")
    identity = path.stat().st_ino
    original_read = os.read
    requests: list[int] = []
    returned: list[bytes] = []

    def read(descriptor: int, size: int) -> bytes:
        content = original_read(descriptor, size)
        if os.fstat(descriptor).st_ino == identity:
            requests.append(size)
            returned.append(content)
            if len(requests) == 1:
                with path.open("ab") as stream:
                    stream.write(b"generated growth beyond metadata bound")
        return content

    monkeypatch.setattr(os, "read", read)
    with pytest.raises(ValueError, match="growth exceeds"):
        _pinned(tmp_path, path.name, sha256(b"{}").hexdigest(), expected_size=2)
    assert requests == [3, 1]
    assert sum(map(len, returned)) == 3


@pytest.mark.parametrize("replacement", ["equal_tree", "redirected_root"])
def test_archive_root_stays_owned_between_manifest_and_index(
    archive_inputs: tuple[Path, str, Path, str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    replacement: str,
) -> None:
    """Equal authenticated bytes cannot transfer an operation to another root."""
    from bijux_pollenomics.reporting.map_document.source_resources import (
        archive_reference,
        load_atlas_resource_catalogue,
        models,
    )

    catalogue, digest, archive, pin = archive_inputs
    prepared = tmp_path / "prepared-foreign-root"
    (prepared / "downloads").mkdir(parents=True)
    for member in ("manifest.json", "downloads/index.json"):
        (prepared / member).write_bytes((archive / member).read_bytes())
    (prepared / "foreign.body").write_bytes(b"unrelated generated owner")
    original = archive_reference._pinned
    reads: list[str] = []
    retained = tmp_path / "retained-original-root"

    def read(root: Path, member: str, *args: Any, **kwargs: Any) -> Any:
        result = original(root, member, *args, **kwargs)
        reads.append(member)
        if member == "manifest.json":
            archive.rename(retained)
            if replacement == "equal_tree":
                prepared.rename(archive)
            else:
                archive.symlink_to(prepared, target_is_directory=True)
        return result

    monkeypatch.setattr(archive_reference, "_pinned", read)
    with pytest.raises(ValueError):
        load_atlas_resource_catalogue(
            models.AtlasResourceCatalogueInput(
                catalogue,
                digest,
                archive=models.AtlasResourceArchiveInput(
                    archive, pin, "/data/neotoma/source-resources/"
                ),
            )
        )
    assert reads == ["manifest.json"]
    assert (retained / "manifest.json").is_file()
    assert (archive / "foreign.body").read_bytes() == b"unrelated generated owner"
