"""Bounded, authenticated logical shards for static atlas indexes."""

from __future__ import annotations

import base64
from collections.abc import Mapping
import hashlib
import json
from math import isfinite
import zlib

from ....core.calendar_support import SignedCalendarSupport
from ..temporal_admission import calendar_profile_metadata, read_calendar_profile
from .budgets import ATLAS_CHUNK_MAX_BYTES, ATLAS_CHUNK_TARGET_BYTES
from .indexes import index_reference_count
from .search import SEARCH_ABI, SEARCH_KIND, validate_search_index
from .search.transport import (
    SEARCH_DOCUMENTS_SCHEMA,
    encode_search_documents,
    read_search_transport,
    restore_search_documents,
    search_document_utf16_units,
)
from .serialization import canonical_gzip_compress, canonical_json

INDEX_BUNDLE_SCHEMA = "atlas-static-indexes.v3"
INDEX_SHARD_SCHEMA = "atlas-static-index-shard.v1"
COMPONENT_INDEX_BUNDLE_SCHEMA = "atlas-static-indexes.v5"
COMPONENT_INDEX_SHARD_SCHEMA = "atlas-static-index-shard.v3"
SIGNED_INDEX_BUNDLE_SCHEMA = "atlas-static-indexes.v4"
SIGNED_INDEX_SHARD_SCHEMA = "atlas-static-index-shard.v2"
INDEX_KINDS = (
    "country_feature_indexes",
    "spatial_degree_feature_indexes",
    "time_interval_feature_indexes",
    "signal_layer_indexes",
    "detail_record_asset_keys",
)


def _kinds(payload: Mapping[str, object]) -> tuple[str, ...]:
    if "search_index_abi" not in payload:
        if SEARCH_KIND in payload:
            raise ValueError("Undeclared search index")
        return INDEX_KINDS
    if payload["search_index_abi"] != SEARCH_ABI:
        raise ValueError("Unsupported search ABI")
    return (*INDEX_KINDS, SEARCH_KIND)


def build_index_bundle(
    indexes: Mapping[str, object], *, search_transport_schema: str | None = None
) -> dict[str, object]:
    """Encode the exact v2 logical indexes as bounded deterministic shards."""
    profile = read_calendar_profile(indexes)
    profile_fields = calendar_profile_metadata(profile)
    component_fields = _component_fields(indexes, profile)
    search_documents: dict[str, object] | None = None
    search_fields: dict[str, object] = {}
    if search_transport_schema is not None:
        if (
            search_transport_schema != SEARCH_DOCUMENTS_SCHEMA
            or SEARCH_KIND not in _kinds(indexes)
        ):
            raise ValueError("Unsupported search transport encoder")
        search_documents, search_counts = encode_search_documents(
            indexes.get(SEARCH_KIND)
        )
        search_fields = {
            "search_transport_schema": SEARCH_DOCUMENTS_SCHEMA,
            "search_transport_counts": search_counts,
        }
    identities = {
        field: _required_text(indexes.get(field), field)
        for field in ("scope_slug", "version", "build_id")
    }
    encoded_shards: list[dict[str, object]] = []
    for kind in _kinds(indexes):
        entries = _index_entries(
            kind,
            search_documents
            if kind == SEARCH_KIND and search_documents is not None
            else indexes.get(kind),
        )
        for part in _partition_entries(
            kind,
            entries,
            temporal_profile=profile,
            component_time_support=bool(component_fields),
            search_transport_schema=search_transport_schema
            if kind == SEARCH_KIND
            else None,
        ):
            shard = {
                "schema_version": SIGNED_INDEX_SHARD_SCHEMA
                if profile is not None
                else COMPONENT_INDEX_SHARD_SCHEMA
                if component_fields
                else INDEX_SHARD_SCHEMA,
                **profile_fields,
                **component_fields,
                "index_kind": kind,
                **(
                    {"search_transport_schema": SEARCH_DOCUMENTS_SCHEMA}
                    if kind == SEARCH_KIND and search_documents is not None
                    else {}
                ),
                "entries": part,
            }
            payload = canonical_json(shard).encode("utf-8")
            if len(payload) > ATLAS_CHUNK_MAX_BYTES:
                raise ValueError("static atlas logical index shard exceeds its budget")
            encoded_shards.append(
                {
                    "shard_number": len(encoded_shards) + 1,
                    "index_kind": kind,
                    "payload_encoding": "gzip_base64",
                    "decoded_byte_count": len(payload),
                    "record_count": len(part),
                    "payload_sha256": hashlib.sha256(payload).hexdigest(),
                    "payload_gzip_base64": base64.b64encode(
                        canonical_gzip_compress(payload)
                    ).decode("ascii"),
                }
            )
    return {
        **identities,
        **({"search_index_abi": SEARCH_ABI} if SEARCH_KIND in _kinds(indexes) else {}),
        "schema_version": SIGNED_INDEX_BUNDLE_SCHEMA
        if profile is not None
        else COMPONENT_INDEX_BUNDLE_SCHEMA
        if component_fields
        else INDEX_BUNDLE_SCHEMA,
        "shard_schema": SIGNED_INDEX_SHARD_SCHEMA
        if profile is not None
        else COMPONENT_INDEX_SHARD_SCHEMA
        if component_fields
        else INDEX_SHARD_SCHEMA,
        **profile_fields,
        **component_fields,
        **search_fields,
        "shard_count": len(encoded_shards),
        "reference_count": index_reference_count(dict(indexes)),
        "shards": encoded_shards,
    }


def decode_index_bundle(payload: Mapping[str, object]) -> dict[str, object]:
    """Authenticate and losslessly restore v3, while accepting legacy v1/v2."""
    _kinds(payload)
    search_counts = read_search_transport(payload)
    profile = read_calendar_profile(payload)
    profile_fields = calendar_profile_metadata(profile)
    schema = payload.get("schema_version")
    component_fields = _component_fields(payload, profile)
    if bool(component_fields) != (schema == COMPONENT_INDEX_BUNDLE_SCHEMA):
        raise ValueError("static atlas component index schema is invalid")
    if profile is None and schema in {
        "atlas-static-indexes.v1",
        "atlas-static-indexes.v2",
    }:
        if search_counts is not None:
            raise ValueError(
                "Document search transport requires authenticated logical shards"
            )
        if "search_index_abi" in payload:
            validate_search_index(payload.get(SEARCH_KIND))
        return dict(payload)
    if schema != (
        SIGNED_INDEX_BUNDLE_SCHEMA
        if profile is not None
        else COMPONENT_INDEX_BUNDLE_SCHEMA
        if component_fields
        else INDEX_BUNDLE_SCHEMA
    ) or payload.get("shard_schema") != (
        SIGNED_INDEX_SHARD_SCHEMA
        if profile is not None
        else COMPONENT_INDEX_SHARD_SCHEMA
        if component_fields
        else INDEX_SHARD_SCHEMA
    ):
        raise ValueError("static atlas index bundle schema is invalid")
    kinds = _kinds(payload)
    raw_shards = payload.get("shards")
    if not isinstance(raw_shards, list) or payload.get("shard_count") != len(
        raw_shards
    ):
        raise ValueError("static atlas index shard inventory is incomplete")
    merged: dict[str, object] = {
        "schema_version": "atlas-static-signed-indexes.v1"
        if profile is not None
        else "atlas-static-indexes.v2",
        **profile_fields,
        **component_fields,
        "country_feature_indexes": {},
        "spatial_degree_feature_indexes": {},
        "time_interval_feature_indexes": [],
        "signal_layer_indexes": {},
        "detail_record_asset_keys": {},
        **(
            {"search_index_abi": SEARCH_ABI, SEARCH_KIND: {}}
            if SEARCH_KIND in kinds
            else {}
        ),
    }
    prior_kind_rank = -1
    observed_kinds: list[str] = []
    observed_digests: set[str] = set()
    accepted_documents = 0
    accepted_utf16_units = 0
    for expected_number, raw_envelope in enumerate(raw_shards, start=1):
        if not isinstance(raw_envelope, Mapping):
            raise ValueError("static atlas index shard envelope is invalid")
        kind = raw_envelope.get("index_kind")
        if not isinstance(kind, str) or kind not in kinds:
            raise ValueError("static atlas index shard kind is invalid")
        kind_rank = kinds.index(kind)
        if kind_rank < prior_kind_rank:
            raise ValueError("static atlas index shard order changed")
        prior_kind_rank = kind_rank
        if not observed_kinds or observed_kinds[-1] != kind:
            observed_kinds.append(kind)
        if raw_envelope.get("shard_number") != expected_number:
            raise ValueError("static atlas index shard numbering changed")
        shard_digest = raw_envelope.get("payload_sha256")
        if not isinstance(shard_digest, str) or shard_digest in observed_digests:
            raise ValueError("static atlas index shard identity is duplicated")
        observed_digests.add(shard_digest)
        shard = _decode_shard(
            raw_envelope,
            kind,
            temporal_profile=profile,
            component_time_support=bool(component_fields),
            search_transport_schema=SEARCH_DOCUMENTS_SCHEMA
            if search_counts is not None
            else None,
        )
        entries = shard["entries"]
        if not isinstance(entries, list):
            raise AssertionError("decoded index shard lost validated entries")
        if raw_envelope.get("record_count") != len(entries):
            raise ValueError("static atlas index shard record count changed")
        if kind == SEARCH_KIND and search_counts is not None:
            for entry in entries:
                if not isinstance(entry, list) or len(entry) != 2:
                    raise ValueError("search transport document entry is malformed")
                accepted_documents += 1
                accepted_utf16_units += search_document_utf16_units(entry[0], entry[1])
                if (
                    accepted_documents > search_counts["document_count"]
                    or accepted_utf16_units > search_counts["utf16_unit_count"]
                ):
                    raise ValueError(
                        "search transport document resource declaration exceeded"
                    )
        _merge_entries(merged, kind, entries)
    if tuple(observed_kinds) != kinds:
        raise ValueError("static atlas index shard kinds are incomplete")
    if search_counts is not None:
        merged[SEARCH_KIND] = restore_search_documents(
            merged[SEARCH_KIND], search_counts
        )
    for field in ("scope_slug", "version", "build_id"):
        merged[field] = _required_text(payload.get(field), field)
    _validate_merged_indexes(merged)
    if payload.get("reference_count") != index_reference_count(merged):
        raise ValueError("static atlas index bundle reference count changed")
    return merged


def _component_fields(
    payload: Mapping[str, object], profile: str | None
) -> dict[str, bool]:
    if "component_time_support" not in payload:
        return {}
    if payload["component_time_support"] is not True or profile is not None:
        raise ValueError("static atlas component time support declaration is invalid")
    return {"component_time_support": True}


def _required_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"static atlas index bundle {label} is invalid")
    return value.strip()


def _index_entries(kind: str, value: object) -> list[object]:
    if kind in {"country_feature_indexes", "spatial_degree_feature_indexes"}:
        if not isinstance(value, Mapping):
            raise TypeError(f"static atlas {kind} must be an object")
        entries: list[object] = []
        for outer, inner_rows in value.items():
            if not isinstance(inner_rows, Mapping):
                raise TypeError(f"static atlas {kind} nested rows must be an object")
            entries.extend(
                [outer, inner, feature_indexes]
                for inner, feature_indexes in inner_rows.items()
            )
        return entries
    if kind == "time_interval_feature_indexes":
        if not isinstance(value, list):
            raise TypeError("static atlas time indexes must be a list")
        return list(value)
    if not isinstance(value, Mapping):
        raise TypeError(f"static atlas {kind} must be an object")
    return [[key, item] for key, item in value.items()]


def _partition_entries(
    kind: str,
    entries: list[object],
    *,
    temporal_profile: str | None = None,
    component_time_support: bool = False,
    search_transport_schema: str | None = None,
) -> list[list[object]]:
    empty_size = len(
        canonical_json(
            {
                "schema_version": SIGNED_INDEX_SHARD_SCHEMA
                if temporal_profile is not None
                else COMPONENT_INDEX_SHARD_SCHEMA
                if component_time_support
                else INDEX_SHARD_SCHEMA,
                **({"component_time_support": True} if component_time_support else {}),
                **calendar_profile_metadata(temporal_profile),
                "index_kind": kind,
                **(
                    {"search_transport_schema": search_transport_schema}
                    if search_transport_schema is not None
                    else {}
                ),
                "entries": [],
            }
        ).encode("utf-8")
    )
    parts: list[list[object]] = []
    current: list[object] = []
    current_size = empty_size
    for entry in entries:
        entry_size = len(canonical_json(entry).encode("utf-8"))
        candidate_size = current_size + entry_size + (1 if current else 0)
        if current and candidate_size > ATLAS_CHUNK_TARGET_BYTES:
            parts.append(current)
            current = [entry]
            current_size = empty_size + entry_size
        else:
            current.append(entry)
            current_size = candidate_size
        if current_size > ATLAS_CHUNK_MAX_BYTES:
            raise ValueError("one static atlas index entry exceeds the chunk budget")
    if current or not parts:
        parts.append(current)
    return parts


def _decode_shard(
    envelope: Mapping[str, object],
    kind: str,
    *,
    temporal_profile: str | None = None,
    component_time_support: bool = False,
    search_transport_schema: str | None = None,
) -> dict[str, object]:
    if envelope.get("payload_encoding") != "gzip_base64":
        raise ValueError("static atlas index shard encoding is invalid")
    encoded = envelope.get("payload_gzip_base64")
    if not isinstance(encoded, str):
        raise ValueError("static atlas index shard payload is missing")
    try:
        compressed = base64.b64decode(encoded, validate=True)
        decoder = zlib.decompressobj(16 + zlib.MAX_WBITS)
        payload = decoder.decompress(compressed, ATLAS_CHUNK_MAX_BYTES + 1)
        if len(payload) > ATLAS_CHUNK_MAX_BYTES or decoder.unconsumed_tail:
            raise ValueError("static atlas index shard exceeds its decoded budget")
        payload += decoder.flush(ATLAS_CHUNK_MAX_BYTES + 1 - len(payload))
    except (ValueError, zlib.error) as exc:
        raise ValueError("static atlas index shard compression is invalid") from exc
    if (
        len(payload) > ATLAS_CHUNK_MAX_BYTES
        or not decoder.eof
        or decoder.unused_data
        or decoder.unconsumed_tail
    ):
        raise ValueError("static atlas index shard exceeds its decoded budget")
    if envelope.get("decoded_byte_count") != len(payload):
        raise ValueError("static atlas index shard byte count changed")
    if envelope.get("payload_sha256") != hashlib.sha256(payload).hexdigest():
        raise ValueError("static atlas index shard digest changed")
    try:
        shard = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("static atlas index shard JSON is invalid") from exc
    if not isinstance(shard, dict):
        raise ValueError("static atlas index shard must be an object")
    if "search_transport_counts" in shard:
        raise ValueError(
            "search transport counts belong only in the index bundle header"
        )
    if kind == SEARCH_KIND and search_transport_schema is not None:
        if shard.get("search_transport_schema") != search_transport_schema:
            raise ValueError("search shard transport marker differs")
    elif "search_transport_schema" in shard:
        raise ValueError("search shard transport marker is undeclared or foreign")
    if (
        shard.get("schema_version")
        != (
            SIGNED_INDEX_SHARD_SCHEMA
            if temporal_profile is not None
            else COMPONENT_INDEX_SHARD_SCHEMA
            if component_time_support
            else INDEX_SHARD_SCHEMA
        )
        or bool(_component_fields(shard, temporal_profile)) != component_time_support
        or read_calendar_profile(shard) != temporal_profile
        or shard.get("index_kind") != kind
    ):
        raise ValueError("static atlas index shard identity changed")
    return shard


def _validate_merged_indexes(indexes: Mapping[str, object]) -> None:
    if SEARCH_KIND in _kinds(indexes):
        validate_search_index(indexes.get(SEARCH_KIND))
    for kind in ("country_feature_indexes", "spatial_degree_feature_indexes"):
        nested = indexes.get(kind)
        if not isinstance(nested, Mapping):
            raise ValueError(f"static atlas {kind} is invalid")
        observed: set[tuple[str, int]] = set()
        for outer, rows in nested.items():
            if not isinstance(outer, str) or not isinstance(rows, Mapping):
                raise ValueError(f"static atlas {kind} key is invalid")
            for layer, feature_indexes in rows.items():
                if not isinstance(layer, str) or not isinstance(feature_indexes, list):
                    raise ValueError(f"static atlas {kind} row is invalid")
                if any(
                    isinstance(index, bool) or not isinstance(index, int) or index < 0
                    for index in feature_indexes
                ) or feature_indexes != sorted(set(feature_indexes)):
                    raise ValueError(f"static atlas {kind} feature indexes are invalid")
                references = {(layer, index) for index in feature_indexes}
                if observed & references:
                    raise ValueError("static atlas index shards overlap")
                observed.update(references)
    profile = read_calendar_profile(indexes)
    intervals = indexes.get("time_interval_feature_indexes")
    if not isinstance(intervals, list):
        raise ValueError("static atlas time interval indexes are invalid")
    interval_references: set[tuple[str, int]] = set()
    component_mode = bool(_component_fields(indexes, profile))
    component_ends: dict[tuple[str, int], float] = {}
    for row in intervals:
        if (
            not isinstance(row, list)
            or len(row) != 4
            or any(isinstance(value, bool) for value in (row[0], row[1], row[3]))
            or not isinstance(row[0], (int, float))
            or not isinstance(row[1], (int, float))
            or not isinstance(row[2], str)
            or not isinstance(row[3], int)
            or (
                profile is None
                and (not isfinite(float(row[0])) or not isfinite(float(row[1])))
            )
            or (profile is None and row[0] < 0)
            or row[0] > row[1]
            or row[3] < 0
        ):
            raise ValueError("static atlas time interval index row is invalid")
        if profile is not None:
            SignedCalendarSupport(
                row[0], row[1], support_kind="declared_stationarity_envelope"
            )
        reference = (row[2], row[3])
        if reference in interval_references and (
            not component_mode or row[0] <= component_ends[reference]
        ):
            raise ValueError("static atlas time index shards overlap")
        component_ends[reference] = float(row[1])
        interval_references.add(reference)
    signals = indexes.get("signal_layer_indexes")
    details = indexes.get("detail_record_asset_keys")
    if not isinstance(signals, Mapping) or any(
        not isinstance(key, str)
        or not isinstance(value, list)
        or any(not isinstance(item, str) for item in value)
        or value != sorted(set(value))
        for key, value in signals.items()
    ):
        raise ValueError("static atlas signal layer indexes are invalid")
    if not isinstance(details, Mapping) or any(
        not isinstance(key, str) or not isinstance(value, str)
        for key, value in details.items()
    ):
        raise ValueError("static atlas detail record indexes are invalid")


def _merge_entries(merged: dict[str, object], kind: str, entries: list[object]) -> None:
    if kind in {"country_feature_indexes", "spatial_degree_feature_indexes"}:
        target = merged[kind]
        if not isinstance(target, dict):
            raise AssertionError("nested index target changed type")
        for entry in entries:
            if not isinstance(entry, list) or len(entry) != 3:
                raise ValueError("nested static atlas index entry is invalid")
            outer, inner, indexes = entry
            if not isinstance(outer, str) or not isinstance(inner, str):
                raise ValueError("nested static atlas index key is invalid")
            rows = target.setdefault(outer, {})
            if not isinstance(rows, dict) or inner in rows:
                raise ValueError("static atlas index shards overlap")
            rows[inner] = indexes
        return
    target = merged[kind]
    if kind == "time_interval_feature_indexes":
        if not isinstance(target, list):
            raise AssertionError("time index target changed type")
        target.extend(entries)
        return
    if not isinstance(target, dict):
        raise AssertionError("flat index target changed type")
    for entry in entries:
        if not isinstance(entry, list) or len(entry) != 2:
            raise ValueError("flat static atlas index entry is invalid")
        key, value = entry
        if not isinstance(key, str) or key in target:
            raise ValueError("static atlas index shards overlap")
        target[key] = value


__all__ = [
    "COMPONENT_INDEX_BUNDLE_SCHEMA",
    "COMPONENT_INDEX_SHARD_SCHEMA",
    "INDEX_BUNDLE_SCHEMA",
    "INDEX_KINDS",
    "INDEX_SHARD_SCHEMA",
    "build_index_bundle",
    "decode_index_bundle",
]
