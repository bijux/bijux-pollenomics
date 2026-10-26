"""Controlled original-token and native-identity laws without original data reads."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.abborrtjarnen_source_counts.sources import (
    AXES,
    classify_token,
    read_native,
    read_original,
)


def original_text(rows: list[tuple[str, ...]]) -> str:
    description = [
        "/* DATA DESCRIPTION:",
        "Giesecke, Thomas (2010): Pollen profile ABBO, Abborrtjärnen, Sweden",
        "doi:10.1594/PANGAEA.738429; archived on 2010-05-11; CC-BY-NC-3.0",
        "DEPTH, sediment/rock [m]",
        *[
            f"{axis.name} [#] ({axis.abbreviation}) * COMMENT: {axis.epd_comment}"
            for axis in AXES
        ],
        "*/",
        "\t".join(["Depth sed [m]", *[axis.column for axis in AXES]]),
        *["\t".join(row) for row in rows],
    ]
    return "\n".join(description) + "\n"


def native_document() -> dict[str, Any]:
    rows = []
    for sample_id, depth, values in (
        (10, 650, (1, 2, 3, 4, 5)),
        (20, 652, (2, 3, 4, 5)),
    ):
        rows.append(
            {
                "sampleid": sample_id,
                "depth": depth,
                "datum": [
                    {
                        "variablename": axis.name,
                        "taxonid": axis.native_id,
                        "units": "NISP",
                        "element": "pollen",
                        "elementtype": "pollen",
                        "value": n,
                    }
                    for axis, n in zip(AXES, values, strict=False)
                ],
            }
        )
    return {
        "status": "success",
        "data": [
            {
                "site": {
                    "siteid": 13338,
                    "collectionunit": {
                        "collectionunitid": 14910,
                        "handle": "ABBO",
                        "dataset": {
                            "datasetid": 19913,
                            "database": "European Pollen Database",
                            "doi": ["10.21233/2vzb-bg61"],
                            "samples": rows,
                        },
                    },
                }
            }
        ],
    }


@pytest.mark.parametrize(
    ("token", "state", "value", "reason"),
    [
        ("0", "explicit_zero", 0, None),
        (" 0.0 ", "explicit_zero", 0, None),
        ("2e1", "explicit_positive_integer", 20, None),
        ("", "blank", None, "empty_cell"),
        (" ", "blank", None, "empty_cell"),
        ("0.5", "invalid", None, "nonintegral_count"),
        ("-1", "invalid", None, "negative_count"),
        ("NaN", "invalid", None, "nonfinite_count"),
        ("inf", "invalid", None, "nonfinite_count"),
        ("<1", "invalid", None, "unparsed_count_token"),
    ],
)
def test_original_cell_states_preserve_count_meaning(
    token: str, state: str, value: int | None, reason: str | None
) -> None:
    assert classify_token(token) == (state, value, reason)


def test_original_schema_retains_morphological_comment_and_literal_blank() -> None:
    text = original_text([("6.50", "0", "2", "", "4", "5")])
    row = read_original(text).rows[0]
    assert row.depth_token == "6.50" and row.depth_m == Decimal("6.50")
    assert row.tokens == ("0", "2", "", "4", "5")
    with pytest.raises(ValueError, match="comment identity"):
        read_original(text.replace("Juniperus-type", "Juniperus communis"))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("value", True),
        ("value", 1.0),
        ("value", None),
        ("value", -1),
        ("taxonid", 29.0),
        ("variablename", "Renamed Betula"),
        ("units", "percent"),
        ("element", "spores"),
    ],
)
def test_native_selected_identity_cannot_masquerade_as_missing(
    field: str, value: Any
) -> None:
    source = deepcopy(native_document())
    source["data"][0]["site"]["collectionunit"]["dataset"]["samples"][0]["datum"][0][
        field
    ] = value
    with pytest.raises(ValueError, match="measurement identity/type"):
        read_native(source)


def test_native_absence_is_not_a_zero_record() -> None:
    rows = read_native(native_document())
    assert "Poaceae" not in rows[1].observed
    assert rows[1].observed == {
        "Betula": 2,
        "Cyperaceae": 3,
        "Juniperus communis": 4,
        "Pinus sylvestris": 5,
    }
