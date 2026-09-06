"""Bounded, authenticated logical shards for static atlas indexes."""

from __future__ import annotations

import base64
import gzip
import hashlib
import json
import zlib
from collections.abc import Mapping
from math import isfinite

from .budgets import ATLAS_CHUNK_MAX_BYTES, ATLAS_CHUNK_TARGET_BYTES
from .indexes import index_reference_count
from .serialization import canonical_json

INDEX_BUNDLE_SCHEMA = "atlas-static-indexes.v3"
INDEX_SHARD_SCHEMA = "atlas-static-index-shard.v1"
INDEX_KINDS = (
    "country_feature_indexes",
    "spatial_degree_feature_indexes",
    "time_interval_feature_indexes",
    "signal_layer_indexes",
    "detail_record_asset_keys",
)


def build_index_bundle(indexes: Mapping[str, object]) -> dict[str, object]:
    """Encode the exact v2 logical indexes as bounded deterministic shards."""
    identities = {
        field: _required_text(indexes.get(field), field)
        for field in ("scope_slug", "version", "build_id")
    }
    encoded_shards: list[dict[str, object]] = []
    for kind in INDEX_KINDS:
        entries = _index_entries(kind, indexes.get(kind))
        for part in _partition_entries(kind, entries):
            shard = {
                "schema_version": INDEX_SHARD_SCHEMA,
                "index_kind": kind,
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
                        gzip.compress(payload, compresslevel=9, mtime=0)
                    ).decode("ascii"),
                }
            )
    return {
        **identities,
        "schema_version": INDEX_BUNDLE_SCHEMA,
        "shard_schema": INDEX_SHARD_SCHEMA,
        "shard_count": len(encoded_shards),
        "reference_count": index_reference_count(dict(indexes)),
        "shards": encoded_shards,
    }


def decode_index_bundle(payload: Mapping[str, object]) -> dict[str, object]:
    """Authenticate and losslessly restore v3, while accepting legacy v1/v2."""
    schema = payload.get("schema_version")
    if schema in {"atlas-static-indexes.v1", "atlas-static-indexes.v2"}:
        return dict(payload)
    if (
        schema != INDEX_BUNDLE_SCHEMA
        or payload.get("shard_schema") != INDEX_SHARD_SCHEMA
    ):
        raise ValueError("static atlas index bundle schema is invalid")
    raw_shards = payload.get("shards")
    if not isinstance(raw_shards, list) or payload.get("shard_count") != len(
        raw_shards
    ):
        raise ValueError("static atlas index shard inventory is incomplete")
    merged: dict[str, object] = {
        "schema_version": "atlas-static-indexes.v2",
        "country_feature_indexes": {},
        "spatial_degree_feature_indexes": {},
        "time_interval_feature_indexes": [],
        "signal_layer_indexes": {},
        "detail_record_asset_keys": {},
    }
    prior_kind_rank = -1
    observed_kinds: list[str] = []
    observed_digests: set[str] = set()
    for expected_number, raw_envelope in enumerate(raw_shards, start=1):
        if not isinstance(raw_envelope, Mapping):
            raise ValueError("static atlas index shard envelope is invalid")
        kind = raw_envelope.get("index_kind")
        if not isinstance(kind, str) or kind not in INDEX_KINDS:
            raise ValueError("static atlas index shard kind is invalid")
        kind_rank = INDEX_KINDS.index(kind)
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
        shard = _decode_shard(raw_envelope, kind)
        entries = shard["entries"]
        if not isinstance(entries, list):
            raise AssertionError("decoded index shard lost validated entries")
        if raw_envelope.get("record_count") != len(entries):
            raise ValueError("static atlas index shard record count changed")
        _merge_entries(merged, kind, entries)
    if tuple(observed_kinds) != INDEX_KINDS:
        raise ValueError("static atlas index shard kinds are incomplete")
    for field in ("scope_slug", "version", "build_id"):
        merged[field] = _required_text(payload.get(field), field)
    _validate_merged_indexes(merged)
    if payload.get("reference_count") != index_reference_count(merged):
        raise ValueError("static atlas index bundle reference count changed")
    return merged


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


def _partition_entries(kind: str, entries: list[object]) -> list[list[object]]:
    empty_size = len(
        canonical_json(
            {"schema_version": INDEX_SHARD_SCHEMA, "index_kind": kind, "entries": []}
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


def _decode_shard(envelope: Mapping[str, object], kind: str) -> dict[str, object]:
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
    if (
        shard.get("schema_version") != INDEX_SHARD_SCHEMA
        or shard.get("index_kind") != kind
    ):
        raise ValueError("static atlas index shard identity changed")
    return shard


def _validate_merged_indexes(indexes: Mapping[str, object]) -> None:
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
    intervals = indexes.get("time_interval_feature_indexes")
    if not isinstance(intervals, list):
        raise ValueError("static atlas time interval indexes are invalid")
    interval_references: set[tuple[str, int]] = set()
    for row in intervals:
        if (
            not isinstance(row, list)
            or len(row) != 4
            or any(isinstance(value, bool) for value in (row[0], row[1], row[3]))
            or not isinstance(row[0], (int, float))
            or not isinstance(row[1], (int, float))
            or not isinstance(row[2], str)
            or not isinstance(row[3], int)
            or not isfinite(float(row[0]))
            or not isfinite(float(row[1]))
            or row[0] > row[1]
            or row[3] < 0
        ):
            raise ValueError("static atlas time interval index row is invalid")
        reference = (row[2], row[3])
        if reference in interval_references:
            raise ValueError("static atlas time index shards overlap")
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
    "INDEX_BUNDLE_SCHEMA",
    "INDEX_KINDS",
    "INDEX_SHARD_SCHEMA",
    "build_index_bundle",
    "decode_index_bundle",
]
