"""Challenge generated production transport through its actual packaged factory."""

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


def query(packet: dict[str, Any], action: str) -> dict[str, Any]:
    return invoke(
        packet,
        "(async()=>{try{const value=await "
        + action
        + ";console.log(JSON.stringify({refused:false,value,calls}));}catch(error){console.log(JSON.stringify({refused:true,error:String(error.message),calls}));}})();",
    )


def test_real_v1_and_v2_keep_native_and_ancillary_denominators_distinct(
    scoped_catalogue: AtlasResourceCatalogue, tmp_path: Path
) -> None:
    v2 = publish(scoped_catalogue, tmp_path / "published-v2")
    v1 = publish(scoped_catalogue, tmp_path / "published-v1", ancillary=False)
    for packet in [v1, v2]:
        value = query(packet, "reader.inventory()")
        assert value["refused"] is False
        counts = {kind: len(rows) for kind, rows in value["value"].items()}
        domain = packet["manifest"]["domains"]["resources"]
        assert counts["resources"] == domain["record_count"]
        assert counts["sites"] == domain["site_count"]
        assert len(value["calls"]) == len(domain["index_part_ids"])
        if packet is v1:
            assert "facet_slots" not in counts
        else:
            assert counts["facet_slots"] == domain["ancillary_slot_count"]
            assert counts["ancillary_context"] == 1


@pytest.mark.parametrize("field", ["site_id", "collection_unit_id"])
def test_selected_facet_detail_cannot_change_index_native_owner(
    scoped_catalogue: AtlasResourceCatalogue, tmp_path: Path, field: str
) -> None:
    packet = publish(scoped_catalogue, tmp_path / "published")
    domain = packet["manifest"]["domains"]["resources"]
    indexes = [
        r
        for key in domain["index_asset_keys"]
        for r in packet["payloads"][key]["records"]
    ]
    indexed = next(r for r in indexes if r["entity_type"] == "facet_slots")
    detail = next(
        r
        for r in packet["payloads"][domain["part_asset_keys"][indexed["part_id"]]][
            "records"
        ]
        if r["slot_key"] == indexed["record_id"]
    )
    original = deepcopy(detail["root_identity"])
    detail["root_identity"][field] += 100000
    result = query(
        packet,
        "reader.ancillary('facet_slots'," + json.dumps(indexed["record_id"]) + ")",
    )
    (tmp_path / "facet-owner-proof.json").write_text(
        json.dumps(
            {
                "field": field,
                "index": indexed,
                "original_owner": original,
                "mutated_owner": detail["root_identity"],
                "browser": result,
            },
            indent=2,
        )
        + "\n"
    )
    assert result["refused"] is True
    assert result["error"].startswith("Source resource metadata:")


def test_selected_detail_cannot_accept_unindexed_payload_member(
    scoped_catalogue: AtlasResourceCatalogue, tmp_path: Path
) -> None:
    packet = publish(scoped_catalogue, tmp_path / "published")
    domain = packet["manifest"]["domains"]["resources"]
    indexes = [
        r
        for key in domain["index_asset_keys"]
        for r in packet["payloads"][key]["records"]
    ]
    indexed = next(r for r in indexes if r["entity_type"] == "facet_slots")
    key = domain["part_asset_keys"][indexed["part_id"]]
    payload = packet["payloads"][key]
    extra = deepcopy(payload["records"][0])
    extra["root_identity"]["dataset_id"] += 100000
    extra["slot_key"] = (
        "dataset-"
        + str(extra["root_identity"]["dataset_id"])
        + "-facet-"
        + extra["facet"]
        + "-current"
    )
    payload["records"].append(extra)
    next(r for r in packet["manifest"]["assets"] if r["asset_key"] == key)[
        "record_count"
    ] += 1
    result = query(
        packet,
        "reader.ancillary('facet_slots'," + json.dumps(indexed["record_id"]) + ")",
    )
    (tmp_path / "unindexed-member-proof.json").write_text(
        json.dumps(
            {"unindexed_identity": extra["slot_key"], "browser": result}, indent=2
        )
        + "\n"
    )
    assert result["refused"] is True


@pytest.mark.parametrize(
    "damage",
    [
        "facet_role",
        "capture_epoch",
        "observation_role",
        "occurrence_join",
        "supporting_scope",
        "supporting_selector",
        "missing_member",
    ],
)
def test_every_selected_part_keeps_indexed_source_posture_and_complete_membership(
    request: pytest.FixtureRequest, tmp_path: Path, damage: str
) -> None:
    supporting = damage.startswith("supporting_")
    catalogue = request.getfixturevalue(
        "supporting_catalogue" if supporting else "scoped_catalogue"
    )
    packet = publish(catalogue, tmp_path / "published")
    domain = packet["manifest"]["domains"]["resources"]
    kind = (
        "supporting_entries"
        if supporting
        else "ancillary_observations"
        if damage in {"capture_epoch", "observation_role"}
        else "linked_occurrences"
        if damage == "occurrence_join"
        else "facet_slots"
    )
    indexes = [
        row
        for key in domain["index_asset_keys"]
        for row in packet["payloads"][key]["records"]
    ]
    indexed = next(row for row in indexes if row["entity_type"] == kind)
    key = domain["part_asset_keys"][indexed["part_id"]]
    payload = packet["payloads"][key]
    identity_field = {
        "facet_slots": "slot_key",
        "ancillary_observations": "observation_id",
        "linked_occurrences": "occurrence_id",
    }.get(kind)
    detail = (
        payload["records"][0]
        if supporting
        else next(
            row
            for row in payload["records"]
            if row[identity_field] == indexed["record_id"]
        )
    )
    if damage == "facet_role":
        detail["current_declared_role"] = "changed_source_role"
    elif damage == "capture_epoch":
        detail["capture_epoch"]["changed_source_epoch"] = True
    elif damage == "observation_role":
        detail["current_use_role"] = "changed_source_role"
    elif damage == "occurrence_join":
        detail["current_owner_join"] = "changed_source_join"
    elif damage == "supporting_scope":
        detail["entry"]["scope"] = {"changed_scope": True}
    elif damage == "supporting_selector":
        detail["entry"]["table_key"] = "changed_source_selector"
    else:
        assert len(payload["records"]) > 1
        removed = next(row for row in payload["records"] if row is not detail)
        payload["records"].remove(removed)
        next(row for row in packet["manifest"]["assets"] if row["asset_key"] == key)[
            "record_count"
        ] -= 1
    result = query(
        packet,
        "reader.ancillary("
        + json.dumps(kind)
        + ","
        + json.dumps(indexed["record_id"])
        + ")",
    )
    assert result["refused"] is True and result["error"].startswith(
        "Source resource metadata:"
    )


@pytest.mark.parametrize("cached", [False, True])
def test_consumed_or_cached_selected_parts_recheck_the_index_join(
    scoped_catalogue: AtlasResourceCatalogue, tmp_path: Path, cached: bool
) -> None:
    packet = publish(scoped_catalogue, tmp_path / "published")
    domain = packet["manifest"]["domains"]["resources"]
    key = domain["part_asset_keys"]["facet_slots:0"]
    identity = packet["payloads"][key]["records"][0]["slot_key"]
    if cached:
        setup = "await reader.ancillary('facet_slots'," + json.dumps(identity) + ");"
    else:
        setup = (
            "reader.consume(manifest.assets.find(row=>row.asset_key==="
            + json.dumps(key)
            + "),payloads["
            + json.dumps(key)
            + "]);"
        )
    action = (
        "(async()=>{"
        + setup
        + "payloads["
        + json.dumps(key)
        + "][\"records\"][0].root_identity.site_id+=100000;return reader.ancillary('facet_slots',"
        + json.dumps(identity)
        + ");})()"
    )
    result = query(packet, action)
    assert result["refused"] is True and result["error"].startswith(
        "Source resource metadata:"
    )


@pytest.mark.parametrize("name", ["scoped_catalogue", "supporting_catalogue"])
def test_all_ancillary_projections_remain_lazy_for_real_publisher_records(
    request: pytest.FixtureRequest, tmp_path: Path, name: str
) -> None:
    packet = publish(request.getfixturevalue(name), tmp_path / name)
    result = query(
        packet,
        "(async()=>{const inventory=await reader.inventory(),before=calls.length;let details=0;for(const [kind,rows] of Object.entries(inventory)){if(['resources','sites','descriptors'].includes(kind)||!rows.length)continue;const detail=await reader.ancillary(kind,rows[0].record_id);if(!detail)throw Error('Missing generated detail');details++;}return {before,after:calls.length,details};})()",
    )
    assert result["refused"] is False
    assert result["value"]["before"] == len(
        packet["manifest"]["domains"]["resources"]["index_part_ids"]
    )
    assert result["value"]["details"] >= 4
    assert (
        result["value"]["after"]
        <= result["value"]["before"] + result["value"]["details"]
    )


def test_cached_part_cannot_duplicate_one_indexed_member_and_omit_another(
    scoped_catalogue: AtlasResourceCatalogue, tmp_path: Path
) -> None:
    packet = publish(scoped_catalogue, tmp_path / "published")
    domain = packet["manifest"]["domains"]["resources"]
    key = domain["part_asset_keys"]["facet_slots:0"]
    records = packet["payloads"][key]["records"]
    assert len(records) > 1
    identity = records[0]["slot_key"]
    result = query(
        packet,
        "(async()=>{await reader.ancillary('facet_slots',"
        + json.dumps(identity)
        + ");const records=payloads["
        + json.dumps(key)
        + "].records;records[1]=JSON.parse(JSON.stringify(records[0]));return reader.ancillary('facet_slots',"
        + json.dumps(identity)
        + ");})()",
    )
    assert result["refused"] is True and result["error"].startswith(
        "Source resource metadata:"
    )
