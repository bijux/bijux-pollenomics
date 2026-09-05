"""Compatibility facade for bounded archive inspection and extraction."""

from .extraction import _copy_member as _copy_member
from .extraction import extract_zip_members
from .inspection import (
    inspect_zip_archive,
    inspected_zip_archive,
    sha256_file,
)

__all__ = [
    "extract_zip_members",
    "inspect_zip_archive",
    "inspected_zip_archive",
    "sha256_file",
]
