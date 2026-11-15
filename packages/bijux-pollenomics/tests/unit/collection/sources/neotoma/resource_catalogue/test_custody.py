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
