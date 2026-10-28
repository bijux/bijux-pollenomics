"""Preserve physical BIFF layout and formula/reference presence without evaluation."""

from __future__ import annotations

import codecs
from collections.abc import Sequence
from dataclasses import dataclass
import hashlib
import io
import struct
from typing import Protocol, TextIO, cast

MAX_SOURCE_BYTES = 32 * 1024**2
MAX_RECORDS = 1_000_000
BOF = 0x0809
EOF = 0x000A
FORMULA = 0x0006
REFERENCE_RECORDS = frozenset((0x0023, 0x0017, 0x01AE))


class DirectoryEntry(Protocol):
    """Pinned container directory fields used to reject stream aliases."""

    name: str
    parent: int
    etype: int
    tot_size: int


class CompoundBook(Protocol):
    """Container streams only; cached worksheet decoding is outside this boundary."""

    @property
    def dirlist(self) -> Sequence[DirectoryEntry]:
        """Expose physical directory entries for stream ownership checks."""
        ...

    def get_named_stream(self, name: str) -> bytes | None:
        """Return the named raw stream without interpreting cell formulas."""
        ...


class CompoundDecoder(Protocol):
    """Caller-pinned read-only CFB decoder with diagnostics retained."""

    def __call__(self, payload: bytes, *, logfile: TextIO) -> CompoundBook:
        """Decode one bounded container while retaining diagnostics."""
        ...


@dataclass(frozen=True)
class Record:
    """Private physical record position and opaque source bytes."""

    offset: int
    code: int
    payload: bytes

    def identity(self) -> dict[str, object]:
        """Bind opaque payload bytes without publishing or executing tokens."""
        return {
            "stream_offset": self.offset,
            "record_code": self.code,
            "payload_bytes": len(self.payload),
            "payload_sha256": hashlib.sha256(self.payload).hexdigest(),
        }


def require(condition: bool, reason: str) -> None:
    """Retain explicit refusals under optimized Python execution."""
    if not condition:
        raise ValueError("native_biff_" + reason)


def _substream(
    stream: bytes, start: int, stop: int, kind: int
) -> tuple[list[Record], int]:
    require(0 <= start < stop <= len(stream), "substream_bounds")
    records: list[Record] = []
    position = start
    while position < stop:
        require(position + 4 <= stop, "truncated_record_header")
        code, size = struct.unpack_from("<HH", stream, position)
        end = position + 4 + size
        require(end <= stop and size <= 8224, "record_bounds")
        record = Record(position, code, stream[position + 4 : end])
        if not records:
            require(code == BOF and size >= 4, "missing_bof")
            version, actual_kind = struct.unpack_from("<HH", record.payload)
            require(
                version in (0x0500, 0x0600) and actual_kind == kind, "unsupported_bof"
            )
        else:
            require(code != BOF, "nested_bof")
        require(code != 0x002F, "encrypted_filepass")
        records.append(record)
        require(len(records) <= MAX_RECORDS, "record_budget")
        position = end
        if code == EOF:
            require(size == 0, "invalid_eof")
            return records, position
    raise ValueError("native_biff_missing_eof")


def _sheet_name(payload: bytes, version: int, codepage: int | None) -> tuple[str, str]:
    require(len(payload) >= 7, "truncated_boundsheet")
    count = payload[6]
    require(0 < count <= 31, "sheet_name_length")
    if version == 0x0600:
        require(len(payload) >= 8 and payload[7] in (0, 1), "unicode_name_flags")
        encoding = "utf-16-le" if payload[7] else "latin1"
        raw = payload[8:]
        require(len(raw) == count * (2 if payload[7] else 1), "sheet_name_bounds")
    else:
        raw = payload[7:]
        require(len(raw) == count, "sheet_name_bounds")
        if all(value < 128 for value in raw):
            encoding = "ascii"
        else:
            require(
                codepage is not None and codepage != 1200, "legacy_codepage_unresolved"
            )
            encoding = "mac_roman" if codepage == 10000 else "cp" + str(codepage)
    try:
        codecs.lookup(encoding)
        name = raw.decode(encoding)
    except (LookupError, UnicodeError) as exc:
        raise ValueError("native_biff_sheet_name_decode") from exc
    require(bool(name) and "\x00" not in name, "invalid_sheet_name")
    return name, encoding


def parse_biff_stream(stream: bytes) -> dict[str, object]:
    """Inspect BIFF5/7 or BIFF8 records; preserve opaque tokens and reference records.

    BIFF5 and BIFF7 share the 0x0500 BOF grammar and are not distinguished by
    that field alone. BIFF8 sheet names use compressed or UTF-16 Unicode,
    independent of workbook CODEPAGE. No cached cell rectangle is decoded.
    """
    require(
        isinstance(stream, bytes) and 0 < len(stream) <= MAX_SOURCE_BYTES,
        "stream_budget",
    )
    global_records, global_end = _substream(stream, 0, len(stream), 0x0005)
    version = struct.unpack_from("<H", global_records[0].payload)[0]
    codepages = [record for record in global_records if record.code == 0x0042]
    require(
        len(codepages) <= 1 and all(len(record.payload) == 2 for record in codepages),
        "ambiguous_codepage",
    )
    codepage = struct.unpack("<H", codepages[0].payload)[0] if codepages else None
    bounds = [record for record in global_records if record.code == 0x0085]
    require(bool(bounds) and len(bounds) <= 65536, "boundsheet_count")
    sheets: list[dict[str, object]] = []
    offsets: set[int] = set()
    names: set[str] = set()
    for ordinal, record in enumerate(bounds):
        require(len(record.payload) >= 7, "truncated_boundsheet")
        offset, visibility, sheet_kind = struct.unpack_from("<IBB", record.payload)
        require(visibility in (0, 1, 2) and sheet_kind in (0, 1, 2, 6), "sheet_flags")
        require(
            global_end <= offset < len(stream) and offset not in offsets, "sheet_offset"
        )
        name, encoding = _sheet_name(record.payload, version, codepage)
        require(name.casefold() not in names, "duplicate_sheet_name")
        names.add(name.casefold())
        offsets.add(offset)
        sheets.append(
            {
                "sheet_ordinal": ordinal,
                "sheet_name": name,
                "sheet_visibility_code": visibility,
                "sheet_type_code": sheet_kind,
                "native_sheet_offset": offset,
                "sheet_name_encoding": encoding,
                "boundsheet_record": record.identity(),
            }
        )
    ordered = sorted(offsets)
    require(not any(stream[global_end : ordered[0]]), "unclaimed_global_gap")
    formula_records: list[dict[str, object]] = []
    references: list[dict[str, object]] = []
    for record in global_records:
        require(record.code not in (FORMULA, 0x0206, 0x0406), "formula_in_globals")
        if record.code in REFERENCE_RECORDS:
            references.append({"scope": "workbook_globals", **record.identity()})
    total_records = len(global_records)
    bof_kind = {0: 0x0010, 1: 0x0040, 2: 0x0020, 6: 0x0006}
    for sheet in sheets:
        offset = cast(int, sheet["native_sheet_offset"])
        stop = (
            ordered[ordered.index(offset) + 1] if offset != ordered[-1] else len(stream)
        )
        records, end = _substream(
            stream, offset, stop, bof_kind[cast(int, sheet["sheet_type_code"])]
        )
        sheet_version = struct.unpack_from("<H", records[0].payload)[0]
        sheet["native_bof_version"] = sheet_version
        require(not any(stream[end:stop]), "unclaimed_sheet_gap")
        total_records += len(records)
        require(total_records <= MAX_RECORDS, "record_budget")
        positions: set[tuple[int, int]] = set()
        for record in records:
            require(record.code not in (0x0206, 0x0406), "unsupported_formula_opcode")
            if record.code == FORMULA:
                require(
                    cast(int, sheet["sheet_type_code"]) in (0, 1), "formula_sheet_kind"
                )
                require(len(record.payload) >= 22, "truncated_formula")
                row, column = struct.unpack_from("<HH", record.payload)
                tokens = struct.unpack_from("<H", record.payload, 20)[0]
                require(
                    row < (16384 if sheet_version == 0x0500 else 65536)
                    and column < 256
                    and tokens <= len(record.payload) - 22,
                    "formula_bounds",
                )
                require((row, column) not in positions, "duplicate_formula_cell")
                positions.add((row, column))
                formula_records.append(
                    {
                        "sheet_ordinal": sheet["sheet_ordinal"],
                        "row_0based": row,
                        "column_0based": column,
                        "token_bytes_declared": tokens,
                        **record.identity(),
                    }
                )
            if record.code in REFERENCE_RECORDS:
                references.append(
                    {
                        "scope": "sheet",
                        "sheet_ordinal": sheet["sheet_ordinal"],
                        **record.identity(),
                    }
                )
    return {
        "schema_version": "quarantined-rootsi-physical-biff.v1",
        "native_bof_version": version,
        "biff_grammar": "BIFF5_or_7" if version == 0x0500 else "BIFF8",
        "native_codepage_record": codepage,
        "mixed_bof_versions": any(
            sheet["native_bof_version"] != version for sheet in sheets
        ),
        "stream_bytes": len(stream),
        "stream_sha256": hashlib.sha256(stream).hexdigest(),
        "physical_record_count": total_records,
        "all_boundsheets": sheets,
        "formula_record_presence": formula_records,
        "reference_record_presence": references,
        "formula_evaluation": "never",
        "cached_cells_decoded": 0,
        "formula_tokens_interpreted": False,
        "external_reference_targets": "unresolved",
        "malware_or_macro_absence_certified": False,
        "scientific_admission": "refused",
    }


def physical_biff_structure(
    payload: bytes, decoder: CompoundDecoder
) -> dict[str, object]:
    """Read one bounded CFB3 stream with strict alias and decoder diagnostics posture."""
    require(
        isinstance(payload, bytes) and 512 <= len(payload) <= MAX_SOURCE_BYTES,
        "source_budget",
    )
    require(payload[:8] == bytes.fromhex("d0cf11e0a1b11ae1"), "unsupported_container")
    require(payload[28:30] == b"\xfe\xff", "container_byte_order")
    version = struct.unpack_from("<H", payload, 26)[0]
    sector, mini = struct.unpack_from("<HH", payload, 30)
    require(
        version == 3 and sector == 9 and mini == 6 and len(payload) % 512 == 0,
        "unsupported_container_extent",
    )
    log = io.StringIO()
    try:
        book = decoder(payload, logfile=log)
        require(not log.getvalue(), "container_decoder_diagnostics")
        aliases = [
            entry
            for entry in book.dirlist
            if entry.parent == 0 and entry.name.casefold() in ("workbook", "book")
        ]
        require(
            len(aliases) == 1 and aliases[0].etype == 2, "ambiguous_workbook_stream"
        )
        entry = aliases[0]
        require(0 < entry.tot_size <= MAX_SOURCE_BYTES, "container_stream_budget")
        stream = book.get_named_stream(entry.name)
        if not isinstance(stream, bytes) or len(stream) != entry.tot_size:
            raise ValueError("native_biff_container_stream_bounds")
        require(not log.getvalue(), "container_decoder_diagnostics")
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("native_biff_container_decode_failed") from exc
    result = parse_biff_stream(stream)
    result.update(
        {
            "container_source_sha256": hashlib.sha256(payload).hexdigest(),
            "container_bytes": len(payload),
            "native_stream_name": entry.name,
            "container_decoder": "caller-pinned xlrd CompDoc; not independent malware certification",
        }
    )
    return result
