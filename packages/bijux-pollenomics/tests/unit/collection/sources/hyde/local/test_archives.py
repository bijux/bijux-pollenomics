"""ZIP directory occurrences remain independently located without extraction."""

import io
from pathlib import Path
import zipfile

import pytest

from bijux_pollenomics.collection.sources.hyde.local import LocalInventoryLimits
from bijux_pollenomics.collection.sources.hyde.local.archives import archive_records
from bijux_pollenomics.collection.sources.quarantine import IntakeRefusal

from .test_inventory import source_fixture


def test_duplicate_names_and_unsafe_members_are_auditable(tmp_path: Path) -> None:
    root = source_fixture(tmp_path / "raw")
    path = root / "native.zip"
    with path.open("rb") as stream:
        rows, directory = archive_records(
            stream, path.name, "a" * 64, path.stat().st_size, LocalInventoryLimits()
        )
    duplicates = [row for row in rows if row["name"] == "taxon-\u00e4.asc"]
    assert [row["name_occurrence"] for row in duplicates] == [0, 1]
    assert all(row["name_occurrences"] == 2 for row in duplicates)
    assert duplicates[0]["header_offset"] != duplicates[1]["header_offset"]
    assert rows[-1]["safe_relative_name"] is False
    assert all(row["extraction_allowed"] is False for row in rows)
    assert bytes.fromhex(str(directory["comment_hex"])) == b"native archive comment"
    assert not (root / "taxon-\u00e4.asc").exists()


@pytest.mark.parametrize("kind", ["truncated", "member_limit", "directory_limit"])
def test_bad_or_unbounded_directory_refuses(tmp_path: Path, kind: str) -> None:
    root = source_fixture(tmp_path / "raw")
    data = (root / "native.zip").read_bytes()
    limits = LocalInventoryLimits()
    if kind == "truncated":
        data = data[:-1]
    elif kind == "member_limit":
        limits = LocalInventoryLimits(maximum_archive_members=1)
    else:
        limits = LocalInventoryLimits(maximum_central_directory_bytes=1)
    with pytest.raises(IntakeRefusal):
        archive_records(io.BytesIO(data), "native.zip", "a" * 64, len(data), limits)


def test_empty_archive_is_distinct_from_missing_archive() -> None:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w"):
        pass
    rows, directory = archive_records(
        stream, "empty.zip", "a" * 64, len(stream.getvalue()), LocalInventoryLimits()
    )
    assert rows == [] and directory["comment_hex"] == "" and directory["zip64"] is False


def test_zip64_locator_cannot_bypass_standard_directory_memory_limit() -> None:
    import struct

    # A locator can override otherwise small32-bit end-record fields in stdlib.
    locator = struct.pack("<4sLQL", b"PK\x06\x07", 0, 0, 1)
    end = struct.pack("<4s4H2LH", b"PK\x05\x06", 0, 0, 0, 0, 0, 0, 0)
    data = locator + end
    with pytest.raises(IntakeRefusal, match="hyde_zip_directory_invalid"):
        archive_records(
            io.BytesIO(data), "native.zip", "a" * 64, len(data), LocalInventoryLimits()
        )


@pytest.mark.parametrize(
    "mutation", ["none", "oversized_directory", "bad_locator", "contradictory_end"]
)
def test_bounded_zip64_profile_retains_occurrences_and_refuses_invalid_bounds(
    mutation: str,
) -> None:
    import struct

    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("native.asc", b"0 -9999")
    original = stream.getvalue()
    end_offset = len(original) - 22
    signature, disk, start, disk_entries, entries, size, offset, comment = (
        struct.unpack("<4s4H2LH", original[-22:])
    )
    large_size = 10**9 if mutation == "oversized_directory" else size
    record = struct.pack(
        "<4sQ2H2L4Q",
        b"PK\x06\x06",
        44,
        45,
        45,
        0,
        0,
        entries,
        entries,
        large_size,
        offset,
    )
    locator = struct.pack(
        "<4sLQL",
        b"PK\x06\x07",
        0,
        end_offset + 1 if mutation == "bad_locator" else end_offset,
        1,
    )
    end = struct.pack(
        "<4s4H2LH",
        signature,
        disk,
        start,
        disk_entries,
        entries,
        size + 1 if mutation == "contradictory_end" else 0xFFFFFFFF,
        0xFFFFFFFF,
        comment,
    )
    data = original[:-22] + record + locator + end
    if mutation != "none":
        with pytest.raises(IntakeRefusal):
            archive_records(
                io.BytesIO(data),
                "native.zip",
                "a" * 64,
                len(data),
                LocalInventoryLimits(),
            )
    else:
        rows, directory = archive_records(
            io.BytesIO(data), "native.zip", "a" * 64, len(data), LocalInventoryLimits()
        )
        assert len(rows) == 1 and rows[0]["name"] == "native.asc"
        assert (
            directory["zip64"] is True and directory["central_directory_bytes"] == size
        )
