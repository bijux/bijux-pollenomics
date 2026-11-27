"""Hold and stage caller-pinned fieldwork gallery bytes for one map."""

from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
import os
from pathlib import Path
import re
import stat
from types import MappingProxyType

from bijux_pollenomics.core.filesystem import (
    BoundedInputTree,
    DirectoryAnchor,
    OwnedTreeWriter,
    read_regular_file,
)

from .shared import FIELDWORK_MEDIA_FILES

_NAMES = tuple(row[2] for row in FIELDWORK_MEDIA_FILES)
_MAX_FILE = 32 * 1024 * 1024
_MAX_TOTAL = 64 * 1024 * 1024
_OUTPUT = "fieldwork-media"


def _presence(anchor: DirectoryAnchor, name: str) -> bool:
    try:
        node = os.stat(name, dir_fd=anchor.fd, follow_symlinks=False)
    except FileNotFoundError:
        return False
    if not stat.S_ISREG(node.st_mode) or node.st_nlink != 1:
        raise ValueError("fieldwork media must be regular unaliased files")
    return True


@dataclass(frozen=True)
class FieldworkMediaInputs:
    """Selected literal media and observed per-file absence; not rights admission."""

    gallery_root: Path
    buffers: Mapping[str, bytes | None]
    expected_sha256: Mapping[str, str | None]

    def __post_init__(self) -> None:
        bodies, pins = dict(self.buffers), dict(self.expected_sha256)
        if set(bodies) != set(_NAMES) or set(pins) != set(_NAMES):
            raise ValueError("fieldwork media inventory differs")
        if (
            any(
                body is not None and (type(body) is not bytes or len(body) > _MAX_FILE)
                for body in bodies.values()
            )
            or sum(len(body) for body in bodies.values() if body is not None)
            > _MAX_TOTAL
        ):
            raise ValueError("fieldwork media size differs")
        for name, body in bodies.items():
            pin = pins[name]
            if body is None:
                if pin is not None:
                    raise ValueError("fieldwork media pin differs")
            elif (
                not isinstance(pin, str)
                or re.fullmatch(r"[0-9a-f]{64}", pin) is None
                or sha256(body).hexdigest() != pin
            ):
                raise ValueError("fieldwork media digest differs")
        gallery = Path(self.gallery_root).absolute()
        with DirectoryAnchor(gallery) as anchor:
            for name, body in bodies.items():
                present = _presence(anchor, name)
                if body is None and present:
                    raise ValueError("fieldwork media absence differs")
                if body is not None and (
                    not present
                    or read_regular_file(gallery / name, max_bytes=_MAX_FILE) != body
                ):
                    raise ValueError("fieldwork media source bytes differ")
            anchor.check()
        object.__setattr__(self, "gallery_root", gallery)
        object.__setattr__(self, "buffers", MappingProxyType(bodies))
        object.__setattr__(self, "expected_sha256", MappingProxyType(pins))

    def identity(self) -> dict[str, object]:
        return {
            "schema_version": "fieldwork-media-inputs.v1",
            "posture": "held_media_not_source_rights_or_scientific_admission",
            "url_base": _OUTPUT,
            "files": {
                name: None
                if body is None
                else {"sha256": sha256(body).hexdigest(), "bytes": len(body)}
                for name, body in self.buffers.items()
            },
        }

    def artifacts(self) -> list[tuple[str, str]]:
        """List the held output files for the map's bundle manifest."""
        return [
            (label, f"{_OUTPUT}/{name}")
            for _, label, name in FIELDWORK_MEDIA_FILES
            if self.buffers[name] is not None
        ]

    def stage(self, output_dir: Path) -> None:
        root = Path(output_dir).absolute()
        if not any(body is not None for body in self.buffers.values()):
            self.validate_staged(root)
            return
        with OwnedTreeWriter(
            root / _OUTPUT, max_bytes=_MAX_TOTAL, max_files=len(_NAMES)
        ) as writer:
            for name in _NAMES:
                body = self.buffers[name]
                if body is not None:
                    writer.write_bytes(name, body)
            writer.validate_attachment()
        self.validate_staged(root)

    def validate_staged(self, output_dir: Path) -> None:
        root = Path(output_dir).absolute()
        selected = {
            name: body for name, body in self.buffers.items() if body is not None
        }
        with DirectoryAnchor(root) as anchor:
            if not selected:
                try:
                    os.stat(_OUTPUT, dir_fd=anchor.fd, follow_symlinks=False)
                except FileNotFoundError:
                    anchor.check()
                    return
                raise ValueError("unselected fieldwork media was staged")
            with BoundedInputTree(
                root / _OUTPUT, max_bytes=_MAX_TOTAL, max_files=len(_NAMES)
            ) as tree:
                if set(tree.files) != set(selected) or set(tree.directories) != {""}:
                    raise ValueError("staged fieldwork media inventory differs")
                for name, body in selected.items():
                    if tree.read(root / _OUTPUT / name, max_bytes=_MAX_FILE) != body:
                        raise ValueError("staged fieldwork media differs")
                tree.validate()
            anchor.check()


def capture_fieldwork_media(
    gallery_root: Path, expected_sha256: Mapping[str, str | None]
) -> FieldworkMediaInputs:
    """Capture fixed gallery files with caller-pinned hashes and observed absence."""
    pins = dict(expected_sha256)
    if set(pins) != set(_NAMES) or any(
        pin is not None
        and (not isinstance(pin, str) or re.fullmatch(r"[0-9a-f]{64}", pin) is None)
        for pin in pins.values()
    ):
        raise ValueError("fieldwork media pins differ")
    gallery = Path(gallery_root).absolute()
    bodies: dict[str, bytes | None] = {}
    with DirectoryAnchor(gallery) as anchor:
        for name in _NAMES:
            present = _presence(anchor, name)
            if present != (pins[name] is not None):
                raise ValueError("fieldwork media presence differs")
            body = (
                read_regular_file(gallery / name, max_bytes=_MAX_FILE)
                if present
                else None
            )
            if body is not None and sha256(body).hexdigest() != pins[name]:
                raise ValueError("fieldwork media digest differs")
            bodies[name] = body
        if any(_presence(anchor, name) != (pins[name] is not None) for name in _NAMES):
            raise ValueError("fieldwork media presence changed")
        anchor.check()
    return FieldworkMediaInputs(gallery, bodies, pins)


def require_fieldwork_capture_owner(
    inputs: FieldworkMediaInputs | None, context_builder: object
) -> None:
    """Refuse captured fieldwork when a caller replaces either maintained owner."""
    if inputs is None:
        return
    from .. import layers
    from .fieldwork import build_fieldwork_point_layer

    if (
        type(inputs) is not FieldworkMediaInputs
        or context_builder is not layers.build_context_layers
        or getattr(layers, "build_fieldwork_point_layer", None)
        is not build_fieldwork_point_layer
    ):
        raise ValueError(
            "fieldwork media capture requires maintained context and fieldwork owners"
        )
