"""Bounded, non-evaluating reader for the exact ROOTSI metadata workbook."""

from __future__ import annotations

import io
from pathlib import PurePosixPath
import re
import stat
from typing import IO
import unicodedata
from xml.etree.ElementTree import Element
from zipfile import BadZipFile, ZipFile, ZipInfo

from defusedxml.ElementTree import fromstring  # type: ignore[import-untyped]

from ..quarantine import IntakeRefusal

_MAIN_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_CELL_REFERENCE = re.compile(r"(?P<column>[A-Z]+)[0-9]+")
_FORBIDDEN_PARTS = ("vbaproject.bin", "/embeddings/", "/externallinks/")
_MAXIMUM_MEMBERS = 1_000
_MAXIMUM_MEMBER_BYTES = 16_000_000
_MAXIMUM_EXPANDED_BYTES = 32_000_000
_MAXIMUM_COMPRESSION_RATIO = 100.0
_BUFFER_BYTES = 1024 * 1024


def _canonical_path(name: str) -> str:
    normalized = name.replace("\\", "/")
    path = PurePosixPath(normalized)
    if not normalized or path.is_absolute() or ".." in path.parts:
        raise IntakeRefusal("unsafe_workbook_path", name)
    if path.parts and path.parts[0].endswith(":"):
        raise IntakeRefusal("unsafe_workbook_path", name)
    return unicodedata.normalize("NFC", path.as_posix()).casefold()


def _validate_parts(infos: list[ZipInfo]) -> dict[str, ZipInfo]:
    if len(infos) > _MAXIMUM_MEMBERS:
        raise IntakeRefusal("workbook_member_limit", str(len(infos)))
    expanded = sum(info.file_size for info in infos)
    if expanded > _MAXIMUM_EXPANDED_BYTES:
        raise IntakeRefusal("workbook_expanded_size_limit", str(expanded))
    names = [info.filename for info in infos]
    if len(set(names)) != len(names):
        raise IntakeRefusal("duplicate_workbook_member", "member names repeat")
    canonical_paths = [_canonical_path(name) for name in names]
    if len(set(canonical_paths)) != len(canonical_paths):
        raise IntakeRefusal(
            "colliding_workbook_member", "normalized member names repeat"
        )
    for info, canonical in zip(infos, canonical_paths, strict=True):
        canonical_locator = f"/{canonical}"
        if any(marker in canonical_locator for marker in _FORBIDDEN_PARTS):
            raise IntakeRefusal("active_workbook_content", info.filename)
        unix_mode = (info.external_attr >> 16) & 0xFFFF
        file_type = stat.S_IFMT(unix_mode)
        if stat.S_ISLNK(unix_mode):
            raise IntakeRefusal("workbook_symlink", info.filename)
        if file_type and not (stat.S_ISREG(unix_mode) or stat.S_ISDIR(unix_mode)):
            raise IntakeRefusal("workbook_special_file", info.filename)
        if info.flag_bits & 1:
            raise IntakeRefusal("encrypted_workbook_member", info.filename)
        if info.file_size > _MAXIMUM_MEMBER_BYTES:
            raise IntakeRefusal("workbook_member_size_limit", info.filename)
        compressed = max(info.compress_size, 1)
        if info.file_size / compressed > _MAXIMUM_COMPRESSION_RATIO:
            raise IntakeRefusal("workbook_compression_ratio_limit", info.filename)
    return dict(zip(names, infos, strict=True))


def _read_part(archive: ZipFile, info: ZipInfo) -> bytes:
    result = io.BytesIO()
    copied = 0
    with archive.open(info) as source:
        while chunk := source.read(_BUFFER_BYTES):
            copied += len(chunk)
            if copied > info.file_size or copied > _MAXIMUM_MEMBER_BYTES:
                raise IntakeRefusal("workbook_output_size_limit", info.filename)
            result.write(chunk)
    if copied != info.file_size:
        raise IntakeRefusal("workbook_output_size_mismatch", info.filename)
    return result.getvalue()


def _shared_strings(archive: ZipFile, parts: dict[str, ZipInfo]) -> tuple[str, ...]:
    name = "xl/sharedStrings.xml"
    info = parts.get(name)
    if info is None:
        return ()
    root = fromstring(_read_part(archive, info))
    return tuple(
        "".join(text.text or "" for text in item.iter(f"{_MAIN_NS}t"))
        for item in root.findall(f"{_MAIN_NS}si")
    )


def _cell_value(cell: Element, shared: tuple[str, ...]) -> str | None:
    if cell.find(f"{_MAIN_NS}f") is not None:
        raise IntakeRefusal("workbook_formula_not_supported", cell.get("r", "?"))
    value = cell.find(f"{_MAIN_NS}v")
    raw = value.text if value is not None else None
    if cell.get("t") == "inlineStr":
        inline = cell.find(f"{_MAIN_NS}is")
        return (
            "".join(text.text or "" for text in inline.iter(f"{_MAIN_NS}t"))
            if inline is not None
            else None
        )
    if cell.get("t") == "s" and raw is not None:
        try:
            return shared[int(raw)]
        except (IndexError, ValueError) as exc:
            raise IntakeRefusal("invalid_shared_string_reference", raw) from exc
    return raw


def read_first_worksheet(stream: IO[bytes]) -> tuple[dict[str, str | None], ...]:
    """Read source cell text from an already identity-bound stream."""
    try:
        stream.seek(0)
        with ZipFile(stream) as archive:
            parts = _validate_parts(archive.infolist())
            shared = _shared_strings(archive, parts)
            sheet_name = "xl/worksheets/sheet1.xml"
            info = parts.get(sheet_name)
            if info is None:
                raise IntakeRefusal("metadata_worksheet_missing", sheet_name)
            root = fromstring(_read_part(archive, info))
    except BadZipFile as exc:
        raise IntakeRefusal("invalid_ooxml_workbook", str(exc)) from exc
    rows: list[dict[str, str | None]] = []
    for row in root.findall(f".//{_MAIN_NS}row"):
        values: dict[str, str | None] = {}
        for cell in row.findall(f"{_MAIN_NS}c"):
            reference = cell.get("r", "")
            match = _CELL_REFERENCE.fullmatch(reference)
            if match is None:
                raise IntakeRefusal("invalid_cell_reference", reference)
            column = match.group("column")
            if column in values:
                raise IntakeRefusal("duplicate_cell_reference", reference)
            values[column] = _cell_value(cell, shared)
        rows.append(values)
    return tuple(rows)
