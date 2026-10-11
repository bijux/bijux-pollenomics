"""Optional pinned xlrd decoder; no formula execution or age conversion."""

from __future__ import annotations

from collections.abc import Iterator
import importlib
from importlib.metadata import PackageNotFoundError, version
from typing import Protocol, cast

from .inputs import read_bytes
from .models import PARSER_VERSION, WorkbookInput, integer, refuse
from .projection import cell_record, source_id


class Cell(Protocol):
    """Only the public decoded xlrd cell surface is consumed."""

    ctype: int
    value: object
    xf_index: int | None


class Sheet(Protocol):
    """Rectangular sheet and native layout claims."""

    name: str
    nrows: int
    ncols: int
    merged_cells: list[tuple[int, int, int, int]]

    def cell(self, rowx: int, colx: int) -> Cell:
        """Return an uncoerced decoded cell."""


class Book(Protocol):
    """Public workbook date mode, sheets and release contract."""

    datemode: int

    def sheets(self) -> list[Sheet]:
        """Return sheets in source order."""

    def release_resources(self) -> None:
        """Release parser-owned workbook resources."""


class Parser(Protocol):
    """The optional module boundary."""

    def open_workbook(self, *, file_contents: bytes, formatting_info: bool) -> Book:
        """Decode cached values and format information from exact workbook bytes."""


def parser() -> Parser:
    """Require the explicitly supported optional parser without a base dependency."""
    try:
        actual = version("xlrd")
        module = importlib.import_module("xlrd")
    except (PackageNotFoundError, ImportError) as exc:
        refuse("optional_parser_unavailable", f"install rootsi-review extra: {exc}")
    if actual != PARSER_VERSION:
        refuse("unsupported_parser_version", actual)
    return cast(Parser, module)


def workbook_records(
    item: WorkbookInput, archive_sha256: str, decoder: Parser
) -> Iterator[tuple[str, dict[str, object]]]:
    """Yield a workbook, all sheets and every decoded rectangle position."""
    payload = read_bytes(item.path, item.sha256, item.byte_count)
    try:
        book = decoder.open_workbook(file_contents=payload, formatting_info=True)
    except Exception as exc:
        refuse(
            "workbook_decode_failed",
            f"{item.archive_member}: {type(exc).__name__}: {exc}",
        )
    try:
        sheets = book.sheets()
        mode = integer(book.datemode, "date_mode")
        if mode not in (0, 1):
            refuse("invalid_date_mode", str(mode))
        identity = source_id(archive_sha256, item.archive_member, item.sha256)
        yield (
            "workbook",
            {
                **item.as_dict(),
                "workbook_id": identity,
                "excel_date_mode": mode,
                "sheet_count": len(sheets),
            },
        )
        names: set[str] = set()
        for ordinal, sheet in enumerate(sheets):
            if not isinstance(sheet.name, str) or not sheet.name or sheet.name in names:
                refuse("invalid_sheet_name", repr(sheet.name))
            names.add(sheet.name)
            rows = integer(sheet.nrows, "nrows")
            columns = integer(sheet.ncols, "ncols")
            if rows > 65536 or columns > 256:
                refuse("unsupported_sheet_extent", f"{rows}x{columns}")
            yield (
                "sheet",
                {
                    "workbook_id": identity,
                    "sheet_ordinal": ordinal,
                    "name": sheet.name,
                    "nrows": rows,
                    "ncols": columns,
                    "rectangle_positions": rows * columns,
                    "merged_ranges": [list(values) for values in sheet.merged_cells],
                },
            )
            for row in range(rows):
                for column in range(columns):
                    cell = sheet.cell(row, column)
                    yield (
                        "cell",
                        cell_record(
                            workbook_id=identity,
                            sheet_ordinal=ordinal,
                            row=row,
                            column=column,
                            cell_type=cell.ctype,
                            value=cell.value,
                            xf_index=cell.xf_index,
                        ),
                    )
    finally:
        book.release_resources()
    read_bytes(item.path, item.sha256, item.byte_count)
