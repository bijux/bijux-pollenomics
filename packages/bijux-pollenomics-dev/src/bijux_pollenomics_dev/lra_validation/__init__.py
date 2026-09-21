"""Independent synthetic oracles for bounded LRA validation."""

from .known_landscape import (
    KNOWN_LANDSCAPE_PROFILE,
    KnownLandscapeError,
    KnownLandscapeReport,
    build_known_landscape_report,
)

__all__ = [
    "KNOWN_LANDSCAPE_PROFILE",
    "KnownLandscapeError",
    "KnownLandscapeReport",
    "build_known_landscape_report",
]
