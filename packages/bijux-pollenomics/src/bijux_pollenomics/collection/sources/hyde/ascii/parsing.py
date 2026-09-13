"""Bounded native ASCII grammar with original tokens and explicit nodata equality."""

from __future__ import annotations

import base64
from collections.abc import Iterator
from decimal import Decimal, InvalidOperation
import re
from typing import Protocol

from ...quarantine import IntakeRefusal
from .contracts import AsciiWindowLimits, AsciiWindowSelection, NativeAsciiHeader

_KEYS = {"ncols", "nrows", "xllcorner", "yllcorner", "cellsize", "nodata_value"}
_NUMBER = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[Ee][+-]?[0-9]+)?\Z")


class ReadStream(Protocol):
    def read(self, size: int = -1) -> bytes: ...
    def readline(self, size: int = -1) -> bytes: ...


def number(token: str, limits: AsciiWindowLimits) -> Decimal:
    if len(token) > limits.maximum_token_bytes or _NUMBER.fullmatch(token) is None:
        raise IntakeRefusal("hyde_ascii_numeric_token_invalid", token[:128])
    try:
        value = Decimal(token)
    except InvalidOperation as exc:
        raise IntakeRefusal("hyde_ascii_numeric_token_invalid", token[:128]) from exc
    if not value.is_finite():
        raise IntakeRefusal("hyde_ascii_numeric_token_invalid", token[:128])
    return value


def parse_header(stream: ReadStream, limits: AsciiWindowLimits) -> NativeAsciiHeader:
    content = bytearray()
    pairs = []
    values = {}
    for _ in range(6):
        line = stream.readline(limits.maximum_header_bytes - len(content) + 1)
        content.extend(line)
        if len(content) > limits.maximum_header_bytes:
            raise IntakeRefusal("hyde_ascii_header_limit", str(len(content)))
        try:
            pieces = line.decode("ascii").split()
        except UnicodeDecodeError as exc:
            raise IntakeRefusal(
                "hyde_ascii_header_invalid", "Non-ASCII header"
            ) from exc
        if len(pieces) != 2:
            raise IntakeRefusal(
                "hyde_ascii_header_invalid", "Six explicit keyword/value lines required"
            )
        keyword, token = pieces
        key = keyword.casefold()
        if key not in _KEYS or key in values:
            raise IntakeRefusal("hyde_ascii_header_invalid", keyword)
        number(token, limits)
        values[key] = token
        pairs.append((keyword, token))
    if set(values) != _KEYS or number(values["cellsize"], limits) <= 0:
        raise IntakeRefusal(
            "hyde_ascii_header_invalid",
            "Explicit corner origin, dimensions, positive step and nodata required",
        )
    dimensions = []
    for field in ("nrows", "ncols"):
        token = values[field]
        if re.fullmatch(r"[0-9]+", token) is None or int(token) <= 0:
            raise IntakeRefusal("hyde_ascii_header_invalid", field)
        dimensions.append(int(token))
    rows, columns = dimensions
    if rows * columns > limits.maximum_source_cells:
        raise IntakeRefusal("hyde_ascii_source_cell_limit", str(rows * columns))
    return NativeAsciiHeader(
        base64.b64encode(content).decode("ascii"), tuple(pairs), rows, columns
    )


def body_tokens(stream: ReadStream, limits: AsciiWindowLimits) -> Iterator[str]:
    """Carry at most one bounded partial token between bounded chunks."""
    carry = b""
    while chunk := stream.read(limits.chunk_bytes):
        block = carry + chunk
        values = block.split()
        carry = b"" if block[-1:] in b" \t\r\n\v\f" else values.pop()
        if len(carry) > limits.maximum_token_bytes:
            raise IntakeRefusal("hyde_ascii_token_limit", str(len(carry)))
        for value in values:
            if len(value) > limits.maximum_token_bytes:
                raise IntakeRefusal("hyde_ascii_token_limit", str(len(value)))
            try:
                yield value.decode("ascii")
            except UnicodeDecodeError as exc:
                raise IntakeRefusal(
                    "hyde_ascii_numeric_token_invalid", "Non-ASCII cell"
                ) from exc
    if carry:
        try:
            yield carry.decode("ascii")
        except UnicodeDecodeError as exc:
            raise IntakeRefusal(
                "hyde_ascii_numeric_token_invalid", "Non-ASCII cell"
            ) from exc


def select_cells(
    stream: ReadStream,
    header: NativeAsciiHeader,
    selection: AsciiWindowSelection,
    limits: AsciiWindowLimits,
) -> tuple[tuple[str, ...], tuple[bool, ...]]:
    if selection.row_stop > header.rows or selection.column_stop > header.columns:
        raise IntakeRefusal("hyde_ascii_window_outside_source", repr(selection))
    count = (selection.row_stop - selection.row_start) * (
        selection.column_stop - selection.column_start
    )
    if count > limits.maximum_selected_cells:
        raise IntakeRefusal("hyde_ascii_window_cell_limit", str(count))
    nodata = number(header.value("nodata_value"), limits)
    tokens = []
    missing = []
    observed = 0
    expected = header.rows * header.columns
    for index, token in enumerate(body_tokens(stream, limits)):
        if index >= expected:
            raise IntakeRefusal(
                "hyde_ascii_cell_count_mismatch", "Extra cells after complete grid"
            )
        value = number(token, limits)
        row, column = divmod(index, header.columns)
        if (
            selection.row_start <= row < selection.row_stop
            and selection.column_start <= column < selection.column_stop
        ):
            tokens.append(token)
            missing.append(value == nodata)
        observed += 1
    if observed != expected or len(tokens) != count:
        raise IntakeRefusal("hyde_ascii_cell_count_mismatch", f"{observed}/{expected}")
    return tuple(tokens), tuple(missing)
