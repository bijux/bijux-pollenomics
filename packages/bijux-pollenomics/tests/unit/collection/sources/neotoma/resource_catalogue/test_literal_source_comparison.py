"""Literal source metadata comparison preserves JSON representation distinctions."""

import pytest

from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.source_projection import (
    _same,
    same_source_json,
)


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        ({"a": 1, "b": ["x", None]}, {"b": ["x", None], "a": 1}, True),
        (True, 1, False),
        (1, 1.0, False),
        (0.0, -0.0, False),
        ({"x": "\ud800"}, {"x": "\ud800"}, True),
        ({"x": "\ud800"}, {"x": "\ud801"}, False),
        ([1, 2], [2, 1], False),
        ("é", "e\u0301", False),
    ],
)
def test_source_json_comparison(left: object, right: object, expected: bool) -> None:
    assert same_source_json(left, right) is expected


@pytest.mark.parametrize(
    ("value", "exception"),
    [
        (float("nan"), ValueError),
        (float("inf"), ValueError),
        (object(), TypeError),
        ({"x": 1, 2: 3}, TypeError),
    ],
)
def test_source_json_comparison_refuses_non_json_values(
    value: object, exception: type[Exception]
) -> None:
    with pytest.raises(exception):
        same_source_json(value, value)


def test_legacy_source_comparison_alias_preserves_existing_owner() -> None:
    assert _same is same_source_json
