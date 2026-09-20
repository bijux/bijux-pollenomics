"""Bind typed observation products back to their exact source bytes."""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from typing import Any, cast

from ...contracts import canonical_json, manifest_sha256
from ..contracts import digest, refuse


def validate_source_closure(
    product: dict[str, object], units: tuple[object, ...]
) -> None:
    """Prove metadata and typed units are an exact rendering of pinned bytes."""
    canonical = product.get("source_canonical_json")
    if not isinstance(canonical, str):
        refuse("Observation product lacks its canonical source payload")
    try:
        source = json.loads(canonical)
    except json.JSONDecodeError as exc:
        refuse(f"Malformed embedded observation source payload: {exc}")
    source_file_sha256 = hashlib.sha256((canonical + "\n").encode()).hexdigest()
    if (
        not isinstance(source, dict)
        or canonical_json(source) != canonical
        or source_file_sha256 != digest(cast(str, product.get("source_file_sha256")))
        or manifest_sha256(source)
        != digest(cast(str, product.get("source_payload_sha256")))
    ):
        refuse("Observation product source bytes or payload identity differ")
    metadata = {
        key: value for key, value in source.items() if key not in {"taxa", "units"}
    }
    source_units = source.get("units")
    if (
        product.get("metadata") != metadata
        or product.get("taxa") != source.get("taxa")
        or not isinstance(source_units, list)
        or any(not isinstance(value, dict) for value in source_units)
    ):
        refuse("Observation product differs from its embedded source fields")
    typed_units: list[dict[str, object]] = []
    for unit in units:
        try:
            value = cast(dict[str, object], asdict(cast(Any, unit)))
        except (TypeError, ValueError) as exc:
            refuse(f"Malformed typed observation source unit: {exc}")
        for field in (
            "source_snapshot_sha256",
            "source_member_sha256",
            "reviewed_taxon_mapping_sha256",
            "normalization_code_sha256",
            "rights_evidence_sha256",
            "source_unit_sha256",
        ):
            value.pop(field, None)
        values = value.get("values")
        if not isinstance(values, tuple):
            refuse("Typed observation source values must be immutable pairs")
        value["values"] = dict(cast(tuple[tuple[str, object], ...], values))
        typed_units.append(value)
    source_index = {
        value.get("observation_id"): value
        for value in cast(list[dict[str, object]], source_units)
    }
    typed_index = {value.get("observation_id"): value for value in typed_units}
    if (
        None in source_index
        or None in typed_index
        or len(source_index) != len(source_units)
        or len(typed_index) != len(typed_units)
        or canonical_json(source_index) != canonical_json(typed_index)
    ):
        refuse("Observation product units differ from their pinned source bytes")
