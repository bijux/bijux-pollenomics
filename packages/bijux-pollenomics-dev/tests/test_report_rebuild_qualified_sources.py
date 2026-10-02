"""Exercise external source identity and confinement before report execution."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild import qualified_sources
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import (
    SCHEMA,
    validated_external_report_sources,
)

DESCRIPTOR = Path("configs/ci/qualified-report-sources/chronology.json")
SOURCE_ID = "chronology/primary"


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _spec(path: Path) -> dict[str, object]:
    return {
        "path": path.name,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "size": path.stat().st_size,
    }


@pytest.fixture
def packet(tmp_path: Path) -> tuple[Path, Path, dict[str, Any]]:
    repository = tmp_path / "repository"
    store = tmp_path / "source-store"
    directory = store / SOURCE_ID
    directory.mkdir(parents=True)
    source = directory / "depths.csv"
    source.write_bytes(b"depth,age\n1,100\n")
    spec = _spec(source)
    authority = "https://example.org/primary"
    receipt = {
        "source_doi": "10.1234/chronology",
        "license": "CC-BY-4.0",
        "license_source": authority,
        "files": [
            {
                "file": source.name,
                "sha256": spec["sha256"],
                "http_status": 200,
                "http": {"content-length": str(spec["size"])},
                "url": "https://example.org/depths.csv",
            }
        ],
    }
    custody = directory / "source-manifest.json"
    _write(custody, receipt)
    descriptor = {
        "schema_version": SCHEMA,
        "source_id": SOURCE_ID,
        "source_doi": receipt["source_doi"],
        "license": receipt["license"],
        "authority_url": authority,
        "custody": _spec(custody),
        "files": [spec],
    }
    _write(repository / DESCRIPTOR, descriptor)
    return repository, store, descriptor


def test_external_bytes_are_bound_without_copying(
    packet: tuple[Path, Path, dict[str, Any]],
) -> None:
    repository, store, _ = packet
    before = sorted(path.relative_to(repository) for path in repository.rglob("*"))
    selected = validated_external_report_sources(repository, store, DESCRIPTOR)
    assert selected.directory == store / SOURCE_ID
    assert set(selected.inputs) == {
        DESCRIPTOR.as_posix(),
        f"external/{SOURCE_ID}/source-manifest.json",
        f"external/{SOURCE_ID}/depths.csv",
    }
    assert (
        selected.inputs[f"external/{SOURCE_ID}/depths.csv"]
        == store / SOURCE_ID / "depths.csv"
    )
    assert (
        sorted(path.relative_to(repository) for path in repository.rglob("*")) == before
    )
    (store / SOURCE_ID / "depths.csv").write_bytes(b"depth,age\n1,999\n")
    with pytest.raises(ReportRebuildError, match="bytes differ"):
        validated_external_report_sources(repository, store, DESCRIPTOR)


@pytest.mark.parametrize("target", ["store", "packet", "file", "custody", "descriptor"])
def test_symlink_sources_refuse_before_consumption(
    packet: tuple[Path, Path, dict[str, Any]], target: str
) -> None:
    repository, store, _ = packet
    paths = {
        "store": store,
        "packet": store / SOURCE_ID,
        "file": store / SOURCE_ID / "depths.csv",
        "custody": store / SOURCE_ID / "source-manifest.json",
        "descriptor": repository / DESCRIPTOR,
    }
    path = paths[target]
    moved = path.with_name(path.name + "-original")
    path.rename(moved)
    path.symlink_to(moved, target_is_directory=moved.is_dir())
    with pytest.raises(ReportRebuildError, match="non-real ancestor|real regular path"):
        validated_external_report_sources(repository, store, DESCRIPTOR)


@pytest.mark.parametrize(
    "field,value",
    [
        ("source_id", "../escaped"),
        ("source_id", "/absolute"),
        ("schema_version", "unsupported"),
        ("license", ""),
        ("authority_url", "http://example.org/primary"),
        ("authority_url", "https://user:secret@example.org/primary"),
    ],
)
def test_descriptor_relabeling_refuses(
    packet: tuple[Path, Path, dict[str, Any]], field: str, value: object
) -> None:
    repository, store, descriptor = packet
    descriptor[field] = value
    _write(repository / DESCRIPTOR, descriptor)
    with pytest.raises(ReportRebuildError):
        validated_external_report_sources(repository, store, DESCRIPTOR)


@pytest.mark.parametrize(
    "mutation",
    ["size", "hash", "traversal", "duplicate", "receipt-as-source", "unknown-field"],
)
def test_source_specification_is_exact(
    packet: tuple[Path, Path, dict[str, Any]], mutation: str
) -> None:
    repository, store, descriptor = packet
    spec = descriptor["files"][0]
    if mutation == "size":
        spec["size"] += 1
    elif mutation == "hash":
        spec["sha256"] = "0" * 64
    elif mutation == "traversal":
        spec["path"] = "../depths.csv"
    elif mutation == "duplicate":
        descriptor["files"].append(spec.copy())
    elif mutation == "receipt-as-source":
        descriptor["files"] = [descriptor["custody"].copy()]
    else:
        spec["unreviewed"] = True
    _write(repository / DESCRIPTOR, descriptor)
    with pytest.raises(ReportRebuildError):
        validated_external_report_sources(repository, store, DESCRIPTOR)


@pytest.mark.parametrize(
    "mutation",
    [
        "rights",
        "doi",
        "authority",
        "status",
        "url",
        "duplicate",
        "length",
        "receipt-bytes",
    ],
)
def test_custody_receipt_cannot_authorize_other_inputs(
    packet: tuple[Path, Path, dict[str, Any]], mutation: str
) -> None:
    repository, store, descriptor = packet
    path = store / SOURCE_ID / "source-manifest.json"
    receipt = json.loads(path.read_bytes())
    row = receipt["files"][0]
    if mutation == "rights":
        receipt["license"] = "unknown"
    elif mutation == "doi":
        receipt["source_doi"] = "10.9999/other"
    elif mutation == "authority":
        receipt["license_source"] = "https://example.org/other"
    elif mutation == "status":
        row["http_status"] = 403
    elif mutation == "url":
        row["url"] = "file:///not-a-retrieval"
    elif mutation == "duplicate":
        receipt["files"].append(row.copy())
    elif mutation == "length":
        row["http"]["content-length"] = "999"
    else:
        receipt["unreviewed"] = True
    _write(path, receipt)
    if mutation != "receipt-bytes":
        descriptor["custody"] = _spec(path)
        _write(repository / DESCRIPTOR, descriptor)
    with pytest.raises(ReportRebuildError):
        validated_external_report_sources(repository, store, DESCRIPTOR)


def test_store_inside_product_is_not_external(
    packet: tuple[Path, Path, dict[str, Any]],
) -> None:
    repository, store, _ = packet
    target = repository / "artifacts/source-store"
    target.parent.mkdir()
    store.rename(target)
    with pytest.raises(ReportRebuildError, match="separate from repository"):
        validated_external_report_sources(repository, target, DESCRIPTOR)


def test_duplicate_descriptor_keys_refuse(
    packet: tuple[Path, Path, dict[str, Any]],
) -> None:
    repository, store, _ = packet
    path = repository / DESCRIPTOR
    path.write_text('{"schema_version":"one","schema_version":"two"}', encoding="utf-8")
    with pytest.raises(ReportRebuildError, match="duplicate"):
        validated_external_report_sources(repository, store, DESCRIPTOR)


def test_receipt_changed_between_hash_and_parse_refuses(
    packet: tuple[Path, Path, dict[str, Any]], monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, store, _ = packet
    checked = qualified_sources._checked_file

    def replace_receipt(directory: Path, spec: dict[str, Any]) -> Path:
        path = checked(directory, spec)
        if path.name == "source-manifest.json":
            value = json.loads(path.read_bytes())
            value["unreviewed"] = True
            _write(path, value)
        return path

    monkeypatch.setattr(qualified_sources, "_checked_file", replace_receipt)
    with pytest.raises(ReportRebuildError, match="changed before parsing"):
        validated_external_report_sources(repository, store, DESCRIPTOR)


def test_repository_descriptor_cannot_replace_external_input_label(
    packet: tuple[Path, Path, dict[str, Any]],
) -> None:
    repository, store, descriptor = packet
    path = Path(f"external/{SOURCE_ID}/source-manifest.json")
    _write(repository / path, descriptor)
    with pytest.raises(ReportRebuildError, match="overlaps external input namespace"):
        validated_external_report_sources(repository, store, path)
