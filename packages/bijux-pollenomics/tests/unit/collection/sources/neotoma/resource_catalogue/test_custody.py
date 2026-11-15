"""Roster and native parent authentication precedes compact source projection."""

from __future__ import annotations

from collections.abc import Callable
from hashlib import sha256
import json
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.resource_catalogue import (
    build_neotoma_resource_catalogue,
)


def test_catalogue_requires_expected_roster_identity(
    catalogue_sources: Callable[..., dict[str, Any]],
) -> None:
    inputs = catalogue_sources()
    inputs["expected_roster_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="roster.*identity|roster.*digest"):
        build_neotoma_resource_catalogue(**inputs)


def test_self_consistent_roster_cannot_borrow_another_native_metadata_row(
    catalogue_sources: Callable[..., dict[str, Any]],
) -> None:
    inputs = catalogue_sources()
    path = inputs["roster_path"]
    roster = json.loads(path.read_bytes())
    roster["resources"][0]["metadata_locator"]["json_pointer"] = (
        "/data/0/site/datasets/1"
    )
    path.write_text(json.dumps(roster))
    inputs["expected_roster_sha256"] = sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="owner|identity"):
        build_neotoma_resource_catalogue(**inputs)


def test_body_drift_refuses_instead_of_retaining_old_compact_counts(
    catalogue_sources: Callable[..., dict[str, Any]],
) -> None:
    inputs = catalogue_sources()
    root = next(iter(inputs["resource_captures"].values()))
    body = next(root.glob("*current*.body"))
    document = json.loads(body.read_bytes())
    document["data"][0]["site"]["collectionunit"]["dataset"]["samples"] *= 2
    body.write_text(json.dumps(document))
    with pytest.raises(ValueError, match="identity|length"):
        build_neotoma_resource_catalogue(**inputs)


@pytest.mark.parametrize("lookup_id", [201, 202])
def test_historical_metadata_requires_exact_dataset_lookup_owner(
    catalogue_sources: Callable[..., dict[str, Any]], lookup_id: int
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture import (
        NeotomaMetadataPlan,
        NeotomaMetadataResponse,
        capture_neotoma_metadata,
    )

    inputs = catalogue_sources(capture_resources=False)
    root = inputs["roster_path"].parent
    roster = json.loads(inputs["roster_path"].read_bytes())
    native = {
        "datasetid": 201,
        "datasettype": "pollen",
        "database": None,
        "doi": [],
        "datasetpi": [],
    }
    original = root / "original-relational"
    (original / "surfaces" / "datasets").mkdir(parents=True)
    part = original / "surfaces/datasets/part.json"
    part.write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "source_dataset_id": 201,
                        "site_id": "neotoma:site:12",
                        "collection_unit_id": "neotoma:collection-unit:100",
                        "source_snapshot_id": "sha256:" + "a" * 64,
                        "build_id": "sha256:" + "b" * 64,
                        "source_payload": native,
                    }
                ]
            }
        )
    )
    part_sha = sha256(part.read_bytes()).hexdigest()
    (original / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "neotoma-relational-materialization-manifest.v1",
                "source_family": "neotoma",
                "source_snapshot_id": "sha256:" + "a" * 64,
                "build_id": "sha256:" + "b" * 64,
                "surfaces": {
                    "datasets": {
                        "row_count": 1,
                        "parts": [
                            {"path": "surfaces/datasets/part.json", "sha256": part_sha}
                        ],
                    }
                },
            }
        )
    )
    lookup_root = root / "current-lookup"
    empty = b'{"status":"success","data":[]}'
    lookup = capture_neotoma_metadata(
        lookup_root,
        plan=NeotomaMetadataPlan(dataset_ids=(lookup_id,)),
        fetch=lambda url, **_: NeotomaMetadataResponse(url, 200, (), empty),
    )
    inputs["metadata_captures"][lookup.manifest_sha256] = lookup_root
    roster["resources"][0]["metadata_locator"] = {
        "source_kind": "retained_relational_dataset_metadata_not_current_HTTP",
        "response_sha256": part_sha,
        "json_pointer": "/rows/0/source_payload",
    }
    roster["resources"][0]["current_metadata_lookup"] = {
        "dataset_id": 201,
        "manifest_sha256": lookup.manifest_sha256,
        "body_sha256": sha256(empty).hexdigest(),
        "successful_empty": True,
        "absence_certified": False,
    }
    inputs["roster_path"].write_text(json.dumps(roster))
    inputs["expected_roster_sha256"] = sha256(
        inputs["roster_path"].read_bytes()
    ).hexdigest()
    inputs["original_relational_root"] = original
    if lookup_id != 201:
        with pytest.raises(ValueError, match="lookup"):
            build_neotoma_resource_catalogue(**inputs)
    else:
        catalogue = build_neotoma_resource_catalogue(**inputs)
        row = catalogue["resources"][0]
        assert row["original_epoch"]["status"] == "retained_dataset_metadata"
        assert (
            row["metadata"]["source"]["current_metadata_lookup"]["absence_certified"]
            is False
        )
        assert (
            row["versions"]["current"]["acquisition_status"]
            == "not_attempted_pending_capture"
        )
        from bijux_pollenomics.collection.sources.neotoma.resource_catalogue import (
            write_neotoma_resource_catalogue,
        )

        row["metadata"]["source"]["current_metadata_lookup_source"]["receipt_file"] = (
            "invented-lookup.receipt.json"
        )
        with pytest.raises(ValueError, match="metadata/source tuple"):
            write_neotoma_resource_catalogue(
                root / "forged-lookup-publication",
                catalogue=catalogue,
                roster_path=inputs["roster_path"],
                capture_sources=inputs["metadata_captures"],
                original_relational_root=original,
            )


def _inventory_inputs(
    catalogue_sources: Callable[..., dict[str, Any]],
    *,
    all_types: bool,
    identical_views: bool = False,
    large_metadata: bool = False,
) -> tuple[dict[str, Any], dict[str, Any], bytes]:
    from urllib.parse import parse_qs, urlsplit

    from bijux_pollenomics.collection.sources.neotoma.capture import (
        NeotomaMetadataLimits,
        NeotomaMetadataPlan,
        NeotomaMetadataResponse,
        capture_neotoma_metadata,
    )

    inputs = catalogue_sources(
        capture_resources=False,
        auxiliary_type="geochronologic" if all_types else "pollen",
    )
    prior = next(iter(inputs["metadata_captures"].values()))
    rows = [
        json.loads((prior / f"site-{site}-datasets.body").read_bytes())["data"][0]
        for site in (12, 13, 14)
    ]
    if large_metadata:
        rows[0]["site"]["datasets"][0]["datasetnotes"] = "x" * (2 * 1024 * 1024)
    primary = json.loads(json.dumps(rows))
    if not identical_views:
        primary[0]["site"]["datasets"].reverse()
    small_limit = 400 if identical_views else 2
    bodies: dict[tuple[int, int], bytes] = {}
    for limit in (small_limit, 10000):
        native_rows = primary if limit == 10000 else rows
        for offset in range(0, len(native_rows) + limit, limit):
            bodies[limit, offset] = json.dumps(
                {
                    "status": "success",
                    "data": native_rows[offset : offset + limit],
                }
            ).encode()
    inventory = inputs["roster_path"].parent / "inventory"
    capture = capture_neotoma_metadata(
        inventory,
        plan=NeotomaMetadataPlan(
            inventory_bbox=(10, 60, 14, 63),
            inventory_limits=(small_limit, 10000),
            inventory_all_dataset_types=all_types,
        ),
        limits=NeotomaMetadataLimits(max_response_bytes=8 * 1024 * 1024),
        fetch=lambda url, **_: NeotomaMetadataResponse(
            url,
            200,
            (),
            bodies[
                int(parse_qs(urlsplit(url).query)["limit"][0]),
                int(parse_qs(urlsplit(url).query)["offset"][0]),
            ],
        ),
    )
    body = bodies[10000, 0]
    receipt_path = inventory / "inventory-limit-10000-offset-0.receipt.json"
    receipt = json.loads(receipt_path.read_bytes())
    roster = json.loads(inputs["roster_path"].read_bytes())
    roster["source_metadata_capture_manifest_sha256"] = [capture.manifest_sha256]
    for resource in roster["resources"]:
        row_index = next(
            i
            for i, row in enumerate(primary)
            if row["site"]["siteid"] == resource["site_id"]
        )
        dataset_index = next(
            i
            for i, dataset in enumerate(primary[row_index]["site"]["datasets"])
            if dataset["datasetid"] == resource["dataset_id"]
        )
        resource["metadata_locator"] = {
            "response_sha256": sha256(body).hexdigest(),
            "json_pointer": f"/data/{row_index}/site/datasets/{dataset_index}",
            "capture_manifest_sha256": capture.manifest_sha256,
            "request_name": "inventory-limit-10000-offset-0",
            "receipt_file": receipt_path.name,
            "receipt_sha256": sha256(receipt_path.read_bytes()).hexdigest(),
            "body_file": receipt["body_file"],
            "role": "dataset_inventory" if all_types else "pollen_inventory",
            "parameters": receipt["parameters"],
        }
    inputs["roster_path"].write_text(json.dumps(roster))
    inputs["expected_roster_sha256"] = sha256(
        inputs["roster_path"].read_bytes()
    ).hexdigest()
    inputs["metadata_captures"] = {capture.manifest_sha256: inventory}
    return inputs, receipt, body


@pytest.mark.parametrize("all_types", [False, True])
def test_inventory_receipts_supply_exact_native_metadata_without_site_requests(
    catalogue_sources: Callable[..., dict[str, Any]],
    all_types: bool,
) -> None:
    inputs, receipt, body = _inventory_inputs(catalogue_sources, all_types=all_types)
    catalogue = build_neotoma_resource_catalogue(**inputs)
    assert catalogue["summary"]["resource_count"] == 4
    assert len(catalogue["sites"]) == 3
    for row in catalogue["resources"]:
        source = row["metadata"]["source"]
        assert source["expected_site_id"] is None
        assert source["request_name"] == "inventory-limit-10000-offset-0"
        assert source["parameters"] == receipt["parameters"]
        assert source["body_sha256"] == sha256(body).hexdigest()
        assert source["role"] == (
            "dataset_inventory" if all_types else "pollen_inventory"
        )
        assert row["metadata"]["native_dataset"]["datasetid"] == row["dataset_id"]
    inventory = next(iter(inputs["metadata_captures"].values()))
    first_small = json.loads(
        (inventory / "inventory-limit-2-offset-0.body").read_bytes()
    )
    first_primary = json.loads(body)
    assert [r["datasetid"] for r in first_small["data"][0]["site"]["datasets"]] == [
        201,
        202,
    ]
    assert [r["datasetid"] for r in first_primary["data"][0]["site"]["datasets"]] == [
        202,
        201,
    ]


@pytest.mark.parametrize(
    "field",
    [
        "capture_manifest_sha256",
        "request_name",
        "receipt_file",
        "receipt_sha256",
        "body_file",
        "role",
        "parameters",
    ],
)
def test_inventory_metadata_locator_cannot_substitute_receipt_or_query_scope(
    catalogue_sources: Callable[..., dict[str, Any]],
    field: str,
) -> None:
    inputs, _, _ = _inventory_inputs(catalogue_sources, all_types=True)
    roster = json.loads(inputs["roster_path"].read_bytes())
    roster["resources"][0]["metadata_locator"][field] = (
        {"limit": "2", "offset": "0"} if field == "parameters" else "invented"
    )
    inputs["roster_path"].write_text(json.dumps(roster))
    inputs["expected_roster_sha256"] = sha256(
        inputs["roster_path"].read_bytes()
    ).hexdigest()
    with pytest.raises(ValueError, match="locator|receipt|scope"):
        build_neotoma_resource_catalogue(**inputs)


def test_identical_inventory_views_keep_explicit_primary_receipt_identity(
    catalogue_sources: Callable[..., dict[str, Any]],
) -> None:
    inputs, _, primary = _inventory_inputs(
        catalogue_sources,
        all_types=True,
        identical_views=True,
    )
    root = next(iter(inputs["metadata_captures"].values()))
    assert (root / "inventory-limit-400-offset-0.body").read_bytes() == primary
    catalogue = build_neotoma_resource_catalogue(**inputs)
    assert all(
        row["metadata"]["source"]["request_name"] == "inventory-limit-10000-offset-0"
        for row in catalogue["resources"]
    )


@pytest.mark.parametrize(
    "field,wrong",
    [
        ("site_id", 999),
        ("collection_unit_id", 999),
        ("dataset_type", "charcoal"),
        ("database", "invented database"),
        ("dataset_doi_values", ["invented DOI"]),
    ],
)
def test_inventory_adapter_preserves_native_owner_type_database_and_doi_checks(
    catalogue_sources: Callable[..., dict[str, Any]],
    field: str,
    wrong: object,
) -> None:
    inputs, _, _ = _inventory_inputs(catalogue_sources, all_types=True)
    roster = json.loads(inputs["roster_path"].read_bytes())
    roster["resources"][0][field] = wrong
    inputs["roster_path"].write_text(json.dumps(roster))
    inputs["expected_roster_sha256"] = sha256(
        inputs["roster_path"].read_bytes()
    ).hexdigest()
    with pytest.raises(ValueError, match="owner|identity"):
        build_neotoma_resource_catalogue(**inputs)


def test_inventory_metadata_reuses_one_authenticated_decoded_body_buffer(
    catalogue_sources: Callable[..., dict[str, Any]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.resource_catalogue import custody

    inputs, _, _ = _inventory_inputs(catalogue_sources, all_types=True)
    original = custody.pinned_object
    body_reads = []

    def read(path: Any, digest: str, bound: int) -> dict[str, Any]:
        if path.name.endswith(".body"):
            body_reads.append(path.name)
        return original(path, digest, bound)

    monkeypatch.setattr(custody, "pinned_object", read)
    catalogue = build_neotoma_resource_catalogue(**inputs)
    assert len(catalogue["resources"]) == 4
    assert body_reads == ["inventory-limit-10000-offset-0.body"]


def test_inventory_metadata_replay_accepts_bounded_captured_large_entities(
    catalogue_sources: Callable[..., dict[str, Any]],
) -> None:
    inputs, _, body = _inventory_inputs(
        catalogue_sources,
        all_types=True,
        large_metadata=True,
    )
    assert len(body) > 2 * 1024 * 1024
    catalogue = build_neotoma_resource_catalogue(**inputs)
    assert len(catalogue["resources"]) == 4
    from bijux_pollenomics.collection.sources.neotoma.resource_catalogue import (
        load_neotoma_resource_catalogue,
        write_neotoma_resource_catalogue,
    )

    output = inputs["roster_path"].parent / "large-metadata-catalogue"
    write_neotoma_resource_catalogue(
        output,
        catalogue=catalogue,
        roster_path=inputs["roster_path"],
        capture_sources=inputs["metadata_captures"],
    )
    loaded = load_neotoma_resource_catalogue(
        output,
        expected_manifest_sha256=sha256(
            (output / "manifest.json").read_bytes()
        ).hexdigest(),
        capture_sources=inputs["metadata_captures"],
        require_source_bodies=True,
    )
    assert len(loaded["resources"]) == 4
