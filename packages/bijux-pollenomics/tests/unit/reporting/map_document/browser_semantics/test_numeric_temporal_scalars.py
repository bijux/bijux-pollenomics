"""Canonical map scalar readers agree without implicit source-text conversion."""

from __future__ import annotations

import json

import pytest

from bijux_pollenomics.reporting.map_document.temporal_admission import finite_number

from .support import run_node_json, template_block


@pytest.mark.parametrize(
    "value",
    [
        None,
        True,
        False,
        "",
        " ",
        "0",
        "0.25",
        "0x10",
        [],
        {},
        -0.25,
        float("inf"),
        float("nan"),
        10**1000,
        2**53 + 1,
    ],
)
def test_canonical_python_scalar_refuses_coercion_and_unsafe_conversion(
    value: object,
) -> None:
    assert finite_number(value) is None


def test_python_and_actual_browser_scalar_reader_agree_on_json_boundary() -> None:
    values: list[object] = [
        None,
        True,
        False,
        "",
        " ",
        "0",
        "0.25",
        "0x10",
        [],
        {},
        -0.25,
        0,
        0.25,
        10,
        100.75,
    ]
    block = template_block("function finiteTimeValue", "function valueIsAvailable")
    result = run_node_json(
        block
        + "\nconsole.log(JSON.stringify("
        + json.dumps(values)
        + ".map(finiteTimeValue)));"
    )
    assert result == [finite_number(value) for value in values]
    assert result[-4:] == [0, 0.25, 10, 100.75]
