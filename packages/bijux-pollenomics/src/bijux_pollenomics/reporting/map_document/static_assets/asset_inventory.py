"""Compact, lossless transport for the static-atlas asset inventory."""

from __future__ import annotations

import base64
from collections.abc import Mapping, Sequence
import math

ASSET_TABLE_SCHEMA = "atlas-static-asset-table.v2"
LEGACY_ASSET_TABLE_SCHEMA = "atlas-static-asset-table.v1"
ASSET_TABLE_FIELDS = (
    "asset_key",
    "domain",
    "sequence",
    "path",
    "sha256",
    "integrity",
    "payload_sha256",
    "payload_encoding",
    "decoded_byte_count",
    "byte_count",
    "record_count",
    "initial_load",
    "layer_index",
    "layer_key",
    "layer_kind",
    "country_keys",
    "bounds",
    "time_min_bp",
    "time_max_bp",
    "untimed_record_count",
    "scientific_signal_ids",
)
_CORE_FIELDS = ASSET_TABLE_FIELDS[:12]
_NODE_FIELDS = ASSET_TABLE_FIELDS[12:]
ASSET_TABLE_STORED_FIELDS = (
    "domain",
    "sha256",
    "payload_sha256",
    "decoded_byte_count",
    "byte_count",
    "record_count",
    *_NODE_FIELDS,
)
_LEGACY_TABLE_KEYS = {"schema_version", "fields", "record_count", "records"}
_TABLE_KEYS = {
    "schema_version",
    "scope_slug",
    "fields",
    "record_count",
    "records",
}
_ASSET_DOMAINS = {
    "provenance",
    "nodes",
    "details",
    "edges",
    "sequences",
    "indexes",
}


def encode_asset_inventory(
    rows: Sequence[Mapping[str, object]],
    *,
    scope_slug: str,
) -> dict[str, object]:
    """Encode exact rows while deriving redundant identity and transport fields."""
    _validate_scope_slug(scope_slug)
    normalized = _validate_rows(rows, require_decoded_counts=True)
    for sequence, row in enumerate(normalized):
        _validate_derived_fields(row, scope_slug=scope_slug, sequence=sequence)
    records = [
        [row.get(field) for field in ASSET_TABLE_STORED_FIELDS] for row in normalized
    ]
    return {
        "schema_version": ASSET_TABLE_SCHEMA,
        "scope_slug": scope_slug,
        "fields": list(ASSET_TABLE_STORED_FIELDS),
        "record_count": len(records),
        "records": records,
    }


def normalize_asset_inventory(value: object) -> list[dict[str, object]]:
    """Expand a legacy list or authenticated columnar inventory into row objects."""
    if isinstance(value, list):
        return _validate_rows(value, require_decoded_counts=False)
    if not isinstance(value, Mapping):
        raise ValueError("static atlas asset table shape is invalid")
    schema = value.get("schema_version")
    if schema == LEGACY_ASSET_TABLE_SCHEMA:
        return _normalize_legacy_table(value)
    if schema != ASSET_TABLE_SCHEMA or set(value) != _TABLE_KEYS:
        raise ValueError("static atlas asset table shape is invalid")
    scope_slug = value.get("scope_slug")
    if not isinstance(scope_slug, str):
        raise ValueError("static atlas asset table scope is invalid")
    _validate_scope_slug(scope_slug)
    fields = value.get("fields")
    if fields != list(ASSET_TABLE_STORED_FIELDS):
        raise ValueError("static atlas asset table fields are invalid")
    records = _validated_records(value, width=len(ASSET_TABLE_STORED_FIELDS))
    rows: list[dict[str, object]] = []
    for sequence, record in enumerate(records):
        stored = dict(zip(ASSET_TABLE_STORED_FIELDS, record, strict=True))
        domain = stored.get("domain")
        digest = stored.get("sha256")
        if not isinstance(domain, str) or domain not in _ASSET_DOMAINS:
            raise ValueError("static atlas asset domain is invalid")
        if not isinstance(digest, str):
            raise ValueError("static atlas asset sha256 is invalid")
        row = {
            "asset_key": f"{domain}:{sequence}",
            "domain": domain,
            "sequence": sequence,
            "path": _asset_path(scope_slug, domain, sequence, digest),
            "sha256": digest,
            "integrity": _integrity_from_digest(digest),
            "payload_sha256": stored["payload_sha256"],
            "payload_encoding": _payload_encoding(domain),
            "decoded_byte_count": stored["decoded_byte_count"],
            "byte_count": stored["byte_count"],
            "record_count": stored["record_count"],
            "initial_load": _initial_load(domain),
        }
        if domain == "nodes":
            row.update({field: stored[field] for field in _NODE_FIELDS})
        elif any(stored[field] is not None for field in _NODE_FIELDS):
            raise ValueError("static atlas non-node selection metadata is invalid")
        rows.append(row)
    return _validate_rows(rows, require_decoded_counts=True)


def _normalize_legacy_table(value: Mapping[str, object]) -> list[dict[str, object]]:
    if set(value) != _LEGACY_TABLE_KEYS:
        raise ValueError("static atlas asset table shape is invalid")
    if value.get("schema_version") != LEGACY_ASSET_TABLE_SCHEMA:
        raise ValueError("static atlas asset table schema is invalid")
    fields = value.get("fields")
    if fields != list(ASSET_TABLE_FIELDS):
        raise ValueError("static atlas asset table fields are invalid")
    records = _validated_records(value, width=len(ASSET_TABLE_FIELDS))
    rows: list[dict[str, object]] = []
    for record in records:
        if not isinstance(record, list) or len(record) != len(ASSET_TABLE_FIELDS):
            raise ValueError("static atlas asset table row width is invalid")
        row = dict(zip(ASSET_TABLE_FIELDS, record, strict=True))
        if row.get("domain") != "nodes":
            for field in _NODE_FIELDS:
                if row[field] is not None:
                    raise ValueError(
                        "static atlas non-node selection metadata is invalid"
                    )
                del row[field]
        rows.append(row)
    return _validate_rows(rows, require_decoded_counts=True)


def _validated_records(
    value: Mapping[str, object], *, width: int
) -> list[list[object]]:
    records = value.get("records")
    record_count = value.get("record_count")
    if (
        not isinstance(records, list)
        or isinstance(record_count, bool)
        or not isinstance(record_count, int)
        or record_count != len(records)
    ):
        raise ValueError("static atlas asset table count is invalid")
    if any(not isinstance(record, list) or len(record) != width for record in records):
        raise ValueError("static atlas asset table row width is invalid")
    return records


def _validate_derived_fields(
    row: Mapping[str, object], *, scope_slug: str, sequence: int
) -> None:
    domain = str(row["domain"])
    digest = str(row["sha256"])
    expected = {
        "asset_key": f"{domain}:{sequence}",
        "sequence": sequence,
        "path": _asset_path(scope_slug, domain, sequence, digest),
        "integrity": _integrity_from_digest(digest),
        "payload_encoding": _payload_encoding(domain),
        "initial_load": _initial_load(domain),
    }
    if any(
        row.get(field) != expected_value for field, expected_value in expected.items()
    ):
        raise ValueError("static atlas derived asset metadata is inconsistent")


def _validate_scope_slug(scope_slug: str) -> None:
    if (
        not scope_slug
        or scope_slug != scope_slug.lower()
        or not scope_slug.replace("-", "").isalnum()
    ):
        raise ValueError("static atlas asset table scope is invalid")


def _asset_path(scope_slug: str, domain: str, sequence: int, digest: str) -> str:
    return f"{scope_slug}.atlas-{domain}.{sequence:04d}.{digest[:16]}.js"


def _integrity_from_digest(digest: str) -> str:
    try:
        raw_digest = bytes.fromhex(digest)
    except ValueError as exc:
        raise ValueError("static atlas asset sha256 is invalid") from exc
    if len(raw_digest) != 32 or digest != digest.lower():
        raise ValueError("static atlas asset sha256 is invalid")
    return "sha256-" + base64.b64encode(raw_digest).decode("ascii")


def _payload_encoding(domain: str) -> str:
    if domain not in _ASSET_DOMAINS:
        raise ValueError("static atlas asset domain is invalid")
    return "gzip_base64" if domain in {"nodes", "details", "provenance"} else "json"


def _initial_load(domain: str) -> bool:
    if domain not in _ASSET_DOMAINS:
        raise ValueError("static atlas asset domain is invalid")
    return domain not in {"nodes", "details", "indexes"}


def _validate_rows(
    rows: Sequence[object], *, require_decoded_counts: bool
) -> list[dict[str, object]]:
    normalized: list[dict[str, object]] = []
    identities: set[str] = set()
    paths: set[str] = set()
    sequences: set[int] = set()
    for position, value in enumerate(rows):
        if not isinstance(value, Mapping):
            raise ValueError("static atlas asset row is invalid")
        row = dict(value)
        required = set(_CORE_FIELDS)
        if not require_decoded_counts:
            required.remove("decoded_byte_count")
        allowed = set(_CORE_FIELDS) | (
            set(_NODE_FIELDS) if row.get("domain") == "nodes" else set()
        )
        if not required <= set(row) or set(row) - allowed:
            raise ValueError("static atlas asset row fields are invalid")
        if row.get("domain") == "nodes":
            expected_node_fields = set(ASSET_TABLE_FIELDS)
            if not require_decoded_counts and "decoded_byte_count" not in row:
                expected_node_fields.remove("decoded_byte_count")
            if set(row) != expected_node_fields:
                raise ValueError("static atlas node selection metadata is incomplete")
        _validate_row_types(row, require_decoded_counts=require_decoded_counts)
        asset_key = str(row["asset_key"])
        path = str(row["path"])
        sequence = int(row["sequence"])
        if asset_key in identities or path in paths or sequence in sequences:
            raise ValueError(
                "static atlas asset identity, path, or sequence is duplicated"
            )
        if sequence != position:
            raise ValueError(
                "static atlas asset sequence is not contiguous and ordered"
            )
        identities.add(asset_key)
        paths.add(path)
        sequences.add(sequence)
        normalized.append(row)
    return normalized


def _validate_row_types(
    row: Mapping[str, object], *, require_decoded_counts: bool
) -> None:
    for field in (
        "asset_key",
        "domain",
        "path",
        "sha256",
        "integrity",
        "payload_sha256",
        "payload_encoding",
    ):
        if not isinstance(row.get(field), str) or not row[field]:
            raise ValueError(f"static atlas asset {field} is invalid")
    for field in ("sequence", "byte_count", "record_count"):
        value = row.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"static atlas asset {field} is invalid")
    decoded_count = row.get("decoded_byte_count")
    if require_decoded_counts and (
        isinstance(decoded_count, bool)
        or not isinstance(decoded_count, int)
        or decoded_count <= 0
    ):
        raise ValueError("static atlas asset decoded_byte_count is invalid")
    if decoded_count is not None and (
        isinstance(decoded_count, bool)
        or not isinstance(decoded_count, int)
        or decoded_count <= 0
    ):
        raise ValueError("static atlas asset decoded_byte_count is invalid")
    if not isinstance(row.get("initial_load"), bool):
        raise ValueError("static atlas asset initial_load is invalid")
    if row.get("domain") == "nodes":
        _validate_node_fields(row)


def _validate_node_fields(row: Mapping[str, object]) -> None:
    for field in ("layer_index", "untimed_record_count"):
        value = row.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"static atlas node {field} is invalid")
    for field in ("layer_key", "layer_kind"):
        if not isinstance(row.get(field), str) or not row[field]:
            raise ValueError(f"static atlas node {field} is invalid")
    for field in ("country_keys", "scientific_signal_ids"):
        value = row.get(field)
        if not isinstance(value, list) or any(
            not isinstance(item, str) or not item for item in value
        ):
            raise ValueError(f"static atlas node {field} is invalid")
    bounds = row.get("bounds")
    if bounds is not None and (
        not isinstance(bounds, list)
        or len(bounds) != 4
        or any(
            isinstance(item, bool)
            or not isinstance(item, (int, float))
            or not math.isfinite(item)
            for item in bounds
        )
    ):
        raise ValueError("static atlas node bounds are invalid")
    for field in ("time_min_bp", "time_max_bp"):
        value = row.get(field)
        if value is not None and (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise ValueError(f"static atlas node {field} is invalid")


__all__ = [
    "ASSET_TABLE_FIELDS",
    "ASSET_TABLE_SCHEMA",
    "ASSET_TABLE_STORED_FIELDS",
    "encode_asset_inventory",
    "normalize_asset_inventory",
]
