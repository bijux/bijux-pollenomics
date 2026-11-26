"""Capture the species-owned inputs used by animal atlas point selection."""

from collections.abc import Iterator, Mapping
from contextlib import ExitStack, contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from hashlib import sha256
import os
from pathlib import Path
import re
import stat
from types import MappingProxyType

from bijux_pollenomics.core.filesystem import BoundedInputTree, DirectoryAnchor

from ...species.definitions import build_species_support_matrix

ANIMAL_POINT_PATHS = (
    "normalized/locality_summaries.json",
    "normalized/sample_records.json",
    "normalized/coordinate_provenance.json",
    "normalized/site_evidence.json",
    "normalized/project_summaries.json",
    "manifests/citation_manifest.csv",
    "review/species_review.json",
    "reports/support_summary.json",
)
_MAX_FILE_BYTES = 64 * 1024 * 1024
_MAX_CAPTURE_BYTES = 256 * 1024 * 1024
_MAX_TREE_BYTES = 1024 * 1024 * 1024
_MAX_TREE_FILES = 50000


def _species() -> set[str]:
    return {
        item.slug
        for item in build_species_support_matrix()
        if item.latin_name != "Homo sapiens"
    }


@dataclass(frozen=True)
class AnimalPointInputs:
    """Held point-owner bytes and observed absence, excluding chronology corpus."""

    context_root: Path
    buffers: Mapping[str, Mapping[str, bytes | None] | None]
    expected_sha256: Mapping[str, Mapping[str, str | None] | None]

    def __post_init__(self) -> None:
        if set(self.buffers) != _species() or set(self.expected_sha256) != _species():
            raise ValueError("animal point species inventory differs")
        result: dict[str, Mapping[str, bytes | None] | None] = {}
        pins: dict[str, Mapping[str, str | None] | None] = {}
        for slug, rows in self.buffers.items():
            expected = self.expected_sha256[slug]
            if rows is None:
                if expected is not None:
                    raise ValueError("animal point pin inventory differs")
                result[slug] = None
                pins[slug] = None
                continue
            if expected is None or set(expected) != set(ANIMAL_POINT_PATHS):
                raise ValueError("animal point pin inventory differs")
            if set(rows) != set(ANIMAL_POINT_PATHS) or any(
                body is not None
                and (type(body) is not bytes or len(body) > _MAX_FILE_BYTES)
                for body in rows.values()
            ):
                raise ValueError("animal point file inventory differs")
            if any(
                (sha256(body).hexdigest() if body is not None else None)
                != expected[name]
                for name, body in rows.items()
            ):
                raise ValueError("animal point captured digest differs")
            result[slug] = MappingProxyType(dict(rows))
            pins[slug] = MappingProxyType(dict(expected))
        if (
            sum(
                len(body)
                for rows in result.values()
                if rows is not None
                for body in rows.values()
                if body is not None
            )
            > _MAX_CAPTURE_BYTES
        ):
            raise ValueError("animal point captured bytes exceed limit")
        object.__setattr__(self, "context_root", Path(self.context_root).absolute())
        object.__setattr__(self, "buffers", MappingProxyType(result))
        object.__setattr__(self, "expected_sha256", MappingProxyType(pins))

    def identity(self) -> dict[str, object]:
        """Report selected point bodies and absence, excluding chronology."""
        return {
            "schema_version": "animal-atlas-point-inputs.v1",
            "posture": "selected_point_bytes_only_not_source_or_scientific_admission",
            "species": {
                slug: None
                if files is None
                else {
                    name: None
                    if body is None
                    else {"sha256": sha256(body).hexdigest(), "bytes": len(body)}
                    for name, body in files.items()
                }
                for slug, files in self.buffers.items()
            },
        }

    def species_present(self, slug: str) -> bool:
        if slug not in self.buffers:
            raise ValueError("unknown animal point species")
        return self.buffers[slug] is not None

    def read(self, slug: str, relative: str) -> bytes | None:
        if slug not in self.buffers or relative not in ANIMAL_POINT_PATHS:
            raise ValueError("unknown animal point input")
        rows = self.buffers[slug]
        return None if rows is None else rows[relative]


def capture_animal_point_inputs(
    context_root: Path, expected: Mapping[str, Mapping[str, str | None] | None]
) -> AnimalPointInputs:
    """Capture the exact caller-pinned point inventory, including absent entries."""
    if set(expected) != _species():
        raise ValueError("animal point species inventory differs")
    for declared in expected.values():
        if declared is not None and (
            set(declared) != set(ANIMAL_POINT_PATHS)
            or any(
                pin is not None
                and (
                    not isinstance(pin, str)
                    or re.fullmatch(r"[0-9a-f]{64}", pin) is None
                )
                for pin in declared.values()
            )
        ):
            raise ValueError("animal point file pin inventory differs")
    root = Path(context_root).absolute()
    species_root = root / "adna" / "species"
    result: dict[str, dict[str, bytes | None] | None] = {}
    total = 0
    with DirectoryAnchor(species_root) as anchor, ExitStack() as stack:
        trees: dict[str, BoundedInputTree] = {}
        for slug, pins in expected.items():
            try:
                node = os.stat(slug, dir_fd=anchor.fd, follow_symlinks=False)
            except FileNotFoundError:
                if pins is not None:
                    raise ValueError("animal point species presence differs") from None
                result[slug] = None
                continue
            if pins is None or not stat.S_ISDIR(node.st_mode):
                raise ValueError("animal point species presence differs")
            tree = stack.enter_context(
                BoundedInputTree(
                    species_root / slug,
                    max_bytes=_MAX_TREE_BYTES,
                    max_files=_MAX_TREE_FILES,
                )
            )
            if (node.st_dev, node.st_ino) != (
                tree.anchor.identity[0],
                tree.anchor.identity[1],
            ):
                raise ValueError("animal point species identity differs")
            trees[slug] = tree
            rows: dict[str, bytes | None] = {}
            for relative, pin in pins.items():
                if (relative in tree.files) != (pin is not None):
                    raise ValueError("animal point file presence differs")
                if pin is None:
                    rows[relative] = None
                else:
                    body = tree.read(
                        species_root / slug / relative, max_bytes=_MAX_FILE_BYTES
                    )
                    total += len(body)
                    if total > _MAX_CAPTURE_BYTES:
                        raise ValueError("animal point captured bytes exceed limit")
                    if sha256(body).hexdigest() != pin:
                        raise ValueError("animal point file digest differs")
                    rows[relative] = body
            result[slug] = rows
        for slug, pins in expected.items():
            try:
                node = os.stat(slug, dir_fd=anchor.fd, follow_symlinks=False)
            except FileNotFoundError:
                if pins is not None:
                    raise ValueError("animal point species presence changed") from None
            else:
                if pins is None or not stat.S_ISDIR(node.st_mode):
                    raise ValueError("animal point species presence changed")
        for tree in trees.values():
            tree.validate()
        anchor.check()
    return AnimalPointInputs(root, result, expected)


@dataclass
class _PointInputLease:
    inputs: AnimalPointInputs
    active: bool = True


_ACTIVE_POINT_INPUTS: ContextVar[_PointInputLease | None] = ContextVar(
    "animal_point_inputs", default=None
)


@contextmanager
def use_animal_point_inputs(
    inputs: AnimalPointInputs, context_root: Path
) -> Iterator[None]:
    """Bind held point inputs to one synchronous animal bundle call."""
    if (
        Path(context_root).absolute() != inputs.context_root
        or _ACTIVE_POINT_INPUTS.get() is not None
    ):
        raise ValueError("animal point capture requires its bound context")
    lease = _PointInputLease(inputs)
    token = _ACTIVE_POINT_INPUTS.set(lease)
    try:
        yield
    finally:
        lease.active = False
        _ACTIVE_POINT_INPUTS.reset(token)


def selected_point_inputs() -> AnimalPointInputs | None:
    """Return the input held by the current point-bundle call, if any."""
    lease = _ACTIVE_POINT_INPUTS.get()
    if lease is not None and not lease.active:
        raise ValueError("animal point capture lease expired")
    return lease.inputs if lease is not None else None


def read_point_file(species_root: Path, relative: str) -> bytes | None:
    """Read held bytes in a capture call, preserving legacy reads otherwise."""
    inputs = selected_point_inputs()
    if inputs is not None:
        if species_root.absolute().parent != inputs.context_root / "adna" / "species":
            raise ValueError("animal point input path differs")
        return inputs.read(species_root.name, relative)
    path = species_root / relative
    return path.read_bytes() if path.is_file() else None
