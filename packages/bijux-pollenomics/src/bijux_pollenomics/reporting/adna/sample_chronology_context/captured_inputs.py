"""Caller-pinned animal chronology registry and project input bodies."""

from collections.abc import Mapping
from contextlib import ExitStack
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import stat
from types import MappingProxyType

from bijux_pollenomics.core.filesystem import (
    BoundedInputTree,
    DirectoryAnchor,
    read_regular_file,
)

_REGISTRY = "project_registry.json"
_FILES = ("sample_master.json", "sample_chronology.json", "sample_sites.json")
_MAX_FILE = 64 * 1024 * 1024
_MAX_TOTAL = 128 * 1024 * 1024


def _registry_present(root: Path) -> bool:
    """Check registry presence without following missing or aliased ancestors."""
    with ExitStack() as stack:
        anchors = [stack.enter_context(DirectoryAnchor(root))]
        for component in ("adna", "governance", "source_library"):
            anchor = anchors[-1]
            try:
                node = os.stat(component, dir_fd=anchor.fd, follow_symlinks=False)
            except FileNotFoundError:
                for held in anchors:
                    held.check()
                return False
            if not stat.S_ISDIR(node.st_mode):
                raise ValueError("animal chronology source directory differs")
            child = stack.enter_context(DirectoryAnchor(anchor.path / component))
            if (node.st_dev, node.st_ino) != child.identity[:2]:
                raise ValueError("animal chronology source directory changed")
            anchors.append(child)
        try:
            node = os.stat(_REGISTRY, dir_fd=anchors[-1].fd, follow_symlinks=False)
        except FileNotFoundError:
            for held in anchors:
                held.check()
            return False
        if not stat.S_ISREG(node.st_mode) or node.st_nlink != 1:
            raise ValueError("animal chronology registry is not a regular file")
        for held in anchors:
            held.check()
        return True


def _project_set(registry: bytes) -> set[str]:
    try:
        doc = json.loads(registry)
        rows = doc["rows"]
        if doc["schema_version"] != "adna-source-library.v1" or not isinstance(
            rows, list
        ):
            raise ValueError
        names = [row["project_accession"] for row in rows]
        if any(
            not isinstance(x, str)
            or not x
            or x != x.strip()
            or Path(x).name != x
            or x in {".", ".."}
            for x in names
        ):
            raise ValueError
        if not names or len(set(names)) != len(names):
            raise ValueError
        return set(names)
    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        raise ValueError("animal chronology registry inventory differs") from exc


@dataclass(frozen=True)
class AnimalChronologyInputs:
    """Held chronology bytes and declared registry presence, not source admission."""

    context_root: Path
    buffers: Mapping[str, bytes] | None
    expected_sha256: Mapping[str, str] | None

    def __post_init__(self) -> None:
        if (self.buffers is None) != (self.expected_sha256 is None):
            raise ValueError("animal chronology pin inventory differs")
        if self.buffers is None and _registry_present(
            Path(self.context_root).absolute()
        ):
            raise ValueError("animal chronology registry presence differs")
        if self.buffers is not None:
            bodies = dict(self.buffers)
            pins = dict(self.expected_sha256 or {})
            if _REGISTRY not in bodies or set(bodies) != set(pins):
                raise ValueError("animal chronology pin inventory differs")
            if (
                any(
                    type(body) is not bytes or len(body) > _MAX_FILE
                    for body in bodies.values()
                )
                or sum(map(len, bodies.values())) > _MAX_TOTAL
            ):
                raise ValueError("animal chronology input size differs")
            if any(
                not isinstance(pin, str)
                or re.fullmatch(r"[0-9a-f]{64}", pin) is None
                or sha256(bodies[name]).hexdigest() != pin
                for name, pin in pins.items()
            ):
                raise ValueError("animal chronology input digest differs")
            projects = _project_set(bodies[_REGISTRY])
            expected_names = {_REGISTRY} | {
                f"projects/{project}/{name}" for project in projects for name in _FILES
            }
            if set(bodies) != expected_names:
                raise ValueError("animal chronology project inputs differ")
            object.__setattr__(self, "buffers", MappingProxyType(bodies))
            object.__setattr__(self, "expected_sha256", MappingProxyType(pins))
        object.__setattr__(self, "context_root", Path(self.context_root).absolute())

    def identity(self) -> dict[str, object]:
        return {
            "schema_version": "animal-chronology-inputs.v1",
            "posture": "held_bytes_not_scientific_admission",
            "registry_present": self.buffers is not None,
            "files": None
            if self.buffers is None
            else {
                name: {"sha256": sha256(body).hexdigest(), "bytes": len(body)}
                for name, body in self.buffers.items()
            },
        }


def capture_animal_chronology_inputs(
    context_root: Path, expected_sha256: Mapping[str, str] | None
) -> AnimalChronologyInputs:
    """Capture pinned selected bodies and declared absence; reads are sequential."""
    root = Path(context_root).absolute()
    present = _registry_present(root)
    if present != (expected_sha256 is not None):
        raise ValueError("animal chronology registry presence differs")
    if not present:
        return AnimalChronologyInputs(root, None, None)
    assert expected_sha256 is not None
    pins = dict(expected_sha256)
    source = root / "adna/governance/source_library"
    registry = read_regular_file(source / _REGISTRY, max_bytes=_MAX_FILE)
    projects = _project_set(registry)
    expected_names = {_REGISTRY} | {
        f"projects/{project}/{name}" for project in projects for name in _FILES
    }
    if set(pins) != expected_names:
        raise ValueError("animal chronology project pins differ")
    if any(
        not isinstance(pin, str) or re.fullmatch(r"[0-9a-f]{64}", pin) is None
        for pin in pins.values()
    ):
        raise ValueError("animal chronology project pins differ")
    if sha256(registry).hexdigest() != pins[_REGISTRY]:
        raise ValueError("animal chronology input digest differs")
    buffers = {_REGISTRY: registry}
    with BoundedInputTree(
        source / "projects", max_bytes=_MAX_TOTAL - len(registry), max_files=10000
    ) as tree:
        actual = {name for name in tree.directories if name and "/" not in name}
        if actual != projects or any("/" not in name for name in tree.files):
            raise ValueError("animal chronology project directories differ")
        for name in sorted(expected_names - {_REGISTRY}):
            body = tree.read(source / name, max_bytes=_MAX_FILE)
            if sha256(body).hexdigest() != pins[name]:
                raise ValueError("animal chronology input digest differs")
            buffers[name] = body
        tree.validate()
        if read_regular_file(source / _REGISTRY, max_bytes=_MAX_FILE) != registry:
            raise ValueError("animal chronology registry changed")
    return AnimalChronologyInputs(root, buffers, pins)
