"""Saved evidence inspection requiring exact raw replay before member access."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path

from bijux_pollenomics.adna.species.homo_sapiens.materialization.members.contracts import (
    MEMBER_FILES,
    SCHEMA_VERSION,
    canonical_bytes,
    object_mapping,
    strings,
    text,
    validate_boundary,
    validate_digest,
)
from bijux_pollenomics.adna.species.homo_sapiens.materialization.members.projection import (
    iter_member_documents,
)
from bijux_pollenomics.adna.species.homo_sapiens.materialization.members.validation import (
    nonnegative_integer,
    validate_member_ownership,
)
from bijux_pollenomics.adna.species.homo_sapiens.materialization.reconciliation import (
    reconcile_aadr_panels,
)

from ..inputs import load_aadr_release_inputs
from .publication import implementation_identity


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("AADR duplicate JSON key")
        result[key] = value
    return result


def _decode(content: bytes) -> dict[str, object]:
    return object_mapping(json.loads(content, object_pairs_hook=_unique_object))


def _documents(
    directory: Path, descriptors: dict[str, object]
) -> Iterator[tuple[str, dict[str, object]]]:
    for name in MEMBER_FILES:
        descriptor = object_mapping(descriptors[name])
        size = nonnegative_integer(descriptor["byte_count"])
        count = nonnegative_integer(descriptor["record_count"])
        digest = text(descriptor["sha256"])
        validate_digest(digest)
        path = directory / name
        if path.is_symlink() or not path.is_file():
            raise ValueError("AADR member must be a regular non-symlink file")
        actual_hash = sha256()
        actual_size = actual_count = 0
        with path.open("rb") as stream:
            for line in stream:
                record = _decode(line)
                if canonical_bytes(record) != line:
                    raise ValueError(
                        "AADR evidence table must use canonical finite JSON lines"
                    )
                actual_hash.update(line)
                actual_size += len(line)
                actual_count += 1
                yield name, record
        if (actual_size, actual_hash.hexdigest(), actual_count) != (
            size,
            digest,
            count,
        ):
            raise ValueError("AADR member table identity mismatch")


@dataclass(frozen=True, slots=True, init=False)
class AadrMemberInspection:
    """Non-admitting evidence lookup after one verified raw-replay inspection."""

    directory: Path
    manifest_bytes: bytes

    def __init__(self) -> None:
        raise TypeError("Use inspect_aadr_member_bundle for raw-replayed inspection")

    @classmethod
    def _verified(cls, directory: Path, content: bytes) -> AadrMemberInspection:
        result = object.__new__(cls)
        object.__setattr__(result, "directory", directory)
        object.__setattr__(result, "manifest_bytes", content)
        return result

    @property
    def manifest_sha256(self) -> str:
        return sha256(self.manifest_bytes).hexdigest()

    def _records(self) -> Iterator[tuple[str, dict[str, object]]]:
        manifest = _decode(self.manifest_bytes)
        for path in (self.directory, *self.directory.parents):
            if path.is_symlink():
                raise ValueError("AADR saved bundle cannot use symlink paths")
        if (self.directory / "manifest.json").read_bytes() != self.manifest_bytes or {
            p.name for p in self.directory.iterdir()
        } != {"manifest.json", *MEMBER_FILES}:
            raise ValueError("AADR inspected bundle changed")
        yield from _documents(self.directory, object_mapping(manifest["files"]))
        if (self.directory / "manifest.json").read_bytes() != self.manifest_bytes:
            raise ValueError("AADR inspected bundle changed")

    def member_ids(self) -> tuple[str, ...]:
        """Return IDs only after the complete current file inventory verifies."""
        return tuple(
            text(row["member_key"])
            for name, row in self._records()
            if name == "members.ndjson"
        )

    def member_evidence(self, key: str) -> dict[str, object]:
        """Return one member and every raw row/claim, without choosing alternatives."""
        selected: dict[str, object] | None = None
        for name, row in self._records():
            if name == "members.ndjson" and row["member_key"] == key:
                selected = row
        if selected is None:
            raise KeyError(key)
        row_keys = set(strings(selected["source_row_keys"]))
        result: dict[str, object] = {
            "member": selected,
            "source_rows": [],
            "coordinate_claims": [],
            "chronology_claims": [],
            "source_files": [],
        }
        raw_rows: list[dict[str, object]] = []
        coordinates: list[dict[str, object]] = []
        chronology: list[dict[str, object]] = []
        for name, row in self._records():
            if name == "source_files.json":
                result["source_files"] = row["source_files"]
            elif (
                name == "source_rows.ndjson"
                and object_mapping(row["source_row"])["key"] in row_keys
            ):
                raw_rows.append(row)
            elif name == "coordinate_claims.ndjson" and row["owner_key"] == key:
                coordinates.append(row)
            elif name == "chronology_claims.ndjson" and row["owner_key"] == key:
                chronology.append(row)
        result.update(
            source_rows=raw_rows,
            coordinate_claims=coordinates,
            chronology_claims=chronology,
        )
        return result


def inspect_aadr_member_bundle(
    directory: Path, *, expected_sha256: str, data_root: Path
) -> AadrMemberInspection:
    """Verify exact tables/ownership and reproduce their bytes from governed raw."""
    validate_digest(expected_sha256)
    for path in (directory, *directory.parents):
        if path.is_symlink():
            raise ValueError("AADR saved bundle cannot use symlink paths")
    if {p.name for p in directory.iterdir()} != {"manifest.json", *MEMBER_FILES} or any(
        p.is_symlink() or not p.is_file() for p in directory.iterdir()
    ):
        raise ValueError("AADR member inventory mismatch")
    content = (directory / "manifest.json").read_bytes()
    if sha256(content).hexdigest() != expected_sha256:
        raise ValueError("AADR member manifest identity mismatch")
    manifest = _decode(content)
    if (
        canonical_bytes(manifest) != content
        or manifest.get("schema_version") != SCHEMA_VERSION
    ):
        raise ValueError("AADR member manifest schema/encoding mismatch")
    validate_boundary(manifest["admission_boundary"])
    descriptors = object_mapping(manifest["files"])
    if set(descriptors) != set(MEMBER_FILES):
        raise ValueError("AADR member descriptor inventory mismatch")
    release = object_mapping(manifest["release_manifest"])
    release_digest = text(release["sha256"])
    counts = validate_member_ownership(
        _documents(directory, descriptors), release_manifest_sha256=release_digest
    )
    if canonical_bytes(counts) != canonical_bytes(manifest["denominators"]):
        raise ValueError("AADR member denominators mismatch")
    implementation = implementation_identity()
    if manifest["implementation"] != implementation:
        raise ValueError("AADR member producer identity mismatch")
    inputs = load_aadr_release_inputs(data_root, text(release["source_release"]))
    actual_release = {
        "source_release": inputs.source_release,
        "logical_path": inputs.logical_manifest_path,
        "sha256": inputs.manifest_sha256,
        "byte_count": len(inputs.manifest_bytes),
    }
    if canonical_bytes(release) != canonical_bytes(actual_release):
        raise ValueError("AADR raw release identity mismatch")
    reconciliation = reconcile_aadr_panels(inputs.source_tables)
    hashes = {name: sha256() for name in MEMBER_FILES}
    sizes = dict.fromkeys(MEMBER_FILES, 0)
    numbers = dict.fromkeys(MEMBER_FILES, 0)
    for name, record in iter_member_documents(
        reconciliation, release_manifest_sha256=inputs.manifest_sha256
    ):
        payload = canonical_bytes(record)
        hashes[name].update(payload)
        sizes[name] += len(payload)
        numbers[name] += 1
    expected = {
        name: {
            "byte_count": sizes[name],
            "sha256": hashes[name].hexdigest(),
            "record_count": numbers[name],
        }
        for name in MEMBER_FILES
    }
    if canonical_bytes(expected) != canonical_bytes(descriptors):
        raise ValueError("AADR raw replay/member projection mismatch")
    inputs.verify_unchanged()
    if (
        implementation_identity() != implementation
        or (directory / "manifest.json").read_bytes() != content
    ):
        raise ValueError("AADR input or producer changed during inspection")
    # Exhaust a final table read so mutation during raw replay cannot pass.
    for _ in _documents(directory, descriptors):
        pass
    return AadrMemberInspection._verified(directory, content)
