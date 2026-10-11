"""Custody ordinals bind duplicate ZIP names and verify complete member integrity."""

from io import BytesIO
from pathlib import Path
import zipfile

import pytest

from bijux_pollenomics.collection.sources.hyde.ascii import (
    AsciiWindowLimits,
    AsciiWindowSelection,
)
from bijux_pollenomics.collection.sources.hyde.ascii.streaming import (
    DigestStream,
    stream_window,
)
from bijux_pollenomics.collection.sources.hyde.local import (
    prepare_local_hyde_inventory,
    select_local_hyde_archive_member,
)
from bijux_pollenomics.collection.sources.quarantine import IntakeRefusal

from .test_preparation import BODY, HEADER, fixture


def test_duplicate_names_are_selected_by_ordinal(tmp_path: Path) -> None:
    source = tmp_path / "raw"
    source.mkdir()
    with zipfile.ZipFile(source / "a.zip", "w") as archive:
        archive.writestr("a.asc", HEADER + BODY)
        with pytest.warns(UserWarning, match="Duplicate name"):
            archive.writestr("a.asc", HEADER + b"7 8 9 10 11 12")
    custody = prepare_local_hyde_inventory(source, tmp_path / "custody")
    outputs = []
    for ordinal in (0, 1):
        bound = select_local_hyde_archive_member(
            custody, archive_path="a.zip", member_index=ordinal
        )
        selection = AsciiWindowSelection("a.zip", ordinal, "a.asc", 0, 1, 0, 1)
        outputs.append(
            stream_window(source, bound, selection, AsciiWindowLimits()).tokens
        )
    assert outputs == [("-9999",), ("7",)]


def test_expanded_limits_and_archive_hash_are_checked(tmp_path: Path) -> None:
    source, custody, selection = fixture(tmp_path)
    bound = select_local_hyde_archive_member(
        custody, archive_path=selection.archive_path, member_index=0
    )
    with pytest.raises(IntakeRefusal, match="member_limit"):
        stream_window(
            source, bound, selection, AsciiWindowLimits(maximum_member_bytes=1)
        )
    raw = source / selection.archive_path
    data = bytearray(raw.read_bytes())
    data[40] ^= 1
    raw.write_bytes(data)
    with pytest.raises(IntakeRefusal, match="digest_mismatch"):
        stream_window(source, bound, selection, AsciiWindowLimits())


def test_digest_stream_forbids_unbounded_or_excess_reads() -> None:
    stream = DigestStream(BytesIO(b"abc"), 2)
    with pytest.raises(IntakeRefusal, match="unbounded_read"):
        stream.read()
    with pytest.raises(IntakeRefusal, match="member_limit"):
        stream.read(3)


def test_native_crc_corruption_is_refused_even_with_new_archive_custody(
    tmp_path: Path,
) -> None:
    source = tmp_path / "raw"
    source.mkdir()
    path = source / "bad.zip"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
        archive.writestr("a.asc", HEADER + BODY)
    content = path.read_bytes()
    path.write_bytes(content.replace(b"1.2500", b"1.2501", 1))
    custody = prepare_local_hyde_inventory(source, tmp_path / "custody")
    selected = select_local_hyde_archive_member(
        custody, archive_path="bad.zip", member_index=0
    )
    with pytest.raises(zipfile.BadZipFile, match="CRC"):
        stream_window(
            source,
            selected,
            AsciiWindowSelection("bad.zip", 0, "a.asc", 0, 1, 0, 1),
            AsciiWindowLimits(),
        )
