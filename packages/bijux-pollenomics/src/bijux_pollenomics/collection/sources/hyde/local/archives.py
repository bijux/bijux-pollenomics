"""Bounded ZIP directory custody using occurrence locators, never extraction."""

from __future__ import annotations

from collections import Counter
from pathlib import PurePosixPath, PureWindowsPath
import stat
import struct
from typing import BinaryIO
import zipfile

from ...quarantine import IntakeRefusal
from .contracts import LocalInventoryLimits, encode


def _directory_bound(
    stream: BinaryIO, size: int, limits: LocalInventoryLimits
) -> dict[str, object]:
    """Bound classic/ZIP64 end records before stdlib allocates a central directory."""
    stream.seek(max(0, size - 65_557))
    tail = stream.read(65_557)
    offset = tail.rfind(b"PK\x05\x06")
    while offset >= 0:
        if len(tail) - offset >= 22:
            end = struct.unpack_from("<4s4H2LH", tail, offset)
            if offset + 22 + end[7] == len(tail):
                break
        offset = tail.rfind(b"PK\x05\x06", 0, offset)
    if offset < 0:
        raise IntakeRefusal("hyde_zip_directory_invalid", "Missing bounded end record")
    _, disk, start_disk, disk_entries, entries, directory_bytes, directory_offset, _ = (
        end
    )
    if disk or start_disk or disk_entries != entries:
        raise IntakeRefusal("hyde_zip_directory_unsupported", "Spanned archive")
    end_offset = size - len(tail) + offset
    locator_offset = end_offset - 20
    locator = b""
    if locator_offset >= 0:
        stream.seek(locator_offset)
        locator = stream.read(20)
    zip64 = locator.startswith(b"PK\x06\x07")
    directory_end = end_offset
    if zip64:
        _, locator_disk, record_offset, disk_count = struct.unpack("<4sLQL", locator)
        if locator_disk or disk_count != 1 or record_offset > locator_offset - 56:
            raise IntakeRefusal("hyde_zip_directory_invalid", "ZIP64 locator bounds")
        stream.seek(record_offset)
        record = stream.read(56)
        if len(record) != 56:
            raise IntakeRefusal("hyde_zip_directory_invalid", "Short ZIP64 end record")
        (
            signature,
            record_bytes,
            _,
            _,
            disk64,
            start64,
            disk_entries64,
            entries64,
            bytes64,
            offset64,
        ) = struct.unpack("<4sQ2H2L4Q", record)
        if (
            signature != b"PK\x06\x06"
            or record_bytes < 44
            or record_bytes > limits.maximum_central_directory_bytes
            or record_offset + 12 + record_bytes != locator_offset
            or disk64
            or start64
            or disk_entries64 != entries64
        ):
            raise IntakeRefusal(
                "hyde_zip_directory_invalid", "ZIP64 end-record identity/bounds"
            )
        for small, large, sentinel in (
            (entries, entries64, 65535),
            (directory_bytes, bytes64, 0xFFFFFFFF),
            (directory_offset, offset64, 0xFFFFFFFF),
        ):
            if small != sentinel and small != large:
                raise IntakeRefusal(
                    "hyde_zip_directory_invalid",
                    "Contradictory classic and ZIP64 records",
                )
        entries, directory_bytes, directory_offset = entries64, bytes64, offset64
        directory_end = record_offset
    elif (
        entries == 65535
        or directory_bytes == 0xFFFFFFFF
        or directory_offset == 0xFFFFFFFF
    ):
        raise IntakeRefusal(
            "hyde_zip_directory_invalid", "ZIP64 sentinel without locator"
        )
    if (
        entries > limits.maximum_archive_members
        or directory_bytes > limits.maximum_central_directory_bytes
    ):
        raise IntakeRefusal("hyde_zip_directory_limit", str(entries))
    if directory_offset + directory_bytes != directory_end:
        raise IntakeRefusal(
            "hyde_zip_directory_unsupported",
            "Central directory must have direct native offsets",
        )
    stream.seek(0)
    return {
        "profile": "zip-central-directory-v1",
        "zip64": zip64,
        "member_count": entries,
        "central_directory_bytes": directory_bytes,
        "central_directory_offset": directory_offset,
    }


def archive_records(
    stream: BinaryIO,
    name: str,
    source_sha256: str,
    size: int,
    limits: LocalInventoryLimits,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Keep names, duplicates and native directory metadata without opening members."""
    rows: list[dict[str, object]] = []
    retained_bytes = 0
    directory = _directory_bound(stream, size, limits)
    with zipfile.ZipFile(stream) as archive:
        members = archive.infolist()
        if len(members) != directory["member_count"]:
            raise IntakeRefusal(
                "hyde_zip_directory_invalid",
                "Entry count disagrees with actual directory",
            )
        totals = Counter(member.orig_filename for member in members)
        occurrences: Counter[str] = Counter()
        for index, member in enumerate(members):
            original = member.orig_filename
            occurrence = occurrences[original]
            occurrences[original] += 1
            safe = safe_member_name(original)
            row: dict[str, object] = {
                "archive_path": name,
                "archive_sha256": source_sha256,
                "member_index": index,
                "name": original,
                "decoded_filename": member.filename,
                "name_occurrence": occurrence,
                "name_occurrences": totals[original],
                "bytes": member.file_size,
                "compressed_bytes": member.compress_size,
                "crc32": member.CRC,
                "header_offset": member.header_offset,
                "compression": member.compress_type,
                "flags": member.flag_bits,
                "date_time": list(member.date_time),
                "create_system": member.create_system,
                "create_version": member.create_version,
                "extract_version": member.extract_version,
                "internal_attributes": member.internal_attr,
                "external_attributes": member.external_attr,
                "comment_hex": member.comment.hex(),
                "extra_hex": member.extra.hex(),
                "directory": member.is_dir(),
                "symlink": stat.S_ISLNK(member.external_attr >> 16),
                "safe_relative_name": safe,
                "extraction_allowed": False,
            }
            retained_bytes += len(encode(row))
            if (
                retained_bytes > limits.maximum_retained_bytes
                or len(rows) >= limits.maximum_archive_members
            ):
                raise IntakeRefusal("hyde_archive_metadata_limit", name)
            rows.append(row)
    directory["comment_hex"] = archive.comment.hex()
    return rows, directory


def safe_member_name(name: str) -> bool:
    """A diagnostic only; no member is eligible for extraction through this API."""
    return not (
        PurePosixPath(name).is_absolute()
        or PureWindowsPath(name).drive
        or ".." in PurePosixPath(name).parts
        or "\\" in name
        or "\x00" in name
    )
