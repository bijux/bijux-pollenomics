"""Scoped capsules reference shared evidence and preserve literal source buffers."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
from typing import Any

from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule import (
    load_neotoma_ancillary_capsule,
    read_neotoma_ancillary_capsule_inventory,
    write_neotoma_ancillary_capsule,
)
from tests.unit.collection.sources.neotoma.reading_observation import (
    capture_opening,
    observe_opening,
)

from .native_products import pin


def test_scoped_capsule_reopens_with_relocated_shared_evidence(
    scoped_inputs: dict[str, Any],
    tmp_path: Path,
) -> None:
    directory = tmp_path / "capsule"
    manifest = write_neotoma_ancillary_capsule(directory, **scoped_inputs)
    assert manifest["schema_version"] == "neotoma-scoped-ancillary-source-capsule.v1"
    assert manifest["predecessor_facets"] == []
    assert set(manifest["captures"]) == set(scoped_inputs["linked_captures"])
    assert manifest["linked_evidence"] == {
        digest: {"schema_version": "neotoma-linked-source-evidence.v1"}
        for digest in scoped_inputs["evidence_sources"]
    }
    assert all(not name.startswith("proofs/") for name in manifest["files"])
    assert all("evidence-manifest.json" not in name for name in manifest["files"])
    original = next(iter(scoped_inputs["linked_captures"].values()))
    digest = next(iter(scoped_inputs["linked_captures"]))
    for source in original.iterdir():
        assert (
            directory / "captures" / digest / source.name
        ).read_bytes() == source.read_bytes()
    evidence_pin, evidence = next(iter(scoped_inputs["evidence_sources"].items()))
    moved = tmp_path / "shared-state-relocated"
    shutil.move(evidence, moved)
    options = {
        key: scoped_inputs[key]
        for key in (
            "context_directory",
            "native_archive_directory",
            "predecessor_facets",
        )
    }
    loaded = load_neotoma_ancillary_capsule(
        directory,
        expected_manifest_sha256=pin(directory / "manifest.json"),
        evidence_sources={evidence_pin: moved},
        **options,
    )
    assert loaded.manifest == manifest
    assert len(loaded.index["observations"]) == 2
    blocked = next(
        row
        for row in loaded.index["observations"]
        if row["identity"]["kind"] == "contact"
    )
    assert blocked["attempts"] == []
    assert blocked["identity"]["exposure_role"] == "heldout_no_numerical_access"
    assert "source_proofs" not in json.dumps(loaded.index)
    assert str(tmp_path) not in json.dumps(manifest)


def test_inventory_opens_no_predecessor_or_target_entities(
    scoped_inputs: dict[str, Any],
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    directory = tmp_path / "capsule"
    write_neotoma_ancillary_capsule(directory, **scoped_inputs)
    numerical = set(scoped_inputs["predecessor_facets"].values())
    numerical.add(directory / "captures" / next(iter(scoped_inputs["linked_captures"])))
    original = capture_opening()

    def observed(path: Path, *args: Any, **kwargs: Any) -> Any:
        assert not (path.suffix == ".body" and path.parent in numerical)
        return original(path, *args, **kwargs)

    observe_opening(monkeypatch, observed)
    result = read_neotoma_ancillary_capsule_inventory(
        directory,
        expected_manifest_sha256=pin(directory / "manifest.json"),
        **{
            key: scoped_inputs[key]
            for key in (
                "context_directory",
                "native_archive_directory",
                "evidence_sources",
            )
        },
    )
    assert result.entity_body_hashes_verified is False
    assert result.source_assessments_replayed is False
    assert len(result.index["observations"]) == 2


def test_streaming_evidence_occurrences_uses_each_part_buffer_once(
    scoped_inputs: dict[str, Any],
    monkeypatch: Any,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources import (
        iter_neotoma_linked_evidence_occurrences,
    )

    digest, state = next(iter(scoped_inputs["evidence_sources"].items()))
    header = json.loads((state / "evidence-manifest.json").read_bytes())
    opened = []
    original = capture_opening()

    def observed(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.parent == state / "proofs":
            opened.append(path.name)
        return original(path, *args, **kwargs)

    observe_opening(monkeypatch, observed)
    rows = list(
        iter_neotoma_linked_evidence_occurrences(state, expected_manifest_sha256=digest)
    )
    assert len(rows) == header["occurrence_count"]
    assert len(opened) == len(set(opened)) == len(header["parts"])
    assert {proof["root_dataset_id"] for proof, _ in rows} == {201, 203}
    assert all(locator["evidence_manifest_sha256"] == digest for _, locator in rows)
    assert any(
        proof["target_kind"] == "contact" and proof["native_id"] == 900
        for proof, _ in rows
    )
