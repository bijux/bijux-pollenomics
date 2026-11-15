"""Pinned federation joins cannot be replaced by rehashed metadata claims."""

from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule import (
    write_neotoma_ancillary_capsule,
)


def _inputs(inputs: dict[str, Any], path: Path) -> dict[str, Any]:
    write_neotoma_ancillary_capsule(path, **inputs)
    return {
        **{
            key: inputs[key]
            for key in (
                "context_directory",
                "expected_context_sha256",
                "native_archive_directory",
            )
        },
        "capsule_sources": {
            sha256((path / "manifest.json").read_bytes()).hexdigest(): path
        },
    }


@pytest.mark.parametrize(
    "mutation",
    [
        "extra",
        "directory",
        "hardlink",
        "symlink",
        "part",
        "rehashed_part",
        "context",
        "native",
        "claims",
        "population",
    ],
)
def test_federation_refuses_tampering_and_false_rehashed_coverage(
    capsule_inputs: dict[str, Any], tmp_path: Path, mutation: str
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.federation import (
        load_neotoma_ancillary_federation,
        write_neotoma_ancillary_federation,
    )

    inputs = _inputs(capsule_inputs, tmp_path / "capsule")
    output = tmp_path / "federation"
    manifest = write_neotoma_ancillary_federation(output, **inputs)
    part = output / next(iter(manifest["files"]))
    if mutation == "extra":
        (output / "foreign").write_bytes(b"foreign")
    elif mutation == "directory":
        (output / "foreign").mkdir()
    elif mutation == "hardlink":
        os.link(part, tmp_path / "foreign")
    elif mutation == "symlink":
        part.unlink()
        part.symlink_to(tmp_path / "missing")
    elif mutation in {"part", "rehashed_part"}:
        old_bytes = part.stat().st_size
        part.write_bytes(b"{}")
        if mutation == "rehashed_part":
            manifest["files"][part.relative_to(output).as_posix()] = {
                "bytes": 2,
                "sha256": sha256(b"{}").hexdigest(),
            }
            manifest["source_bytes"] += 2 - old_bytes
    elif mutation == "context":
        manifest["context_manifest_sha256"] = "0" * 64
    elif mutation == "native":
        manifest["native_archive_manifest_sha256"] = "0" * 64
    elif mutation == "claims":
        manifest["scientific_admission"] = "approved"
    else:
        manifest["summary"]["required_slot_count"] = 1
    (output / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        load_neotoma_ancillary_federation(
            output,
            expected_manifest_sha256=sha256(
                (output / "manifest.json").read_bytes()
            ).hexdigest(),
            **{
                key: value
                for key, value in inputs.items()
                if key != "expected_context_sha256"
            },
        )


def test_capture_owner_is_unique_across_declared_capsules(
    capsule_inputs: dict[str, Any], tmp_path: Path
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.federation import (
        write_neotoma_ancillary_federation,
    )

    inputs = _inputs(capsule_inputs, tmp_path / "capsule")
    digest = next(iter(capsule_inputs["facet_captures"]))
    other = tmp_path / "overlapping-capsule"
    write_neotoma_ancillary_capsule(
        other,
        **{
            **capsule_inputs,
            "facet_captures": {digest: capsule_inputs["facet_captures"][digest]},
            "linked_captures": {},
        },
    )
    inputs["capsule_sources"][
        sha256((other / "manifest.json").read_bytes()).hexdigest()
    ] = other
    with pytest.raises(ValueError, match="capture owner"):
        write_neotoma_ancillary_federation(tmp_path / "federation", **inputs)


def test_existing_destination_is_preserved(
    capsule_inputs: dict[str, Any], tmp_path: Path
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.federation import (
        write_neotoma_ancillary_federation,
    )

    inputs = _inputs(capsule_inputs, tmp_path / "capsule")
    output = tmp_path / "federation"
    output.mkdir()
    (output / "user").write_bytes(b"foreign writer")
    with pytest.raises(FileExistsError):
        write_neotoma_ancillary_federation(output, **inputs)
    assert (output / "user").read_bytes() == b"foreign writer"


def test_extra_unconsumed_capsule_resolver_is_not_opened(
    capsule_inputs: dict[str, Any], tmp_path: Path
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.federation import (
        load_neotoma_ancillary_federation,
        write_neotoma_ancillary_federation,
    )

    inputs = _inputs(capsule_inputs, tmp_path / "capsule")
    output = tmp_path / "federation"
    write_neotoma_ancillary_federation(output, **inputs)
    inputs["capsule_sources"]["0" * 64] = tmp_path / "not-created"
    assert (
        load_neotoma_ancillary_federation(
            output,
            expected_manifest_sha256=sha256(
                (output / "manifest.json").read_bytes()
            ).hexdigest(),
            **{
                key: value
                for key, value in inputs.items()
                if key != "expected_context_sha256"
            },
        ).summary["required_slot_count"]
        == 16
    )


def test_linked_predecessors_resolve_through_owned_capsules(
    capsule_inputs: dict[str, Any], tmp_path: Path
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.federation import (
        load_neotoma_ancillary_federation,
        write_neotoma_ancillary_federation,
    )

    inputs = _inputs(
        {**capsule_inputs, "linked_captures": {}}, tmp_path / "facet-capsule"
    )
    predecessor, source = next(iter(capsule_inputs["facet_captures"].items()))
    linked = tmp_path / "linked-capsule"
    write_neotoma_ancillary_capsule(
        linked,
        **{**capsule_inputs, "facet_captures": {}},
        predecessor_facets={predecessor: source},
    )
    linked_pin = sha256((linked / "manifest.json").read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="predecessor"):
        write_neotoma_ancillary_federation(
            tmp_path / "missing-predecessor",
            **{**inputs, "capsule_sources": {linked_pin: linked}},
        )
    inputs["capsule_sources"][linked_pin] = linked
    output = tmp_path / "federation"
    write_neotoma_ancillary_federation(output, **inputs)
    assert (
        len(
            load_neotoma_ancillary_federation(
                output,
                expected_manifest_sha256=sha256(
                    (output / "manifest.json").read_bytes()
                ).hexdigest(),
                **{
                    key: value
                    for key, value in inputs.items()
                    if key != "expected_context_sha256"
                },
            ).linked_occurrences
        )
        == 1
    )


@pytest.mark.parametrize("budget", ["bytes", "files"])
def test_federation_publication_has_finite_metadata_budget(
    capsule_inputs: dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    budget: str,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.federation import (
        validation,
        write_neotoma_ancillary_federation,
    )

    inputs = _inputs(capsule_inputs, tmp_path / "capsule")
    monkeypatch.setattr(
        validation,
        "MAX_BYTES" if budget == "bytes" else "MAX_FILES",
        1024 if budget == "bytes" else 1,
    )
    output = tmp_path / "federation"
    with pytest.raises(ValueError):
        write_neotoma_ancillary_federation(output, **inputs)
    assert not output.exists()


def test_linked_restriction_projection_keeps_protected_and_unmatched_roots(
    capsule_inputs: dict[str, Any], tmp_path: Path
) -> None:
    from copy import deepcopy

    from bijux_pollenomics.collection.sources.neotoma.ancillary_store import (
        load_neotoma_ancillary_context,
    )
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule import (
        read_neotoma_ancillary_capsule_inventory,
    )
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.federation.models import (
        assemble_view,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.parent_scope import (
        _roster,
    )

    inputs = _inputs(capsule_inputs, tmp_path / "capsule")
    pin, capsule = next(iter(inputs["capsule_sources"].items()))
    inventory = read_neotoma_ancillary_capsule_inventory(
        capsule,
        expected_manifest_sha256=pin,
        context_directory=inputs["context_directory"],
        native_archive_directory=inputs["native_archive_directory"],
    )
    context = load_neotoma_ancillary_context(
        inputs["context_directory"],
        expected_manifest_sha256=inputs["expected_context_sha256"],
        native_archive_directory=inputs["native_archive_directory"],
    )
    roster_pin, scope = next(iter(context.current_scope_inputs.items()))
    roster = _roster(scope.roster_path, roster_pin)
    baseline = next(
        row
        for row in inventory.index["observations"]
        if row["kind"] == "facet"
        and row["root_identity"]["dataset_id"] == 201
        and row["facet"] == "taxa"
    )
    target = deepcopy(
        next(row for row in inventory.index["observations"] if row["kind"] == "linked")
    )
    proof = target["identity"]["source_proofs"][0]
    rows, summaries, attempts, proofs = [], [], {}, []
    # Model three authenticated historical declarations: current owner, a now
    # protected owner, and an old owner tuple that no longer matches its native ID.
    for digest, dataset, site, unit in [
        ("a" * 64, 201, 12, 100),
        ("b" * 64, 203, 13, 101),
        ("c" * 64, 201, 999, 100),
    ]:
        row = deepcopy(baseline)
        row.update(
            source_capture_manifest_sha256=digest,
            source_entry_pointer="/facets/0",
            facet_key=f"dataset-{dataset}-facet-taxa-current",
            parent_scope_verification="not_recorded_legacy_capture",
            parent_scope_role=None,
        )
        row["root_identity"].update(
            dataset_id=dataset,
            site_id=site,
            collection_unit_id=unit,
            exposure_role="development_resource_discovery",
        )
        rows.append(row)
        capture = deepcopy(inventory.index["captures"][0])
        capture["source_capture_manifest_sha256"] = digest
        summaries.append(capture)
        attempts[digest, row["source_entry_pointer"]] = [
            {**attempt, "http_status": 200, "body_complete": True}
            for attempt in row["attempts"]
        ]
        proofs.append(
            {
                **proof,
                "source_capture_manifest_sha256": digest,
                "source_facet_key": row["facet_key"],
                "root_dataset_id": dataset,
                "root_identity": row["root_identity"],
                "inherited_exposure_role": "development_resource_discovery",
            }
        )
    target["identity"]["source_proofs"] = proofs
    rows.append(target)
    original = next(
        row
        for row in inventory.index["captures"]
        if row["source_capture_manifest_sha256"]
        == target["source_capture_manifest_sha256"]
    )
    summaries.append(original)
    attempts[
        target["source_capture_manifest_sha256"], target["source_entry_pointer"]
    ] = [
        {**attempt, "http_status": 200, "body_complete": True}
        for attempt in target["attempts"]
    ]
    _, observations, occurrences, _ = assemble_view(
        roster,
        {201: "development_resource_discovery", 203: "reserved_candidate_confirmation"},
        {pin: {"captures": summaries, "observations": rows}},
        attempts,
    )
    linked = next(row for row in observations if row["kind"] == "linked")
    assert linked["current_use_role"] == "reserved_candidate_confirmation"
    assert linked["current_owner_join"] != "exact_current_owner"
    assert "download_locator" not in linked and "forensic_locator" not in linked
    assert len(occurrences) == 3
    assert any(
        row["current_use_role"] == "reserved_candidate_confirmation"
        for row in occurrences
    )
    assert any(
        row["current_owner_join"] != "exact_current_owner" for row in occurrences
    )


def test_current_role_proof_is_explicit_and_cannot_be_rehashed_to_development(
    capsule_inputs: dict[str, Any], tmp_path: Path
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.federation import (
        load_neotoma_ancillary_federation,
        write_neotoma_ancillary_federation,
    )

    inputs = _inputs(capsule_inputs, tmp_path / "capsule")
    output = tmp_path / "federation"
    manifest = write_neotoma_ancillary_federation(output, **inputs)
    witness = manifest["current_use_parent_obligations"]
    assert witness["path"] == "scope/current-parent-proof.json"
    path = output / witness["path"]
    raw = path.read_bytes()
    assert len(raw) == witness["bytes"]
    assert (
        sha256(raw).hexdigest()
        == witness["sha256"]
        == manifest["current_use_parent_obligations_sha256"]
    )
    proof = json.loads(raw)
    next(row for row in proof["parents"] if row["dataset_id"] == 203)[
        "effective_scope_role"
    ] = "development_resource_discovery"
    path.write_text(json.dumps(proof))
    digest = sha256(path.read_bytes()).hexdigest()
    manifest["source_bytes"] += path.stat().st_size - witness["bytes"]
    witness.update(bytes=path.stat().st_size, sha256=digest)
    manifest["current_use_parent_obligations_sha256"] = digest
    manifest["files"][witness["path"]] = {
        "bytes": path.stat().st_size,
        "sha256": digest,
    }
    (output / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        load_neotoma_ancillary_federation(
            output,
            expected_manifest_sha256=sha256(
                (output / "manifest.json").read_bytes()
            ).hexdigest(),
            **{
                key: value
                for key, value in inputs.items()
                if key != "expected_context_sha256"
            },
        )
