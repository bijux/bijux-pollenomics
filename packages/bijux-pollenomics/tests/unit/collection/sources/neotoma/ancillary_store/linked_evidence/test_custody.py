"""Shared evidence anchors and complete frozen predecessors cannot be substituted."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule import (
    load_neotoma_ancillary_capsule,
    write_neotoma_ancillary_capsule,
)

from .native_products import pin


@pytest.mark.parametrize("replacement", [None, {}])
def test_scoped_publication_requires_external_state_anchor(
    scoped_inputs: dict[str, Any],
    tmp_path: Path,
    replacement: Any,
) -> None:
    scoped_inputs["evidence_sources"] = replacement
    with pytest.raises(ValueError, match="evidence|resolver"):
        write_neotoma_ancillary_capsule(tmp_path / "capsule", **scoped_inputs)


def test_missing_protected_predecessor_cannot_erase_full_scope(
    scoped_inputs: dict[str, Any],
    tmp_path: Path,
) -> None:
    scoped_inputs["predecessor_facets"] = dict(
        list(scoped_inputs["predecessor_facets"].items())[:1]
    )
    with pytest.raises(ValueError, match="source|scope|namespace|predecessor"):
        write_neotoma_ancillary_capsule(tmp_path / "capsule", **scoped_inputs)


def test_changed_source_bytes_refuse_full_reopen(
    scoped_inputs: dict[str, Any],
    tmp_path: Path,
) -> None:
    directory = tmp_path / "capsule"
    write_neotoma_ancillary_capsule(directory, **scoped_inputs)
    source = next(iter(scoped_inputs["predecessor_facets"].values()))
    body = next(source.glob("*.body"))
    body.write_bytes(body.read_bytes() + b" ")
    with pytest.raises(ValueError, match="pins|identity|bytes|budget"):
        load_neotoma_ancillary_capsule(
            directory,
            expected_manifest_sha256=pin(directory / "manifest.json"),
            **{
                key: scoped_inputs[key]
                for key in (
                    "context_directory",
                    "native_archive_directory",
                    "evidence_sources",
                    "predecessor_facets",
                )
            },
        )


@pytest.mark.parametrize(
    "field",
    [
        "role",
        "count",
        "range",
        "dependencies",
        "owner",
        "state",
        "duplicate_predecessor",
        "nonbool_higher",
    ],
)
def test_rehashed_capture_cannot_fabricate_scoped_target_metadata(
    scoped_inputs: dict[str, Any],
    tmp_path: Path,
    field: str,
) -> None:
    from .native_products import replace_target_capture

    def change(control: dict[str, Any], manifest: dict[str, Any]) -> None:
        if field == "duplicate_predecessor":
            control["plan"]["source_facet_manifest_sha256s"].append(
                control["plan"]["source_facet_manifest_sha256s"][0]
            )
            return
        if field == "nonbool_higher":
            control["plan"]["include_higher_taxa"] = 1
            return
        if field == "state":
            control["source_evidence"]["manifest_sha256"] = "0" * 64
            manifest["source_evidence"] = control["source_evidence"]
            return
        for target in control["targets"]:
            if target["kind"] != "taxon":
                continue
            if field == "role":
                target["exposure_role"] = "heldout_no_numerical_access"
            elif field == "count":
                target["source_proof_reference"]["occurrence_count"] += 1
            elif field == "range":
                target["source_proof_reference"]["proof_ranges"][0]["start"] += 1
            elif field == "dependencies":
                target["metadata_dependency_count"] += 1
            elif field == "owner":
                target["native_id"] = True
            next(
                row
                for row in manifest["resources"]
                if row["target_key"] == target["target_key"]
            )["identity"] = target

    replace_target_capture(scoped_inputs, change)
    with pytest.raises(ValueError):
        if field in {"duplicate_predecessor", "nonbool_higher"}:
            from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule.inventory import (
                prepare_capsule_metadata,
            )

            prepare_capsule_metadata(**scoped_inputs)
        else:
            write_neotoma_ancillary_capsule(tmp_path / "capsule", **scoped_inputs)


def test_state_body_hash_drift_refuses_before_linked_entity_access(
    scoped_inputs: dict[str, Any],
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    directory = tmp_path / "capsule"
    write_neotoma_ancillary_capsule(directory, **scoped_inputs)
    state = next(iter(scoped_inputs["evidence_sources"].values()))
    part = next((state / "proofs").iterdir())
    part.write_bytes(part.read_bytes() + b" ")
    original = Path.open
    entities = directory / "captures" / next(iter(scoped_inputs["linked_captures"]))
    opened = []

    def observed(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.parent == entities and path.suffix == ".body":
            opened.append(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observed)
    with pytest.raises(ValueError, match="part|identity|byte|bounded regular file"):
        load_neotoma_ancillary_capsule(
            directory,
            expected_manifest_sha256=pin(directory / "manifest.json"),
            **{
                key: scoped_inputs[key]
                for key in (
                    "context_directory",
                    "native_archive_directory",
                    "evidence_sources",
                    "predecessor_facets",
                )
            },
        )
    assert opened == []


@pytest.mark.parametrize("schema", [[], {}, False, "unknown-capsule-schema"])
def test_malformed_capsule_schema_refuses_before_external_source_access(
    scoped_inputs: dict[str, Any],
    tmp_path: Path,
    schema: Any,
    monkeypatch: Any,
) -> None:
    import json

    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule import (
        read_neotoma_ancillary_capsule_inventory,
    )

    directory = tmp_path / "capsule"
    write_neotoma_ancillary_capsule(directory, **scoped_inputs)
    path = directory / "manifest.json"
    value = json.loads(path.read_bytes())
    value["schema_version"] = schema
    del value["linked_evidence"]
    path.write_text(json.dumps(value))
    original = Path.open
    opened = []

    def observed(source: Path, *args: Any, **kwargs: Any) -> Any:
        if source.suffix == ".body":
            opened.append(source)
        return original(source, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observed)
    with pytest.raises(ValueError, match="schema|fields"):
        read_neotoma_ancillary_capsule_inventory(
            directory,
            expected_manifest_sha256=pin(path),
            **{
                key: scoped_inputs[key]
                for key in (
                    "context_directory",
                    "native_archive_directory",
                    "evidence_sources",
                )
            },
        )
    assert opened == []


@pytest.mark.parametrize("field", ["kind", "native_id"])
def test_blocked_target_missing_identity_is_a_controlled_refusal(
    scoped_inputs: dict[str, Any],
    tmp_path: Path,
    field: str,
) -> None:
    from .native_products import replace_target_capture

    def change(control: dict[str, Any], manifest: dict[str, Any]) -> None:
        target = next(row for row in control["targets"] if row["kind"] == "contact")
        del target[field]
        entry = next(
            row
            for row in manifest["resources"]
            if row["target_key"] == target["target_key"]
        )
        assert entry["attempts"] == []
        entry["identity"] = target

    replace_target_capture(scoped_inputs, change)
    with pytest.raises(ValueError):
        write_neotoma_ancillary_capsule(tmp_path / "capsule", **scoped_inputs)


@pytest.mark.parametrize("reader", ["target", "iterator"])
@pytest.mark.parametrize("alias", ["directory", "leaf"])
@pytest.mark.parametrize("matching", [True, False])
def test_selected_proof_alias_refuses_before_foreign_buffer_open(
    scoped_inputs: dict[str, Any],
    tmp_path: Path,
    monkeypatch: Any,
    reader: str,
    alias: str,
    matching: bool,
) -> None:
    import json

    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources import (
        iter_neotoma_linked_evidence_occurrences,
        read_neotoma_linked_evidence_target,
    )

    digest, state = next(iter(scoped_inputs["evidence_sources"].items()))
    header = json.loads((state / "evidence-manifest.json").read_bytes())
    selected = header["targets"]["taxon-11"]["proof_ranges"][0]["part_sha256"]
    foreign = tmp_path / "foreign-proofs"
    if alias == "directory":
        (state / "proofs").rename(foreign)
        (state / "proofs").symlink_to(foreign, target_is_directory=True)
    else:
        foreign.mkdir()
        (state / "proofs" / f"{selected}.json").rename(foreign / f"{selected}.json")
        (state / "proofs" / f"{selected}.json").symlink_to(foreign / f"{selected}.json")
    if not matching:
        path = foreign / f"{selected}.json"
        raw = path.read_bytes()
        path.write_bytes(raw[:-1] + (b" " if raw[-1:] != b" " else b"\n"))
    original = Path.open
    opened = []

    def observed(source: Path, *args: Any, **kwargs: Any) -> Any:
        if foreign in source.resolve().parents:
            opened.append(source)
        return original(source, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observed)
    with pytest.raises(ValueError):
        if reader == "target":
            read_neotoma_linked_evidence_target(
                state,
                expected_manifest_sha256=digest,
                kind="taxon",
                native_id=11,
            )
        else:
            list(
                iter_neotoma_linked_evidence_occurrences(
                    state, expected_manifest_sha256=digest
                )
            )
    assert opened == []
