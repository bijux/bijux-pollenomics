"""Fail-closed primitives for inspecting quarantined source archives."""

from .archives import (
    extract_zip_members,
    inspect_zip_archive,
    inspected_zip_archive,
    sha256_file,
)
from .inspection import sha256_stream
from .models import (
    ArchiveIdentity,
    ArchiveInventory,
    ArchiveLimits,
    ArchiveMember,
    IntakeRefusal,
)

__all__ = [
    "ArchiveIdentity",
    "ArchiveInventory",
    "ArchiveLimits",
    "ArchiveMember",
    "IntakeRefusal",
    "extract_zip_members",
    "inspect_zip_archive",
    "inspected_zip_archive",
    "sha256_file",
    "sha256_stream",
]
