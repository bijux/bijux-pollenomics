"""Lossless copies of source-owned payload fragments."""

from __future__ import annotations

import copy
from collections.abc import Mapping


def copy_source_payload_excluding(
    payload: Mapping[str, object], *keys: str
) -> dict[str, object]:
    return {
        key: copy.deepcopy(value) for key, value in payload.items() if key not in keys
    }
