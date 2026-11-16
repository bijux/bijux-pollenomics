"""Metadata and selected entities have explicitly different integrity scopes."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pytest

from tests.unit.collection.sources.neotoma.reading_observation import (
    capture_opening,
    observe_opening,
)


def test_inventory_opens_no_entity_and_selected_read_opens_one_buffer_once(
    reference_archive: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = reference_archive
    actual_open = capture_opening()
    opened: list[str] = []

    def observed(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.suffix == ".body":
            opened.append(path.name)
            assert len(opened) == 1
            assert "variableunits" in path.name
        return actual_open(path, *args, **kwargs)

    observe_opening(monkeypatch, observed)
    inventory = archive["owner"].read_neotoma_reference_archive_inventory(
        archive["directory"], expected_manifest_sha256=archive["sha256"]
    )
    assert opened == []
    assert inventory.source_entity_bodies_verified is False
    assert inventory.source_assessments_replayed is False
    selected = archive["owner"].read_neotoma_reference_archive_table(
        archive["directory"],
        expected_manifest_sha256=archive["sha256"],
        table="variableunits",
    )
    assert selected["native_body"] == archive["bodies"]["variableunits"]
    assert selected["body_sha256"] == sha256(selected["native_body"]).hexdigest()
    assert selected["archive"]["unselected_source_bodies_verified"] is False
    assert selected["scientific_admission"] == "not_asserted"
    assert len(opened) == 1


def test_unselected_entity_corruption_is_not_a_selected_integrity_claim(
    reference_archive: dict[str, Any],
) -> None:
    archive = reference_archive
    other = (
        archive["directory"]
        / "capture/reference-table-geopoliticalunits-current-attempt-1.body"
    )
    raw = other.read_bytes()
    other.write_bytes(raw.replace(b"success", b"damaged"))
    selected = archive["owner"].read_neotoma_reference_archive_table(
        archive["directory"],
        expected_manifest_sha256=archive["sha256"],
        table="variableunits",
    )
    assert selected["native_body"] == archive["bodies"]["variableunits"]
    with pytest.raises(ValueError):
        archive["owner"].load_neotoma_reference_archive(
            archive["directory"], expected_manifest_sha256=archive["sha256"]
        )
    with pytest.raises(ValueError):
        archive["owner"].read_neotoma_reference_archive_entity(
            archive["directory"],
            expected_manifest_sha256=archive["sha256"],
            table="geopoliticalunits",
        )


@pytest.mark.parametrize("reference_source", ["incomplete", "http"], indirect=True)
def test_unavailable_table_refuses_before_body_and_forensic_entity_keeps_posture(
    reference_archive: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = reference_archive
    actual_open = capture_opening()
    opened: list[str] = []

    def observed(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.suffix == ".body":
            opened.append(path.name)
        return actual_open(path, *args, **kwargs)

    observe_opening(monkeypatch, observed)
    with pytest.raises(ValueError):
        archive["owner"].read_neotoma_reference_archive_table(
            archive["directory"],
            expected_manifest_sha256=archive["sha256"],
            table="geopoliticalunits",
        )
    assert opened == []
    forensic = archive["owner"].read_neotoma_reference_archive_entity(
        archive["directory"],
        expected_manifest_sha256=archive["sha256"],
        table="geopoliticalunits",
    )
    assert forensic["native_body"] == archive["bodies"]["geopoliticalunits"]
    assert (
        forensic["source_terminal_status"]
        != "received_complete_unqualified_reference_table"
    )
    assert len(opened) == 1


@pytest.mark.parametrize(
    "table", ["samples", "../variableunits", True, "VariableUnits"]
)
def test_arbitrary_selector_refuses_without_reading_source(
    reference_archive: dict[str, Any], table: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = reference_archive

    def forbidden(*_: Any, **__: Any) -> Any:
        pytest.fail("invalid reference selector opened a file")

    observe_opening(monkeypatch, forbidden)
    with pytest.raises(ValueError):
        archive["owner"].read_neotoma_reference_archive_table(
            archive["directory"],
            expected_manifest_sha256=archive["sha256"],
            table=table,
        )


def rebind_receipt(archive: dict[str, Any], field: str, value: Any) -> str:
    """Rehash every metadata link so refusal must come from source semantics."""
    root = archive["directory"]

    def store(path: Path, payload: Any) -> dict[str, Any]:
        raw = (
            json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
        ).encode()
        path.write_bytes(raw)
        return {"bytes": len(raw), "sha256": sha256(raw).hexdigest()}

    manifest = json.loads((root / "manifest.json").read_bytes())
    capture = json.loads((root / "capture/capture-manifest.json").read_bytes())
    index = json.loads((root / "index.json").read_bytes())
    ref = capture["tables"][0]["attempts"][0]
    path = "capture/" + ref["receipt_file"]
    receipt = json.loads((root / path).read_bytes())
    receipt[field] = value
    manifest["files"][path] = store(root / path, receipt)
    ref["receipt_sha256"] = manifest["files"][path]["sha256"]
    capture_member = store(root / "capture/capture-manifest.json", capture)
    manifest["files"]["capture/capture-manifest.json"] = capture_member
    manifest["capture_manifest_sha256"] = capture_member["sha256"]
    index["capture_manifest_sha256"] = capture_member["sha256"]
    index["tables"][0]["attempts"][0]["receipt_sha256"] = ref["receipt_sha256"]
    index["tables"][0]["source"]["receipt_sha256"] = ref["receipt_sha256"]
    index["tables"][0]["source"]["receipt"] = receipt
    manifest["files"]["index.json"] = store(root / "index.json", index)
    manifest["source_bytes"] = sum(row["bytes"] for row in manifest["files"].values())
    digest = store(root / "manifest.json", manifest)["sha256"]
    assert isinstance(digest, str)
    return digest


@pytest.mark.parametrize(
    "field,value",
    [
        ("expected_dataset_id", 123),
        ("response_headers", "Content-Length: 1"),
        ("response_headers", [["Content-Length", "1"]]),
        ("final_url", "https://foreign.example/variableunits"),
        ("role", "numerical_resource"),
    ],
)
def test_rehashed_false_receipt_metadata_refuses_before_any_entity_access(
    reference_archive: dict[str, Any],
    field: str,
    value: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    archive = reference_archive
    anchor = rebind_receipt(archive, field, value)
    actual_open = capture_opening()

    def guarded(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.suffix == ".body":
            pytest.fail("false receipt metadata reached a source entity")
        return actual_open(path, *args, **kwargs)

    observe_opening(monkeypatch, guarded)
    with pytest.raises(ValueError):
        archive["owner"].read_neotoma_reference_archive_inventory(
            archive["directory"], expected_manifest_sha256=anchor
        )
