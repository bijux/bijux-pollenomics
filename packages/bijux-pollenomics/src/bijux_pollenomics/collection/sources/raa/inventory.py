"""Exact source identities and count declarations for the legacy point profile."""

from __future__ import annotations

from collections.abc import Mapping
import json
import math

from ....core.geospatial.geojson import JsonObject, as_mapping


def non_negative_count(value: object) -> int | None:
    """Return a source JSON integer without boolean or float coercion."""
    if type(value) is not int or value < 0:
        return None
    return value


def declared_population(inventory: Mapping[str, object]) -> int:
    """Read WFS population aliases, preserving zero and refusing unknown totals."""
    declarations: list[int] = []
    for field in ("numberMatched", "totalFeatures"):
        if field not in inventory:
            continue
        value = inventory[field]
        count = non_negative_count(value)
        if (
            isinstance(value, str)
            and value.isascii()
            and value.isdecimal()
            and (value == "0" or not value.startswith("0"))
        ):
            count = int(value)
        if count is None:
            raise ValueError(f"RAÄ {field} must declare a nonnegative population")
        declarations.append(count)
    if not declarations:
        raise ValueError("RAÄ feature inventory is missing its population declaration")
    if len(set(declarations)) != 1:
        raise ValueError("RAÄ population declarations disagree")
    return declarations[0]


def source_features(inventory: Mapping[str, object]) -> list[JsonObject]:
    """Preserve every feature member or refuse the complete collection."""
    if inventory.get("type") != "FeatureCollection":
        raise ValueError("RAÄ inventory must be a FeatureCollection")
    values = inventory.get("features")
    if not isinstance(values, list):
        raise ValueError("RAÄ feature inventory must contain a feature list")
    features: list[JsonObject] = []
    for value in values:
        feature = as_mapping(value)
        if feature is None or feature.get("type") != "Feature":
            raise ValueError("RAÄ feature inventory contains a malformed member")
        features.append(feature)
    return features


def native_feature_ids(features: list[JsonObject]) -> list[str]:
    """Require native string identifiers without inventing or normalizing values."""
    identifiers: list[str] = []
    for feature in features:
        properties = as_mapping(feature.get("properties"))
        value = properties.get("lamningsnummer") if properties is not None else None
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                "RAÄ feature archive has a missing or invalid lamningsnummer"
            )
        identifiers.append(value)
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("RAÄ feature archive contains duplicate lamningsnummer values")
    return identifiers


def validate_inventory(inventory: Mapping[str, object]) -> list[JsonObject]:
    """Reconcile the declared population with all native feature identities."""
    features = source_features(inventory)
    population = declared_population(inventory)
    if len(features) != population:
        raise ValueError(
            f"RAÄ feature archive count mismatch: expected {population}, archived {len(features)}"
        )
    native_feature_ids(features)
    return features


def decode_source_object(text: str) -> dict[str, object]:
    """Decode one source JSON object without losing duplicate or nonfinite claims."""
    value = json.loads(
        text,
        object_pairs_hook=_unique_object,
        parse_constant=_reject_nonfinite,
        parse_float=_finite_float,
    )
    if not isinstance(value, dict):
        raise ValueError("RAÄ source JSON must be an object")
    return value


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"RAÄ source JSON contains duplicate key: {key}")
        result[key] = value
    return result


def _reject_nonfinite(value: str) -> float:
    raise ValueError(f"RAÄ source JSON contains a nonfinite number: {value}")


def _finite_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        return _reject_nonfinite(value)
    return number
