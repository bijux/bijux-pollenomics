"""Extract usable source-specific PPE and fall-speed candidates."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
import math
import re
from typing import Any, cast

PARAMETER_KINDS = ("ppe", "fall_speed")
USABLE_STATUS = "usable_finite_positive"
_PPE_SD = re.compile(
    r"^\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?)\s*"
    r"\(([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?)\)\s*$"
)


def _digest(value: object) -> str:
    content = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return hashlib.sha256(content.encode()).hexdigest()


def _source_text(value: object) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return str(value)
    return None


def _parsed_positive(value: object) -> tuple[float | None, str]:
    if value is None:
        return None, "missing_source_value"
    if isinstance(value, str) and not value.strip():
        return None, "empty_source_value"
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        return None, "nonnumeric_source_value"
    try:
        parsed = float(value)
    except ValueError:
        return None, "nonnumeric_source_value"
    if not math.isfinite(parsed):
        return None, "nonfinite_source_value"
    if parsed <= 0:
        return None, "nonpositive_source_value"
    return parsed, USABLE_STATUS


def _parsed_nonnegative(value: object) -> tuple[float | None, str]:
    parsed, status = _parsed_positive(value)
    if status == "nonpositive_source_value":
        try:
            if float(cast(str | int | float, value)) == 0:
                return 0.0, USABLE_STATUS
        except (TypeError, ValueError):
            pass
    return parsed, status


def _candidate(
    *,
    record_id: str,
    candidate_index: int,
    kind: str,
    raw: dict[str, Any],
    source_value_text: str | None,
    source_value: float | None,
    source_units: object,
    units_basis: str,
    parsing_status: str,
    source_uncertainty_text: str | None = None,
    source_uncertainty_value: float | None = None,
) -> dict[str, Any]:
    expected_units = "relative_to_reference_taxon" if kind == "ppe" else "m/s"
    if source_units != expected_units and parsing_status == USABLE_STATUS:
        parsing_status = "incompatible_source_units"
    payload: dict[str, Any] = {
        "parameter_candidate_id": f"{record_id}:candidate:{candidate_index}:{kind}",
        "parameter_kind": kind,
        "source_candidate_index": candidate_index,
        "source_candidate_sha256": _digest(raw),
        "source_value_text": source_value_text,
        "source_value": source_value,
        "source_units": source_units,
        "source_units_basis": units_basis,
        "source_uncertainty_text": source_uncertainty_text,
        "source_uncertainty_value": source_uncertainty_value,
        "parsing_status": parsing_status,
    }
    payload["parameter_candidate_sha256"] = _digest(payload)
    return payload


def _landclim(record_id: str, index: int, raw: dict[str, Any]) -> list[dict[str, Any]]:
    combined = raw.get("ppe_sd_source_text")
    ppe_value: float | None = None
    uncertainty_value: float | None = None
    ppe_status = "missing_source_value"
    uncertainty_text: str | None = None
    if isinstance(combined, str) and not combined.strip():
        ppe_status = "empty_source_value"
    elif isinstance(combined, str):
        match = _PPE_SD.fullmatch(combined)
        if match is None:
            ppe_status = "nonnumeric_source_value"
        else:
            ppe_value, ppe_status = _parsed_positive(match.group(1))
            uncertainty_text = match.group(2)
            uncertainty_value, uncertainty_status = _parsed_nonnegative(
                uncertainty_text
            )
            if uncertainty_status != USABLE_STATUS:
                ppe_status = "unusable_source_uncertainty"
    fall_value = raw.get("fall_speed_source_text")
    parsed_fall, fall_status = _parsed_positive(fall_value)
    return [
        _candidate(
            record_id=record_id,
            candidate_index=index,
            kind="ppe",
            raw=raw,
            source_value_text=_source_text(combined),
            source_value=ppe_value,
            source_units=raw.get("ppe_units", "relative_to_reference_taxon"),
            units_basis=(
                "explicit_candidate_field"
                if "ppe_units" in raw
                else "landclim_ppe_schema"
            ),
            parsing_status=ppe_status,
            source_uncertainty_text=uncertainty_text,
            source_uncertainty_value=uncertainty_value,
        ),
        _candidate(
            record_id=record_id,
            candidate_index=index,
            kind="fall_speed",
            raw=raw,
            source_value_text=_source_text(fall_value),
            source_value=parsed_fall,
            source_units=raw.get("fall_speed_units"),
            units_basis="explicit_candidate_field",
            parsing_status=fall_status,
        ),
    ]


def _source_value(values: dict[str, Any], normalized_key: str) -> tuple[object, str]:
    matches = [
        value
        for key, value in values.items()
        if key.casefold().replace("_", "").replace(".", "") == normalized_key
    ]
    if not matches:
        return None, "missing_source_value"
    if len(matches) != 1:
        return None, "ambiguous_source_fields"
    return matches[0], "present"


def _lra_reference(
    record_id: str, index: int, raw: dict[str, Any]
) -> list[dict[str, Any]]:
    values = raw.get("source_values")
    source_values = cast(dict[str, Any], values) if isinstance(values, dict) else {}
    ppe, ppe_presence = _source_value(source_values, "ppe")
    parsed_ppe, ppe_status = _parsed_positive(ppe)
    if ppe_presence == "ambiguous_source_fields":
        ppe_status = ppe_presence
    uncertainty, uncertainty_presence = _source_value(source_values, "ppeerror")
    parsed_uncertainty: float | None = None
    if uncertainty_presence == "present":
        parsed_uncertainty, uncertainty_status = _parsed_nonnegative(uncertainty)
        if uncertainty_status != USABLE_STATUS:
            ppe_status = "unusable_source_uncertainty"
    elif uncertainty_presence == "ambiguous_source_fields":
        ppe_status = uncertainty_presence
    fall, fall_presence = _source_value(source_values, "fallspeed")
    parsed_fall, fall_status = _parsed_positive(fall)
    if fall_presence == "ambiguous_source_fields":
        fall_status = fall_presence
    return [
        _candidate(
            record_id=record_id,
            candidate_index=index,
            kind="ppe",
            raw=raw,
            source_value_text=_source_text(ppe),
            source_value=parsed_ppe,
            source_units=source_values.get("ppe_units", "relative_to_reference_taxon"),
            units_basis=(
                "explicit_source_value_field"
                if "ppe_units" in source_values
                else "lra_resource_ppe_schema"
            ),
            parsing_status=ppe_status,
            source_uncertainty_text=_source_text(uncertainty),
            source_uncertainty_value=parsed_uncertainty,
        ),
        _candidate(
            record_id=record_id,
            candidate_index=index,
            kind="fall_speed",
            raw=raw,
            source_value_text=_source_text(fall),
            source_value=parsed_fall,
            source_units=source_values.get("fallspeed_units", "m/s"),
            units_basis=(
                "explicit_source_value_field"
                if "fallspeed_units" in source_values
                else "lra_resource_fall_speed_schema"
            ),
            parsing_status=fall_status,
        ),
    ]


def parameter_candidates(
    source_family: str,
    record_id: str,
    raw_candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return canonical candidates and refuse multiple usable values per kind."""
    result = []
    for index, raw in enumerate(raw_candidates, 1):
        parser = _landclim if source_family == "landclim" else _lra_reference
        result.extend(parser(record_id, index, raw))
    usable = Counter(
        candidate["parameter_kind"]
        for candidate in result
        if candidate["parsing_status"] == USABLE_STATUS
    )
    if any(usable[kind] > 1 for kind in PARAMETER_KINDS):
        raise ValueError("Parameter authority has ambiguous usable candidates")
    return result
