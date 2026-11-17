"""Browser contracts consume real publisher v2 without merging source populations."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.reporting.map_document.source_resources import (
    AtlasResourceCatalogue,
)

from .native_transport import invoke, publish


@pytest.mark.parametrize(
    "catalogue_name", ["legacy_catalogue", "scoped_catalogue", "supporting_catalogue"]
)
def test_published_v2_inventory_and_native_search_keep_separate_metadata_populations(
    request: pytest.FixtureRequest, tmp_path: Path, catalogue_name: str
) -> None:
    packet = publish(request.getfixturevalue(catalogue_name), tmp_path / "published")
    domain = packet["manifest"]["domains"]["resources"]
    observed = invoke(
        packet,
        """(async()=>{const inventory=await reader.inventory(),resources=await reader.search('');console.log(JSON.stringify({counts:Object.fromEntries(Object.entries(inventory).map(([kind,rows])=>[kind,rows.length])),resources:resources.map(row=>row.record_id),calls}));})().catch(error=>{console.error(error);process.exit(1)});""",
    )
    assert observed["counts"]["resources"] == domain["record_count"]
    assert observed["counts"]["sites"] == domain["site_count"]
    assert len(observed["resources"]) == domain["record_count"]
    for kind, field in [
        ("facet_slots", "ancillary_slot_count"),
        ("ancillary_observations", "ancillary_observation_count"),
        ("linked_occurrences", "ancillary_linked_occurrence_count"),
        ("supporting_archives", "supporting_archive_count"),
        ("supporting_entries", "supporting_entry_count"),
    ]:
        assert observed["counts"][kind] == domain[field]
    assert observed["counts"]["ancillary_context"] == 1
    assert len(observed["calls"]) == len(domain["index_part_ids"])


def assert_refused(
    packet: dict[str, Any], action: str = "await reader.search('')"
) -> None:
    """Require the metadata reader to refuse, rather than a fixture or syntax error."""
    try:
        result = invoke(
            packet,
            "(async()=>{try{"
            + action
            + ";console.log(JSON.stringify({refused:false}));}catch(error){console.log(JSON.stringify({refused:String(error.message).startsWith('Source resource metadata:')}));}})();",
        )
    except AssertionError as error:
        assert "Source resource metadata:" in str(error)
    else:
        assert result["refused"] is True


@pytest.mark.parametrize(
    "damage",
    [
        "unknown_kind",
        "count",
        "observation_kind",
        "missing_part",
        "missing_index",
        "duplicate_index",
        "wire_schema",
        "mapping_alias",
        "facet_owner",
    ],
)
def test_v2_unknown_or_incomplete_metadata_never_becomes_empty_success(
    scoped_catalogue: AtlasResourceCatalogue, tmp_path: Path, damage: str
) -> None:
    packet = publish(scoped_catalogue, tmp_path / "published")
    domain = packet["manifest"]["domains"]["resources"]
    index = packet["payloads"][domain["index_asset_keys"][0]]
    if damage == "unknown_kind":
        index["records"][0]["entity_type"] = "samples"
    elif damage == "count":
        domain["ancillary_linked_occurrence_count"] += 1
    elif damage == "observation_kind":
        next(
            r for r in index["records"] if r["entity_type"] == "ancillary_observations"
        )["kind"] = "dated_ecological_event"
    elif damage == "missing_part":
        del domain["part_asset_keys"]["linked_occurrences:0"]
        domain["part_count"] -= 1
    elif damage == "missing_index":
        domain["index_part_ids"] = []
    elif damage == "duplicate_index":
        index["records"].append(deepcopy(index["records"][0]))
        next(
            r
            for r in packet["manifest"]["assets"]
            if r["asset_key"] == domain["index_asset_keys"][0]
        )["record_count"] += 1
    elif damage == "wire_schema":
        index["schema_version"] = "atlas-source-resource-chunk.v2"
    elif damage == "mapping_alias":
        domain["part_asset_keys"]["linked_occurrences:0"] = domain["part_asset_keys"][
            "facet_slots:0"
        ]
    else:
        next(r for r in index["records"] if r["entity_type"] == "facet_slots")[
            "root_dataset_id"
        ] = True
    assert_refused(packet)


@pytest.mark.parametrize(
    "damage",
    [
        "native_buffer",
        "active_download",
        "asserted_verification",
        "wrong_record_identity",
        "unsafe_native_owner",
    ],
)
def test_ancillary_detail_refuses_native_routes_authority_or_wrong_identity(
    scoped_catalogue: AtlasResourceCatalogue, tmp_path: Path, damage: str
) -> None:
    packet = publish(scoped_catalogue, tmp_path / "published")
    domain = packet["manifest"]["domains"]["resources"]
    body = packet["payloads"][domain["part_asset_keys"]["facet_slots:0"]]
    record = body["records"][0]
    identity = record["slot_key"]
    if damage == "native_buffer":
        record["extra"] = {"body_buffer": [1, 2, 3]}
    elif damage == "active_download":
        record["extra"] = {"download_url": "https://example.invalid/never.body"}
    elif damage == "asserted_verification":
        record["extra"] = {"native_field_value_verified": True}
    elif damage == "wrong_record_identity":
        record["slot_key"] = "foreign-slot"
    else:
        record["root_identity"]["dataset_id"] = 2**53
    assert_refused(
        packet, "await reader.ancillary('facet_slots'," + json.dumps(identity) + ")"
    )


def test_ancillary_detail_is_lazy_detached_and_does_not_offer_native_download(
    scoped_catalogue: AtlasResourceCatalogue, tmp_path: Path
) -> None:
    packet = publish(scoped_catalogue, tmp_path / "published")
    result = invoke(
        packet,
        """(async()=>{const inventory=await reader.inventory(),before=calls.length,first=inventory.facet_slots[0];const detail=await reader.ancillary('facet_slots',first.record_id),original=detail.slot_key;detail.slot_key='changed caller copy';const again=await reader.ancillary('facet_slots',first.record_id);console.log(JSON.stringify({before,after:calls.length,original,again:again.slot_key,download:typeof reader.downloadAncillary,rows:(await reader.search('',{population:'facet_slots'})).length}));})().catch(error=>{console.error(error);process.exit(1)});""",
    )
    assert result["after"] == result["before"] + 1
    assert result["again"] == result["original"]
    assert result["download"] == "undefined"
    assert (
        result["rows"]
        == packet["manifest"]["domains"]["resources"]["ancillary_slot_count"]
    )


def test_ancillary_search_does_not_silently_ignore_a_native_country_filter(
    scoped_catalogue: AtlasResourceCatalogue, tmp_path: Path
) -> None:
    packet = publish(scoped_catalogue, tmp_path / "published")
    assert_refused(
        packet, "await reader.search('',{population:'linked_occurrences',country:'SE'})"
    )
