"""Version for the LRA engine."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("bijux-pollenomics-lra")
except PackageNotFoundError:
    try:
        from bijux_pollenomics_lra._build_version import __version__
    except ImportError:
        __version__ = "0+unknown"

REFERENCE_PACKAGE = "disqover"

REFERENCE_VERSION = "0.9.14"

REFERENCE_ARCHIVE_SHA256 = (
    "ea496ae82807b52c9dd3d4b39b4dfa294bfac4068e20184ce56187bff70caf5c"
)

COMPATIBILITY_MODE = "disqover-0.9.14"

NUMERICAL_BACKEND = "python-numpy-scipy"
