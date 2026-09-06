from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from math import isfinite


def _source_record_id(row: Mapping[str, object]) -> str | None:
    return (
        _optional_text(row.get("source_record_id"))
        or _optional_text(row.get("sample_id"))
        or _optional_text(row.get("subject_id"))
    )


def _valid_coordinate_pair(latitude: object, longitude: object) -> bool:
    for value, minimum, maximum in (
        (latitude, -90.0, 90.0),
        (longitude, -180.0, 180.0),
    ):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return False
        if not isfinite(float(value)) or not minimum <= float(value) <= maximum:
            return False
    return True


def _text_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise TypeError("expected a list or tuple of identifiers")
    return tuple(sorted({_required_text(item) for item in value}))


def _optional_text(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


def _required_text(value: object) -> str:
    result = _optional_text(value)
    if result is None:
        raise ValueError("required identity must be non-empty")
    return result


def _required_number(value: object) -> float | int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("required temporal value must be numeric")
    return value


def _source_taxon_identity(value: object) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and value >= 0
        or isinstance(value, str)
        and bool(value.strip())
    )


def _is_sha256_identity(value: object) -> bool:
    if type(value) is not str or not value.startswith("sha256:"):
        return False
    digest = value.removeprefix("sha256:")
    return _is_sha256_hex(digest)


def _is_sha256_hex(value: object) -> bool:
    if type(value) is not str:
        return False
    return len(value) == 64 and all(
        character in "0123456789abcdef" for character in value
    )


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _stable_id(prefix: str, *values: str) -> str:
    return f"{prefix}:{_digest(values)[:24]}"
