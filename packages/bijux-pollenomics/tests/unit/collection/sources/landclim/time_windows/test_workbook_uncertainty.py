"""Published mean and error columns must identify the same native taxa."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest

from bijux_pollenomics.collection.sources.landclim.time_windows.marquer import (
    _merge_marquer_time_windows,
)
from tests.support.geography import NORDIC_TEST_BBOX, SWEDEN_BOUNDARIES
from tests.support.workbooks import write_xlsx


def _merge(
    path: Path,
    means_header: list[object],
    errors_header: list[object],
    *,
    estimate: str = "0.25",
    mean_tail: list[object] | None = None,
    error_tail: list[object] | None = None,
) -> dict[tuple[str, str, str], dict[str, object]]:
    write_xlsx(
        path,
        {
            "Code time windows": [["Time", "Code"], ["0-100", "1"]],
            "Metadata": [
                ["Grid", "Label", "Type", "Latitude", "Longitude"],
                ["GC1", "Site", "Lake", "59.5", "17.5"],
            ],
            "REVEALS 36GCs": [
                means_header,
                ["GC1-1", estimate, "0.75", *(mean_tail or [])],
            ],
            "SE_REVEALS 36GCs": [
                errors_header,
                ["GC1-1", "0.01", "0.08", *(error_tail or [])],
            ],
        },
    )
    features: dict[tuple[str, str, str], dict[str, object]] = {}
    _merge_marquer_time_windows(
        features,
        path,
        bbox=NORDIC_TEST_BBOX,
        country_boundaries=cast(dict[str, dict[str, object]], SWEDEN_BOUNDARIES),
    )
    return features


@pytest.mark.parametrize(
    "errors_header", [["", "Pinus", "Picea"], ["", "Picea", "Betula"], ["", "Picea"]]
)
def test_error_column_identity_cannot_be_borrowed_from_mean_sheet(
    tmp_path: Path, errors_header: list[object]
) -> None:
    # Distinct 0.01/0.08 errors make relabeling a real scientific change.
    with pytest.raises(
        ValueError, match="Marquer estimate/standard-error headers differ"
    ):
        _merge(tmp_path / "column-identity.xlsx", ["", "Picea", "Pinus"], errors_header)


def test_duplicate_native_taxon_headers_do_not_collapse_to_one_variable(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="Marquer estimate headers are invalid"):
        _merge(
            tmp_path / "duplicate-taxon.xlsx",
            ["", "Picea", "Picea"],
            ["", "Picea", "Picea"],
        )


@pytest.mark.parametrize("estimate", ["0", "-0.0117533696932253"])
def test_valid_source_blank_identity_header_preserves_taxon_specific_errors(
    tmp_path: Path, estimate: str
) -> None:
    features = _merge(
        tmp_path / "valid-columns.xlsx",
        ["", "Picea", "Pinus"],
        ["", "Picea", "Pinus"],
        estimate=estimate,
    )
    assert set(features) == {("900966", "GC1", "0-100 BP")}
    properties = cast(
        dict[str, object], features[("900966", "GC1", "0-100 BP")]["properties"]
    )
    assert properties["reconstruction_values"] == {
        "Picea": float(estimate),
        "Pinus": 0.75,
    }
    assert properties["standard_errors"] == {"Picea": 0.01, "Pinus": 0.08}
    temporal = cast(dict[str, object], properties["temporal_semantics"])
    assert temporal["provenance_locator"] == "REVEALS 36GCs:GC1-1"


@pytest.mark.parametrize("trailing_blank_header", [False, True])
@pytest.mark.parametrize("populated_sheet", ["mean", "error", "both"])
def test_populated_undeclared_columns_cannot_disappear_from_a_source_pair(
    tmp_path: Path, trailing_blank_header: bool, populated_sheet: str
) -> None:
    headers: list[object] = ["", "Picea", "Pinus"]
    if trailing_blank_header:
        headers.append("")
    with pytest.raises(ValueError, match="populated cells beyond declared headers"):
        _merge(
            tmp_path / "undeclared-column.xlsx",
            headers,
            headers,
            mean_tail=["0.125"] if populated_sheet in {"mean", "both"} else [],
            error_tail=["0.0625"] if populated_sheet in {"error", "both"} else [],
        )


@pytest.mark.parametrize("padding", ["", " ", "\t"])
def test_empty_undeclared_padding_preserves_the_complete_source_pair(
    tmp_path: Path, padding: str
) -> None:
    features = _merge(
        tmp_path / "empty-padding.xlsx",
        ["", "Picea", "Pinus", ""],
        ["", "Picea", "Pinus", ""],
        mean_tail=[padding],
        error_tail=[padding],
    )
    properties = cast(
        dict[str, object], features[("900966", "GC1", "0-100 BP")]["properties"]
    )
    assert properties["reconstruction_values"] == {"Picea": 0.25, "Pinus": 0.75}
    assert properties["standard_errors"] == {"Picea": 0.01, "Pinus": 0.08}
