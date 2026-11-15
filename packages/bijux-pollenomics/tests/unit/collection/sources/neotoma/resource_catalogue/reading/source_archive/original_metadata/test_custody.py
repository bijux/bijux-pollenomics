"""Closed metadata witness claims cannot bypass its native or catalogue proofs."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import shutil
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.resource_catalogue import archive
from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive import (
    original_metadata,
)
from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.custody import (
    _original_metadata,
)


@pytest.mark.parametrize(
    "field,value",
    [
        ("scope", "complete_relational_snapshot"),
        ("dataset_row_count", True),
        ("dataset_row_count", 1),
        ("dataset_part_count", 1.0),
        ("dataset_part_count", 1),
        ("manifest_path", "catalogue/manifest.json"),
        ("manifest_sha256", "0" * 64),
        ("unknown_claim", "admitted"),
    ],
)
def test_rehashed_metadata_claim_must_equal_its_exact_source(
    portable_original: tuple[Path, str, Path], field: str, value: object
) -> None:
    output, _, _ = portable_original
    path = output / "manifest.json"
    manifest = json.loads(path.read_bytes())
    manifest.setdefault("original_metadata", {})[field] = value
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        archive.load_neotoma_source_archive(
            output, expected_manifest_sha256=sha256(path.read_bytes()).hexdigest()
        )


@pytest.mark.parametrize("change_manifest", [False, True])
def test_rehashed_part_still_requires_original_catalogue_epoch(
    portable_original: tuple[Path, str, Path], change_manifest: bool
) -> None:
    output, _, _ = portable_original
    part = output / "captures/original-metadata/surfaces/datasets/201.json"
    assert part.exists()
    document = json.loads(part.read_bytes())
    document["rows"][0]["source_payload"]["datasetid"] = 999
    part.write_text(json.dumps(document))
    root = output / "manifest.json"
    manifest = json.loads(root.read_bytes())
    relative = part.relative_to(output).as_posix()
    manifest["files"][relative] = {
        "bytes": part.stat().st_size,
        "sha256": sha256(part.read_bytes()).hexdigest(),
    }
    if change_manifest:
        witness = output / "captures/original-metadata/manifest.json"
        native = json.loads(witness.read_bytes())
        native["surfaces"]["datasets"]["parts"][0]["sha256"] = sha256(
            part.read_bytes()
        ).hexdigest()
        witness.write_text(json.dumps(native))
        manifest["files"][witness.relative_to(output).as_posix()] = {
            "bytes": witness.stat().st_size,
            "sha256": sha256(witness.read_bytes()).hexdigest(),
        }
        manifest["original_metadata"]["manifest_sha256"] = sha256(
            witness.read_bytes()
        ).hexdigest()
    manifest["source_bytes"] = sum(row["bytes"] for row in manifest["files"].values())
    root.write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        archive.load_neotoma_source_archive(
            output, expected_manifest_sha256=sha256(root.read_bytes()).hexdigest()
        )


def test_matching_external_metadata_is_optional_but_conflicts_refuse(
    portable_original: tuple[Path, str, Path], tmp_path: Path
) -> None:
    output, digest, original = portable_original
    copy = tmp_path / "other-original"
    shutil.copytree(original, copy)
    archive.load_neotoma_source_archive(
        output, expected_manifest_sha256=digest, original_relational_root=copy
    )
    path = copy / "manifest.json"
    document = json.loads(path.read_bytes())
    document["unrelated_native_epoch_field"] = None
    path.write_text(json.dumps(document))
    with pytest.raises(ValueError, match="original.*metadata|metadata.*witness"):
        archive.load_neotoma_source_archive(
            output, expected_manifest_sha256=digest, original_relational_root=copy
        )


@pytest.mark.parametrize("change", ["missing_part", "extra_numerical", "missing_scope"])
def test_original_metadata_namespace_is_exact(
    portable_original: tuple[Path, str, Path], change: str
) -> None:
    output, _, _ = portable_original
    root = output / "manifest.json"
    manifest = json.loads(root.read_bytes())
    if change == "missing_part":
        relative = "captures/original-metadata/surfaces/datasets/201.json"
        (output / relative).unlink()
        del manifest["files"][relative]
    elif change == "extra_numerical":
        relative = "captures/original-metadata/numerical-not-supplied.json"
        content = b'{"unadmitted_source":true}'
        (output / relative).write_bytes(content)
        manifest["files"][relative] = {
            "bytes": len(content),
            "sha256": sha256(content).hexdigest(),
        }
    else:
        del manifest["original_metadata"]
    manifest["source_bytes"] = sum(row["bytes"] for row in manifest["files"].values())
    root.write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        archive.load_neotoma_source_archive(
            output, expected_manifest_sha256=sha256(root.read_bytes()).hexdigest()
        )


@pytest.mark.parametrize("surfaces", [None, []])
def test_rehashed_native_manifest_with_malformed_surfaces_refuses(
    portable_original: tuple[Path, str, Path], surfaces: object
) -> None:
    output, _, _ = portable_original
    path = output / "captures/original-metadata/manifest.json"
    document = json.loads(path.read_bytes())
    document["surfaces"] = surfaces
    path.write_text(json.dumps(document))
    root = output / "manifest.json"
    manifest = json.loads(root.read_bytes())
    manifest["files"][path.relative_to(output).as_posix()] = {
        "bytes": path.stat().st_size,
        "sha256": sha256(path.read_bytes()).hexdigest(),
    }
    manifest["original_metadata"]["manifest_sha256"] = sha256(
        path.read_bytes()
    ).hexdigest()
    manifest["source_bytes"] = sum(row["bytes"] for row in manifest["files"].values())
    root.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="metadata witness"):
        archive.load_neotoma_source_archive(
            output, expected_manifest_sha256=sha256(root.read_bytes()).hexdigest()
        )


def sparse_metadata(root: Path, count: int, size: int) -> None:
    parts = []
    for index in range(count):
        relative = f"surfaces/datasets/{index}.json"
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as stream:
            stream.truncate(size)
        parts.append({"path": relative, "sha256": "a" * 64})
    (root / "manifest.json").write_text(
        json.dumps({"surfaces": {"datasets": {"row_count": 0, "parts": parts}}})
    )


@pytest.mark.parametrize("limit", ["total", "manifest_in_total", "entity"])
def test_external_metadata_preflight_refuses_before_any_native_part_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, limit: str
) -> None:
    root = tmp_path / "external-metadata"
    count = {"total": 33, "manifest_in_total": 32, "entity": 1}[limit]
    sparse_metadata(root, count, 16 * 1024 * 1024 + (1 if limit == "entity" else 0))
    calls: list[Path | None] = []
    native = _original_metadata
    read = Path.open

    def observed_native(selected: Path | None) -> object:
        calls.append(selected)
        return native(selected)

    def observed_buffer(selected: Path, *args: Any, **kwargs: Any) -> Any:
        if selected.parent.name == "datasets":
            pytest.fail("oversized external metadata part buffer opened")
        return read(selected, *args, **kwargs)

    monkeypatch.setattr(original_metadata, "_original_metadata", observed_native)
    monkeypatch.setattr(Path, "open", observed_buffer)
    with pytest.raises(ValueError):
        original_metadata.metadata_inventory(root)
    assert calls == []


def test_archive_preflights_external_metadata_before_initial_catalogue_replay(
    original_catalogue: tuple[Path, str, dict[str, Path], Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    catalogue, digest, sources, original = original_catalogue
    sparse_metadata(original, 33, 16 * 1024 * 1024)
    read = Path.open

    def observed(selected: Path, *args: Any, **kwargs: Any) -> Any:
        if selected.parent.name == "datasets":
            pytest.fail("archive replay opened over-budget external metadata")
        return read(selected, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observed)
    with pytest.raises(ValueError):
        archive.write_neotoma_source_archive(
            tmp_path / "portable",
            catalogue_directory=catalogue,
            expected_catalogue_manifest_sha256=digest,
            capture_sources=sources,
            original_relational_root=original,
        )
    assert not (tmp_path / ".portable.staging").exists()


def test_metadata_preflight_does_not_reread_dataset_buffers(
    original_catalogue: tuple[Path, str, dict[str, Path], Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, _, _, original = original_catalogue
    opened: list[Path] = []
    read = Path.open

    def observed(selected: Path, *args: Any, **kwargs: Any) -> Any:
        if selected.parent.name == "datasets":
            opened.append(selected)
        return read(selected, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observed)
    claim, _ = original_metadata.metadata_inventory(original)
    assert claim["dataset_row_count"] == 2
    assert sorted(opened) == sorted((original / "surfaces/datasets").glob("*.json"))
