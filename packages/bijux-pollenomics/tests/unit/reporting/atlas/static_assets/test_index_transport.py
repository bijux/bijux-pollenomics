"""Physical parts preserve logical indexes while retaining every transport limit."""

from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
from typing import Any, cast

import pytest

from bijux_pollenomics.core.calendar_support import (
    SIGNED_CALENDAR_PROFILE,
    SignedCalendarSupport,
)
from bijux_pollenomics.reporting.map_document.static_assets import (
    index_bundles as logical_transport,
)
from bijux_pollenomics.reporting.map_document.static_assets import (
    index_transport as subject,
)
from bijux_pollenomics.reporting.map_document.static_assets import writer
from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
    normalize_asset_inventory,
)
from bijux_pollenomics.reporting.map_document.static_assets.index_bundles import (
    build_index_bundle,
)
from bijux_pollenomics.reporting.map_document.static_assets.indexes import (
    build_indexes,
    index_reference_count,
)
from bijux_pollenomics.reporting.map_document.static_assets.serialization import (
    canonical_json,
    chunk_script_bytes,
)

from .payloads import read_static_asset_payload


def logical(*, signed: bool = False, components: bool = False) -> dict[str, Any]:
    features: list[dict[str, Any]] = [
        {
            "record_id": "sample:1",
            "title": "Native pollen label",
            "country": "Sweden",
            "latitude": 59,
            "longitude": 18,
            "time_start_bp": -10 if signed else 100,
            "time_end_bp": 20 if signed else 200,
        },
        {
            "record_id": "sample:2",
            "title": "Another source label",
            "country": "Denmark",
            "latitude": 55,
            "longitude": 12,
            "time_start_bp": 300,
            "time_end_bp": 400,
        },
    ]
    if signed:
        for feature in features:
            younger, older = feature["time_start_bp"], feature["time_end_bp"]
            feature.update(
                data_kind="synthetic",
                evidence_role="model_output",
                scientific_acceptance="not_evaluated",
                age_type="calendar_bp",
                source_age_support_bp=[[younger, older]],
                source_calendar_support=SignedCalendarSupport(
                    younger, older, support_kind="closed_age_support"
                ).as_dict(),
                declared_calendar_support=SignedCalendarSupport(
                    younger, older, support_kind="declared_stationarity_envelope"
                ).as_dict(),
            )
    else:
        for feature in features:
            feature["temporal_semantics"] = {
                "schema_version": "temporal-semantics.v1",
                "comparability_posture": "numeric_interval",
            }
    if components:
        features[0].update(
            {
                "chronology_role": "locality_sample_coverage_hull",
                "sample_ids": ["one", "two"],
                "sample_chronologies": [
                    {
                        "schema_version": "adna-sample-chronology-support.v1",
                        "sample_id": "one",
                        "chronology": {
                            "original_text": "original sample one",
                            "precision_posture": "sample_precise_interval",
                            "evidence_class": "controlled_numeric_sample_date",
                            "time_start_bp": 100,
                            "time_end_bp": 110,
                        },
                    },
                    {
                        "schema_version": "adna-sample-chronology-support.v1",
                        "sample_id": "two",
                        "chronology": {
                            "original_text": "original sample two",
                            "precision_posture": "sample_precise_interval",
                            "evidence_class": "controlled_numeric_sample_date",
                            "time_start_bp": 190,
                            "time_end_bp": 200,
                        },
                    },
                ],
            }
        )
    profile = SIGNED_CALENDAR_PROFILE if signed else None
    return {
        **build_indexes(
            [{"key": "owned", "features": features}], temporal_profile=profile
        ),
        "detail_record_asset_keys": {"sample:1": "details:3"},
        "scope_slug": "native",
        "version": "v66",
        "build_id": "atlas-" + "a" * 64,
    }


def inventory(
    bundle: dict[str, Any], parts: list[dict[str, object]]
) -> tuple[list[dict[str, Any]], dict[str, dict[str, object]], dict[str, Any]]:
    split = len(parts) > 1
    rows = [
        {
            "domain": "indexes",
            "asset_key": part["asset_key"],
            "sequence": int(str(part["asset_key"]).split(":")[1]),
            "record_count": len(cast(list[object], part["shards"]))
            if split
            else bundle["reference_count"],
        }
        for part in parts
    ]
    manifest = {
        **{
            key: bundle[key]
            for key in (
                "scope_slug",
                "version",
                "build_id",
                "temporal_profile",
                "temporal_axis",
            )
            if key in bundle
        },
        "compatibility": {
            "index_schema": bundle["schema_version"],
            **(
                {"search_index_abi": bundle["search_index_abi"]}
                if "search_index_abi" in bundle
                else {}
            ),
            **({"index_transport_schema": subject.INDEX_PART_SCHEMA} if split else {}),
        },
        "domains": {"indexes": {"record_count": bundle["reference_count"]}},
    }
    return rows, {str(part["asset_key"]): part for part in parts}, manifest


def split_fixture(
    monkeypatch: pytest.MonkeyPatch, *, signed: bool = False, components: bool = False
) -> tuple[
    dict[str, Any], list[dict[str, Any]], dict[str, dict[str, object]], dict[str, Any]
]:
    monkeypatch.setattr(subject, "ATLAS_CHUNK_MAX_BYTES", 3500)
    bundle = build_index_bundle(logical(signed=signed, components=components))
    parts = subject.partition_index_bundle(bundle, first_sequence=98)
    assert len(parts) > 1
    rows, payloads, manifest = inventory(bundle, parts)
    return bundle, rows, payloads, manifest


def test_fitting_singleton_preserves_exact_payload_and_wire_bytes() -> None:
    bundle = build_index_bundle(logical())
    expected = {**bundle, "asset_key": "indexes:9"}
    parts = subject.partition_index_bundle(bundle, first_sequence=9)
    assert parts == [expected]
    encoded = canonical_json(expected)
    assert chunk_script_bytes(
        asset_key="indexes:9",
        payload_sha256=hashlib.sha256(encoded.encode()).hexdigest(),
        payload_json=encoded,
        payload_encoding="json",
    ) == chunk_script_bytes(
        asset_key="indexes:9",
        payload_sha256=subject._digest(parts[0]),
        payload_json=canonical_json(parts[0]),
        payload_encoding="json",
    )
    rows, payloads, manifest = inventory(bundle, parts)
    assert subject.decode_index_payloads(rows, payloads, manifest=manifest) == logical()
    assert "index_transport_schema" not in manifest["compatibility"]


@pytest.mark.parametrize(
    "signed,components", [(False, False), (True, False), (False, True)]
)
def test_parts_preserve_every_original_shard_and_logical_query(
    monkeypatch: pytest.MonkeyPatch, signed: bool, components: bool
) -> None:
    bundle, rows, payloads, manifest = split_fixture(
        monkeypatch, signed=signed, components=components
    )
    assert (
        subject.assemble_index_payloads(
            rows, dict(reversed(list(payloads.items()))), manifest=manifest
        )
        == bundle
    )
    decoded = subject.decode_index_payloads(rows, payloads, manifest=manifest)
    assert decoded == logical(signed=signed, components=components)
    if signed:
        assert decoded["time_interval_feature_indexes"] == [
            [-10, 20, "owned", 0],
            [300, 400, "owned", 1],
        ]
    if components:
        assert decoded["time_interval_feature_indexes"] == [
            [100, 110, "owned", 0],
            [190, 200, "owned", 0],
            [300, 400, "owned", 1],
        ]
    joined = [
        shard
        for payload in payloads.values()
        for shard in cast(list[object], payload["shards"])
    ]
    assert canonical_json(joined) == canonical_json(bundle["shards"])
    assert sum(row["record_count"] for row in rows) == bundle["shard_count"]
    assert manifest["domains"]["indexes"]["record_count"] == bundle["reference_count"]
    for payload in payloads.values():
        encoded = canonical_json(payload)
        assert len(encoded.encode()) <= 3500
        assert (
            len(
                chunk_script_bytes(
                    asset_key=str(payload["asset_key"]),
                    payload_sha256=subject._digest(payload),
                    payload_json=encoded,
                    payload_encoding="json",
                )
            )
            <= 3500
        )


@pytest.mark.parametrize(
    "tamper",
    [
        "missing",
        "undeclared",
        "duplicate_row",
        "reorder",
        "part_number",
        "part_count",
        "range",
        "build",
        "schema",
        "abi",
        "header",
        "digest",
        "shard_duplicate",
        "row_count",
        "domain_count",
        "marker_null",
    ],
)
def test_parts_refuse_incomplete_foreign_or_inconsistent_inventory(
    monkeypatch: pytest.MonkeyPatch, tamper: str
) -> None:
    _, rows, payloads, manifest = split_fixture(monkeypatch)
    first, second = (
        payloads[str(rows[0]["asset_key"])],
        payloads[str(rows[1]["asset_key"])],
    )
    if tamper == "missing":
        del payloads[str(rows[-1]["asset_key"])]
    elif tamper == "undeclared":
        payloads["indexes:999"] = first
    elif tamper == "duplicate_row":
        rows[1] = rows[0]
    elif tamper == "reorder":
        rows.reverse()
    elif tamper == "part_number":
        second["part_number"] = 1
    elif tamper == "part_count":
        second["part_count"] = 999
    elif tamper == "range":
        second["first_shard_number"] = 1
    elif tamper == "build":
        second["build_id"] = "atlas-" + "b" * 64
    elif tamper == "schema":
        second["bundle_schema"] = "atlas-static-indexes.v4"
    elif tamper == "abi":
        second["search_index_abi"] = "foreign"
    elif tamper == "header":
        second["reference_count"] = 999
    elif tamper == "digest":
        first["bundle_sha256"] = "0" * 64
    elif tamper == "shard_duplicate":
        second["shards"] = first["shards"]
    elif tamper == "row_count":
        rows[0]["record_count"] += 1
    elif tamper == "domain_count":
        manifest["domains"]["indexes"]["record_count"] += 1
    else:
        manifest["compatibility"]["index_transport_schema"] = None
    with pytest.raises(ValueError):
        subject.decode_index_payloads(rows, payloads, manifest=manifest)


@pytest.mark.parametrize("wrong", [True, 1.0])
def test_global_reference_type_refuses_even_with_self_consistent_bundle_digest(
    monkeypatch: pytest.MonkeyPatch, wrong: bool | float
) -> None:
    base = logical()
    base.update(
        build_indexes(
            [
                {
                    "key": "owned",
                    "features": [
                        {
                            "record_id": "one",
                            "country": "Sweden",
                            "latitude": 60,
                            "longitude": 18,
                        }
                    ],
                }
            ]
        )
    )
    base["detail_record_asset_keys"] = {}
    bundle = build_index_bundle(base)
    assert bundle["reference_count"] == 1
    monkeypatch.setattr(subject, "ATLAS_CHUNK_MAX_BYTES", 1800)
    parts = subject.partition_index_bundle(bundle, first_sequence=98)
    assert len(parts) > 1
    rows, payloads, manifest = inventory(bundle, parts)
    bundle["reference_count"] = wrong
    for payload in payloads.values():
        payload["reference_count"] = wrong
        payload["bundle_sha256"] = subject._digest(bundle)
    with pytest.raises(ValueError, match="global reference count"):
        subject.decode_index_payloads(rows, payloads, manifest=manifest)


def test_actual_wire_size_and_asset_key_digits_control_partition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = build_index_bundle(logical())
    payload = {**bundle, "asset_key": "indexes:9"}
    raw = canonical_json(payload)
    size = len(
        chunk_script_bytes(
            asset_key="indexes:9",
            payload_sha256=subject._digest(payload),
            payload_json=raw,
            payload_encoding="json",
        )
    )
    assert len(raw.encode()) < size
    monkeypatch.setattr(subject, "ATLAS_CHUNK_MAX_BYTES", size)
    assert len(subject.partition_index_bundle(bundle, first_sequence=9)) == 1
    assert len(subject.partition_index_bundle(bundle, first_sequence=100000)) > 1
    monkeypatch.setattr(subject, "ATLAS_CHUNK_MAX_BYTES", size - 1)
    assert len(subject.partition_index_bundle(bundle, first_sequence=9)) > 1


@pytest.mark.parametrize(
    "field", ["reference_count", "shard_count", "component_time_support"]
)
def test_later_part_header_types_are_exact(
    monkeypatch: pytest.MonkeyPatch, field: str
) -> None:
    _, rows, payloads, manifest = split_fixture(monkeypatch, components=True)
    monkeypatch.setattr(subject, "ATLAS_CHUNK_MAX_BYTES", 4_194_304)
    later = payloads[str(rows[1]["asset_key"])]
    if field == "component_time_support":
        later[field] = 1
    else:
        later[field] = float(cast(int, later[field]))
    with pytest.raises(ValueError, match="global.*count|common header"):
        subject.decode_index_payloads(rows, payloads, manifest=manifest)


def test_later_part_boolean_cannot_replace_integer_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base = logical()
    base.update(
        build_indexes(
            [
                {
                    "key": "owned",
                    "features": [
                        {
                            "record_id": "one",
                            "country": "Sweden",
                            "latitude": 60,
                            "longitude": 18,
                        }
                    ],
                }
            ]
        )
    )
    base["detail_record_asset_keys"] = {}
    bundle = build_index_bundle(base)
    assert bundle["reference_count"] == 1
    monkeypatch.setattr(subject, "ATLAS_CHUNK_MAX_BYTES", 1800)
    rows, payloads, manifest = inventory(
        bundle, subject.partition_index_bundle(bundle, first_sequence=98)
    )
    assert len(rows) > 1
    monkeypatch.setattr(subject, "ATLAS_CHUNK_MAX_BYTES", 4_194_304)
    payloads[str(rows[1]["asset_key"])]["reference_count"] = True
    with pytest.raises(ValueError, match="global reference count"):
        subject.decode_index_payloads(rows, payloads, manifest=manifest)


def test_indivisible_shard_refuses_without_mutating_original(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = build_index_bundle(logical())
    before = deepcopy(bundle)
    monkeypatch.setattr(subject, "ATLAS_CHUNK_MAX_BYTES", 1)
    with pytest.raises(ValueError, match="one complete index shard"):
        subject.partition_index_bundle(bundle, first_sequence=0)
    assert bundle == before


def test_part_count_and_asset_sequence_digit_boundaries_are_exact(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(logical_transport, "ATLAS_CHUNK_TARGET_BYTES", 256)
    monkeypatch.setattr(subject, "ATLAS_CHUNK_MAX_BYTES", 3500)
    base = logical()
    base.update(
        build_indexes(
            [
                {
                    "key": "owned",
                    "features": [
                        {
                            "record_id": f"row:{index}",
                            "country": f"Country{index:03}",
                            "latitude": 20 + index,
                            "longitude": 10,
                        }
                        for index in range(36)
                    ],
                }
            ]
        )
    )
    bundle = build_index_bundle(base)
    before = canonical_json(bundle)
    parts = subject.partition_index_bundle(bundle, first_sequence=99)
    assert len(parts) >= 10
    assert all(part["part_count"] == len(parts) for part in parts)
    assert parts[0]["asset_key"] == "indexes:99"
    assert parts[1]["asset_key"] == "indexes:100"
    rows, payloads, manifest = inventory(bundle, parts)
    assert subject.decode_index_payloads(rows, payloads, manifest=manifest) == base
    assert canonical_json(bundle) == before
    assert parts == subject.partition_index_bundle(bundle, first_sequence=99)


def test_legacy_negative_age_is_not_admitted_by_new_transport() -> None:
    base = logical()
    base.update(
        build_indexes(
            [
                {
                    "key": "owned",
                    "features": [
                        {
                            "country": "Sweden",
                            "time_start_bp": -10,
                            "time_end_bp": 20,
                            "temporal_semantics": {
                                "schema_version": "temporal-semantics.v1",
                                "comparability_posture": "numeric_interval",
                            },
                        }
                    ],
                }
            ]
        )
    )
    bundle = build_index_bundle(base)
    rows, payloads, manifest = inventory(
        bundle, subject.partition_index_bundle(bundle, first_sequence=0)
    )
    assert (
        subject.decode_index_payloads(rows, payloads, manifest=manifest)[
            "time_interval_feature_indexes"
        ]
        == []
    )


def test_writer_parts_keep_build_id_and_non_index_asset_bytes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    points = [
        {
            "key": "source",
            "features": [
                {
                    "record_id": "one",
                    "country": "Sweden",
                    "latitude": 60,
                    "longitude": 18,
                    "title": "A source-owned pollen observation",
                    "time_start_bp": 100,
                    "time_end_bp": 200,
                }
            ],
        }
    ]
    original, split = tmp_path / "singleton", tmp_path / "parts"
    original.mkdir()
    split.mkdir()
    old = writer.write_static_atlas_assets(
        original, slug="native", version="v66", point_layers=points, polygon_layers=[]
    )
    monkeypatch.setattr(subject, "ATLAS_CHUNK_MAX_BYTES", 1800)
    new = writer.write_static_atlas_assets(
        split, slug="native", version="v66", point_layers=points, polygon_layers=[]
    )
    assert old.manifest["build_id"] == new.manifest["build_id"]
    before = normalize_asset_inventory(old.manifest["assets"])
    after = normalize_asset_inventory(new.manifest["assets"])
    assert [row for row in before if row["domain"] != "indexes"] == [
        row for row in after if row["domain"] != "indexes"
    ]
    for row in before:
        if row["domain"] != "indexes":
            assert (original / str(row["path"])).read_bytes() == (
                split / str(row["path"])
            ).read_bytes()
    index_rows = [row for row in after if row["domain"] == "indexes"]
    assert len(index_rows) > 1
    decoded = subject.decode_index_payloads(
        index_rows,
        {
            str(row["asset_key"]): read_static_asset_payload(split / str(row["path"]))
            for row in index_rows
        },
        manifest=new.manifest,
    )
    assert index_reference_count(decoded) == 1
