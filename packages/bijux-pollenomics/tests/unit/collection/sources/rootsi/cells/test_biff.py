"""Physical source controls distinguish BIFF grammars and refuse ambiguous custody."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import struct
from typing import Any, TextIO

import pytest

from bijux_pollenomics.collection.sources.rootsi.cells.biff import (
    parse_biff_stream,
    physical_biff_structure,
)


def record(code: int, body: bytes = b"") -> bytes:
    return struct.pack("<HH", code, len(body)) + body


def source(
    version: int = 0x0600,
    name: str = "Sheet1",
    *,
    visible: int = 0,
    kind: int = 0,
    formula: bool = False,
    codepage: int | None = 1200,
    reference: bool = False,
) -> bytes:
    bof = record(0x0809, struct.pack("<HH", version, 5))
    page = record(0x0042, struct.pack("<H", codepage)) if codepage is not None else b""
    encoded = name.encode("utf-16-le") if version == 0x0600 else name.encode("cp1252")
    size = len(encoded) // 2 if version == 0x0600 else len(encoded)
    names = bytes([size, 1]) + encoded if version == 0x0600 else bytes([size]) + encoded
    tail = record(0x01AE, b"opaque-link-descriptor") if reference else b""
    bounds = record(0x0085, struct.pack("<IBB", 0, visible, kind) + names)
    offset = len(bof + page + bounds + tail + record(0x000A))
    bounds = record(0x0085, struct.pack("<IBB", offset, visible, kind) + names)
    form = (
        record(0x0006, struct.pack("<HHH8sHIH", 2, 3, 0, b"12345678", 0, 0, 1) + b"x")
        if formula
        else b""
    )
    sbof = record(
        0x0809, struct.pack("<HH", version, {0: 16, 1: 64, 2: 32, 6: 6}[kind])
    )
    return bof + page + bounds + tail + record(0x000A) + sbof + form + record(0x000A)


@pytest.mark.parametrize(
    ("version", "name", "codepage"),
    [(0x0500, "ASCII", None), (0x0500, "Ä", 1252), (0x0600, "Å😀", 1200)],
)
def test_native_name_grammar(version: int, name: str, codepage: int | None) -> None:
    row: Any = parse_biff_stream(source(version, name, codepage=codepage))
    assert row["all_boundsheets"][0]["sheet_name"] == name
    assert row["biff_grammar"] == ("BIFF5_or_7" if version == 0x0500 else "BIFF8")


@pytest.mark.parametrize("kind", [0, 1, 2, 6])
@pytest.mark.parametrize("visible", [0, 1, 2])
def test_preserve_all_sheet_types_and_visibility(kind: int, visible: int) -> None:
    row: Any = parse_biff_stream(source(kind=kind, visible=visible))
    assert row["all_boundsheets"][0]["sheet_type_code"] == kind
    assert row["all_boundsheets"][0]["sheet_visibility_code"] == visible
    assert row["cached_cells_decoded"] == 0


def test_formula_and_reference_records_are_opaque() -> None:
    row: Any = parse_biff_stream(source(formula=True, reference=True))
    formula = row["formula_record_presence"][0]
    assert (
        formula["row_0based"],
        formula["column_0based"],
        formula["token_bytes_declared"],
    ) == (2, 3, 1)
    assert len(formula["payload_sha256"]) == 64
    assert len(row["reference_record_presence"]) == 1
    assert row["external_reference_targets"] == "unresolved"
    assert row["formula_tokens_interpreted"] is False
    assert row["scientific_admission"] == "refused"


@pytest.mark.parametrize(
    "change",
    [
        lambda x: x[:3],
        lambda x: x[:-1],
        lambda x: x.replace(
            b"\x09\x08\x04\x00\x00\x06", b"\x09\x08\x04\x00\x00\x04", 1
        ),
        lambda x: x + b"not-padding",
    ],
)
def test_truncated_or_unsupported_stream_refuses(
    change: Callable[[bytes], bytes],
) -> None:
    with pytest.raises(ValueError, match="native_biff_"):
        parse_biff_stream(change(source()))


def test_duplicate_codepage_refuses() -> None:
    data = source()
    position = 8
    with pytest.raises(ValueError, match="ambiguous_codepage"):
        parse_biff_stream(
            data[:position] + record(0x0042, struct.pack("<H", 1200)) + data[position:]
        )


def test_nonascii_legacy_without_codepage_refuses() -> None:
    with pytest.raises(ValueError, match="legacy_codepage_unresolved"):
        parse_biff_stream(source(0x0500, "Ä", codepage=None))


@dataclass
class Entry:
    name: str
    parent: int = 0
    etype: int = 2
    tot_size: int = 0


class Container:
    def __init__(self, entries: list[Entry], stream: bytes) -> None:
        self.dirlist = entries
        self.stream = stream

    def get_named_stream(self, name: str) -> bytes:
        return self.stream


def cfb_header() -> bytes:
    data = bytearray(512)
    data[:8] = bytes.fromhex("d0cf11e0a1b11ae1")
    struct.pack_into("<HHHH", data, 26, 3, 0xFFFE, 9, 6)
    return bytes(data)


def test_ambiguous_container_alias_refuses() -> None:
    data = source()

    def decode(payload: bytes, *, logfile: TextIO) -> Container:
        return Container(
            [Entry("Book", tot_size=len(data)), Entry("Workbook", tot_size=len(data))],
            data,
        )

    with pytest.raises(ValueError, match="ambiguous_workbook_stream"):
        physical_biff_structure(cfb_header(), decode)


def test_container_stream_size_refuses() -> None:
    data = source()

    def decode(payload: bytes, *, logfile: TextIO) -> Container:
        return Container([Entry("Workbook", tot_size=len(data) + 1)], data)

    with pytest.raises(ValueError, match="container_stream_bounds"):
        physical_biff_structure(cfb_header(), decode)


def test_container_diagnostic_refuses() -> None:
    data = source()

    def decode(payload: bytes, *, logfile: TextIO) -> Container:
        logfile.write("decoder ignored damage")
        return Container([Entry("Workbook", tot_size=len(data))], data)

    with pytest.raises(ValueError, match="container_decoder_diagnostics"):
        physical_biff_structure(cfb_header(), decode)


def two_sheets(
    *, duplicate_name: bool = False, duplicate_offset: bool = False
) -> bytes:
    header = record(0x0809, struct.pack("<HH", 0x0600, 5))

    def bounds(name: str, offset: int) -> bytes:
        return record(
            0x0085,
            struct.pack("<IBB", offset, 0, 0)
            + bytes([len(name), 0])
            + name.encode("ascii"),
        )

    first = bounds("First", 0)
    second = bounds("FIRST" if duplicate_name else "Other", 0)
    offset = len(header + first + second + record(0x000A))
    sheet = record(0x0809, struct.pack("<HH", 0x0600, 16)) + record(0x000A)
    return (
        header
        + bounds("First", offset)
        + bounds(
            "FIRST" if duplicate_name else "Other",
            offset if duplicate_offset else offset + len(sheet),
        )
        + record(0x000A)
        + sheet
        + sheet
    )


def test_compressed_biff8_names_and_multiple_sheets() -> None:
    row: Any = parse_biff_stream(two_sheets())
    assert [s["sheet_name"] for s in row["all_boundsheets"]] == ["First", "Other"]
    assert all(s["sheet_name_encoding"] == "latin1" for s in row["all_boundsheets"])


@pytest.mark.parametrize(
    ("options", "reason"),
    [
        ({"duplicate_name": True}, "duplicate_sheet_name"),
        ({"duplicate_offset": True}, "sheet_offset"),
    ],
)
def test_boundsheet_aliases_refuse(options: dict[str, bool], reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        parse_biff_stream(two_sheets(**options))


def test_formula_token_bounds_refuse() -> None:
    data = bytearray(source(formula=True))
    position = data.find(struct.pack("<HH", 0x0006, 23))
    assert position >= 0
    struct.pack_into("<H", data, position + 4 + 20, 2)
    with pytest.raises(ValueError, match="formula_bounds"):
        parse_biff_stream(bytes(data))


def test_filepass_refuses_before_sheet_decoding() -> None:
    data = source()
    with pytest.raises(ValueError, match="encrypted_filepass"):
        parse_biff_stream(data[:8] + record(0x002F, b"opaque") + data[8:])


@pytest.mark.parametrize(
    "change",
    [
        lambda data: data[1:],
        lambda data: data[:28] + b"\xff\xfe" + data[30:],
        lambda data: data[:30] + struct.pack("<H", 12) + data[32:],
    ],
)
def test_cfb_signature_byteorder_and_extent_refuse(
    change: Callable[[bytes], bytes],
) -> None:
    def decode(payload: bytes, *, logfile: TextIO) -> Container:
        raise AssertionError("must refuse before container decode")

    with pytest.raises(ValueError, match="native_biff_"):
        physical_biff_structure(change(cfb_header()), decode)


def test_declared_container_stream_budget_refuses_before_read() -> None:
    class Oversized(Container):
        def get_named_stream(self, name: str) -> bytes:
            raise AssertionError("oversized stream must refuse before read")

    def decode(payload: bytes, *, logfile: TextIO) -> Oversized:
        return Oversized([Entry("Workbook", tot_size=32 * 1024**2 + 1)], b"")

    with pytest.raises(ValueError, match="container_stream_budget"):
        physical_biff_structure(cfb_header(), decode)


def test_legacy_formula_row_extent_refuses() -> None:
    data = bytearray(source(0x0500, "Sheet1", formula=True, codepage=1252))
    position = data.find(struct.pack("<HH", 0x0006, 23))
    assert position >= 0
    struct.pack_into("<H", data, position + 4, 16384)
    with pytest.raises(ValueError, match="formula_bounds"):
        parse_biff_stream(bytes(data))


def test_mixed_supported_bof_keeps_global_name_grammar() -> None:
    data = bytearray(source(0x0500, "Ä", codepage=1252))
    position = data.rfind(record(0x0809, struct.pack("<HH", 0x0500, 16)))
    assert position >= 0
    struct.pack_into("<H", data, position + 4, 0x0600)
    row: Any = parse_biff_stream(bytes(data))
    assert row["native_bof_version"] == 0x0500
    assert row["all_boundsheets"][0]["native_bof_version"] == 0x0600
    assert row["all_boundsheets"][0]["sheet_name"] == "Ä"
    assert row["all_boundsheets"][0]["sheet_name_encoding"] == "cp1252"
    assert row["mixed_bof_versions"] is True
    assert row["cached_cells_decoded"] == 0


@pytest.mark.parametrize(("version", "kind"), [(0x0400, 16), (0x0600, 32)])
def test_unsupported_local_bof_or_contradictory_type_refuses(
    version: int, kind: int
) -> None:
    data = bytearray(source())
    position = data.rfind(record(0x0809, struct.pack("<HH", 0x0600, 16)))
    assert position >= 0
    struct.pack_into("<HH", data, position + 4, version, kind)
    with pytest.raises(ValueError, match="unsupported_bof"):
        parse_biff_stream(bytes(data))
