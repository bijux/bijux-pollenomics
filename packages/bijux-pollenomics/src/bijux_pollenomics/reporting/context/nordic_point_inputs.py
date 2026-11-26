"""Capture four selected Nordic point inputs without implying Atlas admission."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from types import MappingProxyType

from ...collection.contracts.artifacts import (
    LANDCLIM_SITE_GEOJSON,
    NEOTOMA_POINT_GEOJSON,
    SEAD_ARCHAEOLOGY_DISCOVERY_GEOJSON,
    SEAD_POINT_GEOJSON,
    SEAD_TEMPORAL_EVIDENCE_GEOJSON,
)
from ...core.filesystem import DirectoryAnchor, read_regular_file
from ...core.geospatial.geojson import as_mapping

_POINTS = {
    "landclim-sites": LANDCLIM_SITE_GEOJSON,
    "neotoma-pollen": NEOTOMA_POINT_GEOJSON,
    "sead-sites": SEAD_POINT_GEOJSON,
    "sweden-archaeology-site-discovery": SEAD_ARCHAEOLOGY_DISCOVERY_GEOJSON,
}
_MAX_POINT_BYTES = 64 * 1024 * 1024


def _temporal_presence(root: Path) -> bool:
    path = SEAD_TEMPORAL_EVIDENCE_GEOJSON.path_under(root).absolute()
    with DirectoryAnchor(path.parent) as anchor:
        try:
            node = os.stat(path.name, dir_fd=anchor.fd, follow_symlinks=False)
        except FileNotFoundError:
            anchor.check()
            return False
        if not stat.S_ISREG(node.st_mode) or node.st_nlink != 1:
            raise ValueError("SEAD temporal evidence must be an ordinary file")
        anchor.check()
        return True


@dataclass(frozen=True)
class NordicPointInputs:
    """Held selected point bytes; not the Atlas read-set or scientific admission."""

    context_root: Path
    buffers: Mapping[str, bytes]
    temporal_evidence_present: bool
    expected_sha256: Mapping[str, str]

    def __post_init__(self) -> None:
        """Own only the complete selected byte set and a native presence flag."""
        held = dict(self.buffers)
        pins = dict(self.expected_sha256)
        if (
            set(held) != set(_POINTS)
            or set(pins) != set(_POINTS)
            or any(
                not isinstance(value, str)
                or re.fullmatch(r"[0-9a-f]{64}", value) is None
                for value in pins.values()
            )
            or any(
                type(body) is not bytes or len(body) > _MAX_POINT_BYTES
                for body in held.values()
            )
            or type(self.temporal_evidence_present) is not bool
        ):
            raise ValueError("Nordic point captured inputs differ")
        if any(
            hashlib.sha256(body).hexdigest() != pins[role]
            for role, body in held.items()
        ):
            raise ValueError("Nordic point captured digest differs")
        object.__setattr__(self, "context_root", Path(self.context_root).absolute())
        object.__setattr__(self, "buffers", MappingProxyType(held))
        object.__setattr__(self, "expected_sha256", MappingProxyType(pins))

    def identity(self) -> dict[str, object]:
        """Report selected point-byte identities without claiming a complete read-set."""
        return {
            "schema_version": "nordic-selected-point-inputs.v1",
            "posture": "selected_point_bytes_only_not_source_or_scientific_admission",
            "points": {
                role: {"sha256": self.expected_sha256[role], "bytes": len(body)}
                for role, body in self.buffers.items()
            },
            "sead_temporal_evidence": {
                "present": self.temporal_evidence_present,
                "selection": "suppressed_by_discovery",
            },
        }

    def validate_temporal_presence(self) -> None:
        """Refuse a change to the presence of the suppressed SEAD surface."""
        if _temporal_presence(self.context_root) != self.temporal_evidence_present:
            raise ValueError("SEAD temporal evidence presence changed")

    def validate_staged(self, destination: Path) -> None:
        """Verify selected staged bytes and the discovery precedence before attach."""
        self.validate_temporal_presence()
        root = Path(destination).absolute()
        with DirectoryAnchor(root) as anchor:
            for role, contract in _POINTS.items():
                path = root / contract.filename
                if (
                    read_regular_file(path, max_bytes=_MAX_POINT_BYTES)
                    != self.buffers[role]
                ):
                    raise ValueError(f"Nordic staged point bytes differ: {role}")
            try:
                os.stat(
                    SEAD_TEMPORAL_EVIDENCE_GEOJSON.filename,
                    dir_fd=anchor.fd,
                    follow_symlinks=False,
                )
            except FileNotFoundError:
                pass
            else:
                raise ValueError("suppressed SEAD temporal evidence was staged")
            anchor.check()
        self.validate_temporal_presence()

    def decode(self, role: str) -> dict[str, object]:
        """Decode the exact selected buffer for the layer owner."""
        if role not in _POINTS or role not in self.buffers:
            raise ValueError("Nordic point role differs")
        try:
            value = as_mapping(json.loads(self.buffers[role]))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("Nordic point source JSON differs") from error
        if value is None:
            raise ValueError("Nordic point source must be a JSON object")
        return {str(key): item for key, item in value.items()}

    def stage(self, role: str, destination: Path) -> Path:
        """Write one selected buffer exclusively, and verify the staged bytes."""
        if role not in _POINTS or role not in self.buffers:
            raise ValueError("Nordic point role differs")
        name = _POINTS[role].filename
        root = Path(destination).absolute()
        with DirectoryAnchor(root) as anchor:
            descriptor = os.open(
                name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=anchor.fd,
            )
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(self.buffers[role])
            anchor.check()
            path = root / name
            if (
                read_regular_file(path, max_bytes=_MAX_POINT_BYTES)
                != self.buffers[role]
            ):
                raise ValueError("Nordic staged point bytes differ")
            anchor.check()
        return path


def capture_nordic_point_inputs(
    context_root: Path, expected_sha256: Mapping[str, str]
) -> NordicPointInputs:
    """Capture exactly four caller-pinned inputs; other Atlas sources are excluded."""
    if set(expected_sha256) != set(_POINTS) or any(
        not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None
        for value in expected_sha256.values()
    ):
        raise ValueError("Nordic point pin set differs")
    root = Path(context_root).absolute()
    present = _temporal_presence(root)
    held: dict[str, bytes] = {}
    for role, contract in _POINTS.items():
        body = read_regular_file(contract.path_under(root), max_bytes=_MAX_POINT_BYTES)
        if hashlib.sha256(body).hexdigest() != expected_sha256[role]:
            raise ValueError(f"Nordic point digest differs: {role}")
        held[role] = body
    if _temporal_presence(root) != present:
        raise ValueError("SEAD temporal evidence presence changed during capture")
    return NordicPointInputs(root, held, present, dict(expected_sha256))
