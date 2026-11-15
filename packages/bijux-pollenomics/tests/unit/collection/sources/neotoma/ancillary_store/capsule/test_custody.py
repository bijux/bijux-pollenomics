"""Capsule budgets, namespace and source joins refuse consequential forgeries."""

from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Any

import pytest

from tests.unit.collection.sources.neotoma.reading_observation import (
    capture_opening,
    observe_opening,
)


@pytest.mark.parametrize(
    "mutation",
    [
        "body",
        "extra",
        "directory",
        "hardlink",
        "symlink",
        "index",
        "kind",
        "scope",
        "context",
        "predecessor",
    ],
)
def test_capsule_refuses_changed_bytes_and_rehashed_claims(
    capsule_inputs: dict[str, Any], tmp_path: Path, mutation: str
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule import (
        load_neotoma_ancillary_capsule,
        write_neotoma_ancillary_capsule,
    )

    output = tmp_path / "capsule"
    manifest = write_neotoma_ancillary_capsule(output, **capsule_inputs)
    body = next((output / "captures").glob("*/*.body"))
    if mutation == "body":
        body.write_bytes(b"foreign")
    elif mutation == "extra":
        (output / "foreign").write_bytes(b"foreign")
    elif mutation == "directory":
        (output / "foreign").mkdir()
    elif mutation == "hardlink":
        os.link(body, tmp_path / "foreign")
    elif mutation == "symlink":
        moved = tmp_path / "foreign"
        body.rename(moved)
        body.symlink_to(moved)
    elif mutation == "index":
        path = output / "index.json"
        index = json.loads(path.read_bytes())
        index["observations"][0]["terminal_status"] = "scientifically_admitted"
        path.write_text(json.dumps(index))
        raw = path.read_bytes()
        old_size = manifest["files"]["index.json"]["bytes"]
        manifest["files"]["index.json"] = {
            "bytes": len(raw),
            "sha256": sha256(raw).hexdigest(),
        }
        manifest["source_bytes"] += len(raw) - old_size
    elif mutation == "kind":
        next(iter(manifest["captures"].values()))["kind"] = "native_current"
    elif mutation == "scope":
        manifest["scientific_admission"] = "approved"
    elif mutation == "context":
        manifest["context_manifest_sha256"] = "0" * 64
    else:
        manifest["predecessor_facets"] = ["0" * 64]
    (output / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        load_neotoma_ancillary_capsule(
            output,
            expected_manifest_sha256=sha256(
                (output / "manifest.json").read_bytes()
            ).hexdigest(),
            **{
                key: capsule_inputs[key]
                for key in ("context_directory", "native_archive_directory")
            },
        )


@pytest.mark.parametrize("budget", ["physical_entity", "cumulative", "files"])
def test_input_budget_refuses_before_numerical_buffer(
    capsule_inputs: dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    budget: str,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule import (
        validation,
        write_neotoma_ancillary_capsule,
    )

    source = next(iter(capsule_inputs["facet_captures"].values()))
    body = next(source.glob("*.body"))
    if budget == "physical_entity":
        with body.open("wb") as stream:
            stream.truncate(513 * 1024 * 1024)
    elif budget == "cumulative":
        monkeypatch.setattr(validation, "MAX_BYTES", 1024)
    else:
        monkeypatch.setattr(validation, "MAX_FILES", 3)
    original = capture_opening()

    def observed(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.suffix == ".body":
            pytest.fail("Numerical buffer opened before finite input budget")
        return original(path, *args, **kwargs)

    observe_opening(monkeypatch, observed)
    output = tmp_path / "capsule"
    with pytest.raises(ValueError):
        write_neotoma_ancillary_capsule(output, **capsule_inputs)
    assert not output.exists()


def test_unconsumed_predecessor_mapping_is_not_opened(
    capsule_inputs: dict[str, Any], tmp_path: Path
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule import (
        write_neotoma_ancillary_capsule,
    )

    source = tmp_path / "not-created"
    manifest = write_neotoma_ancillary_capsule(
        tmp_path / "capsule", predecessor_facets={"0" * 64: source}, **capsule_inputs
    )
    assert manifest["predecessor_facets"] == []


def test_protected_attempt_cannot_disguise_numerical_entity_as_receipt(
    capsule_inputs: dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule import (
        write_neotoma_ancillary_capsule,
    )

    source = next(iter(capsule_inputs["facet_captures"].values()))
    manifest = json.loads((source / "capture-manifest.json").read_bytes())
    protected = next(
        row
        for row in manifest["facets"]
        if row["root_identity"]["exposure_role"] == "reserved_candidate_confirmation"
    )
    blocked = source / "blocked.body"
    raw = b'{"protected_numerical_outcome":123}'
    blocked.write_bytes(raw)
    protected["attempts"] = [
        {"receipt_file": blocked.name, "receipt_sha256": sha256(raw).hexdigest()}
    ]
    raw = json.dumps(manifest).encode()
    (source / "capture-manifest.json").write_bytes(raw)
    capsule_inputs["facet_captures"] = {sha256(raw).hexdigest(): source}
    original = capture_opening()

    def observed(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path == blocked:
            pytest.fail(
                "Protected entity opened as a purported receipt before role refusal"
            )
        return original(path, *args, **kwargs)

    observe_opening(monkeypatch, observed)
    with pytest.raises(ValueError):
        write_neotoma_ancillary_capsule(tmp_path / "capsule", **capsule_inputs)


def test_legacy_capture_cannot_fabricate_original_roster_source_locator(
    capsule_inputs: dict[str, Any],
    tmp_path: Path,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule import (
        write_neotoma_ancillary_capsule,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.facets import (
        replay_neotoma_facet_capture,
    )

    source = next(
        root
        for root in capsule_inputs["facet_captures"].values()
        if root.name == "legacy-facets"
    )
    control = json.loads((source / "request-plan.json").read_bytes())
    manifest = json.loads((source / "capture-manifest.json").read_bytes())
    control["plan"]["resources"][0]["metadata_sha256"] = "0" * 64
    for row in manifest["facets"]:
        if row["root_identity"]["dataset_id"] == 201:
            row["root_identity"]["metadata_sha256"] = "0" * 64
    (source / "request-plan.json").write_text(json.dumps(control))
    manifest["plan_sha256"] = sha256(
        (source / "request-plan.json").read_bytes()
    ).hexdigest()
    raw = json.dumps(manifest).encode()
    (source / "capture-manifest.json").write_bytes(raw)
    pin = sha256(raw).hexdigest()
    # Native legacy replay authenticates its recorded plan, not an external roster.
    assert (
        replay_neotoma_facet_capture(source, expected_manifest_sha256=pin).request_count
        == 2
    )
    capsule_inputs["facet_captures"] = {pin: source}
    capsule_inputs["linked_captures"] = {}
    with pytest.raises(ValueError, match="legacy native owner/role/source locator"):
        write_neotoma_ancillary_capsule(tmp_path / "capsule", **capsule_inputs)


def test_combined_physical_closure_is_bounded_before_capture_metadata_buffers(
    capsule_inputs: dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule import (
        validation,
        write_neotoma_ancillary_capsule,
    )

    roots = {
        *capsule_inputs["facet_captures"].values(),
        *capsule_inputs["linked_captures"].values(),
    }
    total = sum(path.stat().st_size for root in roots for path in root.iterdir())
    monkeypatch.setattr(validation, "MAX_BYTES", total - 1)
    original = capture_opening()

    def observed(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.parent in roots:
            pytest.fail(
                "Capture metadata buffer opened before combined physical budget refusal"
            )
        return original(path, *args, **kwargs)

    observe_opening(monkeypatch, observed)
    with pytest.raises(ValueError):
        write_neotoma_ancillary_capsule(tmp_path / "capsule", **capsule_inputs)
