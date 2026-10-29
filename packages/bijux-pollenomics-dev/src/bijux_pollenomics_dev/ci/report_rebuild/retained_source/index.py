"""One pinned portable source-transport registry and scoped capsule readers."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

from ..contracts import require_relative_path
from .capsule import native_reference_members, validate_physical_capsule
from .descriptor import (
    MAX_DESCRIPTOR_BYTES,
    Descriptor,
    decode,
    json_object,
    normalize_members,
    object_fields,
    pinned_bytes,
)
from .generated import reconstruct
from .objects import (
    MAX_TOTAL_BYTES,
    hexadecimal,
    physical,
    read_blob,
    read_blobs,
    require,
)

INDEX_PATH = "configs/ci/source-retention/index.json"
INDEX_SHA256 = "1f4cfd74f21074bddbaf61c93ca9f1f95430eb07ee9c91bd7a58556206241b08"
INDEX_BYTES = 2638


def _seal(path: Path) -> tuple[int, int, int, int, int]:
    physical(path)
    require(
        path.is_file() and path.stat().st_nlink == 1, "physical metadata file required"
    )
    stat = path.stat()
    return stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns


def _refs(repository: Path) -> tuple[tuple[str, bytes], ...]:
    """Detect current ref movement without launching Git for every payload callback."""
    git = repository / ".git"
    physical(git)
    require(git.is_dir(), "normal physical clone Git directory required")
    grafts = git / "info/grafts"
    physical(grafts)
    require(not grafts.exists(), "legacy Git graft ancestry is not supported")
    head = git / "HEAD"
    _seal(head)
    raw = head.read_bytes()
    require(len(raw) <= 4096, "bounded Git HEAD required")
    rows = [("HEAD", raw)]
    if raw.startswith(b"ref: "):
        ref = raw[5:].decode("ascii").strip()
        require_relative_path(ref, "Git HEAD ref")
        require(ref.startswith("refs/heads/"), "ordinary current branch ref required")
        path = git / ref
        if path.exists() or path.is_symlink():
            _seal(path)
            body = path.read_bytes()
            require(len(body) <= 4096, "bounded Git ref required")
            rows.append((ref, body))
    packed = git / "packed-refs"
    if packed.exists() or packed.is_symlink():
        _seal(packed)
        require(
            packed.stat().st_size <= 8 * 1024**2, "packed ref metadata bound exceeded"
        )
        rows.append(("packed-refs", packed.read_bytes()))
    return tuple(rows)


@lru_cache(maxsize=8)
def _index_buffer(
    path: Path, checksum: str, size: int, seal: tuple[int, int, int, int, int]
) -> dict[str, Any]:
    del seal
    row = object_fields(
        json_object(pinned_bytes(path, checksum, size, 4 * 1024**2)),
        {"schema_version", "capsules", "source_revisions"},
    )
    require(
        row["schema_version"] == "retained-source-index.v1"
        and type(row["capsules"]) is dict
        and type(row["source_revisions"]) is dict,
        "configured source index schema differs",
    )
    for prefix, entry in row["capsules"].items():
        require_relative_path(prefix, "indexed source capsule")
        entry = object_fields(entry, {"descriptor", "sha256", "bytes"})
        require_relative_path(entry["descriptor"], "indexed descriptor")
        require(
            hexadecimal(entry["sha256"], 64)
            and type(entry["bytes"]) is int
            and 0 < entry["bytes"] <= MAX_DESCRIPTOR_BYTES,
            "pinned source descriptor entry required",
        )
    for old, new in row["source_revisions"].items():
        require(
            hexadecimal(old, 40) and hexadecimal(new, 40),
            "exact old-to-reachable source revision required",
        )
    return row


def configured_index(repository: Path) -> dict[str, Any]:
    """Authenticate the exact configured registry; missing migrations never fall back."""
    path = repository / INDEX_PATH
    return _index_buffer(path, INDEX_SHA256, INDEX_BYTES, _seal(path))


def source_revision(repository: Path, historical: str) -> str:
    """Map source storage only; never relabel the native epoch that executed."""
    require(hexadecimal(historical, 40), "literal historical source revision required")
    return str(
        configured_index(repository)["source_revisions"].get(historical, historical)
    )


@dataclass
class SourceCapsule:
    """Per-call authenticated source buffers; never a physical path or execution authority."""

    repository: Path
    prefix: str
    descriptor_name: str
    descriptor: Descriptor
    controls: tuple[tuple[Path, tuple[int, int, int, int, int]], ...]
    refs: tuple[tuple[str, bytes], ...]
    _payloads: dict[str, bytes] = field(default_factory=dict)
    _validated: bool = False

    @property
    def detached(self) -> frozenset[str]:
        """Return exact logical names whose physical copies are absent."""
        return self.descriptor.detached

    def fresh(self) -> None:
        """Reject changed pinned metadata, aliases, or current ref context."""
        require(
            all(_seal(path) == seal for path, seal in self.controls)
            and _refs(self.repository) == self.refs,
            "source reader metadata/ref context changed",
        )

    def validate(self) -> frozenset[str]:
        """Check all original identities once and retain a bounded per-call source cache."""
        self.fresh()
        validate_physical_capsule(
            self.repository,
            self.prefix,
            self.descriptor.members,
            self.detached,
            self.descriptor_name,
            self.descriptor.capture,
            self.descriptor.capture_name,
        )
        self._payloads = read_blobs(
            self.repository, self.descriptor.resolve(self.repository)
        )
        for row in self.descriptor.generated:
            self._payloads[row["member"]] = reconstruct(
                row, self.descriptor.members[row["member"]]
            )
        require(
            sum(len(body) for body in self._payloads.values()) <= MAX_TOTAL_BYTES,
            "scoped source buffer ceiling exceeded",
        )
        require(
            set(self._payloads) == set(self.detached), "source body population differs"
        )
        self.fresh()
        self._validated = True
        return self.detached

    def read_source(self, name: str) -> bytes:
        """Authenticate one logical read; validated packet callbacks reuse their batch proof."""
        self.fresh()
        require_relative_path(name, "retained source read")
        require(name in self.descriptor.members, "unlisted retained member read")
        expected = self.descriptor.members[name]
        if name in self._payloads:
            return self._payloads[name]
        if name in self.detached:
            generated = [
                row for row in self.descriptor.generated if row["member"] == name
            ]
            if generated:
                return reconstruct(generated[0], expected)
            rows = self.descriptor.resolve(self.repository, frozenset({name}))
            require(len(rows) == 1, "exact declared Git member required")
            body = read_blob(self.repository, rows[0])
            self.fresh()
            return body
        path = self.repository / self.prefix / name
        return (
            pinned_bytes(path, expected["sha256"], expected["bytes"], 128 * 1024**2)
            if expected["bytes"]
            else self._empty(path, expected)
        )

    def _empty(self, path: Path, expected: dict[str, Any]) -> bytes:
        physical(path)
        require(
            path.is_file() and path.stat().st_nlink == 1 and path.stat().st_size == 0,
            "empty retained member differs",
        )
        import hashlib

        require(
            expected["sha256"] == hashlib.sha256(b"").hexdigest(),
            "empty retained member digest differs",
        )
        return b""


def _descriptor(
    repository: Path,
    prefix: str,
    members: Any,
    *,
    descriptor_name: str | None = None,
    descriptor_sha256: str | None = None,
    descriptor_bytes: int | None = None,
) -> SourceCapsule:
    physical(repository)
    require_relative_path(prefix, "source capsule prefix")
    controls = []
    if descriptor_name is None:
        require(
            descriptor_sha256 is None and descriptor_bytes is None,
            "partial explicit descriptor authority",
        )
        index = configured_index(repository)
        require(
            prefix in index["capsules"],
            "source capsule is not in pinned migration index",
        )
        entry = index["capsules"][prefix]
        descriptor_name, descriptor_sha256, descriptor_bytes = (
            entry["descriptor"],
            entry["sha256"],
            entry["bytes"],
        )
        controls.append(repository / INDEX_PATH)
    require(
        type(descriptor_name) is str
        and type(descriptor_sha256) is str
        and type(descriptor_bytes) is int,
        "exact complete descriptor authority required",
    )
    assert (
        descriptor_name is not None
        and descriptor_sha256 is not None
        and descriptor_bytes is not None
    )
    require_relative_path(descriptor_name, "source descriptor name")
    path = repository / prefix / descriptor_name
    raw = pinned_bytes(path, descriptor_sha256, descriptor_bytes, MAX_DESCRIPTOR_BYTES)
    descriptor = decode(raw, members, capsule_prefix=prefix)
    controls.append(path)
    capture = repository / prefix / descriptor.capture_name
    require(
        _capture_members(
            capture,
            descriptor.capture["sha256"],
            descriptor.capture["bytes"],
            _seal(capture),
        )
        == descriptor.members,
        "supplied original member catalogue differs from pinned capture buffer",
    )
    controls.append(capture)
    return SourceCapsule(
        repository,
        prefix,
        descriptor_name,
        descriptor,
        tuple((path, _seal(path)) for path in controls),
        _refs(repository),
    )


def validated_descriptor(
    repository: Path, prefix: str, members: Any, **authority: Any
) -> SourceCapsule:
    """Return a scoped batch-validated resolver for CAS packet payload callbacks."""
    result = _descriptor(repository, prefix, members, **authority)
    result.validate()
    return result


def validate_capsule(
    repository: Path, prefix: str, members: Any, **authority: Any
) -> frozenset[str]:
    """Validate complete retained source custody and return exact detached logical names."""
    return validated_descriptor(repository, prefix, members, **authority).detached


def read_source(
    repository: Path, prefix: str, name: str, members: Any, **authority: Any
) -> bytes:
    """Read one exact member; packet loops should retain a validated scoped resolver."""
    return _descriptor(repository, prefix, members, **authority).read_source(name)


read_member = read_source


@lru_cache(maxsize=2)
def _capture_members(
    path: Path, checksum: str, size: int, seal: tuple[int, int, int, int, int]
) -> dict[str, dict[str, Any]]:
    del seal
    capture = json_object(pinned_bytes(path, checksum, size, 128 * 1024**2))
    if capture.get("schema_version") == "native-r-finite-covariance-capture.v1":
        return native_reference_members(capture)
    if capture.get("schema_version") in {
        "qualified-native-r-capture.v1",
        "qualified-native-r-annulus-capture.v1",
        "qualified-native-r-count-domain-capture.v1",
    }:
        from .capsule import native_oracle_members

        return native_oracle_members(capture)
    if capture.get("schema_version") == "lra-live-r-certification.v2":
        from .capsule import r_certificate_members

        return r_certificate_members(capture)
    field = "members" if "members" in capture else "files"
    require(field in capture, "capture has no original member catalogue")
    return normalize_members(capture[field])


def read_source_path(repository: Path, logical_path: str | Path) -> bytes:
    """Resolve only an exact indexed logical source path, without materializing it."""
    raw = Path(logical_path)
    if raw.is_absolute():
        require(
            raw.is_relative_to(repository), "retained source path escaped repository"
        )
        logical = raw.relative_to(repository).as_posix()
    else:
        logical = raw.as_posix()
    require_relative_path(logical, "retained logical path")
    index = configured_index(repository)
    matches = [
        prefix for prefix in index["capsules"] if logical.startswith(prefix + "/")
    ]
    require(len(matches) == 1, "retained source path has no unique indexed capsule")
    prefix = matches[0]
    entry = index["capsules"][prefix]
    path = repository / prefix / entry["descriptor"]
    data = json_object(
        pinned_bytes(path, entry["sha256"], entry["bytes"], MAX_DESCRIPTOR_BYTES)
    )
    capture = object_fields(data["capture"], {"name", "sha256", "bytes"})
    require_relative_path(capture["name"], "indexed capture name")
    capture_path = repository / prefix / capture["name"]
    members = _capture_members(
        capture_path, capture["sha256"], capture["bytes"], _seal(capture_path)
    )
    return read_source(repository, prefix, logical[len(prefix) + 1 :], members)
