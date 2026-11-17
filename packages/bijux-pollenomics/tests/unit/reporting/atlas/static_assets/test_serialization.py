"""Canonical identity hashing preserves bytes without a complete JSON buffer."""

from __future__ import annotations

import hashlib
import json
import tracemalloc
from typing import Any

import pytest

from bijux_pollenomics.reporting.map_document.static_assets import serialization


@pytest.mark.parametrize(
    "value",
    [
        None,
        True,
        False,
        0,
        1,
        -1,
        0.0,
        -0.0,
        1e-100,
        1e100,
        1.2345678901234567,
        [],
        {},
        "",
        {
            "unicode": "å漢字😀\ud800",
            "escaped": '\n\t"\\',
            "z": None,
            "a": [False, 0, 1.0, -0.0],
        },
        {"b": 2, "a": 1},
        ("tuple", 1),
        {1: "numeric-key"},
    ],
)
def test_digest_preserves_existing_canonical_bytes(value: Any) -> None:
    expected = json.dumps(
        value, ensure_ascii=True, allow_nan=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    assert (
        serialization._canonical_json_sha256(value)
        == hashlib.sha256(expected).hexdigest()
    )


@pytest.mark.parametrize(
    "value",
    [
        float("nan"),
        float("inf"),
        -float("inf"),
        {"x": float("nan")},
        {1: "one", "a": "a"},
        object(),
    ],
)
def test_digest_preserves_encoding_refusals(value: Any) -> None:
    with pytest.raises((ValueError, TypeError)) as original:
        serialization.canonical_json(value)
    with pytest.raises(type(original.value)):
        serialization._canonical_json_sha256(value)


def test_digest_preserves_circular_reference_refusal() -> None:
    value: list[Any] = []
    value.append(value)
    with pytest.raises(ValueError, match="Circular reference"):
        serialization._canonical_json_sha256(value)


def test_digest_allocation_does_not_scale_with_the_complete_encoding() -> None:
    value = [{"id": number, "label": "generated" * 20} for number in range(5000)]
    expected = hashlib.sha256(
        serialization.canonical_json(value).encode("utf-8")
    ).hexdigest()
    tracemalloc.start()
    try:
        actual = serialization._canonical_json_sha256(value)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert actual == expected
    assert peak < 128 * 1024
