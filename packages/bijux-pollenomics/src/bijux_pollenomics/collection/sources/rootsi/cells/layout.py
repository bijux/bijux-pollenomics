"""Native worksheet layout sidecars without changing retained typed-cell evidence."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol, cast

from .decoding import Cell, Parser
from .inputs import read_bytes
from .models import WorkbookInput, integer, refuse, text
from .projection import source_id


class LayoutSheet(Protocol):
    """Pinned xlrd public layout surface, including hidden worksheets."""

    name: str
    nrows: int
    ncols: int
    visibility: int
    merged_cells: list[tuple[int, int, int, int]]

    def cell(self, rowx: int, colx: int) -> Cell: ...


class LayoutBook(Protocol):
    """Source date mode and recorded character decoding authority."""

    datemode: int
    codepage: int | None
    encoding: str | None

    def sheets(self) -> list[LayoutSheet]: ...

    def release_resources(self) -> None: ...


def worksheet_layout_records(
    item: WorkbookInput, archive_sha256: str, decoder: Parser
) -> Iterator[dict[str, object]]:
    """Preserve every decoded sheet's layout; visibility never selects observations.

    This sidecar leaves the historical typed-cell schema unchanged. Values are
    stored decoder outputs, with no formula recalculation, recovered formula
    provenance, physical BIFF record census or external-link interpretation.
    """
    payload = read_bytes(item.path, item.sha256, item.byte_count)
    try:
        book = cast(
            LayoutBook,
            decoder.open_workbook(file_contents=payload, formatting_info=True),
        )
    except Exception as exc:
        refuse(
            "workbook_decode_failed",
            f"{item.archive_member}: {type(exc).__name__}: {exc}",
        )
    try:
        mode = integer(book.datemode, "date_mode")
        if mode not in (0, 1):
            refuse("invalid_date_mode", str(mode))
        codepage = book.codepage
        if codepage is not None:
            integer(codepage, "codepage")
        encoding = book.encoding
        if encoding is not None:
            text(encoding, "encoding")
        identity = source_id(archive_sha256, item.archive_member, item.sha256)
        names: set[str] = set()
        for ordinal, sheet in enumerate(book.sheets()):
            name = text(sheet.name, "sheet_name")
            if name in names:
                refuse("invalid_sheet_name", name)
            names.add(name)
            visibility = integer(sheet.visibility, "sheet_visibility")
            if visibility not in (0, 1, 2):
                refuse("invalid_sheet_visibility", str(visibility))
            rows = integer(sheet.nrows, "nrows")
            columns = integer(sheet.ncols, "ncols")
            if rows > 65536 or columns > 256:
                refuse("unsupported_sheet_extent", f"{rows}x{columns}")
            merged = []
            for raw in sheet.merged_cells:
                bounds = [integer(value, "merged_bound") for value in raw]
                if len(bounds) != 4 or not (
                    bounds[0] < bounds[1] <= 65536 and bounds[2] < bounds[3] <= 256
                ):
                    refuse("merged_range", repr(bounds))
                merged.append(bounds)
            errors: dict[str, int] = {}
            for row in range(rows):
                for column in range(columns):
                    cell = sheet.cell(row, column)
                    if cell.ctype == 5:
                        code = str(integer(cell.value, "cached_error_code"))
                        errors[code] = errors.get(code, 0) + 1
            yield {
                "schema_version": "quarantined-rootsi-worksheet-layout.v1",
                **item.as_dict(),
                "workbook_id": identity,
                "excel_date_mode": mode,
                "codepage": codepage,
                "decoder_encoding": encoding,
                "sheet_ordinal": ordinal,
                "sheet_name": name,
                "sheet_visibility_code": visibility,
                "sheet_visibility": ("visible", "hidden", "very_hidden")[visibility],
                "nrows": rows,
                "ncols": columns,
                "rectangle_positions": rows * columns,
                "merged_ranges": merged,
                "cached_error_code_counts": errors,
                "cached_values_recalculated": False,
                "formula_origin": "unavailable",
                "physical_biff_record_presence": "unavailable",
                "external_link_presence": "not_inspected",
                "scientific_admission": "refused",
                "unit": "unreviewed",
                "chronology": "unreviewed",
                "taxonomy": "unreviewed",
            }
    finally:
        book.release_resources()
    read_bytes(item.path, item.sha256, item.byte_count)
