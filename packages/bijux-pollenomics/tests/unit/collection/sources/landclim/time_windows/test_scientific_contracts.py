"""Scientific interval, uncertainty, and serialization contracts."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
from typing import cast
from zipfile import ZipFile

import pytest

from bijux_pollenomics.collection.sources.landclim import time_windows
from tests.support.geography import NORDIC_TEST_BBOX, SWEDEN_BOUNDARIES
from tests.support.workbooks import write_landclim_ii_zip

_MEANS_MEMBER = "LANDCLIMII.RV.means.JUN2021/TW1.RV.estimates.jun21.csv"
_ERRORS_MEMBER = "LANDCLIMII.RV.standarderrors.JUN2021/TW1.standarderrors.jun21.csv"


def _csv_payload(headers: list[str], rows: list[dict[str, str]]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=headers)
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def _write_published_pair(
    path: Path,
    *,
    mean_headers: list[str],
    mean_rows: list[dict[str, str]],
    error_headers: list[str] | None = None,
    error_rows: list[dict[str, str]] | None = None,
) -> None:
    with ZipFile(path, "w") as archive:
        archive.writestr(_MEANS_MEMBER, _csv_payload(mean_headers, mean_rows))
        archive.writestr(
            _ERRORS_MEMBER,
            _csv_payload(
                error_headers or mean_headers,
                mean_rows if error_rows is None else error_rows,
            ),
        )


def _merge_published_pair(path: Path) -> None:
    time_windows._merge_landclim_ii_time_windows(
        {},
        path,
        quality_by_grid={"GC001": {"0-100 BP": "high"}},
        bbox=NORDIC_TEST_BBOX,
        country_boundaries=cast(dict[str, dict[str, object]], SWEDEN_BOUNDARIES),
    )


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
        "b018bf99efa45b261a3dcf5416c3359fe82d51f19db316c0ab13648e96390f94"
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


def test_landclim_ii_refuses_duplicate_published_rows(tmp_path: Path) -> None:
    archive_path = tmp_path / "duplicate.zip"
    row = {
        "LCGRID_ID": "GC001",
        "lonDD": "17.5",
        "latDD": "59.5",
        "PICEA": "1.0",
    }
    write_landclim_ii_zip(archive_path, [row, row], time_window_count=1)

    with pytest.raises(ValueError, match=r"duplicate \(TW, LCGRID_ID\) row"):
        _merge_published_pair(archive_path)


def test_landclim_ii_refuses_different_paired_headers(tmp_path: Path) -> None:
    archive_path = tmp_path / "headers.zip"
    identity = {"LCGRID_ID": "GC001", "lonDD": "17.5", "latDD": "59.5"}
    _write_published_pair(
        archive_path,
        mean_headers=["LCGRID_ID", "lonDD", "latDD", "PICEA"],
        mean_rows=[{**identity, "PICEA": "1.0"}],
        error_headers=["LCGRID_ID", "lonDD", "latDD", "PINUS"],
        error_rows=[{**identity, "PINUS": "0.1"}],
    )

    with pytest.raises(ValueError, match="headers differ"):
        _merge_published_pair(archive_path)


def test_landclim_ii_refuses_extra_row_tokens(tmp_path: Path) -> None:
    archive_path = tmp_path / "tokens.zip"
    headers = "LCGRID_ID,lonDD,latDD,PICEA\n"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr(_MEANS_MEMBER, headers + "GC001,17.5,59.5,1.0,extra\n")
        archive.writestr(_ERRORS_MEMBER, headers + "GC001,17.5,59.5,0.1\n")

    with pytest.raises(ValueError, match="tokens do not match its headers"):
        _merge_published_pair(archive_path)


def test_landclim_ii_refuses_different_paired_coordinates(tmp_path: Path) -> None:
    archive_path = tmp_path / "coordinates.zip"
    headers = ["LCGRID_ID", "lonDD", "latDD", "PICEA"]
    _write_published_pair(
        archive_path,
        mean_headers=headers,
        mean_rows=[
            {
                "LCGRID_ID": "GC001",
                "lonDD": "17.5",
                "latDD": "59.5",
                "PICEA": "1.0",
            }
        ],
        error_rows=[
            {
                "LCGRID_ID": "GC001",
                "lonDD": "17.6",
                "latDD": "59.5",
                "PICEA": "0.1",
            }
        ],
    )

    with pytest.raises(ValueError, match="coordinates differ"):
        _merge_published_pair(archive_path)


def test_landclim_ii_validates_then_excludes_paired_published_missing_coordinates(
    tmp_path: Path,
) -> None:
    archive_path = tmp_path / "missing-coordinates.zip"
    headers = ["LCGRID_ID", "lonDD", "latDD", "PICEA"]
    missing = {"LCGRID_ID": "GC001", "lonDD": "#N/A", "latDD": "#N/A"}
    _write_published_pair(
        archive_path,
        mean_headers=headers,
        mean_rows=[{**missing, "PICEA": "1.0"}],
        error_rows=[{**missing, "PICEA": "0.1"}],
    )
    features: dict[tuple[str, str, str], dict[str, object]] = {}

    time_windows._merge_landclim_ii_time_windows(
        features,
        archive_path,
        quality_by_grid={},
        bbox=NORDIC_TEST_BBOX,
        country_boundaries=cast(dict[str, dict[str, object]], SWEDEN_BOUNDARIES),
    )

    assert features == {}


def test_landclim_ii_refuses_partial_or_unrecognized_missing_coordinates(
    tmp_path: Path,
) -> None:
    archive_path = tmp_path / "invalid-coordinates.zip"
    headers = ["LCGRID_ID", "lonDD", "latDD", "PICEA"]
    _write_published_pair(
        archive_path,
        mean_headers=headers,
        mean_rows=[
            {
                "LCGRID_ID": "GC001",
                "lonDD": "#N/A",
                "latDD": "59.5",
                "PICEA": "1.0",
            }
        ],
        error_rows=[
            {
                "LCGRID_ID": "GC001",
                "lonDD": "#N/A",
                "latDD": "59.5",
                "PICEA": "0.1",
            }
        ],
    )

    with pytest.raises(ValueError, match="identity is missing or invalid"):
        _merge_published_pair(archive_path)


@pytest.mark.parametrize(
    ("mean_token", "error_token"),
    [("", ""), ("not-a-number", "0.1"), ("1", "-0.1")],
)
def test_landclim_ii_refuses_missing_or_invalid_paired_tokens(
    tmp_path: Path, mean_token: str, error_token: str
) -> None:
    archive_path = tmp_path / "tokens.zip"
    headers = ["LCGRID_ID", "lonDD", "latDD", "PICEA"]
    identity = {"LCGRID_ID": "GC001", "lonDD": "17.5", "latDD": "59.5"}
    _write_published_pair(
        archive_path,
        mean_headers=headers,
        mean_rows=[{**identity, "PICEA": mean_token}],
        error_rows=[{**identity, "PICEA": error_token}],
    )

    with pytest.raises(ValueError, match="tokens are missing or invalid"):
        _merge_published_pair(archive_path)


def test_landclim_ii_preserves_finite_published_negative_mean(
    tmp_path: Path,
) -> None:
    archive_path = tmp_path / "signed-source-estimate.zip"
    headers = ["LCGRID_ID", "lonDD", "latDD", "PICEA"]
    identity = {"LCGRID_ID": "GC001", "lonDD": "17.5", "latDD": "59.5"}
    _write_published_pair(
        archive_path,
        mean_headers=headers,
        mean_rows=[{**identity, "PICEA": "-0.0117533696932253"}],
        error_rows=[{**identity, "PICEA": "0.1"}],
    )
    features: dict[tuple[str, str, str], dict[str, object]] = {}

    time_windows._merge_landclim_ii_time_windows(
        features,
        archive_path,
        quality_by_grid={"GC001": {"0-100 BP": "high"}},
        bbox=NORDIC_TEST_BBOX,
        country_boundaries=cast(dict[str, dict[str, object]], SWEDEN_BOUNDARIES),
    )

    [feature] = features.values()
    properties = cast(dict[str, object], feature["properties"])
    assert properties["reconstruction_values"] == {"PICEA": -0.0117533696932253}
    assert properties["standard_errors"] == {"PICEA": 0.1}


def test_landclim_ii_refuses_unpaired_row_denominators(tmp_path: Path) -> None:
    archive_path = tmp_path / "denominators.zip"
    headers = ["LCGRID_ID", "lonDD", "latDD", "PICEA"]
    first = {"LCGRID_ID": "GC001", "lonDD": "17.5", "latDD": "59.5"}
    second = {"LCGRID_ID": "GC002", "lonDD": "18.5", "latDD": "60.5"}
    _write_published_pair(
        archive_path,
        mean_headers=headers,
        mean_rows=[{**first, "PICEA": "1.0"}],
        error_rows=[
            {**first, "PICEA": "0.1"},
            {**second, "PICEA": "0.2"},
        ],
    )

    with pytest.raises(ValueError, match="row denominators differ"):
        _merge_published_pair(archive_path)
