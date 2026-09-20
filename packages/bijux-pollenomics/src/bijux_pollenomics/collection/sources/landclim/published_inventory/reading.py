"""Read the exact paired LandClim II published mean/SE archive."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal, InvalidOperation
import hashlib
from pathlib import Path
from zipfile import BadZipFile, ZipFile

from ..catalog import (
    LANDCLIM_DATASET_METADATA,
    LANDCLIM_II_MEANS_DIRECTORY,
    LANDCLIM_II_STANDARD_ERRORS_DIRECTORY,
    time_window_sort_key,
)
from ..collection.model import LandClimRawReceiptError
from ..collection.receipt.validation import validate_landclim_raw_receipt
from ..time_windows.landclim_ii_rows import (
    _read_landclim_ii_standard_errors,
)
from ..time_windows.values import _require_uncertainty_pair
from .contracts import (
    LandClimPublishedEstimate,
    LandClimPublishedEstimateInventory,
    LandClimPublishedEstimateRow,
    LandClimPublishedInventoryRefusal,
    _mint_inventory,
)
from .source_rows import (
    _read_source_table,
    _require_existing_standard_error_parser,
    _SourceRow,
    _SourceTable,
)

_RECEIPT = "landclim_sources.json"
_ARCHIVE = "landclim_ii_reveals_results.zip"
_RECEIPT_SHA256 = "eb4350724c176d0dbcb7e441f2d21489bdae1cfff7ebe3088eab27093f315677"
_ARCHIVE_SHA256 = "c585f0691ad95342b8aba083b90fe91dc398f985b6b7fbc19561299389c4fb86"
_DATASET_DOI = "https://doi.org/10.1594/PANGAEA.937075"
_EXPECTED_WINDOWS = (
    "0-100 BP",
    "100-350 BP",
    "350-700 BP",
    "700-1200 BP",
    "1200-1700 BP",
    "1700-2200 BP",
    "2200-2700 BP",
    "2700-3200 BP",
    "3200-3700 BP",
    "3700-4200 BP",
    "4200-4700 BP",
    "4700-5200 BP",
    "5200-5700 BP",
    "5700-6200 BP",
    "6200-6700 BP",
    "6700-7200 BP",
    "7200-7700 BP",
    "7700-8200 BP",
    "8200-8700 BP",
    "8700-9200 BP",
    "9200-9700 BP",
    "9700-10200 BP",
    "10200-10700 BP",
    "10700-11200 BP",
    "11200-11700 BP",
)
_EXPECTED_RECORD_COUNT = 10500
_EXPECTED_VARIABLE_COUNT = 47
_EXPECTED_VALUE_PAIR_COUNT = 493500
_EXPECTED_COORDINATE_AVAILABLE = 10350
_EXPECTED_COORDINATE_REFUSED = 150
_EXPECTED_COORDINATE_REFUSED_IDS = 6
_EXPECTED_MEAN_ZEROS = 251123
_EXPECTED_MEANS_ABOVE_ONE = 138862
_EXPECTED_NEGATIVE_MEANS = 3
_EXPECTED_NEGATIVE_MEAN_ROWS = 2


def read_landclim_published_inventory(
    raw_dir: Path,
) -> LandClimPublishedEstimateInventory:
    """Authenticate every paired published estimate and uncertainty value."""
    return _read_landclim_published_inventory(
        raw_dir,
        expected_receipt_sha256=_RECEIPT_SHA256,
        expected_archive_sha256=_ARCHIVE_SHA256,
    )


def reopen_landclim_published_inventory(
    canonical_bytes: bytes, raw_dir: Path
) -> LandClimPublishedEstimateInventory:
    """Reconstruct from pinned raw parents and require exact canonical bytes."""
    if type(canonical_bytes) is not bytes:
        raise LandClimPublishedInventoryRefusal(
            "LandClim published inventory canonical payload must be exact bytes"
        )
    product = read_landclim_published_inventory(raw_dir)
    if product.canonical_bytes != canonical_bytes:
        raise LandClimPublishedInventoryRefusal(
            "LandClim published inventory does not match its raw inputs"
        )
    return product


def _read_landclim_published_inventory(
    raw_dir: Path,
    *,
    expected_receipt_sha256: str,
    expected_archive_sha256: str,
) -> LandClimPublishedEstimateInventory:
    raw_dir = Path(raw_dir)
    receipt_path = raw_dir / _RECEIPT
    archive_path = raw_dir / _ARCHIVE
    before_receipt = _pinned_digest(receipt_path, expected_receipt_sha256, "receipt")
    before_archive = _pinned_digest(
        archive_path, expected_archive_sha256, "published archive"
    )
    try:
        validate_landclim_raw_receipt(raw_dir)
        with ZipFile(archive_path) as archive:
            parsed_standard_errors = _read_landclim_ii_standard_errors(archive)
            means = _read_source_table(
                archive,
                prefix=LANDCLIM_II_MEANS_DIRECTORY,
                value_kind="mean",
                require_nonnegative=False,
            )
            standard_errors = _read_source_table(
                archive,
                prefix=LANDCLIM_II_STANDARD_ERRORS_DIRECTORY,
                value_kind="standard-error",
                require_nonnegative=True,
            )
            _require_existing_standard_error_parser(
                standard_errors, parsed_standard_errors
            )
            product = _build_inventory(
                means,
                standard_errors,
                receipt_sha256=before_receipt,
                archive_sha256=before_archive,
            )
    except LandClimPublishedInventoryRefusal:
        raise
    except (BadZipFile, LandClimRawReceiptError, OSError, ValueError) as error:
        raise LandClimPublishedInventoryRefusal(
            f"LandClim published inventory source refused: {error}"
        ) from error
    if _pinned_digest(receipt_path, before_receipt, "receipt") != before_receipt:
        raise LandClimPublishedInventoryRefusal(
            "LandClim receipt changed while reading published outputs"
        )
    if (
        _pinned_digest(archive_path, before_archive, "published archive")
        != before_archive
    ):
        raise LandClimPublishedInventoryRefusal(
            "LandClim published archive changed while reading"
        )
    return product


def _build_inventory(
    means: _SourceTable,
    standard_errors: _SourceTable,
    *,
    receipt_sha256: str,
    archive_sha256: str,
) -> LandClimPublishedEstimateInventory:
    variables = _require_table_closure(means, standard_errors)
    records = tuple(
        _paired_row(key, means.rows[key], standard_errors.rows[key], variables)
        for key in sorted(
            means.rows,
            key=lambda item: (
                time_window_sort_key(item[0]),
                means.rows[item].source_row,
            ),
        )
    )
    statistics = _statistics(records)
    _require_expected_denominators(records, variables, statistics)
    return _mint_inventory(
        receipt_sha256=receipt_sha256,
        archive_sha256=archive_sha256,
        dataset_doi=_dataset_doi(),
        time_windows=_EXPECTED_WINDOWS,
        variables=variables,
        records=records,
        coordinate_available_record_count=statistics["coordinate_available"],
        coordinate_refused_record_count=statistics["coordinate_refused"],
        mean_zero_value_count=statistics["mean_zero"],
        mean_above_one_value_count=statistics["mean_above_one"],
        mean_negative_value_count=statistics["mean_negative"],
        mean_negative_record_count=statistics["negative_records"],
    )


def _require_table_closure(
    means: _SourceTable, standard_errors: _SourceTable
) -> tuple[str, ...]:
    expected_windows = set(_EXPECTED_WINDOWS)
    for table, kind in ((means, "mean"), (standard_errors, "standard-error")):
        if set(table.headers_by_window) != expected_windows:
            raise LandClimPublishedInventoryRefusal(
                f"LandClim {kind} window universe is incomplete"
            )
    if means.headers_by_window != standard_errors.headers_by_window:
        raise LandClimPublishedInventoryRefusal(
            "LandClim mean/standard-error headers differ"
        )
    if set(means.rows) != set(standard_errors.rows):
        raise LandClimPublishedInventoryRefusal(
            "LandClim mean/standard-error row universes differ"
        )
    first_window = _EXPECTED_WINDOWS[0]
    variables = means.variables_by_window[first_window]
    if len(variables) != _EXPECTED_VARIABLE_COUNT:
        raise LandClimPublishedInventoryRefusal(
            "LandClim published variable denominator is not 47"
        )
    if any(value != variables for value in means.variables_by_window.values()):
        raise LandClimPublishedInventoryRefusal(
            "LandClim mean variable order changes between windows"
        )
    if means.variables_by_window != standard_errors.variables_by_window:
        raise LandClimPublishedInventoryRefusal(
            "LandClim mean/standard-error variable orders differ"
        )
    return variables


def _paired_row(
    key: tuple[str, str],
    mean_row: _SourceRow,
    standard_error_row: _SourceRow,
    variables: tuple[str, ...],
) -> LandClimPublishedEstimateRow:
    if mean_row.cell_id != standard_error_row.cell_id or key[1] != mean_row.cell_id:
        raise LandClimPublishedInventoryRefusal(
            f"LandClim paired row identity differs: {key}"
        )
    if (
        mean_row.longitude_float != standard_error_row.longitude_float
        or mean_row.latitude_float != standard_error_row.latitude_float
    ):
        raise LandClimPublishedInventoryRefusal(
            f"LandClim paired coordinate tokens differ: {key}"
        )
    _require_uncertainty_pair(
        mean_row.parsed_values,
        standard_error_row.parsed_values,
        dataset_id="937075",
        record_id=f"{key[1]}:{key[0]}",
    )
    estimates = tuple(
        LandClimPublishedEstimate(
            variable=variable,
            mean_token=mean_token,
            mean=_decimal(mean_token, "mean", key, variable),
            standard_error_token=standard_error_token,
            standard_error=_decimal(
                standard_error_token, "standard-error", key, variable
            ),
        )
        for variable, mean_token, standard_error_token in zip(
            variables,
            mean_row.value_tokens,
            standard_error_row.value_tokens,
            strict=True,
        )
    )
    missing = mean_row.longitude_token == mean_row.latitude_token == "#N/A"
    longitude = None if missing else _decimal_coordinate(mean_row.longitude_token)
    latitude = None if missing else _decimal_coordinate(mean_row.latitude_token)
    if not missing and (
        longitude is None
        or latitude is None
        or not Decimal("-180") <= longitude <= Decimal("180")
        or not Decimal("-90") <= latitude <= Decimal("90")
    ):
        raise LandClimPublishedInventoryRefusal(
            f"LandClim paired coordinates are outside WGS84: {key}"
        )
    return LandClimPublishedEstimateRow(
        time_window=key[0],
        cell_id=key[1],
        mean_cell_id_token=mean_row.cell_id_token,
        standard_error_cell_id_token=standard_error_row.cell_id_token,
        mean_source_locator=(
            f"{_ARCHIVE}#{mean_row.member_name}!row={mean_row.source_row}"
        ),
        standard_error_source_locator=(
            f"{_ARCHIVE}#{standard_error_row.member_name}!row="
            f"{standard_error_row.source_row}"
        ),
        mean_longitude_token=mean_row.longitude_token,
        mean_latitude_token=mean_row.latitude_token,
        standard_error_longitude_token=standard_error_row.longitude_token,
        standard_error_latitude_token=standard_error_row.latitude_token,
        longitude=longitude,
        latitude=latitude,
        coordinate_status="refused" if missing else "available",
        coordinate_refusal_reason="published_coordinates_missing" if missing else None,
        estimates=estimates,
    )


def _decimal(token: str, kind: str, key: tuple[str, str], variable: str) -> Decimal:
    try:
        value = Decimal(token)
    except InvalidOperation as error:
        raise LandClimPublishedInventoryRefusal(
            f"LandClim {kind} token is invalid: {key}: {variable}"
        ) from error
    if not value.is_finite() or (kind == "standard-error" and value < 0):
        raise LandClimPublishedInventoryRefusal(
            f"LandClim {kind} value is invalid: {key}: {variable}"
        )
    return value


def _decimal_coordinate(token: str) -> Decimal | None:
    try:
        value = Decimal(token)
    except InvalidOperation:
        return None
    return value if value.is_finite() else None


def _statistics(
    records: tuple[LandClimPublishedEstimateRow, ...],
) -> dict[str, int]:
    negative_record_keys: set[tuple[str, str]] = set()
    refused_ids: set[str] = set()
    result = {
        "coordinate_available": 0,
        "coordinate_refused": 0,
        "coordinate_refused_ids": 0,
        "mean_zero": 0,
        "mean_above_one": 0,
        "mean_negative": 0,
        "negative_records": 0,
    }
    for record in records:
        if record.coordinate_status == "available":
            result["coordinate_available"] += 1
        else:
            result["coordinate_refused"] += 1
            refused_ids.add(record.cell_id)
        for estimate in record.estimates:
            if estimate.mean == 0:
                result["mean_zero"] += 1
            if estimate.mean > 1:
                result["mean_above_one"] += 1
            if estimate.mean < 0:
                result["mean_negative"] += 1
                negative_record_keys.add((record.time_window, record.cell_id))
    result["coordinate_refused_ids"] = len(refused_ids)
    result["negative_records"] = len(negative_record_keys)
    return result


def _require_expected_denominators(
    records: tuple[LandClimPublishedEstimateRow, ...],
    variables: tuple[str, ...],
    statistics: Mapping[str, int],
) -> None:
    expected = {
        "record_count": _EXPECTED_RECORD_COUNT,
        "variable_count": _EXPECTED_VARIABLE_COUNT,
        "value_pair_count": _EXPECTED_VALUE_PAIR_COUNT,
        "coordinate_available": _EXPECTED_COORDINATE_AVAILABLE,
        "coordinate_refused": _EXPECTED_COORDINATE_REFUSED,
        "coordinate_refused_ids": _EXPECTED_COORDINATE_REFUSED_IDS,
        "mean_zero": _EXPECTED_MEAN_ZEROS,
        "mean_above_one": _EXPECTED_MEANS_ABOVE_ONE,
        "mean_negative": _EXPECTED_NEGATIVE_MEANS,
        "negative_records": _EXPECTED_NEGATIVE_MEAN_ROWS,
    }
    actual = {
        "record_count": len(records),
        "variable_count": len(variables),
        "value_pair_count": sum(len(record.estimates) for record in records),
        **statistics,
    }
    if actual != expected:
        raise LandClimPublishedInventoryRefusal(
            "LandClim published denominators differ: "
            f"expected={expected}, actual={actual}"
        )


def _pinned_digest(path: Path, expected: str, label: str) -> str:
    if not path.is_file() or path.is_symlink():
        raise LandClimPublishedInventoryRefusal(
            f"LandClim published {label} is missing or unsafe"
        )
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != _digest(expected, label):
        raise LandClimPublishedInventoryRefusal(
            f"LandClim published {label} digest does not match"
        )
    return actual


def _digest(value: str, label: str) -> str:
    if len(value) != 64 or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise LandClimPublishedInventoryRefusal(
            f"LandClim published {label} digest is invalid"
        )
    return value


def _dataset_doi() -> str:
    value = LANDCLIM_DATASET_METADATA["937075"]["doi"]
    if type(value) is not str or value != _DATASET_DOI:
        raise LandClimPublishedInventoryRefusal(
            "LandClim published dataset authority is invalid"
        )
    return value
