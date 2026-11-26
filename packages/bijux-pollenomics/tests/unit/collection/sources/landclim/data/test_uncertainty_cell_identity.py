"""Mean and standard errors must refer to the same native decimal cell."""

from decimal import Decimal
from pathlib import Path
from zipfile import ZipFile

import pytest

from bijux_pollenomics.collection.sources.landclim.catalog import (
    LANDCLIM_II_MEANS_DIRECTORY,
    LANDCLIM_II_STANDARD_ERRORS_DIRECTORY,
)
from bijux_pollenomics.collection.sources.landclim.published_inventory.contracts import (
    LandClimPublishedEstimateRow,
    LandClimPublishedInventoryRefusal,
)
from bijux_pollenomics.collection.sources.landclim.published_inventory.reading import (
    _paired_row,
)
from bijux_pollenomics.collection.sources.landclim.published_inventory.source_rows import (
    _read_source_table,
)
from tests.support.workbooks import write_landclim_ii_zip
from tests.unit.collection.sources.landclim.data.test_quality_correspondence import (
    _project,
    _quality,
)


def _archive(
    tmp_path: Path,
    error_longitude: str,
    error_latitude: str = "59.5",
    mean_longitude: str = "17.5",
    mean_latitude: str = "59.5",
) -> Path:
    original = tmp_path / "original.zip"
    result = tmp_path / "results.zip"
    write_landclim_ii_zip(
        original,
        [
            {
                "LCGRID_ID": "GC001",
                "lonDD": mean_longitude,
                "latDD": mean_latitude,
                "PICEA": "0.12",
            }
        ],
    )
    with ZipFile(original) as source, ZipFile(result, "w") as target:
        for name in source.namelist():
            raw = source.read(name)
            if name.startswith(LANDCLIM_II_STANDARD_ERRORS_DIRECTORY):
                raw = raw.replace(
                    f"GC001,{mean_longitude},{mean_latitude}".encode(),
                    f"GC001,{error_longitude},{error_latitude}".encode(),
                )
            target.writestr(name, raw)
    return result


def _inventory_pair(path: Path) -> LandClimPublishedEstimateRow:
    with ZipFile(path) as archive:
        means = _read_source_table(
            archive,
            prefix=LANDCLIM_II_MEANS_DIRECTORY,
            value_kind="mean",
            require_nonnegative=False,
        )
        errors = _read_source_table(
            archive,
            prefix=LANDCLIM_II_STANDARD_ERRORS_DIRECTORY,
            value_kind="standard-error",
            require_nonnegative=True,
        )
    key = next(iter(means.rows))
    return _paired_row(key, means.rows[key], errors.rows[key], ("PICEA",))


@pytest.mark.parametrize("consumer", ["temporal", "inventory"])
@pytest.mark.parametrize(
    "error_longitude,error_latitude",
    [("17.500000000000000001", "59.5"), ("17.5", "59.500000000000000001")],
)
def test_distinct_source_decimals_cannot_pair_after_float_rounding(
    tmp_path: Path, consumer: str, error_longitude: str, error_latitude: str
) -> None:
    path = _archive(tmp_path, error_longitude, error_latitude)
    if consumer == "temporal":
        quality = _quality(tmp_path / "quality.xlsx", "17.5", "59.5")
        with pytest.raises(ValueError, match="coordinates differ"):
            _project(path, quality, "temporal")
    else:
        with pytest.raises(
            LandClimPublishedInventoryRefusal, match="coordinate tokens differ"
        ):
            _inventory_pair(path)


def test_equal_decimal_spellings_pair_in_both_consumers(tmp_path: Path) -> None:
    path = _archive(tmp_path, "17.5000")
    quality = _quality(tmp_path / "quality.xlsx", "17.5", "59.5")
    assert len(_project(path, quality, "temporal")) == 1
    assert _inventory_pair(path).estimates[0].standard_error == Decimal("0.01")


def test_published_missing_coordinates_remain_unavailable(tmp_path: Path) -> None:
    path = _archive(tmp_path, "#N/A", "#N/A", "#N/A", "#N/A")
    quality = _quality(tmp_path / "quality.xlsx", "17.5", "59.5")
    assert _project(path, quality, "temporal") == {}
    assert _inventory_pair(path).coordinate_status == "refused"


def test_out_of_scope_row_still_requires_matching_coordinates(tmp_path: Path) -> None:
    path = _archive(tmp_path, "1.000000000000000001", "59.5", "1", "59.5")
    quality = _quality(tmp_path / "quality.xlsx", "17.5", "59.5")
    with pytest.raises(ValueError, match="coordinates differ"):
        _project(path, quality, "temporal")
