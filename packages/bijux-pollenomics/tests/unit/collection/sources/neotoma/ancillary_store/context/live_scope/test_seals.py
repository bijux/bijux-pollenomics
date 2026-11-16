"""Current source metadata stays physical, finite and scoped to one lifetime."""

import os
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context.seals import (
    _CurrentContextSeals,
)


def options(inputs: dict[str, Any]) -> dict[str, Any]:
    return {
        key: inputs[key]
        for key in (
            "context_directory",
            "expected_context_sha256",
            "native_archive_directory",
        )
    }


def permission(inputs: dict[str, Any], member: str) -> Path:
    context = Path(inputs["context_directory"])
    native = Path(inputs["native_archive_directory"])
    body = next((native / "captures").glob("*/*.body"))
    return {
        "context": context / "manifest.json",
        "roster": native / "catalogue/source-inventory.json",
        "native": native / "manifest.json",
        "catalogue": native / "catalogue/manifest.json",
        "catalogue_body": native / "catalogue/catalogue.json",
        "catalogue_descriptor": next(
            (native / "catalogue/captures").glob("*/descriptor.json")
        ),
        "metadata_manifest": body.parent / "capture-manifest.json",
        "metadata_body": body,
        "legacy": next((context / "rosters").glob("*.json")),
        "exposure": next((context / "evidence/exposure").glob("*.json")),
    }[member]


def observe(monkeypatch: Any) -> tuple[list[int], list[Path]]:
    original = os.open
    descriptors: list[int] = []
    bodies: list[Path] = []

    def opened(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        fd = original(path, flags, *args, **kwargs)
        descriptors.append(fd)
        if not flags & os.O_DIRECTORY and Path(path).suffix == ".body":
            bodies.append(Path(path))
        return fd

    monkeypatch.setattr(os, "open", opened)
    monkeypatch.setattr(os, "supports_dir_fd", os.supports_dir_fd | {opened})
    return descriptors, bodies


def test_guard_is_single_lifetime_and_opens_no_entity_body(
    capsule_inputs: dict[str, Any], monkeypatch: Any
) -> None:
    guard = _CurrentContextSeals(**options(capsule_inputs))
    descriptors, bodies = observe(monkeypatch)
    with pytest.raises(ValueError, match="not active"):
        guard.check()
    with guard:
        guard.check()
    with pytest.raises(ValueError, match="not active"):
        guard.check()
    with pytest.raises(ValueError, match="reused"):
        guard.__enter__()
    assert bodies == [] and descriptors
    for fd in descriptors:
        with pytest.raises(OSError):
            os.fstat(fd)


@pytest.mark.parametrize(
    "member",
    [
        "context",
        "roster",
        "native",
        "catalogue",
        "catalogue_body",
        "catalogue_descriptor",
        "metadata_manifest",
        "metadata_body",
        "legacy",
        "exposure",
    ],
)
@pytest.mark.parametrize("change", ["inplace", "replacement"])
def test_every_current_dependency_is_checked_without_body_reads(
    capsule_inputs: dict[str, Any], monkeypatch: Any, member: str, change: str
) -> None:
    path = permission(capsule_inputs, member)
    _, bodies = observe(monkeypatch)
    with (
        pytest.raises(ValueError, match="changed"),
        _CurrentContextSeals(**options(capsule_inputs)) as guard,
    ):
        if change == "inplace":
            path.write_bytes(path.read_bytes() + b"\n")
        else:
            replacement = path.with_suffix(".replacement")
            replacement.write_bytes(path.read_bytes())
            replacement.replace(path)
        guard.check()
    assert bodies == []


@pytest.mark.parametrize("alias", ["symlink", "hardlink", "fifo"])
def test_metadata_alias_refuses_without_opening_its_body(
    capsule_inputs: dict[str, Any], tmp_path: Path, monkeypatch: Any, alias: str
) -> None:
    path = permission(capsule_inputs, "metadata_body")
    foreign = tmp_path / "foreign.body"
    path.rename(foreign)
    if alias == "symlink":
        path.symlink_to(foreign)
    elif alias == "hardlink":
        os.link(foreign, path)
    else:
        os.mkfifo(path)
    _, bodies = observe(monkeypatch)
    with pytest.raises(ValueError), _CurrentContextSeals(**options(capsule_inputs)):
        pytest.fail("Aliased current dependency was accepted")
    assert bodies == [] and foreign.is_file()


def test_subclass_cannot_replace_live_checks(capsule_inputs: dict[str, Any]) -> None:
    class Unchecked(_CurrentContextSeals):
        def check(self) -> None:
            return None

    with pytest.raises(ValueError), Unchecked(**options(capsule_inputs)):
        pytest.fail("Subclass replaced the current source operation")


def test_unique_metadata_bytes_are_bounded_without_reading_sparse_members(
    capsule_inputs: dict[str, Any], tmp_path: Path, monkeypatch: Any
) -> None:
    from bijux_pollenomics.core.filesystem import BoundedInputTree

    guard = _CurrentContextSeals(**options(capsule_inputs))
    monkeypatch.setattr(
        BoundedInputTree,
        "read",
        lambda *args, **kwargs: pytest.fail(
            "A metadata budget inventory opened a body"
        ),
    )
    try:
        for name in ("first-budget", "second-budget"):
            directory = tmp_path / name
            directory.mkdir()
            with (directory / "member.bin").open("wb") as stream:
                stream.truncate(320 * 1024 * 1024)
        guard._seal(tmp_path / "first-budget")
        with pytest.raises(ValueError, match="finite bounds"):
            guard._seal(tmp_path / "second-budget")
    finally:
        guard._close()


def test_metadata_count_bound_is_aggregate_across_independent_roots(
    capsule_inputs: dict[str, Any], tmp_path: Path
) -> None:
    guard = _CurrentContextSeals(**options(capsule_inputs))
    try:
        for name in ("first-count", "second-count"):
            directory = tmp_path / name
            directory.mkdir()
            for index in range(10000):
                (directory / str(index)).touch()
            guard._seal(directory)
        assert len(guard._members) == 20000
        extra = tmp_path / "excess-count"
        extra.mkdir()
        (extra / "one").touch()
        with pytest.raises(ValueError, match="finite bounds"):
            guard._seal(extra)
    finally:
        guard._close()


def test_primary_error_survives_a_later_current_context_change(
    capsule_inputs: dict[str, Any],
) -> None:
    primary = OSError("Source operation failed")
    with (
        pytest.raises(OSError) as raised,
        _CurrentContextSeals(**options(capsule_inputs)),
    ):
        path = permission(capsule_inputs, "context")
        path.write_bytes(path.read_bytes() + b"\n")
        raise primary
    assert raised.value is primary
