"""Fail-closed normalization of pinned SpatioCompoMixed modeled exports."""

from __future__ import annotations

import csv
import hashlib
import io
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ..quarantine import IntakeRefusal
from .authority import (
    EXPECTED_ROWS_PER_SLICE,
    SOURCE_ATTRIBUTION,
    SOURCE_CITATION_DOI,
    SOURCE_COMMIT,
    SOURCE_DATA_LICENSE,
    SOURCE_REPOSITORY,
    expected_header,
)
from .models import (
    ExportFileAuthority,
    ModeledHumanLandUseCell,
    ModeledHumanLandUseSlice,
)

_COMPOSITION_TOLERANCE = Decimal("0.000000001")
_EQUATION_TOLERANCE = Decimal("0.000000001")


def _decimal(value: str, *, locator: str) -> Decimal:
    if not value.strip():
        raise IntakeRefusal("missing_spatiocompo_value", locator)
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise IntakeRefusal("invalid_spatiocompo_decimal", locator) from exc
    if not result.is_finite():
        raise IntakeRefusal("invalid_spatiocompo_decimal", locator)
    return result


def _validate_proportions(values: tuple[Decimal, ...], *, locator: str) -> None:
    if any(value < 0 or value > 1 for value in values):
        raise IntakeRefusal("invalid_spatiocompo_proportion", locator)


def _validate_scientific_relationships(
    values: tuple[Decimal, ...], *, locator: str
) -> None:
    lcc_c, lcc_b, lcc_u, nlc_c, nlc_b, nlc_o, hlu = values
    if abs(lcc_c + lcc_b + lcc_u - 1) > _COMPOSITION_TOLERANCE:
        raise IntakeRefusal("invalid_spatiocompo_lcc_composition", locator)
    if abs(nlc_c + nlc_b + nlc_o - 1) > _COMPOSITION_TOLERANCE:
        raise IntakeRefusal("invalid_spatiocompo_nlc_composition", locator)
    expected = (
        nlc_c * (1 - hlu),
        nlc_b * (1 - hlu),
        nlc_o * (1 - hlu) + hlu,
    )
    if any(
        abs(observed - derived) > _EQUATION_TOLERANCE
        for observed, derived in zip(values[:3], expected, strict=True)
    ):
        raise IntakeRefusal("invalid_spatiocompo_land_use_equation", locator)


def _cell(
    row: list[str], *, row_number: int, authority: ExportFileAuthority
) -> ModeledHumanLandUseCell:
    locator = f"{authority.relative_path}:{row_number}"
    longitude = _decimal(row[0], locator=f"{locator} Lon")
    latitude = _decimal(row[1], locator=f"{locator} Lat")
    if not Decimal(-180) <= longitude <= Decimal(180):
        raise IntakeRefusal("invalid_spatiocompo_longitude", locator)
    if not Decimal(-90) <= latitude <= Decimal(90):
        raise IntakeRefusal("invalid_spatiocompo_latitude", locator)
    values = tuple(
        _decimal(value, locator=f"{locator} column {column}")
        for column, value in enumerate(row[2:], start=3)
    )
    _validate_proportions(values, locator=locator)
    _validate_scientific_relationships(values, locator=locator)
    return ModeledHumanLandUseCell(
        source_relative_path=authority.relative_path,
        source_file_sha256=authority.sha256,
        source_git_blob_sha=authority.git_blob_sha,
        source_row_number=row_number,
        source_values=tuple(row),
        period_key=authority.period.key,
        period_label=authority.period.label,
        oldest_to_present_index=authority.period.oldest_to_present_index,
        model_variant=authority.variant.key,
        model_covariate_posture=authority.variant.covariate_posture,
        longitude_claim=longitude,
        latitude_claim=latitude,
        lcc_coniferous_proportion=values[0],
        lcc_broadleaved_proportion=values[1],
        lcc_unforested_proportion=values[2],
        nlc_coniferous_proportion=values[3],
        nlc_broadleaved_proportion=values[4],
        nlc_open_proportion=values[5],
        human_land_use_proportion=values[6],
        source_repository=SOURCE_REPOSITORY,
        source_commit=SOURCE_COMMIT,
        source_citation_doi=SOURCE_CITATION_DOI,
        source_data_license=SOURCE_DATA_LICENSE,
        attribution_requirement=SOURCE_ATTRIBUTION,
    )


def _grid_digest(coordinates: frozenset[tuple[Decimal, Decimal]]) -> str:
    canonical = "".join(
        f"{longitude.normalize()}\t{latitude.normalize()}\n"
        for longitude, latitude in sorted(coordinates)
    )
    return hashlib.sha256(canonical.encode("ascii")).hexdigest()


def normalize_export_file(
    path: Path,
    authority: ExportFileAuthority,
    *,
    expected_grid: frozenset[tuple[Decimal, Decimal]] | None = None,
) -> ModeledHumanLandUseSlice:
    """Normalize one exact source export without variant substitution."""
    if not path.is_file() or path.is_symlink():
        raise IntakeRefusal("missing_or_unsafe_spatiocompo_export", str(path))
    payload = path.read_bytes()
    if len(payload) != authority.size_bytes:
        raise IntakeRefusal("spatiocompo_size_mismatch", authority.relative_path)
    if hashlib.sha256(payload).hexdigest() != authority.sha256:
        raise IntakeRefusal("spatiocompo_digest_mismatch", authority.relative_path)
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise IntakeRefusal(
            "invalid_spatiocompo_encoding", authority.relative_path
        ) from exc
    reader = csv.reader(io.StringIO(text, newline=""), strict=True)
    try:
        header = tuple(next(reader))
    except StopIteration as exc:
        raise IntakeRefusal(
            "empty_spatiocompo_export", authority.relative_path
        ) from exc
    except csv.Error as exc:
        raise IntakeRefusal("invalid_spatiocompo_csv", authority.relative_path) from exc
    if header != expected_header(authority):
        raise IntakeRefusal("spatiocompo_header_mismatch", authority.relative_path)
    if authority.upstream_status == "known_corrupt_refused":
        raise IntakeRefusal(
            "upstream_spatiocompo_slice_known_corrupt",
            f"{authority.observed_valid_row_count} valid rows, "
            f"{authority.observed_malformed_row_count} malformed row, expected "
            f"{EXPECTED_ROWS_PER_SLICE}; variant substitution prohibited",
        )
    cells: list[ModeledHumanLandUseCell] = []
    coordinates: set[tuple[Decimal, Decimal]] = set()
    try:
        for row_number, row in enumerate(reader, start=2):
            if len(row) != 9:
                raise IntakeRefusal(
                    "spatiocompo_column_count_mismatch",
                    f"{authority.relative_path}:{row_number} expected 9 got {len(row)}",
                )
            cell = _cell(row, row_number=row_number, authority=authority)
            coordinate = (cell.longitude_claim, cell.latitude_claim)
            if coordinate in coordinates:
                raise IntakeRefusal("duplicate_spatiocompo_coordinate", str(coordinate))
            coordinates.add(coordinate)
            cells.append(cell)
    except csv.Error as exc:
        raise IntakeRefusal("invalid_spatiocompo_csv", authority.relative_path) from exc
    if len(cells) != EXPECTED_ROWS_PER_SLICE:
        raise IntakeRefusal("spatiocompo_row_count_mismatch", str(len(cells)))
    frozen_grid = frozenset(coordinates)
    if expected_grid is not None and frozen_grid != expected_grid:
        raise IntakeRefusal(
            "spatiocompo_coordinate_grid_mismatch", authority.relative_path
        )
    return ModeledHumanLandUseSlice(
        authority=authority,
        coordinate_grid_sha256=_grid_digest(frozen_grid),
        cells=tuple(cells),
    )


__all__ = ["normalize_export_file"]
