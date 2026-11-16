"""Bounded native-container validation without scientific interpretation."""

from __future__ import annotations

import csv
from io import BytesIO, StringIO
from pathlib import PurePosixPath
import re
import stat
import struct
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile

from defusedxml import ElementTree  # type: ignore[import-untyped]

MAX_PAYLOAD = 32 * 1024 * 1024
MAX_MEMBER = 8 * 1024 * 1024
MAX_EXPANDED = 64 * 1024 * 1024


def validate_payload(filename: str, payload: bytes) -> None:
    """Require readable native XLSX, result ZIP or a rectangular UTF-8 CSV."""
    if not payload:
        raise ValueError(f"LandClim raw asset download was empty for {filename}")
    try:
        if len(payload) > MAX_PAYLOAD:
            raise ValueError("payload size limit")
        if filename.endswith((".xlsx", ".zip")):
            _container(payload, workbook=filename.endswith(".xlsx"))
        elif filename.endswith(".csv"):
            if not {
                "Plant taxa/Pollen-morphological types",
                "FSP (m/s)",
                "PPE (SD)",
            } <= set(_csv(payload)):
                raise ValueError("PPE CSV identifiers")
        else:
            raise ValueError("unsupported native format")
    except Exception as error:
        raise ValueError(
            f"LandClim raw asset format is invalid for {filename}: {error}"
        ) from error


def _csv(payload: bytes) -> list[str]:
    text = payload.decode("utf-8-sig")
    if "\x00" in text or text.lstrip().startswith("<"):
        raise ValueError("non-CSV response")
    rows = csv.reader(StringIO(text), strict=True)
    header = next(rows, [])
    if len(header) < 2 or not any(cell.strip() for cell in header):
        raise ValueError("missing CSV header")
    count = 0
    for row in rows:
        if row:
            if len(row) != len(header):
                raise ValueError("ragged CSV row")
            count += 1
    if not count:
        raise ValueError("missing CSV records")
    return header


def _container(payload: bytes, *, workbook: bool) -> None:
    end = payload.rfind(b"PK\x05\x06", max(0, len(payload) - 65557))
    if end < 0 or end + 22 > len(payload):
        raise ValueError("missing ZIP end record")
    _, disk, directory_disk, local_count, count, size, offset, comment = (
        struct.unpack_from("<4s4H2IH", payload, end)
    )
    if (
        disk
        or directory_disk
        or local_count != count
        or not 0 < count <= 1024
        or size > 2 * 1024 * 1024
        or offset + size != end
        or end + 22 + comment != len(payload)
        or payload[max(0, end - 20) : end - 16] == b"PK\x06\x07"
    ):
        raise ValueError("ZIP directory limit or unsupported layout")
    with ZipFile(BytesIO(payload)) as archive:
        members = archive.infolist()
        names = [member.filename for member in members]
        if not members or len(members) > 1024 or len(names) != len(set(names)):
            raise ValueError("container member inventory")
        if sum(member.file_size for member in members) > MAX_EXPANDED:
            raise ValueError("container expansion limit")
        for member in members:
            path = PurePosixPath(member.filename)
            mode = member.external_attr >> 16
            if (
                path.is_absolute()
                or ".." in path.parts
                or "\\" in member.filename
                or member.flag_bits & 1
                or member.compress_type not in (ZIP_STORED, ZIP_DEFLATED)
                or (
                    stat.S_IFMT(mode) and not (stat.S_ISREG(mode) or stat.S_ISDIR(mode))
                )
                or member.file_size > MAX_MEMBER
                or member.file_size > max(1, member.compress_size) * 1000
            ):
                raise ValueError("unsafe or oversized container member")
            if not member.is_dir():
                with archive.open(member) as stream:
                    while stream.read(64 * 1024):
                        pass
        if workbook:
            required = {"[Content_Types].xml", "xl/workbook.xml"}
            if not required <= set(names) or not any(
                name.startswith("xl/worksheets/") and name.endswith(".xml")
                for name in names
            ):
                raise ValueError("missing workbook package members")
            types = ElementTree.fromstring(archive.read("[Content_Types].xml"))
            document = ElementTree.fromstring(archive.read("xl/workbook.xml"))
            if (
                types.tag
                != "{http://schemas.openxmlformats.org/package/2006/content-types}Types"
                or document.tag
                != "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}workbook"
                or not any(
                    item.get("ContentType", "").endswith("spreadsheetml.sheet.main+xml")
                    for item in types
                )
            ):
                raise ValueError("invalid workbook XML")
        else:
            windows: dict[str, set[int]] = {"means": set(), "standarderrors": set()}
            for member in members:
                if (
                    member.is_dir()
                    or not member.filename.endswith(".csv")
                    or not member.filename.startswith(
                        (
                            "LANDCLIMII.RV.means.JUN2021/",
                            "LANDCLIMII.RV.standarderrors.JUN2021/",
                        )
                    )
                ):
                    continue
                match = re.fullmatch(
                    r"LANDCLIMII\.RV\.(means|standarderrors)\.JUN2021/TW(\d+)\.[^/]+\.csv",
                    member.filename,
                )
                if match is None or int(match[2]) in windows[match[1]]:
                    raise ValueError("result archive member identity")
                windows[match[1]].add(int(match[2]))
                header = _csv(archive.read(member))
                if not {"LCGRID_ID", "lonDD", "latDD"} < set(header):
                    raise ValueError("result archive CSV identifiers")
            if any(value != set(range(1, 26)) for value in windows.values()):
                raise ValueError("result archive window inventory")
