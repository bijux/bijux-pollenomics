"""Hash the selected external archive and stream exactly one custody-bound occurrence."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import stat
import zipfile
import zlib

from ...quarantine import IntakeRefusal
from ..local import BoundArchiveMember, LocalInventoryLimits
from ..local.archives import archive_records
from ..local.contracts import checked_path, encode, integer
from ..local.inventory import FileStamp, hash_file, stable_file
from .contracts import AsciiWindowLimits, AsciiWindowSelection, NativeAsciiHeader
from .parsing import ReadStream, parse_header, select_cells


@dataclass(frozen=True)
class StreamedWindow:
    header: NativeAsciiHeader
    tokens: tuple[str, ...]
    missing: tuple[bool, ...]
    member_sha256: str
    member_bytes: int
    member_crc32: int
    source_stamp: FileStamp


class DigestStream:
    """Bound every expanded read and hash all consumed header/body bytes."""

    def __init__(self, stream: ReadStream, limit: int) -> None:
        self.stream = stream
        self.limit = limit
        self.bytes = 0
        self.digest = hashlib.sha256()
        self.crc32 = 0

    def _consume(self, value: bytes) -> bytes:
        self.bytes += len(value)
        if self.bytes > self.limit:
            raise IntakeRefusal("hyde_ascii_member_limit", str(self.bytes))
        self.digest.update(value)
        self.crc32 = zlib.crc32(value, self.crc32)
        return value

    def read(self, size: int = -1) -> bytes:
        if size < 0:
            raise IntakeRefusal("hyde_ascii_unbounded_read", str(size))
        return self._consume(self.stream.read(min(size, self.limit - self.bytes + 1)))

    def readline(self, size: int = -1) -> bytes:
        if size < 0:
            raise IntakeRefusal("hyde_ascii_unbounded_read", str(size))
        return self._consume(
            self.stream.readline(min(size, self.limit - self.bytes + 1))
        )


def source_unchanged(path: Path, expected: FileStamp) -> None:
    path = checked_path(path)
    if FileStamp.from_stat(path.lstat()) != expected:
        raise IntakeRefusal("hyde_ascii_source_changed", str(path))


def stream_window(
    source_root: Path,
    selected: BoundArchiveMember,
    selection: AsciiWindowSelection,
    limits: AsciiWindowLimits,
) -> StreamedWindow:
    source_root = checked_path(source_root)
    path = checked_path(source_root / selected.archive_path)
    before = FileStamp.from_stat(path.lstat())
    if not stat.S_ISREG(before.mode) or before.size != selected.archive_bytes:
        raise IntakeRefusal(
            "hyde_ascii_archive_identity_mismatch", selected.archive_path
        )
    row = selected.occurrence()
    if (
        selection.expected_member_name != selected.name
        or Path(selected.name).suffix.casefold() != ".asc"
        or row["directory"]
        or row["symlink"]
        or not row["safe_relative_name"]
        or integer(row["flags"], "flags") & 1
    ):
        raise IntakeRefusal("hyde_ascii_member_selection_invalid", selected.name)
    expanded = integer(row["bytes"], "member bytes")
    compressed = integer(row["compressed_bytes"], "compressed bytes")
    if (
        expanded > limits.maximum_member_bytes
        or expanded > compressed * limits.maximum_expansion_ratio
    ):
        raise IntakeRefusal("hyde_ascii_member_limit", selected.name)
    custody_limits = LocalInventoryLimits(chunk_bytes=limits.chunk_bytes)
    if hash_file(path, before, custody_limits) != selected.archive_sha256:
        raise IntakeRefusal("hyde_ascii_archive_digest_mismatch", selected.archive_path)
    with stable_file(path, before) as source:
        occurrences, directory = archive_records(
            source,
            selected.archive_path,
            selected.archive_sha256,
            before.size,
            custody_limits,
        )
        if (
            encode(directory).decode("ascii") != selected.archive_directory_json
            or selected.member_index >= len(occurrences)
            or encode(occurrences[selected.member_index]).decode("ascii")
            != selected.occurrence_json
        ):
            raise IntakeRefusal("hyde_ascii_archive_occurrence_mismatch", selected.name)
        source.seek(0)
        with zipfile.ZipFile(source) as archive:
            member = archive.infolist()[selected.member_index]
            with archive.open(member) as payload:
                stream = DigestStream(payload, limits.maximum_member_bytes)
                header = parse_header(stream, limits)
                tokens, missing = select_cells(stream, header, selection, limits)
                if stream.bytes != expanded or stream.crc32 != row["crc32"]:
                    raise IntakeRefusal(
                        "hyde_ascii_member_integrity_mismatch", selected.name
                    )
    source_unchanged(path, before)
    return StreamedWindow(
        header,
        tokens,
        missing,
        stream.digest.hexdigest(),
        stream.bytes,
        stream.crc32,
        before,
    )
