"""Strict country-coverage payload decoding and scalar validation."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
import hashlib
import json
from typing import Any, cast
from .constants import (
    CountryCoverageError,
    _NAME_TO_CODE,
    _RAW_SHA256_PATTERN,
    _SHA256_ID_PATTERN,
)


def _geojson_country_counts(document: Mapping[str, object]) -> Counter[str]:
    return Counter(
        _country_code(
            _object(feature.get("properties"), "feature properties").get("country")
        )
        for feature in _features(document, "country GeoJSON")
    )


def _features(document: Mapping[str, object], label: str) -> list[Mapping[str, object]]:
    features = document.get("features")
    if not isinstance(features, list) or any(
        not isinstance(feature, Mapping) for feature in features
    ):
        raise CountryCoverageError(f"{label} must contain feature objects")
    return cast(list[Mapping[str, object]], features)


def _integer_counts(value: object, label: str) -> dict[str, int]:
    mapping = _object(value, label)
    return {str(key): _integer(item, label) for key, item in mapping.items()}


def _country_code(value: object) -> str:
    if value is None:
        return "UNASSIGNED"
    if not isinstance(value, str):
        raise CountryCoverageError(f"unsupported country label: {value!r}")
    try:
        return _NAME_TO_CODE[value]
    except KeyError as error:
        raise CountryCoverageError(f"unsupported country label: {value!r}") from error


def _rows(
    document: Mapping[str, object], label: str, *, key: str = "rows"
) -> list[Mapping[str, object]]:
    value = document.get(key)
    if not isinstance(value, list) or any(
        not isinstance(row, Mapping) for row in value
    ):
        raise CountryCoverageError(f"{label} must contain object rows")
    return cast(list[Mapping[str, object]], value)


def _decode_object(payload: bytes, label: str) -> dict[str, Any]:
    try:
        return _object(
            json.loads(payload, object_pairs_hook=_unique_json_object), label
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CountryCoverageError(f"cannot decode governed input: {label}") from error


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise CountryCoverageError(
                f"governed input contains duplicate JSON key: {key}"
            )
        result[key] = value
    return result


def _object(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CountryCoverageError(f"{label} must be an object")
    return cast(dict[str, Any], value)


def _integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise CountryCoverageError(f"{label} must be a non-negative integer")
    return value


def _positive_integer(value: object, label: str) -> int:
    result = _integer(value, label)
    if result == 0:
        raise CountryCoverageError(f"{label} must be positive")
    return result


def _coordinate(value: object, label: str, minimum: float, maximum: float) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not minimum <= value <= maximum
    ):
        raise CountryCoverageError(
            f"{label} must be a finite coordinate in [{minimum}, {maximum}]"
        )
    result = float(value)
    if not (minimum <= result <= maximum):
        raise CountryCoverageError(
            f"{label} must be a finite coordinate in [{minimum}, {maximum}]"
        )
    return result


def _bbox(value: object, label: str) -> tuple[float, float, float, float]:
    if not isinstance(value, list) or len(value) != 4:
        raise CountryCoverageError(f"{label} must have four coordinates")
    minimum_longitude = _coordinate(value[0], label, -180, 180)
    minimum_latitude = _coordinate(value[1], label, -90, 90)
    maximum_longitude = _coordinate(value[2], label, -180, 180)
    maximum_latitude = _coordinate(value[3], label, -90, 90)
    if minimum_longitude > maximum_longitude or minimum_latitude > maximum_latitude:
        raise CountryCoverageError(f"{label} bounds are reversed")
    return (
        minimum_longitude,
        minimum_latitude,
        maximum_longitude,
        maximum_latitude,
    )


def _sha256_id_from_raw(value: str, label: str) -> str:
    if _RAW_SHA256_PATTERN.fullmatch(value) is None:
        raise CountryCoverageError(f"{label} must be a lowercase SHA-256 digest")
    return f"sha256:{value}"


def _require_sha256_id(value: str, label: str) -> str:
    if _SHA256_ID_PATTERN.fullmatch(value) is None:
        raise CountryCoverageError(f"{label} must be a sha256 identity")
    return value


def _text_list(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item for item in value
    ):
        raise CountryCoverageError(f"{label} must be a list of non-empty strings")
    return cast(list[str], value)


def _required_text(document: Mapping[str, object], *path: str) -> str:
    value: object = document
    for key in path:
        if not isinstance(value, Mapping):
            raise CountryCoverageError(f"missing required field: {'.'.join(path)}")
        value = value.get(key)
    if not isinstance(value, str) or not value:
        raise CountryCoverageError(f"missing required field: {'.'.join(path)}")
    return value


def _canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True)
        + "\n"
    ).encode("utf-8")


def _sead_canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()
