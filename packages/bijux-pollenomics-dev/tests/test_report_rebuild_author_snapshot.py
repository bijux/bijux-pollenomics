"""Require complete author custody identity without inventing source permission."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild import author_snapshot
from bijux_pollenomics_dev.ci.report_rebuild.author_snapshot import SCHEMA
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import _checked_file
from bijux_pollenomics_dev.ci.report_rebuild.source_qualification import (
    validated_external_report_sources,
)

DESCRIPTOR = Path("configs/ci/qualified-report-sources/author-snapshot.json")
SOURCE_ID = "study/author-reference"


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _spec(directory: Path, name: str) -> dict[str, Any]:
    payload = (directory / name).read_bytes()
    return {
        "path": name,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "size": len(payload),
    }


@pytest.fixture
def packet(tmp_path: Path) -> tuple[Path, Path, dict[str, Any]]:
    repository = tmp_path / "repository"
    store = tmp_path / "source-store"
    directory = store / SOURCE_ID
    (directory / "author").mkdir(parents=True)
    (directory / "author/counts.csv").write_bytes(b"taxon,count\nA,10\n")
    (directory / "author/py.typed").write_bytes(b"")
    specs = [
        _spec(directory, name) for name in ("author/counts.csv", "author/py.typed")
    ]
    manifest = {
        "schema_version": "original-author-snapshot.v1",
        "file_count": len(specs),
        "files": {spec["path"]: spec["sha256"] for spec in specs},
    }
    _write(directory / "snapshot-manifest.json", manifest)
    descriptor = {
        "schema_version": SCHEMA,
        "source_id": SOURCE_ID,
        "snapshot_schema_version": manifest["schema_version"],
        "file_count": len(specs),
        "manifest": _spec(directory, "snapshot-manifest.json"),
        "files": specs,
    }
    _write(repository / DESCRIPTOR, descriptor)
    return repository, store, descriptor


def _repin_manifest(
    packet: tuple[Path, Path, dict[str, Any]], manifest: object
) -> None:
    repository, store, descriptor = packet
    directory = store / SOURCE_ID
    _write(directory / "snapshot-manifest.json", manifest)
    descriptor["manifest"] = _spec(directory, "snapshot-manifest.json")
    _write(repository / DESCRIPTOR, descriptor)


def test_complete_snapshot_is_read_in_place_including_empty_marker(
    packet: tuple[Path, Path, dict[str, Any]],
) -> None:
    repository, store, descriptor = packet
    before = {
        path: path.read_bytes()
        for root in (repository, store)
        for path in root.rglob("*")
        if path.is_file()
    }
    selected = validated_external_report_sources(repository, store, DESCRIPTOR)
    expected = {
        DESCRIPTOR.as_posix(): repository / DESCRIPTOR,
        f"external/{SOURCE_ID}/snapshot-manifest.json": store
        / SOURCE_ID
        / "snapshot-manifest.json",
        **{
            f"external/{SOURCE_ID}/{row['path']}": store / SOURCE_ID / row["path"]
            for row in descriptor["files"]
        },
    }
    assert selected.directory == store / SOURCE_ID
    assert selected.inputs == expected
    assert (
        selected.descriptor_sha256
        == hashlib.sha256((repository / DESCRIPTOR).read_bytes()).hexdigest()
    )
    assert before == {
        path: path.read_bytes()
        for root in (repository, store)
        for path in root.rglob("*")
        if path.is_file()
    }


@pytest.mark.parametrize(
    "target",
    ["repository", "store", "packet", "ancestor", "file", "manifest", "descriptor"],
)
def test_symlinked_roots_ancestors_and_leaves_refuse(
    packet: tuple[Path, Path, dict[str, Any]], target: str
) -> None:
    repository, store, _ = packet
    paths = {
        "repository": repository,
        "store": store,
        "packet": store / SOURCE_ID,
        "ancestor": store / SOURCE_ID / "author",
        "file": store / SOURCE_ID / "author/counts.csv",
        "manifest": store / SOURCE_ID / "snapshot-manifest.json",
        "descriptor": repository / DESCRIPTOR,
    }
    path = paths[target]
    retained = path.with_name(path.name + "-original")
    path.rename(retained)
    path.symlink_to(retained, target_is_directory=retained.is_dir())
    with pytest.raises(ReportRebuildError, match="non-real ancestor|real regular path"):
        validated_external_report_sources(repository, store, DESCRIPTOR)


@pytest.mark.parametrize(
    "field,value",
    [
        ("schema_version", "unsupported"),
        ("snapshot_schema_version", "other-snapshot.v1"),
        ("snapshot_schema_version", ""),
        ("source_id", "../escaped"),
        ("source_id", "/absolute"),
        ("source_id", "study//author-reference"),
        ("source_id", "study\\author-reference"),
        ("source_id", "null\x00name"),
        ("file_count", True),
        ("file_count", 2.0),
        ("file_count", 0),
        ("file_count", 4097),
        ("file_count", 1),
        ("license", "invented permission"),
    ],
)
def test_descriptor_contract_cannot_be_relabelled(
    packet: tuple[Path, Path, dict[str, Any]], field: str, value: object
) -> None:
    repository, store, descriptor = packet
    descriptor[field] = value
    _write(repository / DESCRIPTOR, descriptor)
    with pytest.raises(ReportRebuildError):
        validated_external_report_sources(repository, store, DESCRIPTOR)


@pytest.mark.parametrize(
    "mutation",
    [
        "duplicate",
        "order",
        "subset",
        "traversal",
        "null",
        "hash",
        "uppercase-hash",
        "bool-size",
        "negative-size",
        "float-size",
        "extra-field",
        "manifest-as-source",
    ],
)
def test_independent_file_list_is_exact(
    packet: tuple[Path, Path, dict[str, Any]], mutation: str
) -> None:
    repository, store, descriptor = packet
    first = descriptor["files"][0]
    if mutation == "duplicate":
        descriptor["files"][1] = first.copy()
    elif mutation == "order":
        descriptor["files"].reverse()
    elif mutation == "subset":
        descriptor["files"].pop()
    elif mutation == "traversal":
        first["path"] = "../escaped"
    elif mutation == "null":
        first["path"] = "null\x00file"
    elif mutation == "hash":
        first["sha256"] = "0" * 64
    elif mutation == "uppercase-hash":
        first["sha256"] = first["sha256"].upper()
    elif mutation == "bool-size":
        first["size"] = True
    elif mutation == "negative-size":
        first["size"] = -1
    elif mutation == "float-size":
        first["size"] = float(first["size"])
    elif mutation == "extra-field":
        first["license"] = "unreviewed"
    else:
        descriptor["files"][0] = descriptor["manifest"].copy()
    _write(repository / DESCRIPTOR, descriptor)
    with pytest.raises(ReportRebuildError):
        validated_external_report_sources(repository, store, DESCRIPTOR)


@pytest.mark.parametrize(
    "mutation",
    [
        "count",
        "bool-count",
        "schema",
        "subset",
        "extra-file",
        "file-digest",
        "extra-field",
    ],
)
def test_repinning_manifest_cannot_override_independent_population(
    packet: tuple[Path, Path, dict[str, Any]], mutation: str
) -> None:
    _, store, _ = packet
    manifest = json.loads((store / SOURCE_ID / "snapshot-manifest.json").read_bytes())
    if mutation == "count":
        manifest["file_count"] -= 1
    elif mutation == "bool-count":
        manifest["file_count"] = True
    elif mutation == "schema":
        manifest["schema_version"] = "other-snapshot.v1"
    elif mutation == "subset":
        manifest["files"].pop("author/py.typed")
    elif mutation == "extra-file":
        manifest["files"]["author/unapproved.csv"] = "0" * 64
    elif mutation == "file-digest":
        manifest["files"]["author/counts.csv"] = "0" * 64
    else:
        manifest["license"] = "unreviewed"
    _repin_manifest(packet, manifest)
    repository, store, _ = packet
    with pytest.raises(ReportRebuildError):
        validated_external_report_sources(repository, store, DESCRIPTOR)


@pytest.mark.parametrize("target", ["source", "manifest"])
def test_original_byte_mutation_refuses(
    packet: tuple[Path, Path, dict[str, Any]], target: str
) -> None:
    repository, store, _ = packet
    name = "author/counts.csv" if target == "source" else "snapshot-manifest.json"
    (store / SOURCE_ID / name).write_bytes(b"changed\n")
    with pytest.raises(ReportRebuildError, match="bytes differ"):
        validated_external_report_sources(repository, store, DESCRIPTOR)


@pytest.mark.parametrize(
    "mutation", ["size", "hash", "zero-size", "oversize", "traversal", "unknown-field"]
)
def test_manifest_pin_is_independent(
    packet: tuple[Path, Path, dict[str, Any]], mutation: str
) -> None:
    repository, store, descriptor = packet
    spec = descriptor["manifest"]
    if mutation == "size":
        spec["size"] += 1
    elif mutation == "hash":
        spec["sha256"] = "0" * 64
    elif mutation == "zero-size":
        spec["size"] = 0
    elif mutation == "oversize":
        spec["size"] = 8 * 1024 * 1024 + 1
    elif mutation == "traversal":
        spec["path"] = "../snapshot-manifest.json"
    else:
        spec["unreviewed"] = True
    _write(repository / DESCRIPTOR, descriptor)
    with pytest.raises(ReportRebuildError):
        validated_external_report_sources(repository, store, DESCRIPTOR)


@pytest.mark.parametrize("target", ["descriptor", "manifest"])
def test_duplicate_json_keys_refuse_even_with_repinned_manifest(
    packet: tuple[Path, Path, dict[str, Any]], target: str
) -> None:
    repository, store, descriptor = packet
    path = (
        repository / DESCRIPTOR
        if target == "descriptor"
        else store / SOURCE_ID / "snapshot-manifest.json"
    )
    path.write_bytes(b'{"files":{},"files":{}}')
    if target == "manifest":
        descriptor["manifest"] = _spec(store / SOURCE_ID, "snapshot-manifest.json")
        _write(repository / DESCRIPTOR, descriptor)
    with pytest.raises(ReportRebuildError, match="duplicate"):
        validated_external_report_sources(repository, store, DESCRIPTOR)


@pytest.mark.parametrize("placement", ["inside", "ancestor"])
def test_external_store_cannot_overlap_product(
    packet: tuple[Path, Path, dict[str, Any]], placement: str
) -> None:
    repository, store, _ = packet
    if placement == "inside":
        destination = repository / "artifacts/source-store"
        destination.parent.mkdir()
        store.rename(destination)
    else:
        destination = repository.parent
    with pytest.raises(ReportRebuildError, match="separate from repository"):
        validated_external_report_sources(repository, destination, DESCRIPTOR)


@pytest.mark.parametrize(
    "target", ["source", "manifest-before-parse", "manifest-after-parse", "descriptor"]
)
def test_changes_during_validation_refuse(
    packet: tuple[Path, Path, dict[str, Any]],
    monkeypatch: pytest.MonkeyPatch,
    target: str,
) -> None:
    repository, store, _ = packet
    checked = _checked_file
    changed = False

    def mutate(directory: Path, spec: dict[str, Any]) -> Path:
        nonlocal changed
        path = checked(directory, spec)
        if not changed and spec["path"] == (
            "snapshot-manifest.json"
            if target == "manifest-before-parse"
            else "author/py.typed"
        ):
            changed = True
            names = {
                "source": directory / "author/counts.csv",
                "manifest-before-parse": directory / "snapshot-manifest.json",
                "manifest-after-parse": directory / "snapshot-manifest.json",
                "descriptor": repository / DESCRIPTOR,
            }
            with names[target].open("ab") as stream:
                stream.write(b" ")
        return path

    monkeypatch.setattr(author_snapshot, "_checked_file", mutate)
    with pytest.raises(ReportRebuildError, match="bytes differ|changed"):
        validated_external_report_sources(repository, store, DESCRIPTOR)


def test_descriptor_namespace_remains_disjoint(
    packet: tuple[Path, Path, dict[str, Any]],
) -> None:
    repository, store, descriptor = packet
    path = Path(f"external/{SOURCE_ID}/snapshot-manifest.json")
    _write(repository / path, descriptor)
    with pytest.raises(ReportRebuildError, match="overlaps external input namespace"):
        validated_external_report_sources(repository, store, path)


@pytest.mark.parametrize("kind", ["directory", "fifo", "missing"])
def test_nonregular_source_refuses_without_opening(
    packet: tuple[Path, Path, dict[str, Any]], kind: str
) -> None:
    repository, store, _ = packet
    path = store / SOURCE_ID / "author/counts.csv"
    path.unlink()
    if kind == "directory":
        path.mkdir()
    elif kind == "fifo":
        os.mkfifo(path)
    with pytest.raises(ReportRebuildError, match="real regular path|unreadable"):
        validated_external_report_sources(repository, store, DESCRIPTOR)


def test_duplicate_nested_manifest_paths_refuse(
    packet: tuple[Path, Path, dict[str, Any]],
) -> None:
    repository, store, descriptor = packet
    directory = store / SOURCE_ID
    path = directory / "snapshot-manifest.json"
    path.write_bytes(
        b'{"schema_version":"original-author-snapshot.v1","file_count":2,"files":{"author/counts.csv":"first","author/counts.csv":"second"}}'
    )
    descriptor["manifest"] = _spec(directory, path.name)
    _write(repository / DESCRIPTOR, descriptor)
    with pytest.raises(ReportRebuildError, match="duplicate"):
        validated_external_report_sources(repository, store, DESCRIPTOR)


def test_source_size_is_checked_independently_of_manifest_hash(
    packet: tuple[Path, Path, dict[str, Any]],
) -> None:
    repository, store, descriptor = packet
    descriptor["files"][0]["size"] += 1
    _write(repository / DESCRIPTOR, descriptor)
    with pytest.raises(ReportRebuildError, match="bytes differ"):
        validated_external_report_sources(repository, store, DESCRIPTOR)
