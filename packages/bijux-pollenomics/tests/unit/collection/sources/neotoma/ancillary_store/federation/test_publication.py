"""Federation coverage distinguishes source observations from pending scientific inputs."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule import (
    write_neotoma_ancillary_capsule,
)
from tests.unit.collection.sources.neotoma.reading_observation import (
    capture_opening,
    observe_opening,
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


def test_federation_derives_slots_and_preserves_all_original_occurrences(
    capsule_inputs: dict[str, Any], tmp_path: Path
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.federation import (
        load_neotoma_ancillary_federation,
        write_neotoma_ancillary_federation,
    )

    inputs = _inputs(capsule_inputs, tmp_path / "capsule")
    output = tmp_path / "federation"
    manifest = write_neotoma_ancillary_federation(output, **inputs)
    loaded = load_neotoma_ancillary_federation(
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
    assert loaded.manifest == manifest
    assert len(loaded.slots) == 16
    assert len(loaded.observations) == 9
    assert len(loaded.linked_occurrences) == 1
    assert Counter(row["coverage_status"] for row in loaded.slots) == {
        "protected_current_scope": 8,
        "pending_capture": 6,
        "complete_source_entity": 2,
    }
    taxa = next(
        row
        for row in loaded.slots
        if row["slot_key"] == "dataset-201-facet-taxa-current"
    )
    assert len(taxa["observation_ids"]) == 2
    assert taxa["selected_observation_id"] is None
    assert {
        row["capture_parent_scope_verification"]
        for row in loaded.observations
        if row["kind"] == "facet"
    } == {"authenticated_original_parent_scope", "not_recorded_legacy_capture"}
    assert all(
        row["current_use_scope_verification"] == "authenticated_current_context_only"
        for row in loaded.slots
    )
    assert loaded.entity_body_hashes_verified is False
    assert loaded.source_assessments_replayed is False
    assert (
        manifest["payload_copies"] == 0
        and manifest["scientific_admission"] == "not_asserted"
    )
    assert str(tmp_path) not in json.dumps(manifest)
    assert not list(output.rglob("*.body"))
    assert "source_payload" not in json.dumps(loaded.observations)


def test_write_and_load_open_no_native_numerical_facet_or_linked_body(
    capsule_inputs: dict[str, Any], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.federation import (
        load_neotoma_ancillary_federation,
        write_neotoma_ancillary_federation,
    )

    inputs = _inputs(capsule_inputs, tmp_path / "capsule")
    native = inputs["native_archive_directory"]
    metadata = {
        native / "captures" / directory.name
        for directory in (native / "catalogue/captures").iterdir()
        if json.loads((directory / "descriptor.json").read_bytes())["capture_kind"]
        == "metadata"
    }
    original = capture_opening()

    def observed(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.suffix == ".body" and path.parent not in metadata:
            pytest.fail(
                "Federation metadata opened a numerical/native/facet/linked body"
            )
        return original(path, *args, **kwargs)

    observe_opening(monkeypatch, observed)
    output = tmp_path / "federation"
    write_neotoma_ancillary_federation(output, **inputs)
    loaded = load_neotoma_ancillary_federation(
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
    assert len(loaded.slots) == 16
    assert all(
        not row.get("download_locator")
        for row in loaded.observations
        if row["current_use_role"] == "reserved_candidate_confirmation"
    )


def test_empty_capsule_view_is_pending_not_an_empty_source_population(
    capsule_inputs: dict[str, Any], tmp_path: Path
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.federation import (
        load_neotoma_ancillary_federation,
        write_neotoma_ancillary_federation,
    )

    inputs = {
        **{
            key: capsule_inputs[key]
            for key in (
                "context_directory",
                "expected_context_sha256",
                "native_archive_directory",
            )
        },
        "capsule_sources": {},
    }
    output = tmp_path / "federation"
    write_neotoma_ancillary_federation(output, **inputs)
    loaded = load_neotoma_ancillary_federation(
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
    assert len(loaded.slots) == 16 and loaded.observations == []
    assert loaded.summary["slot_coverage_counts"] == {
        "protected_current_scope": 8,
        "pending_capture": 8,
    }


def test_source_hash_verification_is_separate_from_metadata(
    capsule_inputs: dict[str, Any], tmp_path: Path
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.federation import (
        load_neotoma_ancillary_federation,
        validate_neotoma_ancillary_federation_sources,
        write_neotoma_ancillary_federation,
    )

    inputs = _inputs(capsule_inputs, tmp_path / "capsule")
    output = tmp_path / "federation"
    write_neotoma_ancillary_federation(output, **inputs)
    kwargs = {
        key: value for key, value in inputs.items() if key != "expected_context_sha256"
    }
    pin = sha256((output / "manifest.json").read_bytes()).hexdigest()
    assert (
        validate_neotoma_ancillary_federation_sources(
            output, expected_manifest_sha256=pin, **kwargs
        )["source_assessments_replayed"]
        is True
    )
    body = next((tmp_path / "capsule/captures").glob("*/*.body"))
    body.write_bytes(b"x" * body.stat().st_size)
    assert (
        load_neotoma_ancillary_federation(
            output, expected_manifest_sha256=pin, **kwargs
        ).entity_body_hashes_verified
        is False
    )
    with pytest.raises(ValueError):
        validate_neotoma_ancillary_federation_sources(
            output, expected_manifest_sha256=pin, **kwargs
        )


def test_multiple_current_epochs_remain_unselected_observations(
    capsule_inputs: dict[str, Any], tmp_path: Path
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store import (
        load_neotoma_ancillary_context,
    )
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.federation import (
        load_neotoma_ancillary_federation,
        write_neotoma_ancillary_federation,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture import (
        NeotomaMetadataResponse,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.facets import (
        capture_neotoma_dataset_facets,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.facets.protocol import (
        plan_from_json,
    )

    inputs = _inputs(capsule_inputs, tmp_path / "capsule")
    original = next(iter(capsule_inputs["facet_captures"].values()))
    plan, _ = plan_from_json(json.loads((original / "request-plan.json").read_bytes()))
    context = load_neotoma_ancillary_context(
        inputs["context_directory"],
        expected_manifest_sha256=inputs["expected_context_sha256"],
        native_archive_directory=inputs["native_archive_directory"],
    )
    document = json.loads((original / "capture-manifest.json").read_bytes())
    bodies = {
        row["facet"]: (original / row["attempts"][0]["body_file"]).read_bytes()
        for row in document["facets"]
        if row["attempts"]
    }
    source = tmp_path / "independent-source-epoch"
    captured = capture_neotoma_dataset_facets(
        source,
        plan=plan,
        scope=context.current_scope_inputs[plan.roster_sha256],
        fetch=lambda url, **_: NeotomaMetadataResponse(
            url, 200, (), bodies[url.rsplit("/", 1)[-1]]
        ),
    )
    capsule = tmp_path / "epoch-capsule"
    write_neotoma_ancillary_capsule(
        capsule,
        **{
            **capsule_inputs,
            "facet_captures": {captured.manifest_sha256: source},
            "linked_captures": {},
        },
    )
    inputs["capsule_sources"][
        sha256((capsule / "manifest.json").read_bytes()).hexdigest()
    ] = capsule
    output = tmp_path / "federation"
    write_neotoma_ancillary_federation(output, **inputs)
    loaded = load_neotoma_ancillary_federation(
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
    row = next(
        row
        for row in loaded.slots
        if row["slot_key"] == "dataset-201-facet-taxa-current"
    )
    assert len(row["observation_ids"]) == 3 and row["selected_observation_id"] is None
    assert len(loaded.observations) == 13


@pytest.mark.parametrize(
    "owner_field,owner_value",
    [
        ("site_id", 999),
        ("collection_unit_id", 999),
        ("dataset_type", "stomata"),
        ("database", None),
    ],
)
def test_original_owner_drift_stays_unmatched_and_has_no_download(
    capsule_inputs: dict[str, Any], tmp_path: Path, owner_field: str, owner_value: Any
) -> None:
    import shutil

    from bijux_pollenomics.collection.sources.neotoma.ancillary_store import (
        load_neotoma_ancillary_context,
        write_neotoma_ancillary_context,
    )
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.federation import (
        load_neotoma_ancillary_federation,
        write_neotoma_ancillary_federation,
    )

    context = load_neotoma_ancillary_context(
        capsule_inputs["context_directory"],
        expected_manifest_sha256=capsule_inputs["expected_context_sha256"],
        native_archive_directory=capsule_inputs["native_archive_directory"],
    )
    legacy = next(
        root
        for root in capsule_inputs["facet_captures"].values()
        if root.name == "legacy-facets"
    )
    variant = tmp_path / "original-owner-variant"
    shutil.copytree(legacy, variant)
    control = json.loads((variant / "request-plan.json").read_bytes())
    roster = json.loads(
        context.legacy_rosters[control["plan"]["roster_sha256"]].read_bytes()
    )
    next(row for row in roster["resources"] if row["dataset_id"] == 201)[
        owner_field
    ] = owner_value
    roster_path = tmp_path / "original-owner-roster.json"
    roster_path.write_text(json.dumps(roster))
    roster_pin = sha256(roster_path.read_bytes()).hexdigest()
    control["plan"]["roster_sha256"] = roster_pin
    next(row for row in control["plan"]["resources"] if row["dataset_id"] == 201)[
        owner_field
    ] = owner_value
    (variant / "request-plan.json").write_text(json.dumps(control))
    manifest = json.loads((variant / "capture-manifest.json").read_bytes())
    manifest["plan_sha256"] = sha256(
        (variant / "request-plan.json").read_bytes()
    ).hexdigest()
    for entry in manifest["facets"]:
        if entry["root_identity"]["dataset_id"] != 201:
            continue
        entry["root_identity"][owner_field] = owner_value
        for attempt in entry["attempts"]:
            receipt_path = variant / attempt["receipt_file"]
            receipt = json.loads(receipt_path.read_bytes())
            if owner_field == "site_id":
                receipt["expected_site_id"] = owner_value
            receipt_path.write_text(json.dumps(receipt))
            attempt["receipt_sha256"] = sha256(receipt_path.read_bytes()).hexdigest()
    (variant / "capture-manifest.json").write_text(json.dumps(manifest))
    authority = context.manifest["exposure_authority"]
    new_context = tmp_path / "owner-context"
    write_neotoma_ancillary_context(
        new_context,
        native_archive_directory=capsule_inputs["native_archive_directory"],
        expected_native_archive_sha256=context.manifest["native_archive"][
            "manifest_sha256"
        ],
        legacy_rosters={roster_pin: roster_path},
        exposure_authority=capsule_inputs["context_directory"] / authority["path"],
        expected_exposure_authority_sha256=authority["sha256"],
    )
    facets = {
        pin: path
        for pin, path in capsule_inputs["facet_captures"].items()
        if path != legacy
    }
    facets[sha256((variant / "capture-manifest.json").read_bytes()).hexdigest()] = (
        variant
    )
    inputs = _inputs(
        {
            **capsule_inputs,
            "context_directory": new_context,
            "expected_context_sha256": sha256(
                (new_context / "manifest.json").read_bytes()
            ).hexdigest(),
            "facet_captures": facets,
        },
        tmp_path / "owner-capsule",
    )
    output = tmp_path / "federation"
    write_neotoma_ancillary_federation(output, **inputs)
    loaded = load_neotoma_ancillary_federation(
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
    unmatched = [
        row
        for row in loaded.observations
        if row["current_owner_join"] != "exact_current_owner"
    ]
    assert (
        len(unmatched) == 2 and loaded.summary["unmatched_facet_observation_count"] == 2
    )
    assert all(
        "download_locator" not in row and "forensic_locator" not in row
        for row in unmatched
    )
    assert (
        len(
            next(
                row
                for row in loaded.slots
                if row["slot_key"] == "dataset-201-facet-taxa-current"
            )["observation_ids"]
        )
        == 1
    )


def test_metadata_partitions_keep_native_coverage_and_no_larger_metadata_cap(
    capsule_inputs: dict[str, Any], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.federation import (
        load_neotoma_ancillary_federation,
        models,
        write_neotoma_ancillary_federation,
    )

    inputs = _inputs(capsule_inputs, tmp_path / "capsule")
    monkeypatch.setattr(models, "MAX_PART_BYTES", 8192)
    output = tmp_path / "federation"
    manifest = write_neotoma_ancillary_federation(output, **inputs)
    assert all(
        member["bytes"] <= 8192
        for name, member in manifest["files"].items()
        if not name.startswith("scope/")
    )
    assert manifest["current_use_parent_obligations"]["bytes"] <= 16 * 1024 * 1024
    index = json.loads((output / "index.json").read_bytes())
    assert sum(row["population"] == "slots" for row in index["parts"]) > 1
    loaded = load_neotoma_ancillary_federation(
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
    assert len(loaded.slots) == 16 and len(loaded.observations) == 9
