"""Source-row ownership without representative geometry or scientific admission."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterator
from hashlib import sha256
import json
import re
import sqlite3
import struct

from .contracts import BOUNDARY, GEOMETRY_TYPES, SOURCE_COLUMNS
from .reading import quote_identifier, source_profile


def canonical_bytes(value: object) -> bytes:
    """Encode finite source projections without float or null coercion."""
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode()


def geometry_descriptor(value: bytes) -> dict[str, object]:
    """Bind original bytes and check only the standard container header."""
    result: dict[str, object] = {
        "sqlite_storage_type": "blob",
        "sha256": sha256(value).hexdigest(),
        "byte_count": len(value),
        "geometry_validation": "not_evaluated",
    }
    status = "unsupported_header"
    if len(value) >= 8 and value[:3] == b"GP\x00":
        flags = value[3]
        code = (flags >> 1) & 7
        if not flags & 0xE0 and code < 5:
            length = 8 + (0, 32, 48, 48, 64)[code]
            srs = struct.unpack("<i" if flags & 1 else ">i", value[4:8])[0]
            result.update(
                header_srs_id=srs,
                empty_flag=bool(flags & 16),
                envelope_code=code,
                header_byte_count=length,
            )
            if len(value) < length + 5:
                status = "truncated_geometry_payload"
            elif srs != 3006:
                status = "declared_crs_mismatch"
            else:
                status = "supported_header_only"
                result["header_hex"] = value[:length].hex()
    result["header_status"] = status
    return result


def _uuid(value: object) -> str | None:
    if isinstance(value, str) and re.fullmatch(
        r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", value
    ):
        return value
    return None


def _rows(connection: sqlite3.Connection, table: str) -> Iterator[dict[str, object]]:
    for row in connection.execute(
        f"SELECT * FROM {quote_identifier(table)} ORDER BY fid"
    ):
        result = dict(row)
        if type(result["fid"]) is not int:
            raise ValueError("RAÄ source row identity must be a native integer")
        yield result


def iter_audit_documents(
    connection: sqlite3.Connection,
) -> Iterator[dict[str, object]]:
    """Emit all seven base tables and explicit source-owned relationship partitions."""
    profile = source_profile(connection)
    yield {"kind": "source_profile", "profile": profile, "boundary": BOUNDARY}
    owners = Counter(
        owner_uuid
        for row in connection.execute("SELECT uuid FROM lamning")
        if (owner_uuid := _uuid(row[0])) is not None
    )
    nested: dict[int, list[object]] = defaultdict(list)
    for row in connection.execute("SELECT id,lamning_uuid FROM ingaendelamning"):
        if type(row[0]) is int:
            nested[row[0]].append(row[1])
    membership: dict[str, Counter[str]] = defaultdict(Counter)
    for table in GEOMETRY_TYPES:
        for row in connection.execute(
            f"SELECT lamning_uuid FROM {quote_identifier(table)}"
        ):
            if (owner_uuid := _uuid(row[0])) is not None:
                membership[owner_uuid][table] += 1

    def direct(value: object) -> dict[str, object]:
        key = _uuid(value)
        status = (
            "invalid_or_missing_native_uuid"
            if key is None
            else "orphan_owner"
            if owners[key] == 0
            else "ambiguous_owner"
            if owners[key] > 1
            else "linked"
        )
        return {
            "status": status,
            "native_lamning_uuid": value,
            "matching_source_rows": owners[key] if key is not None else 0,
        }

    def relation(table: str, row: dict[str, object]) -> dict[str, object]:
        if table == "lamning":
            return {"domain": "lamning", **direct(row["uuid"])}
        parent = row["lamning_uuid"]
        if table != "egenskap":
            return {"domain": "lamning", **direct(parent)}
        child = row["ingaendelamning_id"]
        if child is None:
            return {"domain": "lamning", **direct(parent)}
        matches = nested.get(child, []) if type(child) is int else []
        result: dict[str, object] = {
            "domain": "ingaendelamning",
            "native_id": child,
            "matching_source_rows": len(matches),
            "declared_lamning_uuid": parent,
        }
        if parent is not None:
            result["status"] = "both_owner_domains_declared"
        elif type(child) is not int:
            result["status"] = "invalid_native_nested_id"
        elif not matches:
            result["status"] = "orphan_nested_owner"
        elif len(matches) > 1:
            result["status"] = "ambiguous_nested_owner"
        else:
            lineage = direct(matches[0])
            result["status"] = lineage["status"]
            result["lamning_lineage_via_nested_row"] = lineage
        return result

    totals: dict[str, dict[str, object]] = {}
    geometry_headers: Counter[str] = Counter()
    for table in SOURCE_COLUMNS:
        count = 0
        statuses: Counter[str] = Counter()
        cells: dict[str, Counter[str]] = {
            name: Counter() for name in SOURCE_COLUMNS[table]
        }
        for row in _rows(connection, table):
            count += 1
            for name, value in row.items():
                cells[name]["null" if value is None else "non_null"] += 1
                if type(value) in (int, float) and value == 0:
                    cells[name]["numeric_zero"] += 1
                if isinstance(value, str) and value == "":
                    cells[name]["empty_text"] += 1
            values: dict[str, object] = {}
            for name, value in row.items():
                if isinstance(value, bytes):
                    values[name] = (
                        geometry_descriptor(value)
                        if name == "geometri"
                        else {
                            "sqlite_storage_type": "blob",
                            "byte_count": len(value),
                            "sha256": sha256(value).hexdigest(),
                        }
                    )
                else:
                    values[name] = value
            owner = relation(table, row)
            statuses[str(owner["status"])] += 1
            record: dict[str, object] = {
                "kind": "source_row",
                "table": table,
                "fid": row["fid"],
                "source_values": values,
                "owner_relation": owner,
            }
            if table == "lamning":
                key = _uuid(row["uuid"])
                record["geometry_row_membership"] = (
                    dict(membership.get(key, {})) if key else {}
                )
            if table in GEOMETRY_TYPES:
                value = values["geometri"]
                if isinstance(value, dict):
                    header = str(value["header_status"])
                else:
                    header = "source_null" if value is None else "non_blob_source_value"
                geometry_headers[header] += 1
                record["geometry_header_status"] = header
                record["declared_geometry_type"] = GEOMETRY_TYPES[table]
            yield record
        totals[table] = {
            "source_rows": count,
            "owner_status_counts": dict(statuses),
            "source_cells": {key: dict(value) for key, value in cells.items()},
        }
    yield {
        "kind": "summary",
        "tables": totals,
        "unique_valid_native_uuid_values": len(owners),
        "duplicate_native_uuid_values": sum(count > 1 for count in owners.values()),
        "unique_native_nested_ids": len(nested),
        "duplicate_native_nested_ids": sum(len(rows) > 1 for rows in nested.values()),
        "geometry_header_status_counts": dict(geometry_headers),
        "boundary": BOUNDARY,
    }
