"""One anchored portable projection retains every direct native occurrence."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

import pytest

from .native_products import products


def owner() -> Any:
    return importlib.import_module(
        "bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.evidence"
    )


def test_complete_publication_reopens_with_exact_source_and_restrictive_metadata(
    tmp_path: Path,
) -> None:
    inputs = products(tmp_path)
    destination = tmp_path / "evidence"
    result = owner().publish_neotoma_linked_evidence(destination, **inputs)
    index = owner().load_neotoma_linked_evidence(
        destination,
        expected_manifest_sha256=result.manifest_sha256,
        **inputs,
    )
    assert index["authority"]["resource_count"] == 3
    assert index["authority"]["facet_slot_count"] == 24
    assert index["occurrence_count"] == 8
    assert (
        index["targets"]["contact-900"]["exposure_role"]
        == "heldout_no_numerical_access"
    )
    assert index["targets"]["taxon-11"]["occurrence_count"] == 2
    assert b"/Users/" not in (destination / "evidence-manifest.json").read_bytes()
    selected = owner().read_neotoma_linked_evidence_target(
        destination,
        expected_manifest_sha256=result.manifest_sha256,
        kind="taxon",
        native_id=11,
    )
    assert len(selected["source_proofs"]) == len(selected["proof_locators"]) == 2
    assert {row["root_dataset_id"] for row in selected["source_proofs"]} == {201, 203}
    assert all(
        row["evidence_manifest_sha256"] == result.manifest_sha256
        for row in selected["proof_locators"]
    )


def test_reopen_hashes_old_sources_without_repeating_semantic_discovery(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs = products(tmp_path)
    module = owner()
    result = module.publish_neotoma_linked_evidence(tmp_path / "evidence", **inputs)
    monkeypatch.setattr(
        module,
        "discover_neotoma_facet_links",
        lambda *a, **k: pytest.fail("semantic source replay repeated"),
    )
    module.load_neotoma_linked_evidence(
        result.directory, expected_manifest_sha256=result.manifest_sha256, **inputs
    )
    source = next(iter(inputs["source_facets"].values()))
    next(source.glob("*.body")).write_bytes(b'{"changed":true}')
    with pytest.raises(ValueError, match="source|digest|pin"):
        module.load_neotoma_linked_evidence(
            result.directory, expected_manifest_sha256=result.manifest_sha256, **inputs
        )


def test_rehashed_index_cannot_replace_the_external_evidence_anchor(
    tmp_path: Path,
) -> None:
    inputs = products(tmp_path)
    result = owner().publish_neotoma_linked_evidence(tmp_path / "evidence", **inputs)
    path = result.directory / "evidence-manifest.json"
    index = json.loads(path.read_bytes())
    index["targets"]["contact-900"]["exposure_role"] = "development_resource_discovery"
    path.write_text(json.dumps(index))
    with pytest.raises(ValueError, match="identity|digest|manifest"):
        owner().load_neotoma_linked_evidence(
            result.directory, expected_manifest_sha256=result.manifest_sha256, **inputs
        )


def test_existing_foreign_output_is_refused_without_source_authentication(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "foreign"
    destination.mkdir()
    (destination / "user.txt").write_bytes(b"user bytes")
    with pytest.raises(FileExistsError):
        owner().publish_neotoma_linked_evidence(
            destination, expected_roster_sha256="f" * 64, scope=None, source_facets={}
        )
    assert (destination / "user.txt").read_bytes() == b"user bytes"


def test_protected_metadata_is_validated_before_any_predecessor_body_buffer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs = products(tmp_path, native_pi=True)
    source_roots = set(inputs["source_facets"].values())
    original = Path.open
    reads = []

    def observe(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.parent in source_roots and path.suffix == ".body":
            reads.append(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observe)
    with pytest.raises(ValueError):
        owner().publish_neotoma_linked_evidence(tmp_path / "evidence", **inputs)
    assert reads == []


def test_source_mutation_during_evidence_read_is_refused(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs = products(tmp_path)
    module = owner()
    result = module.publish_neotoma_linked_evidence(tmp_path / "evidence", **inputs)
    original = module._part
    body = next(next(iter(inputs["source_facets"].values())).glob("*.body"))

    def mutate(*args: Any, **kwargs: Any) -> Any:
        part = original(*args, **kwargs)
        body.write_bytes(b'{"late":"source mutation"}')
        return part

    monkeypatch.setattr(module, "_part", mutate)
    with pytest.raises(ValueError, match="source|pin|namespace"):
        module.load_neotoma_linked_evidence(
            result.directory, expected_manifest_sha256=result.manifest_sha256, **inputs
        )


def test_unclaimed_protected_body_is_not_hashed_as_a_source_input(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs = products(tmp_path, separate=True)
    root = next(
        p for p in inputs["source_facets"].values() if p.name == "protected-facets"
    )
    foreign = root / "unclaimed.body"
    foreign.write_bytes(b'{"protected":"unreviewed outcome"}')
    original = Path.open
    reads = []

    def observe(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path == foreign:
            reads.append(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observe)
    with pytest.raises(ValueError):
        owner().publish_neotoma_linked_evidence(tmp_path / "evidence", **inputs)
    assert reads == []


def test_namespace_refuses_unexpected_subtree_before_descent_or_body_open(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import os

    module = owner()
    result = module.publish_neotoma_linked_evidence(
        tmp_path / "evidence", **products(tmp_path)
    )
    index = json.loads((result.directory / "evidence-manifest.json").read_bytes())
    foreign = result.directory / "foreign-tree"
    foreign.mkdir()
    (foreign / "outcome.body").write_bytes(b'{"foreign":"not authorized"}')
    original_scan, original_open = os.scandir, Path.open
    forbidden = foreign.stat().st_ino
    body_reads = []

    def scan(directory: Any) -> Any:
        node = os.fstat(directory) if type(directory) is int else Path(directory).stat()
        assert node.st_ino != forbidden, "Unexpected subtree was descended"
        return original_scan(directory)

    def observe(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.suffix == ".body":
            body_reads.append(path)
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(os, "scandir", scan)
    monkeypatch.setattr(Path, "open", observe)
    with pytest.raises(ValueError, match="[Nn]amespace"):
        module._namespace(result.directory, index)
    assert body_reads == []


def test_namespace_stops_growing_enumerator_without_materializing_all_entries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import os

    module = owner()
    result = module.publish_neotoma_linked_evidence(
        tmp_path / "evidence", **products(tmp_path)
    )
    index = json.loads((result.directory / "evidence-manifest.json").read_bytes())
    original_scan = os.scandir
    with original_scan(result.directory) as entries:
        initial = sorted(entries, key=lambda entry: entry.name)
    inode = result.directory.stat().st_ino
    consumed = []

    class Growing:
        def __enter__(self) -> Any:
            return self

        def __exit__(self, *args: Any) -> None:
            return None

        def __iter__(self) -> Any:
            for entry in initial:
                consumed.append(entry.name)
                yield entry
            for _ in range(4):
                consumed.append(initial[0].name)
                yield initial[0]
            pytest.fail("Unbounded namespace enumerator was fully consumed")

    def scan(directory: Any) -> Any:
        node = os.fstat(directory) if type(directory) is int else Path(directory).stat()
        return Growing() if node.st_ino == inode else original_scan(directory)

    monkeypatch.setattr(os, "scandir", scan)
    with pytest.raises(ValueError, match="[Nn]amespace"):
        module._namespace(result.directory, index)
    assert len(consumed) <= len(initial) + 1
