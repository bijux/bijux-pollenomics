"""Decode only the exposed selected dataset from a pinned raw part."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

_SPACE = b" \t\r\n"


def _space(body: bytes, position: int) -> int:
    while position < len(body) and body[position] in _SPACE:
        position += 1
    return position


def _end(body: bytes, start: int) -> int:
    """Find a JSON value's end without interpreting its numerical payload."""
    if start >= len(body):
        raise ValueError("Truncated source value")
    stack: list[int] = []
    quoted = escaped = False
    for position in range(start, len(body)):
        token = body[position]
        if quoted:
            if escaped:
                escaped = False
            elif token == 92:
                escaped = True
            elif token == 34:
                quoted = False
                if not stack:
                    return position + 1
        elif token == 34:
            quoted = True
        elif token in (91, 123):
            stack.append(token)
        elif token in (93, 125):
            if not stack:
                return position
            if (stack.pop(), token) not in ((91, 93), (123, 125)):
                raise ValueError("Mismatched source delimiters")
            if not stack:
                return position + 1
        elif not stack and (token == 44 or token in _SPACE):
            return position
    raise ValueError("Truncated source value")


def _member(body: bytes, name: str) -> bytes | None:
    """Read exactly one object member; similarly named nested keys stay opaque."""
    position = _space(body, 0)
    if position >= len(body) or body[position] != 123:
        raise ValueError("Source metadata path must traverse objects")
    position += 1
    found = []
    while position < len(body):
        position = _space(body, position)
        if body[position] == 125:
            break
        if body[position] == 44:
            position = _space(body, position + 1)
        if body[position] != 34:
            raise ValueError("Invalid source metadata key")
        end = _end(body, position)
        key = json.loads(body[position:end])
        position = _space(body, end)
        if body[position] != 58:
            raise ValueError("Missing source metadata colon")
        start = _space(body, position + 1)
        position = _end(body, start)
        if key == name:
            found.append(body[start:position])
    if len(found) > 1:
        raise ValueError("Ambiguous source metadata member")
    return found[0] if found else None


def read_dataset(path: Path, dataset_id: int) -> dict[str, Any]:
    """Select the exact site.dataset.datasetid before decoding any outcome."""
    if type(dataset_id) is not int or dataset_id <= 0:
        raise ValueError("Positive selected dataset identity required")
    array = _member(path.read_bytes(), "rows")
    if array is None or not array.startswith(b"["):
        raise ValueError("Source part rows are missing")
    position = 1
    selected = []
    while position < len(array):
        position = _space(array, position)
        if array[position] == 93:
            break
        if array[position] == 44:
            position = _space(array, position + 1)
        end = _end(array, position)
        row = array[position:end]
        position = end
        site = _member(row, "site")
        dataset = _member(site, "dataset") if site is not None else None
        identity = _member(dataset, "datasetid") if dataset is not None else None
        if (
            identity is not None
            and re.fullmatch(rb"[1-9][0-9]*", identity)
            and identity == str(dataset_id).encode()
        ):
            selected.append(json.loads(row))
    if len(selected) != 1:
        raise ValueError("Unique selected dataset required")
    return {"rows": selected}
