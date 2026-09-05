"""Validated streaming normalization for the 25 source-authored CSV slices."""

from __future__ import annotations

import csv
from decimal import Decimal, InvalidOperation
import io
from pathlib import Path
from collections.abc import Iterator

from ..quarantine import (
    ArchiveInventory,
    ArchiveLimits,
    IntakeRefusal,
    inspected_zip_archive,
)
from .authority import (
    ADMITTED_CSV_MEMBERS,
    ARCHIVE_EXPANDED_BYTES,
    ARCHIVE_MEMBER_COUNT,
    ARCHIVE_SHA256,
    CSV_HEADERS,
    MODELED_CELL_COUNT,
    SOURCE_TIME_SLICES_BP,
    csv_member_path,
)
from .models import ModeledLandCoverCell, OpenLandSummary

_COMPOSITION_TOLERANCE = Decimal("0.000000001")


_ARCHIVE_LIMITS = ArchiveLimits(
    maximum_members=100,
    maximum_member_bytes=250_000_000,
    maximum_expanded_bytes=250_000_000,
    maximum_compression_ratio=10.0,
)


def _inspect(inventory: ArchiveInventory) -> None:
    if len(inventory.members) != ARCHIVE_MEMBER_COUNT:
        raise IntakeRefusal(
            "open_land_member_count_mismatch", str(len(inventory.members))
        )
    if inventory.expanded_bytes != ARCHIVE_EXPANDED_BYTES:
        raise IntakeRefusal(
            "open_land_expanded_size_mismatch", str(inventory.expanded_bytes)
        )
    paths = {member.path for member in inventory.members}
    missing = sorted(set(ADMITTED_CSV_MEMBERS) - paths)
    if missing:
        raise IntakeRefusal("open_land_csv_inventory_mismatch", ", ".join(missing))


def _decimal(value: str | None, *, field: str, locator: str) -> Decimal:
    if value is None or not value.strip():
        raise IntakeRefusal("missing_open_land_value", f"{locator} {field}")
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise IntakeRefusal("invalid_open_land_decimal", f"{locator} {field}") from exc
    if not result.is_finite():
        raise IntakeRefusal("invalid_open_land_decimal", f"{locator} {field}")
    return result


def _normalize_row(
    row: dict[str, str | None],
    *,
    member: str,
    member_sha256: str,
    row_number: int,
    age_bp: int,
) -> ModeledLandCoverCell:
    locator = f"{member}:{row_number}"
    raw = tuple(row.get(header) for header in CSV_HEADERS)
    if any(value is None for value in raw):
        raise IntakeRefusal("missing_open_land_value", locator)
    values = tuple(value for value in raw if value is not None)
    longitude, latitude, coniferous, broadleaved, open_land = (
        _decimal(row.get(header), field=header, locator=locator)
        for header in CSV_HEADERS
    )
    if not Decimal("-180") <= longitude <= Decimal("180"):
        raise IntakeRefusal("invalid_longitude", locator)
    if not Decimal("-90") <= latitude <= Decimal("90"):
        raise IntakeRefusal("invalid_latitude", locator)
    components = (coniferous, broadleaved, open_land)
    if any(value < 0 or value > 1 for value in components):
        raise IntakeRefusal("invalid_modeled_proportion", locator)
    if abs(sum(components) - Decimal(1)) > _COMPOSITION_TOLERANCE:
        raise IntakeRefusal("invalid_modeled_composition", locator)
    return ModeledLandCoverCell(
        source_member=member,
        source_member_sha256=member_sha256,
        source_row_number=row_number,
        time_slice_bp=age_bp,
        longitude_claim=longitude,
        latitude_claim=latitude,
        coniferous_proportion=coniferous,
        broadleaved_proportion=broadleaved,
        unforested_open_proportion=open_land,
        source_values=(values[0], values[1], values[2], values[3], values[4]),
    )


def iter_modeled_land_cover(path: Path) -> Iterator[ModeledLandCoverCell]:
    """Yield only exact source slices; never interpolate or assign countries."""
    with inspected_zip_archive(
        path, expected_sha256=ARCHIVE_SHA256, limits=_ARCHIVE_LIMITS
    ) as (inventory, archive):
        _inspect(inventory)
        members = {member.path: member for member in inventory.members}
        for age_bp in SOURCE_TIME_SLICES_BP:
            member = csv_member_path(age_bp)
            member_sha256 = members[member].content_sha256
            if member_sha256 is None:
                raise IntakeRefusal("open_land_member_digest_missing", member)
            with archive.open(member) as binary:
                text = io.TextIOWrapper(binary, encoding="utf-8-sig", newline="")
                reader = csv.DictReader(text)
                if tuple(reader.fieldnames or ()) != CSV_HEADERS:
                    raise IntakeRefusal("open_land_header_mismatch", member)
                for row_number, row in enumerate(reader, start=2):
                    yield _normalize_row(
                        row,
                        member=member,
                        member_sha256=member_sha256,
                        row_number=row_number,
                        age_bp=age_bp,
                    )


def summarize_open_land(path: Path) -> OpenLandSummary:
    """Reconcile row and spatial denominators without publishing values."""
    cells = iter_modeled_land_cover(path)
    count = 0
    longitudes: list[Decimal] = []
    latitudes: list[Decimal] = []
    for cell in cells:
        count += 1
        longitudes.append(cell.longitude_claim)
        latitudes.append(cell.latitude_claim)
    if count != MODELED_CELL_COUNT:
        raise IntakeRefusal("open_land_cell_count_mismatch", str(count))
    return OpenLandSummary(
        archive_sha256=ARCHIVE_SHA256,
        archive_member_count=ARCHIVE_MEMBER_COUNT,
        admitted_csv_count=len(ADMITTED_CSV_MEMBERS),
        modeled_cell_count=count,
        time_slices_bp=SOURCE_TIME_SLICES_BP,
        longitude_extent=(min(longitudes), max(longitudes)),
        latitude_extent=(min(latitudes), max(latitudes)),
    )
