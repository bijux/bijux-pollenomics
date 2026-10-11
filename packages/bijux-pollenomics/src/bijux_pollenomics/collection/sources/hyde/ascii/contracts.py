"""Source-index ASCII windows preserve numeric spelling without semantic conversion."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ...quarantine import IntakeRefusal
from ..local.contracts import integer, relative_path, text

SCHEMA = "hyde-native-ascii-window.v1"
FORMAT = "esri-ascii-corner-explicit-nodata-v1"
POSTURE: dict[str, object] = {
    "native_release_status": "unverified",
    "scientific_acceptance": "not_evaluated",
    "public_release_allowed": False,
    "coordinate_reference_system": None,
    "variable_units": None,
    "calendar_support": None,
    "grid_conversion": "not_performed",
    "native_labels_status": "caller_declared_uninterpreted_source_text",
}


@dataclass(frozen=True)
class AsciiWindowSelection:
    """An exact ZIP occurrence and half-open zero-based source-index rectangle."""

    archive_path: str
    member_index: int
    expected_member_name: str
    row_start: int
    row_stop: int
    column_start: int
    column_stop: int
    native_labels: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        relative_path(self.archive_path)
        integer(self.member_index, "member_index")
        text(self.expected_member_name, "expected_member_name")
        for name in ("row_start", "row_stop", "column_start", "column_stop"):
            integer(getattr(self, name), name)
        if self.row_start >= self.row_stop or self.column_start >= self.column_stop:
            raise IntakeRefusal("hyde_ascii_window_empty_or_reversed", repr(self))
        keys = []
        if not isinstance(self.native_labels, tuple):
            raise IntakeRefusal(
                "hyde_ascii_labels_invalid", "Immutable native label pairs required"
            )
        for pair in self.native_labels:
            if not isinstance(pair, tuple) or len(pair) != 2:
                raise IntakeRefusal("hyde_ascii_labels_invalid", repr(pair))
            key, label = pair
            key = text(key, "native label role")
            if (
                key not in {"scenario", "time", "variable"}
                or text(label, "native label")
                not in self.archive_path + "/" + self.expected_member_name
            ):
                raise IntakeRefusal("hyde_ascii_labels_invalid", repr(pair))
            keys.append(key)
        if len(keys) != len(set(keys)):
            raise IntakeRefusal("hyde_ascii_labels_invalid", "Repeated label role")


@dataclass(frozen=True)
class AsciiWindowLimits:
    chunk_bytes: int = 1024 * 1024
    maximum_header_bytes: int = 8192
    maximum_token_bytes: int = 128
    maximum_member_bytes: int = 256 * 1024 * 1024
    maximum_source_cells: int = 10_000_000
    maximum_selected_cells: int = 250_000
    maximum_retained_bytes: int = 16 * 1024 * 1024
    maximum_expansion_ratio: int = 1000

    def __post_init__(self) -> None:
        caps = {
            "chunk_bytes": 1024 * 1024,
            "maximum_header_bytes": 8192,
            "maximum_token_bytes": 128,
            "maximum_member_bytes": 256 * 1024 * 1024,
            "maximum_source_cells": 10_000_000,
            "maximum_selected_cells": 250_000,
            "maximum_retained_bytes": 16 * 1024 * 1024,
            "maximum_expansion_ratio": 1000,
        }
        for name, value in vars(self).items():
            if integer(value, name) == 0 or value > caps[name]:
                raise IntakeRefusal("hyde_ascii_limit_invalid", name)


@dataclass(frozen=True)
class NativeAsciiHeader:
    """Exact source header bytes/tokens plus validated integer dimensions."""

    bytes_base64: str
    tokens: tuple[tuple[str, str], ...]
    rows: int
    columns: int

    def value(self, name: str) -> str:
        return next(
            value for keyword, value in self.tokens if keyword.casefold() == name
        )


@dataclass(frozen=True)
class NativeAsciiWindow:
    """A retained native-index preview; no CRS, units, time or public admission."""

    directory: Path
    manifest_sha256: str
    custody_manifest_sha256: str
    member_sha256: str
    selection: AsciiWindowSelection
    header: NativeAsciiHeader
    source_tokens: tuple[str, ...]
    missing_mask: tuple[bool, ...]
