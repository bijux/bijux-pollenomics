"""Scientific interval, uncertainty, and serialization contracts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import cast

import pytest
from bijux_pollenomics.collection.sources.landclim import time_windows

from tests.support.geography import NORDIC_TEST_BBOX, SWEDEN_BOUNDARIES
from tests.support.workbooks import write_landclim_ii_zip


def _representative_feature() -> dict[str, object]:
    return time_windows._temporal_grid_feature(
        dataset_id="937075",
        cell_id="GC001",
        cell_label="17.5E 59.5N",
        time_window="0-100 BP",
        country="Sweden",
        geometry={
            "type": "Polygon",
            "coordinates": [
                [
                    [17.0, 59.0],
                    [18.0, 59.0],
                    [18.0, 60.0],
                    [17.0, 60.0],
                    [17.0, 59.0],
                ]
            ],
        },
        provenance_path="data/landclim/raw/source.zip",
        provenance_locator="means/TW01.csv",
        value_unit="percentage_cover",
    )


def test_representative_feature_serialization_and_bp_interval_are_frozen() -> None:
    feature = _representative_feature()
    payload = (
        json.dumps(feature, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()
    properties = feature["properties"]
    assert isinstance(properties, dict)
    assert (properties["time_start_bp"], properties["time_end_bp"]) == (0, 100)
    assert properties["time_mean_bp"] == 50
    assert hashlib.sha256(payload).hexdigest() == (
        "a84c415733cc6c2102978587ab199c31ac4c1572ed00ebd7ec7ab22ce13bc8d8"
    )


def test_missing_uncertainty_is_refused_with_exact_evidence_identity() -> None:
    with pytest.raises(ValueError) as caught:
        time_windows._require_uncertainty_pair(
            {"Picea": 0.2},
            {},
            dataset_id="900966",
            record_id="GC1:0-100 BP",
        )
    assert str(caught.value) == (
        "LandClim estimate/standard-error variables differ for dataset 900966 "
        "record GC1:0-100 BP: missing=['Picea'], unexpected=[]"
    )


def test_absent_and_non_numeric_values_remain_absent_not_zero() -> None:
    assert (
        time_windows._numeric_mapping(
            {"LCGRID_ID": "GC1", "Picea": "", "Pinus": "not-numeric"},
            excluded={"LCGRID_ID"},
        )
        == {}
    )


def test_in_scope_landclim_ii_row_requires_joined_quality(
    tmp_path: Path,
) -> None:
    archive_path = tmp_path / "reveals.zip"
    write_landclim_ii_zip(
        archive_path,
        [
            {
                "LCGRID_ID": "GC001",
                "lonDD": "17.5",
                "latDD": "59.5",
                "PICEA": "0",
            }
        ],
        time_window_count=1,
    )

    with pytest.raises(
        ValueError,
        match=(
            "LandClim II quality is missing or invalid for in-scope record "
            "GC001:0-100 BP"
        ),
    ):
        time_windows._merge_landclim_ii_time_windows(
            {},
            archive_path,
            quality_by_grid={},
            bbox=NORDIC_TEST_BBOX,
            country_boundaries=cast(dict[str, dict[str, object]], SWEDEN_BOUNDARIES),
        )


def test_valid_quality_row_preserves_true_numeric_zero(tmp_path: Path) -> None:
    archive_path = tmp_path / "reveals.zip"
    write_landclim_ii_zip(
        archive_path,
        [
            {
                "LCGRID_ID": "GC001",
                "lonDD": "17.5",
                "latDD": "59.5",
                "PICEA": "0",
            }
        ],
        time_window_count=1,
    )
    features: dict[tuple[str, str, str], dict[str, object]] = {}

    time_windows._merge_landclim_ii_time_windows(
        features,
        archive_path,
        quality_by_grid={"GC001": {"0-100 BP": "high"}},
        bbox=NORDIC_TEST_BBOX,
        country_boundaries=cast(dict[str, dict[str, object]], SWEDEN_BOUNDARIES),
    )

    properties = cast(
        dict[str, object], features[("937075", "GC001", "0-100 BP")]["properties"]
    )
    reconstruction = cast(dict[str, float], properties["reconstruction_values"])
    assert reconstruction["PICEA"] == 0.0
    assert properties["quality_class"] == "high"
