"""Immutable archive evidence and refusal types."""

from __future__ import annotations

from dataclasses import dataclass


class IntakeRefusal(ValueError):
    """Refuse an archive or scientific claim with a stable reason code."""

    def __init__(self, reason_code: str, detail: str) -> None:
        self.reason_code = reason_code
        super().__init__(f"{reason_code}: {detail}")


@dataclass(frozen=True)
class ArchiveLimits:
    """Resource limits applied before any archive member is read."""

    maximum_members: int = 10_000
    maximum_member_bytes: int = 512_000_000
    maximum_expanded_bytes: int = 2_000_000_000
    maximum_compression_ratio: float = 200.0


@dataclass(frozen=True)
class ArchiveMember:
    """Security-relevant metadata for one archive member."""

    path: str
    size_bytes: int
    compressed_size_bytes: int
    crc32: str | None
    is_directory: bool
    is_encrypted: bool
    unix_mode: int | None
    content_sha256: str | None


@dataclass(frozen=True)
class ArchiveIdentity:
    """Byte identity of an archive kept outside the repository."""

    filename: str
    size_bytes: int
    sha256: str
    media_type: str


@dataclass(frozen=True)
class ArchiveInventory:
    """Validated member inventory bound to an archive identity."""

    identity: ArchiveIdentity
    members: tuple[ArchiveMember, ...]
    expanded_bytes: int
    member_manifest_sha256: str

    @property
    def regular_file_count(self) -> int:
        return sum(not member.is_directory for member in self.members)
