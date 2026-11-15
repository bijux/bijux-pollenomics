"""Resolve entrance-distance reference labels without rewriting native unit evidence."""

from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path
from typing import Any

from ...client import decode_neotoma_json_object, positive_native_id
from ..receipts import _object, _read, _safe_root
from ..reference_tables import (
    read_neotoma_reference_table_body,
    replay_neotoma_reference_tables,
)
from ..resources.models import DEFAULT_RESOURCE_LIMITS, NeotomaResourceLimits
from .profiles import parse_neotoma_unit_source, summarize_unit_source
from .replay import read_neotoma_unit_body, replay_neotoma_unit_resources

_REFERENCE_FIELDS = {
    "variableunitsid",
    "variableunits",
    "recdatecreated",
    "recdatemodified",
}


def _dictionary(body: bytes) -> tuple[dict[int, tuple[int, dict[str, Any]]], int]:
    """Validate every native row before a selected token can supply a label."""
    native = decode_neotoma_json_object(body)
    if native.get("status") != "success" or not isinstance(native.get("data"), list):
        raise ValueError("Variable-unit reference source status or array differs")
    result = {}
    for index, row in enumerate(native["data"]):
        if not isinstance(row, dict) or set(row) != _REFERENCE_FIELDS:
            raise ValueError(
                "Variable-unit reference fields are missing or unsupported"
            )
        identity = positive_native_id(row["variableunitsid"])
        if (
            identity in result
            or not isinstance(row["variableunits"], str)
            or not row["variableunits"]
            or any(
                row[field] is not None and not isinstance(row[field], str)
                for field in ("recdatecreated", "recdatemodified")
            )
        ):
            raise ValueError("Variable-unit reference identity, label or dates differ")
        result[identity] = index, row
    return result, len(native["data"])


def _source(
    directory: Path,
    capture_sha256: str,
    reference: dict[str, Any],
    body_sha256: str,
    receipt_sha256: str,
) -> dict[str, Any]:
    """Keep both independently timed source epochs with their actual receipt pins."""
    raw = _read(_safe_root(directory) / reference["receipt_file"], 1024 * 1024)
    if sha256(raw).hexdigest() != receipt_sha256:
        raise ValueError("Reference-resolution source receipt identity differs")
    record = _object(raw)
    if record.get("retained_body_sha256") != body_sha256:
        raise ValueError("Reference-resolution source body and receipt differ")
    return {
        "capture_manifest_sha256": capture_sha256,
        "content_version": "current",
        "api_version": "v2.0",
        "requested_url": record["requested_url"],
        "utc_start": record["utc_start"],
        "utc_end": record["utc_end"],
        "receipt_file": reference["receipt_file"],
        "receipt_sha256": receipt_sha256,
        "body_file": reference["body_file"],
        "body_sha256": body_sha256,
    }


def resolve_neotoma_entrance_distance_reference(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    collection_unit_id: int,
    roster_path: Path,
    metadata_captures: Mapping[str, Path],
    reference_directory: Path,
    expected_reference_manifest_sha256: str,
    limits: NeotomaResourceLimits = DEFAULT_RESOURCE_LIMITS,
) -> dict[str, Any]:
    """Join exact native integer references only after whole-unit role admission.

    The current lookup establishes a source dictionary label for the recorded
    token under the pinned SQL's intended join. It does not authenticate the
    deployed SQL version, interpret other measurements, or modify the unit's
    raw payload and original source qualification.
    """
    unit_id = positive_native_id(collection_unit_id)
    body = read_neotoma_unit_body(
        directory,
        expected_manifest_sha256=expected_manifest_sha256,
        unit_key=f"speleothem-unit-{unit_id}",
        roster_path=roster_path,
        metadata_captures=metadata_captures,
        limits=limits,
    )
    parsed = parse_neotoma_unit_source(
        body.scope, body.body, expected_body_sha256=body.body_sha256
    )
    reference_body = read_neotoma_reference_table_body(
        reference_directory,
        expected_manifest_sha256=expected_reference_manifest_sha256,
        table="variableunits",
    )
    dictionary, received = _dictionary(reference_body.body)
    unit_capture = replay_neotoma_unit_resources(
        directory,
        expected_manifest_sha256=expected_manifest_sha256,
        roster_path=roster_path,
        metadata_captures=metadata_captures,
        limits=limits,
    )
    reference_capture = replay_neotoma_reference_tables(
        reference_directory,
        expected_manifest_sha256=expected_reference_manifest_sha256,
    )
    unit_entry = next(
        row for row in unit_capture.units if row["unit_key"] == body.unit_key
    )
    reference_entry = next(
        row for row in reference_capture.tables if row["table"] == "variableunits"
    )
    rows = []
    for index, native in enumerate(parsed.records):
        token = native["entrancedistanceunits"]
        row: dict[str, Any] = {
            "native_record_pointer": f"/data/{index}/speleothem",
            "native_entity_id": native["entityid"],
            "raw_reference_token": token,
            "absence_certified": False,
            "reference_resolution_status": "unavailable_explicit_null_reference"
            if token is None
            else "unavailable_reference_token_not_returned",
        }
        if token is not None and token in dictionary:
            position, reference = dictionary[token]
            row.update(
                reference_resolution_status="resolved_current_reference_label",
                reference_record_pointer=f"/data/{position}",
                reference_native_row=reference,
            )
        rows.append(row)
    return {
        "schema_version": "neotoma-entrance-distance-reference-resolution.v1",
        "scope": parsed.scope,
        "source_capture_relabelled": False,
        "unit_source": _source(
            directory,
            unit_capture.manifest_sha256,
            unit_entry["attempts"][-1],
            body.body_sha256,
            body.receipt_sha256,
        ),
        "reference_source": _source(
            reference_directory,
            reference_capture.manifest_sha256,
            reference_entry["attempts"][0],
            reference_body.body_sha256,
            reference_body.receipt_sha256,
        ),
        "dictionary_rows": received,
        "distinct_reference_ids": len(dictionary),
        "dictionary_completeness": "not_established",
        "source_intended_reference_binding": summarize_unit_source(parsed)[
            "unit_field_contract"
        ],
        "records": rows,
        "physical_measurement_unit_admission": "not_asserted",
        "unit_inheritance_to_other_fields": False,
        "other_fields_not_resolved": [
            "dripheightunits",
            "entitycoverthickness",
            "sample_depth",
            "chronology_control_depth",
        ],
        "scientific_admission": "not_asserted",
        "HTTP_requests": 0,
    }
