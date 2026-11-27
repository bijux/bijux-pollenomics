"""Refuse decimal count tokens that binary64 would falsely make integral."""

from decimal import Decimal, InvalidOperation
import json
import math
from typing import Any

from .relational.variables import unit_family


class _FloatToken(str):
    """Retain JSON float spelling only for pre-conversion count checks."""


def _check(value: object) -> None:
    if not isinstance(value, _FloatToken):
        return
    number = float(value)
    if not math.isfinite(number) or number < 0 or not number.is_integer():
        return
    mantissa = value.lower().split("e", 1)[0]
    if number == 0:
        if any(digit in "123456789" for digit in mantissa):
            raise ValueError(
                "Neotoma count token loses precision before integer assessment"
            )
        return
    try:
        if Decimal(value) != Decimal.from_float(number):
            raise ValueError(
                "Neotoma count token loses precision before integer assessment"
            )
    except InvalidOperation as error:
        raise ValueError("Neotoma count token exponent is unsupported") from error


def _mapping(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _rows(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def _native_values(payload: object) -> list[object]:
    payload = _mapping(payload)
    roots = _rows(payload.get("rows")) + _rows(payload.get("data"))
    if "site" in payload:
        roots.append(payload)
    values: list[object] = []
    for root in roots:
        site = _mapping(_mapping(root).get("site"))
        unit = _mapping(site.get("collectionunit"))
        dataset = _mapping(unit.get("dataset"))
        for sample in _rows(dataset.get("samples")):
            for raw in _rows(_mapping(sample).get("datum")):
                datum = _mapping(raw)
                units = datum.get("units")
                if isinstance(units, str) and unit_family(units.strip()) == "count":
                    values.append(datum.get("value"))
    return values


def _observation_values(payload: object) -> list[object]:
    values: list[object] = []
    for raw in _rows(_mapping(payload).get("rows")):
        row = _mapping(raw)
        source = _mapping(row.get("source_payload"))
        unit = row.get("source_unit")
        if isinstance(unit, str) and unit_family(unit.strip()) == "count":
            values.extend((row.get("source_value"), source.get("value")))
    return values


def check_native_count_tokens(content: bytes | str, parsed: object) -> None:
    """Check download count spellings without reparsing unrelated responses."""
    if any(isinstance(value, float) for value in _native_values(parsed)):
        for value in _native_values(json.loads(content, parse_float=_FloatToken)):
            _check(value)


def check_observation_count_tokens(content: bytes | str, parsed: object) -> None:
    """Check normalized count spellings without changing accepted values."""
    if any(isinstance(value, float) for value in _observation_values(parsed)):
        for value in _observation_values(json.loads(content, parse_float=_FloatToken)):
            _check(value)
