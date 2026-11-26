"""Capture the selected Nordic display boundary and temporal grid."""

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
from types import MappingProxyType

from ...collection.contracts.artifacts import (
    BOUNDARY_COLLECTION,
    LANDCLIM_GRID_GEOJSON,
    LANDCLIM_TEMPORAL_GRID_GEOJSON,
)
from ...core.filesystem import DirectoryAnchor, read_regular_file
from ...core.geospatial.geojson import as_mapping

_POLYGONS = {
    "country-boundaries": BOUNDARY_COLLECTION,
    "landclim-reveals-temporal-grid": LANDCLIM_TEMPORAL_GRID_GEOJSON,
}
_MAX_BYTES = 64 * 1024 * 1024


@dataclass(frozen=True)
class NordicPolygonInputs:
    """Held selected polygon bytes; not the complete Atlas source set."""

    context_root: Path
    buffers: Mapping[str, bytes]
    expected_sha256: Mapping[str, str]

    def __post_init__(self) -> None:
        held, pins = dict(self.buffers), dict(self.expected_sha256)
        if (
            set(held) != set(_POLYGONS)
            or set(pins) != set(_POLYGONS)
            or any(
                type(body) is not bytes or len(body) > _MAX_BYTES
                for body in held.values()
            )
            or any(
                not isinstance(value, str)
                or re.fullmatch(r"[0-9a-f]{64}", value) is None
                for value in pins.values()
            )
        ):
            raise ValueError("Nordic polygon input set differs")
        if any(
            hashlib.sha256(body).hexdigest() != pins[key] for key, body in held.items()
        ):
            raise ValueError("Nordic polygon input digest differs")
        object.__setattr__(self, "context_root", Path(self.context_root).absolute())
        object.__setattr__(self, "buffers", MappingProxyType(held))
        object.__setattr__(self, "expected_sha256", MappingProxyType(pins))

    def identity(self) -> dict[str, object]:
        """Identify selected display inputs without asserting source admission."""
        return {
            "schema_version": "nordic-selected-polygon-inputs.v1",
            "posture": "selected_polygon_bytes_only_not_source_or_scientific_admission",
            "grid_selection": "temporal",
            "polygons": {
                key: {"sha256": self.expected_sha256[key], "bytes": len(body)}
                for key, body in self.buffers.items()
            },
        }

    def decode(self, role: str) -> dict[str, object]:
        if role not in _POLYGONS:
            raise ValueError("Nordic polygon role differs")
        try:
            value = as_mapping(json.loads(self.buffers[role]))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("Nordic polygon JSON differs") from exc
        if value is None:
            raise ValueError("Nordic polygon must be a JSON object")
        return {str(key): item for key, item in value.items()}

    def stage(self, role: str, destination: Path) -> Path:
        if role not in _POLYGONS:
            raise ValueError("Nordic polygon role differs")
        root = Path(destination).absolute()
        name = _POLYGONS[role].filename
        with DirectoryAnchor(root) as anchor:
            fd = os.open(
                name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=anchor.fd,
            )
            with os.fdopen(fd, "wb") as stream:
                stream.write(self.buffers[role])
            anchor.check()
            path = root / name
            if read_regular_file(path, max_bytes=_MAX_BYTES) != self.buffers[role]:
                raise ValueError("Nordic staged polygon bytes differ")
            anchor.check()
        return path

    def validate_staged(self, destination: Path) -> None:
        root = Path(destination).absolute()
        with DirectoryAnchor(root) as anchor:
            for role, contract in _POLYGONS.items():
                if (
                    read_regular_file(root / contract.filename, max_bytes=_MAX_BYTES)
                    != self.buffers[role]
                ):
                    raise ValueError(f"Nordic staged polygon bytes differ: {role}")
            try:
                os.stat(
                    LANDCLIM_GRID_GEOJSON.filename,
                    dir_fd=anchor.fd,
                    follow_symlinks=False,
                )
            except FileNotFoundError:
                pass
            else:
                raise ValueError("suppressed LandClim static grid was staged")
            anchor.check()


def capture_nordic_polygon_inputs(
    context_root: Path, expected_sha256: Mapping[str, str]
) -> NordicPolygonInputs:
    """Capture the required boundary and temporal grid; static fallback is unsupported."""
    if set(expected_sha256) != set(_POLYGONS) or any(
        not isinstance(x, str) or re.fullmatch(r"[0-9a-f]{64}", x) is None
        for x in expected_sha256.values()
    ):
        raise ValueError("Nordic polygon pin set differs")
    root = Path(context_root).absolute()
    held = {
        key: read_regular_file(contract.path_under(root), max_bytes=_MAX_BYTES)
        for key, contract in _POLYGONS.items()
    }
    return NordicPolygonInputs(root, held, dict(expected_sha256))
