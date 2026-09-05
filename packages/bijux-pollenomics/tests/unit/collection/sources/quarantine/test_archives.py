from __future__ import annotations

import hashlib
from dataclasses import replace
from io import BytesIO
from pathlib import Path
import stat
import unicodedata
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

import pytest

from bijux_pollenomics.collection.sources.quarantine import (
    ArchiveLimits,
    ArchiveMember,
    IntakeRefusal,
    extract_zip_members,
    inspect_zip_archive,
)
from bijux_pollenomics.collection.sources.quarantine import archives
from bijux_pollenomics.collection.sources.quarantine import inspection


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_safe_inventory_is_deterministic_and_selective_extraction_is_bounded(
    tmp_path: Path,
) -> None:
    archive_path = tmp_path / "source.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("source/data.csv", "x\n1\n")
        archive.writestr("source/ignored.txt", "not selected")

    first = inspect_zip_archive(archive_path, expected_sha256=_digest(archive_path))
    second = inspect_zip_archive(archive_path, expected_sha256=_digest(archive_path))
    destination = tmp_path / "output"
    destination.mkdir()
    outputs = extract_zip_members(
        archive_path, destination, first, ("source/data.csv",)
    )

    assert first == second
    assert first.regular_file_count == 2
    assert first.members[0].content_sha256 == hashlib.sha256(b"x\n1\n").hexdigest()
    assert len(first.member_manifest_sha256) == 64
    assert outputs == (destination / "source" / "data.csv",)
    assert outputs[0].read_text(encoding="utf-8") == "x\n1\n"
    assert not (destination / "source" / "ignored.txt").exists()


@pytest.mark.parametrize("name", ("../escape.csv", "/absolute.csv", "C:/drive.csv"))
def test_archive_paths_fail_closed(tmp_path: Path, name: str) -> None:
    archive_path = tmp_path / "unsafe.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr(name, "payload")

    with pytest.raises(IntakeRefusal, match="unsafe_archive_path"):
        inspect_zip_archive(archive_path, expected_sha256=_digest(archive_path))


def test_archive_symlink_and_digest_mismatch_fail_closed(tmp_path: Path) -> None:
    archive_path = tmp_path / "symlink.zip"
    member = ZipInfo("source/link")
    member.create_system = 3
    member.external_attr = (stat.S_IFLNK | 0o777) << 16
    with ZipFile(archive_path, "w") as archive:
        archive.writestr(member, "target")

    with pytest.raises(IntakeRefusal, match="archive_digest_mismatch"):
        inspect_zip_archive(archive_path, expected_sha256="0" * 64)
    with pytest.raises(IntakeRefusal, match="archive_symlink"):
        inspect_zip_archive(archive_path, expected_sha256=_digest(archive_path))


@pytest.mark.parametrize(
    ("first", "second"),
    (
        ("source/Data.csv", "source/data.csv"),
        ("source/data.csv", "source\\data.csv"),
        (
            "source/caf\N{LATIN SMALL LETTER E WITH ACUTE}.csv",
            "source/cafe\N{COMBINING ACUTE ACCENT}.csv",
        ),
    ),
)
def test_normalized_member_collisions_fail_closed(
    tmp_path: Path, first: str, second: str
) -> None:
    archive_path = tmp_path / "collision.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr(first, "first")
        archive.writestr(second, "second")

    with pytest.raises(IntakeRefusal, match="colliding_archive_member"):
        inspect_zip_archive(archive_path, expected_sha256=_digest(archive_path))

    assert unicodedata.normalize("NFC", first.replace("\\", "/")).casefold() == (
        unicodedata.normalize("NFC", second.replace("\\", "/")).casefold()
    )


def test_extraction_refuses_nonempty_destination(tmp_path: Path) -> None:
    archive_path = tmp_path / "source.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("source/data.csv", "x\n")
    inventory = inspect_zip_archive(archive_path, expected_sha256=_digest(archive_path))
    destination = tmp_path / "output"
    destination.mkdir()
    (destination / "existing").write_text("preserve", encoding="utf-8")

    with pytest.raises(IntakeRefusal, match="extraction_target_not_empty"):
        extract_zip_members(archive_path, destination, inventory, ("source/data.csv",))
    assert (destination / "existing").read_text(encoding="utf-8") == "preserve"


def test_extraction_refuses_symlink_destination(tmp_path: Path) -> None:
    archive_path = tmp_path / "source.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("source/data.csv", "x\n")
    inventory = inspect_zip_archive(archive_path, expected_sha256=_digest(archive_path))
    real_destination = tmp_path / "real-output"
    real_destination.mkdir()
    destination = tmp_path / "output"
    destination.symlink_to(real_destination, target_is_directory=True)

    with pytest.raises(IntakeRefusal, match="invalid_extraction_target"):
        extract_zip_members(archive_path, destination, inventory, ("source/data.csv",))
    assert list(real_destination.iterdir()) == []


def test_duplicate_members_and_changed_archive_are_refused(tmp_path: Path) -> None:
    duplicate_path = tmp_path / "duplicate.zip"
    with ZipFile(duplicate_path, "w") as archive:
        archive.writestr("source/data.csv", "first")
        with pytest.warns(UserWarning, match="Duplicate name"):
            archive.writestr("source/data.csv", "second")
    with pytest.raises(IntakeRefusal, match="duplicate_archive_member"):
        inspect_zip_archive(duplicate_path, expected_sha256=_digest(duplicate_path))

    source_path = tmp_path / "source.zip"
    with ZipFile(source_path, "w") as archive:
        archive.writestr("source/data.csv", "first")
    inventory = inspect_zip_archive(source_path, expected_sha256=_digest(source_path))
    with ZipFile(source_path, "w") as archive:
        archive.writestr("source/data.csv", "changed")
    destination = tmp_path / "output"
    destination.mkdir()
    with pytest.raises(IntakeRefusal, match="archive_changed_after_inspection"):
        extract_zip_members(source_path, destination, inventory, ("source/data.csv",))


def test_limits_are_enforced_before_integrity_decompression(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive_path = tmp_path / "compressed.zip"
    with ZipFile(archive_path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("source/large.csv", b"0" * 100_000)

    def unexpected_testzip(_archive: ZipFile) -> str | None:
        raise AssertionError("testzip decompressed before metadata limits")

    monkeypatch.setattr(ZipFile, "testzip", unexpected_testzip)
    with pytest.raises(IntakeRefusal, match="archive_expanded_size_limit"):
        inspect_zip_archive(
            archive_path,
            expected_sha256=_digest(archive_path),
            limits=ArchiveLimits(maximum_expanded_bytes=10),
        )


def test_extraction_rejects_forged_inventory_before_writing(tmp_path: Path) -> None:
    archive_path = tmp_path / "source.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("source/data.csv", "exact")
    inventory = inspect_zip_archive(archive_path, expected_sha256=_digest(archive_path))
    forged = replace(inventory, expanded_bytes=0)
    destination = tmp_path / "output"
    destination.mkdir()

    with pytest.raises(IntakeRefusal, match="archive_inventory_mismatch"):
        extract_zip_members(archive_path, destination, forged, ("source/data.csv",))
    assert list(destination.iterdir()) == []


def test_stream_copy_refuses_more_than_declared_member_bytes() -> None:
    member = ArchiveMember(
        path="source/data.csv",
        size_bytes=1,
        compressed_size_bytes=1,
        crc32=None,
        is_directory=False,
        is_encrypted=False,
        unix_mode=None,
        content_sha256=hashlib.sha256(b"t").hexdigest(),
    )

    with pytest.raises(IntakeRefusal, match="archive_output_size_limit"):
        archives._copy_member(BytesIO(b"too large"), BytesIO(), member, ArchiveLimits())


def test_special_and_encrypted_members_fail_before_content_read() -> None:
    special = ZipInfo("source/pipe")
    special.create_system = 3
    special.external_attr = (stat.S_IFIFO | 0o600) << 16
    with pytest.raises(IntakeRefusal, match="archive_special_file"):
        inspection._member_from_zip(special)

    encrypted = ZipInfo("source/secret.csv")
    encrypted.flag_bits |= 1
    with pytest.raises(IntakeRefusal, match="encrypted_archive_member"):
        inspection._member_from_zip(encrypted)


def test_compression_ratio_limit_precedes_member_content_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive_path = tmp_path / "compressed.zip"
    with ZipFile(archive_path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("source/data.csv", b"0" * 100_000)

    def unexpected_open(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("member content opened before ratio limit")

    monkeypatch.setattr(ZipFile, "open", unexpected_open)
    with pytest.raises(IntakeRefusal, match="archive_compression_ratio_limit"):
        inspect_zip_archive(
            archive_path,
            expected_sha256=_digest(archive_path),
            limits=ArchiveLimits(maximum_compression_ratio=2),
        )
