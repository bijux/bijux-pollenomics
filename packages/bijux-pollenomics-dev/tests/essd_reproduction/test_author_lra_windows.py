"""Author time columns retain native axes and distinguish unavailable source rows."""

from __future__ import annotations

from copy import deepcopy
import inspect

import pytest

from bijux_pollenomics_dev.essd_reproduction.author_lra_development import (
    materialize_author_lra_development,
)
from bijux_pollenomics_dev.essd_reproduction.author_lra_windows import (
    selected_counts,
    source_window,
)

TAXA = ["taxon-" + str(index) for index in range(31)]


@pytest.fixture
def source_rows() -> list[list[str]]:
    labels = ["50", "225", "550", *[str(1000 + index * 500) for index in range(22)]]
    return [
        ["TW", *labels],
        ["radius", *["150"] * 25],
        ["model", *["2"] * 25],
        *[[taxon, *[str(index + 1)] * 25] for index, taxon in enumerate(TAXA)],
    ]


@pytest.mark.parametrize(
    ("index", "label", "younger", "older", "eligible"),
    [
        (4, "1000", 750, 1250, 13),
        (5, "1500", 1250, 1750, 15),
        (6, "2000", 1750, 2250, 14),
    ],
)
def test_calendar_bin_and_native_thirty_one_taxon_column(
    source_rows: list[list[str]],
    index: int,
    label: str,
    younger: int,
    older: int,
    eligible: int,
) -> None:
    window = source_window(index)
    assert window.label_bp == label and window.eligible_count == eligible
    assert window.temporal_bin == {
        "bin_id": "author-TW" + str(index),
        "younger_bp": younger,
        "older_bp": older,
    }
    assert selected_counts(source_rows, TAXA, "BECKHAM", 150.0, window) == (
        150.0,
        list(range(1, 32)),
    )


@pytest.mark.parametrize("index", [4, 5, 6])
def test_source_filled_unavailable_is_not_a_measured_zero(
    source_rows: list[list[str]], index: int
) -> None:
    window = source_window(index)
    for row in source_rows[1:]:
        row[index] = "0"
    assert selected_counts(source_rows, TAXA, "EXEBRID", 50.0, window) is None
    with pytest.raises(ValueError, match="unavailable window"):
        selected_counts(source_rows, TAXA, "BECKHAM", 150.0, window)


@pytest.mark.parametrize("identity", [True, 0, 3, 7, 4.0, "4"])
def test_only_declared_integer_windows_are_admitted(identity: object) -> None:
    with pytest.raises(ValueError):
        source_window(identity)  # type: ignore[arg-type]


def test_default_materializer_retains_the_original_time_column(
    source_rows: list[list[str]],
) -> None:
    assert (
        inspect.signature(materialize_author_lra_development)
        .parameters["window"]
        .default
        == 5
    )
    column = source_rows[0].index("1500")
    assert selected_counts(source_rows, TAXA, "BECKHAM", 150.0, source_window(5)) == (
        float(source_rows[1][column]),
        [int(row[column]) for row in source_rows[3:]],
    )


@pytest.mark.parametrize(
    "change",
    [
        "missing",
        "NA",
        "negative",
        "fraction",
        "short",
        "duplicate_label",
        "duplicate_taxon",
        "wrong_label_position",
        "radius",
        "zero_mask",
        "positive_mask",
        "model",
        "empty_with_geometry",
        "nonfinite_geometry",
    ],
)
def test_malformed_column_or_availability_contract_refuses(
    source_rows: list[list[str]], change: str
) -> None:
    table = deepcopy(source_rows)
    taxa = list(TAXA)
    site, radius = "BECKHAM", 150.0
    if change in {"missing", "NA", "negative", "fraction"}:
        table[3][5] = {"missing": "", "NA": "NA", "negative": "-1", "fraction": "1.5"}[
            change
        ]
    elif change == "short":
        table[2] = []
    elif change == "duplicate_label":
        table[0][4] = "1500"
    elif change == "duplicate_taxon":
        taxa[1] = taxa[0]
    elif change == "wrong_label_position":
        table[0][4], table[0][5] = table[0][5], table[0][4]
    elif change == "radius":
        radius = 50.0
    elif change == "positive_mask":
        site = "EXEBRID"
    elif change == "model":
        table[2][5] = "1"
    elif change == "nonfinite_geometry":
        radius = float("nan")
    else:
        for row in table[1:]:
            row[5] = "0"
        if change == "empty_with_geometry":
            table[1][5] = "150"
    with pytest.raises(ValueError):
        selected_counts(table, taxa, site, radius, source_window(5))
