"""Bounded capsules preserve literal captures and compact source occurrence joins."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pytest


def test_capsule_is_portable_with_separate_legacy_and_current_proofs(
    capsule_inputs: dict[str, Any], tmp_path: Path
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule import (
        load_neotoma_ancillary_capsule,
        write_neotoma_ancillary_capsule,
    )

    output = tmp_path / "capsule"
    originals = {
        f"captures/{digest}/{p.name}": p.read_bytes()
        for sources in (
            capsule_inputs["facet_captures"],
            capsule_inputs["linked_captures"],
        )
        for digest, root in sources.items()
        for p in root.iterdir()
    }
    manifest = write_neotoma_ancillary_capsule(output, **capsule_inputs)
    for relative, raw in originals.items():
        assert (output / relative).read_bytes() == raw
    for sources in (
        capsule_inputs["facet_captures"],
        capsule_inputs["linked_captures"],
    ):
        for root in sources.values():
            root.rename(root.with_name(root.name + "-detached"))
    loaded = load_neotoma_ancillary_capsule(
        output,
        expected_manifest_sha256=sha256(
            (output / "manifest.json").read_bytes()
        ).hexdigest(),
        **{
            key: capsule_inputs[key]
            for key in ("context_directory", "native_archive_directory")
        },
    )
    assert loaded.manifest == manifest
    assert manifest["native_body_copies"] == 0
    assert manifest["scientific_admission"] == "not_asserted"
    assert len(loaded.index["observations"]) == 9
    assert {
        row["parent_scope_verification"]
        for row in loaded.index["captures"]
        if row["kind"] == "facet"
    } == {"authenticated_original_parent_scope", "not_recorded_legacy_capture"}
    linked = [row for row in loaded.index["observations"] if row["kind"] == "linked"]
    assert (
        linked[0]["identity"]["source_proofs"][0]["json_pointer"] == "/data/0/taxonid"
    )
    assert "source_payload" not in json.dumps(loaded.index)
    assert str(tmp_path) not in json.dumps(manifest)


def test_linked_capsule_references_predecessor_without_copy(
    capsule_inputs: dict[str, Any], tmp_path: Path
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule import (
        load_neotoma_ancillary_capsule,
        write_neotoma_ancillary_capsule,
    )

    source = next(iter(capsule_inputs["facet_captures"]))
    predecessor = {source: capsule_inputs["facet_captures"][source]}
    capsule_inputs["facet_captures"] = {}
    output = tmp_path / "capsule"
    manifest = write_neotoma_ancillary_capsule(
        output, predecessor_facets=predecessor, **capsule_inputs
    )
    assert manifest["predecessor_facets"] == [source]
    assert not (output / "captures" / source).exists()
    kwargs = {
        key: capsule_inputs[key]
        for key in ("context_directory", "native_archive_directory")
    }
    pin = sha256((output / "manifest.json").read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="predecessor"):
        load_neotoma_ancillary_capsule(output, expected_manifest_sha256=pin, **kwargs)
    loaded = load_neotoma_ancillary_capsule(
        output, expected_manifest_sha256=pin, predecessor_facets=predecessor, **kwargs
    )
    assert len(loaded.index["observations"]) == 1


def test_existing_capsule_destination_is_preserved(
    capsule_inputs: dict[str, Any], tmp_path: Path
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule import (
        write_neotoma_ancillary_capsule,
    )

    output = tmp_path / "capsule"
    output.mkdir()
    (output / "user").write_bytes(b"foreign writer")
    with pytest.raises(FileExistsError):
        write_neotoma_ancillary_capsule(output, **capsule_inputs)
    assert (output / "user").read_bytes() == b"foreign writer"


def test_compact_occurrences_partition_without_increasing_metadata_limit(
    capsule_inputs: dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule import (
        load_neotoma_ancillary_capsule,
        models,
        write_neotoma_ancillary_capsule,
    )

    monkeypatch.setattr(models, "MAX_INDEX_BYTES", 8192)
    output = tmp_path / "capsule"
    manifest = write_neotoma_ancillary_capsule(output, **capsule_inputs)
    root = json.loads((output / "index.json").read_bytes())
    assert "observations" not in root
    assert root["observation_count"] == 9
    assert root["observation_parts"]
    assert all(
        member["bytes"] <= 8192
        for name, member in manifest["files"].items()
        if name.startswith("index")
    )
    loaded = load_neotoma_ancillary_capsule(
        output,
        expected_manifest_sha256=sha256(
            (output / "manifest.json").read_bytes()
        ).hexdigest(),
        **{
            key: capsule_inputs[key]
            for key in ("context_directory", "native_archive_directory")
        },
    )
    assert len(loaded.index["observations"]) == 9
