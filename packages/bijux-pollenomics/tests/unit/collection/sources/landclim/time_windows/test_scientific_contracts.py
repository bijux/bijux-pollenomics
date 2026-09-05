"""Scientific interval, uncertainty, and serialization contracts."""

from __future__ import annotations

import hashlib
import json

import pytest

from bijux_pollenomics.collection.sources.landclim import time_windows


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
