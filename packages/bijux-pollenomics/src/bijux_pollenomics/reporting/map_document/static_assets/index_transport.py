"""Bound physical index transport without changing its authenticated logical shards."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
from typing import cast

from .budgets import ATLAS_CHUNK_MAX_BYTES
from .index_bundles import decode_index_bundle
from .indexes import index_reference_count
from .search.transport import SEARCH_DOCUMENTS_SCHEMA, read_search_transport
from .serialization import canonical_json, chunk_script_bytes

INDEX_PART_SCHEMA = "atlas-static-index-part.v1"
_LOGICAL_SCHEMAS = {
    "atlas-static-indexes.v3",
    "atlas-static-indexes.v4",
    "atlas-static-indexes.v5",
}
_PART_FIELDS = {
    "asset_key",
    "bundle_schema",
    "bundle_sha256",
    "part_number",
    "part_count",
    "first_shard_number",
    "last_shard_number",
}
_HEADER_FIELDS = {
    "schema_version",
    "scope_slug",
    "version",
    "build_id",
    "search_index_abi",
    "search_transport_schema",
    "search_transport_counts",
    "shard_schema",
    "component_time_support",
    "temporal_profile",
    "temporal_axis",
    "shard_count",
    "reference_count",
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _integer(value: object, label: str, minimum: int = 0) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not minimum <= value < 2**53
    ):
        raise ValueError(f"static atlas index {label} is invalid")
    return value


def _digest(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _shards(payload: Mapping[str, object]) -> list[Mapping[str, object]]:
    value = payload.get("shards")
    if not isinstance(value, list) or any(
        not isinstance(row, Mapping) for row in value
    ):
        raise ValueError("static atlas index shards must be objects")
    return cast(list[Mapping[str, object]], value)


def _fits(payload: Mapping[str, object]) -> bool:
    encoded = canonical_json(payload)
    if len(encoded.encode("utf-8")) > ATLAS_CHUNK_MAX_BYTES:
        return False
    script = chunk_script_bytes(
        asset_key=str(payload["asset_key"]),
        payload_sha256=hashlib.sha256(encoded.encode("utf-8")).hexdigest(),
        payload_json=encoded,
        payload_encoding="json",
    )
    return len(script) <= ATLAS_CHUNK_MAX_BYTES


def partition_index_bundle(
    bundle: Mapping[str, object], *, first_sequence: int
) -> list[dict[str, object]]:
    """Keep a fitting singleton exact, otherwise pack complete contiguous shards."""
    _integer(first_sequence, "first asset sequence")
    _require(
        not _PART_FIELDS.intersection(bundle),
        "index bundle already has transport fields",
    )
    singleton = {**bundle, "asset_key": f"indexes:{first_sequence}"}
    if _fits(singleton):
        return [singleton]
    _require(
        isinstance(bundle.get("schema_version"), str)
        and bundle.get("schema_version") in _LOGICAL_SCHEMAS,
        "index bundle cannot be physically partitioned",
    )
    _require(
        set(bundle) <= _HEADER_FIELDS | {"shards"},
        "index bundle header contains unknown fields",
    )
    shards = _shards(bundle)
    count = _integer(bundle.get("shard_count"), "global shard count", 1)
    _require(count == len(shards), "index bundle shard count differs")
    for number, shard in enumerate(shards, 1):
        _require(
            _integer(shard.get("shard_number"), "shard number", 1) == number,
            "index bundle shard order differs",
        )
    header = {key: value for key, value in bundle.items() if key != "shards"}
    bundle_sha256 = _digest(bundle)

    def part(first: int, stop: int, number: int, total: int) -> dict[str, object]:
        return {
            **header,
            "schema_version": INDEX_PART_SCHEMA,
            "bundle_schema": bundle["schema_version"],
            "bundle_sha256": bundle_sha256,
            "part_number": number,
            "part_count": total,
            "first_shard_number": first + 1,
            "last_shard_number": stop,
            "shards": list(shards[first:stop]),
            "asset_key": f"indexes:{first_sequence + number - 1}",
        }

    def pack(total: int) -> list[dict[str, object]]:
        parts: list[dict[str, object]] = []
        first = 0
        while first < count:
            number = len(parts) + 1
            low, high, best = first + 1, count, first
            while low <= high:
                stop = (low + high) // 2
                if _fits(part(first, stop, number, total)):
                    best, low = stop, stop + 1
                else:
                    high = stop - 1
            _require(
                best > first,
                "one complete index shard exceeds the physical chunk budget",
            )
            parts.append(part(first, best, number, total))
            first = best
        return parts

    total = count
    while True:
        parts = pack(total)
        actual = len(parts)
        _require(actual <= total, "index part-count packing did not converge")
        if actual == total:
            _require(
                actual > 1, "oversized index bundle cannot use singleton transport"
            )
            return parts
        total = actual


def assemble_index_payloads(
    index_rows: Sequence[Mapping[str, object]],
    payloads: Mapping[str, Mapping[str, object]],
    *,
    manifest: Mapping[str, object],
) -> dict[str, object]:
    """Authenticate a complete declared physical inventory before logical decoding."""
    compatibility = manifest.get("compatibility")
    if not isinstance(compatibility, Mapping):
        raise ValueError("static atlas index compatibility is missing")
    _require(
        "search_transport_counts" not in compatibility,
        "search transport counts belong only in the index bundle header",
    )
    _require(bool(index_rows), "static atlas index payload is missing")
    keys = [row.get("asset_key") for row in index_rows]
    _require(
        all(isinstance(key, str) for key in keys),
        "static atlas index asset key is invalid",
    )
    _require(
        len(set(keys)) == len(keys), "static atlas index asset identity is duplicated"
    )
    _require(
        set(payloads) == set(keys), "index transport has undeclared or missing payloads"
    )
    ordered: list[Mapping[str, object]] = []
    prior_sequence = -1
    for row in index_rows:
        _require(
            row.get("domain") == "indexes", "foreign row in index transport inventory"
        )
        sequence = _integer(row.get("sequence"), "asset sequence")
        _require(sequence > prior_sequence, "index transport manifest order differs")
        prior_sequence = sequence
        key = cast(str, row["asset_key"])
        _require(
            key == f"indexes:{sequence}" and key in payloads,
            "index transport asset is missing or foreign",
        )
        payload = payloads[key]
        search_counts = read_search_transport(payload)
        if "search_transport_schema" in compatibility:
            _require(
                compatibility["search_transport_schema"] == SEARCH_DOCUMENTS_SCHEMA
                and search_counts is not None,
                "search transport compatibility differs",
            )
        else:
            _require(
                search_counts is None, "search transport compatibility is undeclared"
            )
        _require(
            payload.get("asset_key") == key, "index transport payload identity differs"
        )
        _require(_fits(payload), "index transport exceeds its physical chunk budget")
        for field in (
            "scope_slug",
            "version",
            "build_id",
            "temporal_profile",
            "temporal_axis",
        ):
            _require(
                payload.get(field) == manifest.get(field),
                f"index transport {field} differs",
            )
        _require(
            payload.get("search_index_abi") == compatibility.get("search_index_abi"),
            "index transport search ABI differs",
        )
        ordered.append(payload)
    transport = compatibility.get("index_transport_schema")
    if "index_transport_schema" not in compatibility:
        _require(
            len(ordered) == 1 and ordered[0].get("schema_version") != INDEX_PART_SCHEMA,
            "singleton and part index transports are mixed",
        )
        _require(
            ordered[0].get("schema_version") == compatibility.get("index_schema"),
            "singleton index schema differs",
        )
        return dict(ordered[0])
    _require(
        transport == INDEX_PART_SCHEMA and len(ordered) > 1,
        "index part transport declaration is invalid",
    )
    first = ordered[0]
    common = {
        key: value
        for key, value in first.items()
        if key not in _PART_FIELDS | {"shards"}
    }
    _require(set(common) <= _HEADER_FIELDS, "index part header contains unknown fields")
    _require(
        common.get("schema_version") == INDEX_PART_SCHEMA, "index part schema differs"
    )
    schema = first.get("bundle_schema")
    _require(
        isinstance(schema, str)
        and schema in _LOGICAL_SCHEMAS
        and schema == compatibility.get("index_schema"),
        "index logical bundle schema differs",
    )
    count = _integer(first.get("shard_count"), "global shard count", 1)
    _integer(first.get("reference_count"), "global reference count")
    part_count = _integer(first.get("part_count"), "part count", 2)
    _require(part_count == len(index_rows), "index part inventory is incomplete")
    expected_digest = first.get("bundle_sha256")
    _require(
        isinstance(expected_digest, str)
        and len(expected_digest) == 64
        and all(char in "0123456789abcdef" for char in expected_digest),
        "index bundle digest is invalid",
    )
    joined: list[Mapping[str, object]] = []
    digests: set[str] = set()
    for number, (row, payload) in enumerate(zip(index_rows, ordered, strict=True), 1):
        _require(
            row["sequence"]
            == _integer(index_rows[0].get("sequence"), "first asset sequence")
            + number
            - 1,
            "index part asset sequences are not contiguous",
        )
        _require(
            set(payload) == set(common) | _PART_FIELDS | {"shards"},
            "index part fields differ",
        )
        _integer(payload.get("shard_count"), "global shard count", 1)
        _integer(payload.get("reference_count"), "global reference count")
        _require(
            canonical_json(
                {
                    key: value
                    for key, value in payload.items()
                    if key not in _PART_FIELDS | {"shards"}
                }
            )
            == canonical_json(common),
            "index part common header differs",
        )
        _require(
            payload.get("bundle_schema") == schema
            and payload.get("bundle_sha256") == expected_digest,
            "index parts refer to different bundles",
        )
        _require(
            _integer(payload.get("part_count"), "part count", 2) == part_count
            and _integer(payload.get("part_number"), "part number", 1) == number,
            "index part numbering differs",
        )
        shards = _shards(payload)
        _require(bool(shards), "index part has no shards")
        _require(
            _integer(row.get("record_count"), "part record count", 1) == len(shards),
            "index part record count differs",
        )
        _require(
            _integer(payload.get("first_shard_number"), "first shard", 1)
            == len(joined) + 1,
            "index part first shard differs",
        )
        _require(
            _integer(payload.get("last_shard_number"), "last shard", 1)
            == len(joined) + len(shards),
            "index part last shard differs",
        )
        for shard in shards:
            _require(
                _integer(shard.get("shard_number"), "shard number", 1)
                == len(joined) + 1,
                "global index shard order differs",
            )
            checksum = shard.get("payload_sha256")
            _require(
                isinstance(checksum, str) and checksum not in digests,
                "index shard identity is missing or duplicated",
            )
            digests.add(cast(str, checksum))
            joined.append(shard)
    _require(len(joined) == count, "global index shard inventory is incomplete")
    bundle = {**common, "schema_version": schema, "shards": joined}
    _require(
        _digest(bundle) == expected_digest, "assembled index bundle digest differs"
    )
    return bundle


def decode_index_payloads(
    index_rows: Sequence[Mapping[str, object]],
    payloads: Mapping[str, Mapping[str, object]],
    *,
    manifest: Mapping[str, object],
) -> dict[str, object]:
    """Decode all declared index parts and reconcile the global reference count."""
    bundle = assemble_index_payloads(index_rows, payloads, manifest=manifest)
    decoded = decode_index_bundle(bundle)
    references = index_reference_count(decoded)
    domains = manifest.get("domains")
    if not isinstance(domains, Mapping) or not isinstance(
        domains.get("indexes"), Mapping
    ):
        raise ValueError("static atlas index domain accounting is missing")
    domain = cast(Mapping[str, object], domains["indexes"])
    _require(
        _integer(domain.get("record_count"), "domain reference count") == references,
        "static atlas global index reference count differs",
    )
    compatibility = cast(Mapping[str, object], manifest["compatibility"])
    if "index_transport_schema" not in compatibility:
        _require(
            _integer(index_rows[0].get("record_count"), "singleton reference count")
            == references,
            "singleton index reference count differs",
        )
    return decoded
