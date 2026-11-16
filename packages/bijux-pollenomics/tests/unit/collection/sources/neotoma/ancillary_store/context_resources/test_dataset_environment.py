"""Dataset-filtered environment sources preserve native ownership and unknowns."""

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context_resources import (
    load_neotoma_context_resource_archive,
    read_neotoma_context_resource,
    read_neotoma_context_resource_entity,
    read_neotoma_context_resource_inventory,
    write_neotoma_context_resource_archive,
)
from bijux_pollenomics.collection.sources.neotoma.capture import NeotomaMetadataResponse
from bijux_pollenomics.collection.sources.neotoma.capture.context_resources import (
    NeotomaContextResourcePlan,
    capture_neotoma_context_resources,
)
from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive.files import (
    encoded_json,
)

from .native_products import make_binding, observe_context_bodies, pin

KIND = "dataset_depositional_environment"


@pytest.fixture
def dataset_products(tmp_path: Path) -> Any:
    def create(*, rows: Any = None, change: str | None = None) -> dict[str, Any]:
        original = make_binding(tmp_path / "original")
        native = (
            [
                {
                    "siteid": 12,
                    "collectionunitid": 100,
                    "datasetid": 201,
                    "depenvt": "Lacustrine",
                },
                {
                    "siteid": 12,
                    "collectionunitid": 100,
                    "datasetid": 202,
                    "depenvt": "Lacustrine",
                },
            ]
            if rows is None
            else rows
        )

        def response(url: str, **kwargs: Any) -> NeotomaMetadataResponse:
            assert "datasetid=201%2C202&limit=2&offset=0" in url
            return NeotomaMetadataResponse(
                url, 200, (), encoded_json({"status": "success", "data": native})
            )

        capture = tmp_path / "capture"
        plan = NeotomaContextResourcePlan(
            (12,),
            original.expected_context_sha256,
            original.expected_native_archive_sha256,
            (KIND,),
        )
        result = capture_neotoma_context_resources(
            capture,
            plan=plan,
            context_directory=original.context_directory,
            native_archive_directory=original.native_archive_directory,
            fetch=response,
        )
        current = (
            original if change is None else make_binding(tmp_path / "current", change)
        )
        reader = {"original": original, "current": current}
        return {
            "capture": capture,
            "rows": native,
            "reader": reader,
            "writer": {
                "capture_directory": capture,
                "expected_capture_manifest_sha256": result.manifest_sha256,
                **reader,
            },
        }

    return create


def publish(products: dict[str, Any], tmp_path: Path) -> tuple[Path, dict[str, Any]]:
    output = tmp_path / "archive"
    write_neotoma_context_resource_archive(output, **products["writer"])
    return output, {
        "expected_manifest_sha256": pin(output / "manifest.json"),
        **products["reader"],
    }


def test_dataset_query_replays_and_selects_one_same_buffer_with_exact_native_owners(
    dataset_products: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inputs = dataset_products()
    output, reader = publish(inputs, tmp_path)
    full = load_neotoma_context_resource_archive(output, **reader)
    assert full["native_profile_partitions"] == {"qualified_native_environment_rows": 1}
    own = (
        output
        / "capture/site-12-dataset_depositional_environment-current-attempt-1.body"
    )
    opened = observe_context_bodies(monkeypatch, {own})
    typed = read_neotoma_context_resource(
        output, site_id=12, resource_kind=KIND, **reader
    )
    assert opened == [own]
    assert typed["body"] == own.read_bytes()
    assert typed["source_payload"] == {"status": "success", "data": inputs["rows"]}
    profile = typed["profile"]
    assert profile["native_payload_owner_verified"] is True
    assert profile["requested_native_dataset_ids"] == [201, 202]
    assert profile["returned_native_dataset_ids"] == [201, 202]
    assert profile["missing_requested_native_dataset_ids"] == []
    assert profile["absence_certified"] is False
    assert profile["dated_basin_geometry_admitted"] is False
    assert profile["complete_environment_coverage_established"] is False
    assert typed["unselected_source_bodies_verified"] is False


def test_dataset_query_inventory_opens_zero_context_entities(
    dataset_products: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output, reader = publish(dataset_products(), tmp_path)
    opened = observe_context_bodies(monkeypatch, set())
    inventory = read_neotoma_context_resource_inventory(output, **reader)
    assert opened == []
    assert inventory.body_hashes_verified is False
    assert inventory.native_profiles_verified is False


@pytest.mark.parametrize(
    "rows",
    [
        [],
        [{"siteid": 12, "collectionunitid": 100, "datasetid": 201, "depenvt": None}],
        [{"siteid": 12, "collectionunitid": 100, "datasetid": 202, "depenvt": ""}],
    ],
)
def test_empty_missing_and_null_environment_evidence_remains_literal(
    dataset_products: Any, tmp_path: Path, rows: list[dict[str, Any]]
) -> None:
    output, reader = publish(dataset_products(rows=rows), tmp_path)
    typed = read_neotoma_context_resource(
        output, site_id=12, resource_kind=KIND, **reader
    )
    assert typed["source_payload"]["data"] == rows
    profile = typed["profile"]
    returned = sorted(row["datasetid"] for row in rows)
    assert profile["requested_native_dataset_ids"] == [201, 202]
    assert profile["returned_native_dataset_ids"] == returned
    assert profile["missing_requested_native_dataset_ids"] == sorted(
        {201, 202} - set(returned)
    )
    assert profile["native_payload_owner_verified"] is bool(rows)
    assert profile["absence_certified"] is False
    assert profile["environment_inferred_from_prose_or_collection_type"] is False


@pytest.mark.parametrize(
    "field,value",
    [
        ("siteid", 13),
        ("collectionunitid", 200),
        ("datasetid", 401),
        ("siteid", True),
        ("collectionunitid", 100.0),
        ("datasetid", 201.9),
        ("datasetid", None),
        ("depenvt", False),
        ("depenvt", []),
    ],
)
def test_foreign_or_malformed_native_rows_refuse_typed_but_retain_forensic_bytes(
    dataset_products: Any,
    tmp_path: Path,
    field: str,
    value: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    row = {
        "siteid": 12,
        "collectionunitid": 100,
        "datasetid": 201,
        "depenvt": "Lacustrine",
    }
    row[field] = value
    output, reader = publish(dataset_products(rows=[row]), tmp_path)
    own = (
        output
        / "capture/site-12-dataset_depositional_environment-current-attempt-1.body"
    )
    opened = observe_context_bodies(monkeypatch, {own})
    with pytest.raises(ValueError):
        read_neotoma_context_resource(output, site_id=12, resource_kind=KIND, **reader)
    assert opened == [own]
    opened.clear()
    forensic = read_neotoma_context_resource_entity(
        output, site_id=12, resource_kind=KIND, **reader
    )
    assert opened == [own]
    assert json.loads(forensic["body"])["data"] == [row]


def test_duplicate_native_owner_rows_are_not_silently_collapsed(
    dataset_products: Any, tmp_path: Path
) -> None:
    row = {
        "siteid": 12,
        "collectionunitid": 100,
        "datasetid": 201,
        "depenvt": "Lacustrine",
    }
    output, reader = publish(dataset_products(rows=[row, deepcopy(row)]), tmp_path)
    with pytest.raises(ValueError, match="ambiguous"):
        read_neotoma_context_resource(output, site_id=12, resource_kind=KIND, **reader)
    forensic = read_neotoma_context_resource_entity(
        output, site_id=12, resource_kind=KIND, **reader
    )
    assert json.loads(forensic["body"])["data"] == [row, row]


@pytest.mark.parametrize("change", ["protected", "database", "span", "alias"])
def test_current_whole_site_or_alias_restriction_blocks_writer_before_body(
    dataset_products: Any,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    change: str,
) -> None:
    inputs = dataset_products(change=change)
    opened = observe_context_bodies(monkeypatch, set())
    with pytest.raises(ValueError, match="owner|protected scope"):
        publish(inputs, tmp_path)
    assert opened == []


def test_rehashed_narrower_receipt_query_refuses_before_source_entity(
    dataset_products: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inputs = dataset_products()
    root = inputs["capture"]
    source = json.loads((root / "capture-manifest.json").read_bytes())
    reference = source["resources"][0]["attempts"][0]
    path = root / reference["receipt_file"]
    record = json.loads(path.read_bytes())
    record["parameters"] = {"datasetid": "201", "limit": "1", "offset": "0"}
    path.write_bytes(encoded_json(record))
    reference["receipt_sha256"] = sha256(path.read_bytes()).hexdigest()
    (root / "capture-manifest.json").write_bytes(encoded_json(source))
    inputs["writer"]["expected_capture_manifest_sha256"] = pin(
        root / "capture-manifest.json"
    )
    opened = observe_context_bodies(monkeypatch, set())
    with pytest.raises(ValueError, match="request owner"):
        publish(inputs, tmp_path)
    assert opened == []
