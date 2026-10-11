"""Partition a byte-bound SVAR registry without treating screening as approval."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
import math
from pathlib import Path
from typing import TypedDict
import unicodedata

from ...collection.spatial.representative_points import geometry_to_representative_point


class LakeRow(TypedDict):
    """One eligible named feature with its unchanged native properties."""

    lake_id: str
    name_key: str
    latitude: float
    longitude: float
    source_geometry_type: str
    feature: dict[str, object]
    properties: dict[str, object]


def normalize_name(value: str) -> str:
    """Apply the existing case/accent folding solely for matching display names."""
    folded = unicodedata.normalize("NFKD", value.casefold())
    return "".join(character for character in folded if character.isalnum())


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Refuse ambiguous JSON object members before projecting source fields."""
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("svar_review_duplicate_json_key")
        result[key] = value
    return result


def _finite(token: str) -> float:
    """Decode finite JSON numbers without admitting overflow or nonfinite tokens."""
    value = float(token)
    if not math.isfinite(value):
        raise ValueError("svar_review_nonfinite_json_number")
    return value


def read_screened_registry(path: Path) -> tuple[list[LakeRow], dict[str, object]]:
    """Bind complete source bytes and partition every input feature occurrence."""
    content = path.read_bytes()
    payload = json.loads(
        content, object_pairs_hook=_unique, parse_float=_finite, parse_constant=_finite
    )
    if not isinstance(payload, dict) or payload.get("type") != "FeatureCollection":
        raise ValueError("svar_review_feature_collection_required")
    features = payload.get("features")
    if not isinstance(features, list):
        raise ValueError("svar_review_features_array_required")
    eligible: list[LakeRow] = []
    exclusions: list[dict[str, object]] = []
    reasons: Counter[str] = Counter()
    for index, feature in enumerate(features):
        row, reason = _screen(feature)
        if row is not None:
            eligible.append(row)
            continue
        native_fields = {}
        if isinstance(feature, dict) and isinstance(feature.get("properties"), dict):
            native_fields = {
                key: feature["properties"][key]
                for key in ("record_id", "sjoid", "name")
                if key in feature["properties"]
            }
        excluded: dict[str, object] = {
            "source_feature_index": index,
            "reason_code": reason,
            "source_fields": native_fields,
        }
        if not isinstance(feature, dict):
            excluded["source_feature_value"] = feature
        elif reason == "feature_kind_invalid" and "type" in feature:
            excluded["source_feature_type"] = feature["type"]
        exclusions.append(excluded)
        reasons[reason] += 1
    return eligible, {
        "source_lake_count": len(features),
        "registry_sha256": sha256(content).hexdigest(),
        "registry_byte_count": len(content),
        "screening_eligible_lake_count": len(eligible),
        "screening_excluded_lake_count": len(exclusions),
        "screening_exclusion_reason_counts": dict(sorted(reasons.items())),
        "screening_exclusions": exclusions,
    }


def _identity(properties: dict[str, object]) -> tuple[str | None, str]:
    """Resolve existing string-ID precedence while distinguishing missing tokens."""
    for key in ("sjoid", "record_id"):
        value = properties.get(key)
        if value is None or value == "":
            continue
        if not isinstance(value, str):
            return None, "identity_not_string"
        if value.strip():
            return value, ""
    if not any(key in properties for key in ("sjoid", "record_id")):
        return None, "identity_absent"
    values = [properties[key] for key in ("sjoid", "record_id") if key in properties]
    return None, "identity_null" if all(v is None for v in values) else "identity_empty"


def _screen(value: object) -> tuple[LakeRow | None, str]:
    """Admit a typed named Feature or retain its first screening refusal reason."""
    if not isinstance(value, dict):
        return None, "feature_not_object"
    if not isinstance(value.get("type"), str) or value["type"] != "Feature":
        return None, "feature_kind_invalid"
    properties = value.get("properties")
    if not isinstance(properties, dict):
        return None, "properties_not_object"
    geometry = value.get("geometry")
    if not isinstance(geometry, dict):
        return None, "geometry_not_object"
    try:
        point = geometry_to_representative_point(geometry)
    except (OverflowError, ValueError, TypeError):
        return None, "representative_point_unavailable"
    if point is None or not all(math.isfinite(v) for v in point[:2]):
        return None, "representative_point_unavailable"
    lake_id, identity_reason = _identity(properties)
    if lake_id is None:
        return None, identity_reason
    if "name" not in properties:
        return None, "name_absent"
    name = properties["name"]
    if name is None:
        return None, "name_null"
    if not isinstance(name, str):
        return None, "name_not_string"
    if not name.strip():
        return None, "name_empty"
    longitude, latitude, geometry_type = point
    return {
        "lake_id": lake_id,
        "name_key": normalize_name(name.strip()),
        "latitude": round(latitude, 6),
        "longitude": round(longitude, 6),
        "source_geometry_type": geometry_type,
        "feature": value,
        "properties": properties,
    }, ""
