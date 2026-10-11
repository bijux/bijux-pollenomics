"""Assert source-library audit payload shapes before comparing their claims."""

from __future__ import annotations


def mapping(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise AssertionError("expected a source-library evidence mapping")
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise AssertionError("source-library evidence keys must be strings")
        result[key] = item
    return result


def rows(value: object) -> tuple[dict[str, object], ...]:
    if not isinstance(value, list):
        raise AssertionError("expected source-library evidence rows")
    return tuple(mapping(row) for row in value)


def strings(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise AssertionError("expected source-library evidence labels")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise AssertionError("source-library evidence labels must be strings")
        result.append(item)
    return tuple(result)


def count(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise AssertionError("expected a source-library evidence count")
    return value
