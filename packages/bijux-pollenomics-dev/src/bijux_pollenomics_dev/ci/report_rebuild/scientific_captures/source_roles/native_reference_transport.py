"""Authenticate finite native reference IO extensions without new execution."""

from __future__ import annotations

import hashlib
from pathlib import Path

from ...contracts import JsonObject, ReportRebuildError
from ...ownership import _regular_confined_file
from ...retained_source import SourceCapsule

_NATIVE_REFERENCE_TRANSPORT_CONTRACTS: dict[
    str, tuple[int, str, tuple[tuple[bytes, bytes], ...]]
] = {
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/lra_reference/contracts.py": (
        7076,
        "88a147b637044b62e4221d00ebba8e4eef15d8973f134a590092a3be321e32be",
        (
            (
                b"""
def _load_lock(path: Path) -> ReferenceLock:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
""",
                b"""
def _load_lock(path: Path, *, raw: bytes | None = None) -> ReferenceLock:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
""",
            ),
            (
                b"""
    value = json.loads(path.read_bytes(), object_pairs_hook=unique)
    if (
""",
                b"""
    value = json.loads(
        path.read_bytes() if raw is None else raw, object_pairs_hook=unique
    )
    if (
""",
            ),
            (
                b'''
def load_lock(path: Path) -> ReferenceLock:
    """Malformed or unsupported lock content is always a typed refusal."""
    try:
        result = _load_lock(path)
        reference = result.payload["reference"]
''',
                b'''
def load_lock(path: Path, *, raw: bytes | None = None) -> ReferenceLock:
    """Malformed or unsupported lock content is always a typed refusal."""
    try:
        result = _load_lock(path, raw=raw)
        reference = result.payload["reference"]
''',
            ),
        ),
    ),
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/lra_reference/evidence.py": (
        17083,
        "9bd4b32cdaba1a1cd313ad3209d3e63b5ea17a2a41b1125070cf3bd2c4472a0c",
        (
            (
                b"""import re
from typing import Any

""",
                b"""import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from bijux_pollenomics_dev.ci.report_rebuild.retained_source import SourceCapsule

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError

""",
            ),
            (
                b'''
def file_inventory(root: Path) -> dict[str, dict[str, Any]]:
    """Inventory regular evidence files by digest and byte count."""
''',
                b'''
def file_inventory(
    root: Path, *, source_transport: SourceCapsule | None = None
) -> dict[str, dict[str, Any]]:
    """Inventory regular evidence files by digest and byte count."""
''',
            ),
            (
                b"""            raise ReferenceRefusal("Evidence trees may contain only regular files")
    return result
""",
                b"""            raise ReferenceRefusal("Evidence trees may contain only regular files")
    if source_transport is not None:
        detached = frozenset(
            {
                "source-domains/r_support.R",
                "source-domains/run_source_domains.py",
                "source-domains/source_domains.R",
                "source-lock.json",
            }
        )
        if (
            source_transport.repository / source_transport.prefix != root
            or source_transport.descriptor.capture_name != "certificate.json"
            or source_transport.detached != detached
        ):
            raise ReferenceRefusal("Retained reference transport scope differs")
        try:
            source_transport.fresh()
            expected = (set(source_transport.descriptor.members) - set(detached)) | {
                "certificate.json",
                source_transport.descriptor_name,
            }
            if set(result) != expected:
                raise ReferenceRefusal("Retained reference physical projection differs")
            result.pop(source_transport.descriptor_name)
            for name in sorted(detached):
                data = source_transport.read_source(name)
                result[name] = {
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "byte_count": len(data),
                }
            source_transport.fresh()
        except ReportRebuildError as error:
            raise ReferenceRefusal(str(error)) from error
    return result
""",
            ),
            (
                b"""    expected_run: tuple[str, int, int] | None = None,
) -> dict[str, Any]:
""",
                b"""    expected_run: tuple[str, int, int] | None = None,
    source_transport: SourceCapsule | None = None,
) -> dict[str, Any]:
""",
            ),
            (
                b"""            raise ReferenceRefusal("Certification source lock differs")
        inventory = file_inventory(root)
        inventory.pop("certificate.json", None)
""",
                b"""            raise ReferenceRefusal("Certification source lock differs")
        inventory = file_inventory(root, source_transport=source_transport)
        inventory.pop("certificate.json", None)
""",
            ),
            (
                b"""        lock_path = root / "source-lock.json"
        if hashlib.sha256(lock_path.read_bytes()).hexdigest() != expected_lock_sha256:
            raise ReferenceRefusal("Bundled source-lock bytes differ")
        lock = load_lock(lock_path)
        if certificate.get("profile_id") != lock.payload["profile_id"]:
""",
                b"""        lock_path = root / "source-lock.json"
        lock_raw = (
            lock_path.read_bytes()
            if source_transport is None
            else source_transport.read_source("source-lock.json")
        )
        if hashlib.sha256(lock_raw).hexdigest() != expected_lock_sha256:
            raise ReferenceRefusal("Bundled source-lock bytes differ")
        lock = load_lock(lock_path, raw=lock_raw)
        if certificate.get("profile_id") != lock.payload["profile_id"]:
""",
            ),
            (
                b"""        validate_source_domains(
            root / "source-domains", lock.payload["reference"]["sha256"]
        )
""",
                b"""        validate_source_domains(
            root / "source-domains",
            lock.payload["reference"]["sha256"],
            read_source=(
                None if source_transport is None else source_transport.read_source
            ),
        )
""",
            ),
            (
                b"""        raise
    except (OSError, KeyError, TypeError, ValueError, AttributeError) as error:
        raise ReferenceRefusal(
""",
                b"""        raise
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        AttributeError,
        ReportRebuildError,
    ) as error:
        raise ReferenceRefusal(
""",
            ),
        ),
    ),
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/lra_reference/profiles.py": (
        4019,
        "d6f56773b5af238e54166bb7b1e8a8d15dbbf1e5c100b420196ecf39382ccc9a",
        (
            (
                b"""
import csv
""",
                b"""
from collections.abc import Callable
import csv
""",
            ),
            (
                b'''
def validate_source_domains(root: Path, reference_hash: str) -> dict[str, Any]:
    """Validate source-domain and corrected-forward R cases against executed evidence."""
''',
                b'''
def validate_source_domains(
    root: Path,
    reference_hash: str,
    *,
    read_source: Callable[[str], bytes] | None = None,
) -> dict[str, Any]:
    """Validate source-domain and corrected-forward R cases against executed evidence."""
''',
            ),
            (
                b"""        or any(
            hashlib.sha256((root / name).read_bytes()).hexdigest() != identities[name]
            for name in required
""",
                b"""        or any(
            hashlib.sha256(
                (root / name).read_bytes()
                if read_source is None
                else read_source("source-domains/" + name)
            ).hexdigest()
            != identities[name]
            for name in required
""",
            ),
        ),
    ),
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/native_reference/annulus_capture.py": (
        10937,
        "47af109200a23537843078d241628273f08270e30150c34e1bbfdf76ffd0603b",
        (
            (
                b"""
from dataclasses import dataclass
import hashlib
""",
                b"""
from collections.abc import Callable
from dataclasses import dataclass, field
import hashlib
""",
            ),
            (
                b"""from typing import Any

""",
                b"""from typing import Any

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.retained_source import validated_descriptor
from bijux_pollenomics_dev.ci.report_rebuild.retained_source.capsule import (
    native_oracle_members,
)

""",
            ),
            (
                b"""    source_context: dict[str, Any]

""",
                b"""    source_context: dict[str, Any]
    read_input: Callable[[str], bytes] | None = field(
        default=None, compare=False, repr=False
    )

""",
            ),
            (
                b"""
def _checked(repository: Path, name: str, spec: dict[str, Any]) -> bytes:
    _relative(name, "native R capture member")
""",
                b"""
def _checked(
    repository: Path,
    name: str,
    spec: dict[str, Any],
    *,
    read_source: Callable[[str], bytes] | None = None,
) -> bytes:
    _relative(name, "native R capture member")
""",
            ),
            (
                b"""        raise ValueError("native R capture member identity is invalid")
    payload = _file(repository, name)
    if (
""",
                b"""        raise ValueError("native R capture member identity is invalid")
    payload = _file(repository, name) if read_source is None else read_source(name)
    if (
""",
            ),
            (
                b"""        raise ValueError("annulus capture requires 97 retained numeric CSV files")
    inputs = {manifest_path: CAPTURE_MANIFEST_SHA256}
    for name, spec in raw.items():
        path = f"{CAPTURE_ROOT}/capture/{_relative(name, 'native raw member')}"
        _checked(repository, path, spec)
        inputs[path] = spec["sha256"]
""",
                b"""        raise ValueError("annulus capture requires 97 retained numeric CSV files")
    try:
        resolver = validated_descriptor(
            repository, CAPTURE_ROOT, native_oracle_members(record)
        )
    except ReportRebuildError as error:
        raise ValueError("Native R source transport differs: " + str(error)) from error

    def source_member(path: str) -> bytes:
        prefix = CAPTURE_ROOT + "/"
        if not path.startswith(prefix):
            raise ValueError("Native input escaped its capture")
        try:
            return resolver.read_source(path.removeprefix(prefix))
        except ReportRebuildError as error:
            raise ValueError(
                "Native R retained input changed: " + str(error)
            ) from error

    inputs = {manifest_path: CAPTURE_MANIFEST_SHA256}

    def read_input(path: str) -> bytes:
        if path not in inputs:
            raise ValueError("Unlisted native input read")
        body = _file(repository, path) if path == manifest_path else source_member(path)
        if hashlib.sha256(body).hexdigest() != inputs[path]:
            raise ValueError("Native admission changed during validation")
        return body

    for name, spec in raw.items():
        path = f"{CAPTURE_ROOT}/capture/{_relative(name, 'native raw member')}"
        _checked(repository, path, spec, read_source=source_member)
        inputs[path] = spec["sha256"]
""",
            ),
            (
                b"""    receipt = json.loads(
        _checked(repository, receipt_path, record["execution_receipt"])
    )
""",
                b"""    receipt = json.loads(
        _checked(
            repository,
            receipt_path,
            record["execution_receipt"],
            read_source=source_member,
        )
    )
""",
            ),
            (
                b"""        path = f"{CAPTURE_ROOT}/{_relative(row['path'], 'public native archive')}"
        _checked(repository, path, {"size": row["size"], "sha256": row["sha256"]})
        inputs[path] = row["sha256"]
""",
                b"""        path = f"{CAPTURE_ROOT}/{_relative(row['path'], 'public native archive')}"
        _checked(
            repository,
            path,
            {"size": row["size"], "sha256": row["sha256"]},
            read_source=source_member,
        )
        inputs[path] = row["sha256"]
""",
            ),
            (
                b"""    _checked(
        repository, public_path, {"sha256": public["sha256"], "size": public["size"]}
    )
""",
                b"""    _checked(
        repository,
        public_path,
        {"sha256": public["sha256"], "size": public["size"]},
        read_source=source_member,
    )
""",
            ),
            (
                b"""        physical.add(member.relative_to(repository).as_posix())
    if physical != set(inputs):
        raise ValueError("native R source packet has missing or extra members")
    if any(
        hashlib.sha256(_file(repository, name)).hexdigest() != digest
        for name, digest in inputs.items()
""",
                b"""        physical.add(member.relative_to(repository).as_posix())
    if physical != (
        set(inputs) - {CAPTURE_ROOT + "/" + name for name in resolver.detached}
    ) | {CAPTURE_ROOT + "/source-transport.json"}:
        raise ValueError("native R source packet has missing or extra members")
    if any(
        hashlib.sha256(read_input(name)).hexdigest() != digest
        for name, digest in inputs.items()
""",
            ),
            (
                b"""        {name: spec["sha256"] for name, spec in raw.items()},
        inputs,
        context,
    )
""",
                b"""        {name: spec["sha256"] for name, spec in raw.items()},
        dict(inputs),
        context,
        read_input,
    )
""",
            ),
        ),
    ),
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/native_reference/capture.py": (
        6846,
        "873b8a968223ca88f8235f999ad803d7f0b66c36dc503850e69478a23506849b",
        (
            (
                b"""
from dataclasses import dataclass
import hashlib
""",
                b"""
from collections.abc import Callable
from dataclasses import dataclass, field
import hashlib
""",
            ),
            (
                b"""from typing import Any

""",
                b"""from typing import Any

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.retained_source import validated_descriptor
from bijux_pollenomics_dev.ci.report_rebuild.retained_source.capsule import (
    native_oracle_members,
)

""",
            ),
            (
                b"""    input_sha256: dict[str, str]

""",
                b"""    input_sha256: dict[str, str]
    read_input: Callable[[str], bytes] | None = field(
        default=None, compare=False, repr=False
    )

""",
            ),
            (
                b"""
def _checked(repository: Path, name: str, spec: dict[str, Any]) -> bytes:
    _relative(name, "native R capture member")
""",
                b"""
def _checked(
    repository: Path,
    name: str,
    spec: dict[str, Any],
    *,
    read_source: Callable[[str], bytes] | None = None,
) -> bytes:
    _relative(name, "native R capture member")
""",
            ),
            (
                b"""        raise ValueError("native R capture member identity is invalid")
    payload = _file(repository, name)
    if (
""",
                b"""        raise ValueError("native R capture member identity is invalid")
    payload = _file(repository, name) if read_source is None else read_source(name)
    if (
""",
            ),
            (
                b"""        raise ValueError("native R raw/retained report membership differs")
    inputs = {manifest_path: CAPTURE_MANIFEST_SHA256}
    for name, spec in raw.items():
        path = f"{CAPTURE_ROOT}/capture/{_relative(name, 'native raw member')}"
        _checked(repository, path, spec)
        inputs[path] = spec["sha256"]
""",
                b"""        raise ValueError("native R raw/retained report membership differs")
    try:
        resolver = validated_descriptor(
            repository, CAPTURE_ROOT, native_oracle_members(record)
        )
    except ReportRebuildError as error:
        raise ValueError("Native R source transport differs: " + str(error)) from error

    def source_member(path: str) -> bytes:
        prefix = CAPTURE_ROOT + "/"
        if not path.startswith(prefix):
            raise ValueError("Native input escaped its capture")
        try:
            return resolver.read_source(path.removeprefix(prefix))
        except ReportRebuildError as error:
            raise ValueError(
                "Native R retained input changed: " + str(error)
            ) from error

    inputs = {manifest_path: CAPTURE_MANIFEST_SHA256}

    def read_input(path: str) -> bytes:
        if path not in inputs:
            raise ValueError("Unlisted native input read")
        body = _file(repository, path) if path == manifest_path else source_member(path)
        if hashlib.sha256(body).hexdigest() != inputs[path]:
            raise ValueError("Native admission changed during validation")
        return body

    for name, spec in raw.items():
        path = f"{CAPTURE_ROOT}/capture/{_relative(name, 'native raw member')}"
        _checked(repository, path, spec, read_source=source_member)
        inputs[path] = spec["sha256"]
""",
            ),
            (
                b"""    receipt = json.loads(
        _checked(repository, receipt_path, record["execution_receipt"])
    )
""",
                b"""    receipt = json.loads(
        _checked(
            repository,
            receipt_path,
            record["execution_receipt"],
            read_source=source_member,
        )
    )
""",
            ),
            (
                b"""        path = f"{CAPTURE_ROOT}/{_relative(row['path'], 'public native archive')}"
        _checked(repository, path, {"size": row["size"], "sha256": row["sha256"]})
        inputs[path] = row["sha256"]
""",
                b"""        path = f"{CAPTURE_ROOT}/{_relative(row['path'], 'public native archive')}"
        _checked(
            repository,
            path,
            {"size": row["size"], "sha256": row["sha256"]},
            read_source=source_member,
        )
        inputs[path] = row["sha256"]
""",
            ),
            (
                b"""    _checked(
        repository, public_path, {"sha256": public["sha256"], "size": public["size"]}
    )
""",
                b"""    _checked(
        repository,
        public_path,
        {"sha256": public["sha256"], "size": public["size"]},
        read_source=source_member,
    )
""",
            ),
            (
                b"""        physical.add(member.relative_to(repository).as_posix())
    if physical != set(inputs):
        raise ValueError("native R source packet has missing or extra members")
    if any(
        hashlib.sha256(_file(repository, name)).hexdigest() != digest
        for name, digest in inputs.items()
""",
                b"""        physical.add(member.relative_to(repository).as_posix())
    if physical != (
        set(inputs) - {CAPTURE_ROOT + "/" + name for name in resolver.detached}
    ) | {CAPTURE_ROOT + "/source-transport.json"}:
        raise ValueError("native R source packet has missing or extra members")
    if any(
        hashlib.sha256(read_input(name)).hexdigest() != digest
        for name, digest in inputs.items()
""",
            ),
            (
                b"""        {name: spec["sha256"] for name, spec in raw.items()},
        inputs,
    )
""",
                b"""        {name: spec["sha256"] for name, spec in raw.items()},
        dict(inputs),
        read_input,
    )
""",
            ),
        ),
    ),
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/native_reference/count_domain_capture.py": (
        23947,
        "256ba71ff27976534da4b4c7a5fc496270a4e59c9a2af5100f078cccff8cc761",
        (
            (
                b"""
from dataclasses import dataclass
import hashlib
""",
                b"""
from collections.abc import Callable
from dataclasses import dataclass, field
import hashlib
""",
            ),
            (
                b"""
from bijux_pollenomics_dev.lra_validation.native_reference.annulus_capture import (
""",
                b"""
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.retained_source import validated_descriptor
from bijux_pollenomics_dev.ci.report_rebuild.retained_source.capsule import (
    native_oracle_members,
)
from bijux_pollenomics_dev.lra_validation.native_reference.annulus_capture import (
""",
            ),
            (
                b"""    source_context: dict[str, Any]

""",
                b"""    source_context: dict[str, Any]
    read_input: Callable[[str], bytes] | None = field(
        default=None, compare=False, repr=False
    )

""",
            ),
            (
                b"""        raise ValueError("Exact numeric/raw membership differs")
    inputs = {manifest_path: CAPTURE_MANIFEST_SHA256}
    raw_digests: dict[str, str] = {}
""",
                b"""        raise ValueError("Exact numeric/raw membership differs")
    try:
        resolver = validated_descriptor(
            repository, CAPTURE_ROOT, native_oracle_members(record)
        )
    except ReportRebuildError as error:
        raise ValueError("Native R source transport differs: " + str(error)) from error

    def source_member(path: str) -> bytes:
        prefix = CAPTURE_ROOT + "/"
        if not path.startswith(prefix):
            raise ValueError("Native input escaped its capture")
        try:
            return resolver.read_source(path.removeprefix(prefix))
        except ReportRebuildError as error:
            raise ValueError(
                "Native R retained input changed: " + str(error)
            ) from error

    inputs = {manifest_path: CAPTURE_MANIFEST_SHA256}

    def read_input(path: str) -> bytes:
        if path not in inputs:
            raise ValueError("Unlisted native input read")
        body = _file(repository, path) if path == manifest_path else source_member(path)
        if hashlib.sha256(body).hexdigest() != inputs[path]:
            raise ValueError("Native admission changed during validation")
        return body

    raw_digests: dict[str, str] = {}
""",
            ),
            (
                b"""        path = f"{CAPTURE_ROOT}/capture/{_relative(name, 'count-domain raw member')}"
        _checked(repository, path, spec)
        inputs[path] = digest
""",
                b"""        path = f"{CAPTURE_ROOT}/capture/{_relative(name, 'count-domain raw member')}"
        _checked(repository, path, spec, read_source=source_member)
        inputs[path] = digest
""",
            ),
            (
                b"""    receipt = json.loads(
        _checked(repository, receipt_path, record["execution_receipt"])
    )
""",
                b"""    receipt = json.loads(
        _checked(
            repository,
            receipt_path,
            record["execution_receipt"],
            read_source=source_member,
        )
    )
""",
            ),
            (
                b"""        path = f"{CAPTURE_ROOT}/{_relative(row['path'], 'cached native archive')}"
        _checked(repository, path, {"size": row["size"], "sha256": row["sha256"]})
        inputs[path] = row["sha256"]
""",
                b"""        path = f"{CAPTURE_ROOT}/{_relative(row['path'], 'cached native archive')}"
        _checked(
            repository,
            path,
            {"size": row["size"], "sha256": row["sha256"]},
            read_source=source_member,
        )
        inputs[path] = row["sha256"]
""",
            ),
            (
                b"""    _checked(
        repository, public_path, {"size": public["size"], "sha256": public["sha256"]}
    )
""",
                b"""    _checked(
        repository,
        public_path,
        {"size": public["size"], "sha256": public["sha256"]},
        read_source=source_member,
    )
""",
            ),
            (
                b"""        physical.add(member.relative_to(repository).as_posix())
    if physical != set(inputs):
        raise ValueError("Native source packet has extra/missing members")
""",
                b"""        physical.add(member.relative_to(repository).as_posix())
    if physical != (
        set(inputs) - {CAPTURE_ROOT + "/" + name for name in resolver.detached}
    ) | {CAPTURE_ROOT + "/source-transport.json"}:
        raise ValueError("Native source packet has extra/missing members")
""",
            ),
            (
                b"""        any(
            hashlib.sha256(_file(repository, name)).hexdigest() != digest
            for name, digest in inputs.items()
""",
                b"""        any(
            hashlib.sha256(read_input(name)).hexdigest() != digest
            for name, digest in inputs.items()
""",
            ),
            (
                b"""        raw_digests,
        inputs,
        context,
    )
""",
                b"""        raw_digests,
        dict(inputs),
        context,
        read_input,
    )
""",
            ),
        ),
    ),
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/retained_reference/identity.py": (
        4875,
        "bab7252e9e0b8059a58aa486555163b1cbde321bf1b870da719b23a3253f44bf",
        (
            (
                b"""
from bijux_pollenomics_dev.ci.lra_reference.evidence import validate_bundle

PROFILE = Path(__file__).with_name("reference_profile.json")

""",
                b'''
from bijux_pollenomics_dev.ci.lra_reference.contracts import ReferenceRefusal
from bijux_pollenomics_dev.ci.lra_reference.evidence import (
    file_inventory,
    validate_bundle,
)
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.retained_source import (
    SourceCapsule,
    validated_descriptor,
)

PROFILE = Path(__file__).with_name("reference_profile.json")
_BUNDLE_PREFIX = "data/method-certification/source-locked-linux-r/reference-bundle"


class _ReferenceIdentity(dict[str, Any]):
    """Keep the scoped source reader private while public evidence remains plain JSON."""

    def __init__(self, document: dict[str, Any], source: SourceCapsule | None) -> None:
        super().__init__(document)
        self.source = source


def _source_transport(bundle: Path, profile: dict[str, Any]) -> SourceCapsule | None:
    """Only the exact indexed repository bundle may detach historical source bodies."""
    if len(bundle.parents) < 4:
        return None
    repository = bundle.parents[3]
    if repository / _BUNDLE_PREFIX != bundle:
        return None
    members = {
        name: {"sha256": row["sha256"], "bytes": row["byte_count"]}
        for name, row in profile["files"].items()
        if name != "certificate.json"
    }
    try:
        source = validated_descriptor(repository, _BUNDLE_PREFIX, members)
    except ReportRebuildError as error:
        raise ValueError(str(error)) from error
    if source.detached != frozenset(
        {
            "source-domains/r_support.R",
            "source-domains/run_source_domains.py",
            "source-domains/source_domains.R",
            "source-lock.json",
        }
    ):
        raise ValueError("Retained reference source transport population differs")
    return source

''',
            ),
            (
                b'''    """Read only the authenticated member bytes selected for a comparison."""
    path = bundle / name
    if (
        any(member.is_symlink() for member in (path, *path.parents))
        or not path.resolve(strict=True).is_relative_to(bundle.resolve(strict=True))
        or not path.is_file()
    ):
        raise ValueError("Retained comparison member is not confined and regular")
    payload = path.read_bytes()
    if {
''',
                b'''    """Read only the authenticated member bytes selected for a comparison."""
    source = identity.source if isinstance(identity, _ReferenceIdentity) else None
    if source is not None and name in source.detached:
        try:
            payload = source.read_source(name)
        except ReportRebuildError as error:
            raise ValueError(str(error)) from error
    else:
        path = bundle / name
        if (
            any(member.is_symlink() for member in (path, *path.parents))
            or not path.resolve(strict=True).is_relative_to(bundle.resolve(strict=True))
            or not path.is_file()
        ):
            raise ValueError("Retained comparison member is not confined and regular")
        payload = path.read_bytes()
    if {
''',
            ),
            (
                b"""    profile = load_profile()
    files: dict[str, dict[str, int | str]] = {}
    for path in sorted(bundle.rglob("*")):
        if path.is_symlink() or not path.resolve(strict=True).is_relative_to(bundle):
            raise ValueError("Retained reference member is not confined")
        if path.is_dir():
            continue
        if not path.is_file():
            raise ValueError("Retained reference member is not regular")
        payload = path.read_bytes()
        files[path.relative_to(bundle).as_posix()] = {
            "sha256": hashlib.sha256(payload).hexdigest(),
            "byte_count": len(payload),
        }
    if files != profile["files"]:
""",
                b"""    profile = load_profile()
    source_transport = _source_transport(bundle, profile)
    if source_transport is not None:
        try:
            files: dict[str, dict[str, Any]] = file_inventory(
                bundle, source_transport=source_transport
            )
        except (ReportRebuildError, ReferenceRefusal) as error:
            raise ValueError(str(error)) from error
    else:
        files = {}
        for path in sorted(bundle.rglob("*")):
            if path.is_symlink() or not path.resolve(strict=True).is_relative_to(
                bundle
            ):
                raise ValueError("Retained reference member is not confined")
            if path.is_dir():
                continue
            if not path.is_file():
                raise ValueError("Retained reference member is not regular")
            payload = path.read_bytes()
            files[path.relative_to(bundle).as_posix()] = {
                "sha256": hashlib.sha256(payload).hexdigest(),
                "byte_count": len(payload),
            }
    if files != profile["files"]:
""",
            ),
            (
                b"""        expected_lock_sha256=profile["source_lock_sha256"],
    )
    lock = json.loads((bundle / "source-lock.json").read_bytes())
    if any(
""",
                b"""        expected_lock_sha256=profile["source_lock_sha256"],
        source_transport=source_transport,
    )
    lock = json.loads(
        read_member(
            bundle,
            "source-lock.json",
            _ReferenceIdentity({"files": files}, source_transport),
        )
    )
    if any(
""",
            ),
            (
                b"""        raise ValueError("Public retained reference identity differs")
    return {
        "reference_id": profile["reference_id"],
        "certificate_sha256": profile["certificate_sha256"],
        "source_commit": profile["source_commit"],
        "source_tree": profile["source_tree"],
        "source_lock_sha256": profile["source_lock_sha256"],
        "public_reference": profile["public_reference"],
        "r_runtime": profile["r_runtime"],
        "files": files,
        "required_profiles": profile["required_profiles"],
    }
""",
                b"""        raise ValueError("Public retained reference identity differs")
    return _ReferenceIdentity(
        {
            "reference_id": profile["reference_id"],
            "certificate_sha256": profile["certificate_sha256"],
            "source_commit": profile["source_commit"],
            "source_tree": profile["source_tree"],
            "source_lock_sha256": profile["source_lock_sha256"],
            "public_reference": profile["public_reference"],
            "r_runtime": profile["r_runtime"],
            "files": files,
            "required_profiles": profile["required_profiles"],
        },
        source_transport,
    )
""",
            ),
        ),
    ),
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/lra_reference/certification.py": (
        11711,
        "bbdae578ba499bc2ed8e70ccec48aedce6af8984828c88205d2c781c94f041df",
        (
            (
                b"""            timeout=1900,
        )
        from .profiles import validate_source_domains

        validate_source_domains(
            output / "source-domains", lock.payload["reference"]["sha256"]
        )
        if (
""",
                b"""            timeout=1900,
        )
        from .profiles import canonical_domain_source_reader, validate_source_domains

        validate_source_domains(
            output / "source-domains",
            lock.payload["reference"]["sha256"],
            read_source=canonical_domain_source_reader(repository, sources),
        )
        if (
""",
            ),
            (
                b"""            json.dumps(report, indent=2, allow_nan=False) + "\\n"
        )
        validate_bundle(bundle, target_sha=commit, expected_lock_sha256=lock_hash)
    except BaseException as error:
        report.update(status="failed", error=type(error).__name__ + ": " + str(error))
""",
                b"""            json.dumps(report, indent=2, allow_nan=False) + "\\n"
        )
        validate_bundle(
            bundle,
            target_sha=commit,
            expected_lock_sha256=lock_hash,
            current_repository=repository,
        )
    except BaseException as error:
        report.update(status="failed", error=type(error).__name__ + ": " + str(error))
""",
            ),
        ),
    ),
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/lra_reference/native_parity.py": (
        4656,
        "71f3d67783abab8fc1ec3c2dc7048c2c913f618a5e93848171c828d18b1834d6",
        (
            (
                b'''    target_sha: str,
    output: Path,
) -> dict[str, Any]:
    """Require equal cases and a complete actual-R certificate before passing."""
''',
                b'''    target_sha: str,
    output: Path,
    repository: Path | None = None,
) -> dict[str, Any]:
    """Require equal cases and a complete actual-R certificate before passing."""
''',
            ),
            (
                b"""    lock_hash = _sha(lock.read_bytes())
    certificate = validate_bundle(
        live, target_sha=target_sha, expected_lock_sha256=lock_hash
    )
    live_report = read_json((live / "oracle/report.json").read_bytes())
""",
                b"""    lock_hash = _sha(lock.read_bytes())
    certificate = validate_bundle(
        live,
        target_sha=target_sha,
        expected_lock_sha256=lock_hash,
        current_repository=repository,
    )
    live_report = read_json((live / "oracle/report.json").read_bytes())
""",
            ),
            (
                b"""    parser.add_argument("--target-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
""",
                b"""    parser.add_argument("--target-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repository", type=Path)
    args = parser.parse_args()
    try:
""",
            ),
            (
                b"""            target_sha=args.target_sha,
            output=args.output,
        )
    except (OSError, ValueError) as error:
""",
                b"""            target_sha=args.target_sha,
            output=args.output,
            repository=args.repository,
        )
    except (OSError, ValueError) as error:
""",
            ),
        ),
    ),
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/lra_reference/release_gate.py": (
        16347,
        "01759213114f82aca8ae3fbaf4ac9fbbf7f0fe5b4bc7715e807c8ec907cba0b4",
        (
            (
                b"""        expected_lock_sha256=lock_hash,
        expected_run=(repository, run_id, attempt),
    )
    if (
""",
                b"""        expected_lock_sha256=lock_hash,
        expected_run=(repository, run_id, attempt),
        current_repository=repository_root,
    )
    if (
""",
            ),
        ),
    ),
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/live_reference_comparison.py": (
        12289,
        "8e725129e23f92c594084116c0d2a5e282af9fb71048b28ea58adac3f2e460d2",
        (
            (
                b"""
from .native_reference.finite_covariance_capture import (
    validated_finite_covariance_capture,
)
from .native_reference.source_replay import build_source_replay
""",
                b"""
from .native_reference.finite_covariance_capture import (
    historical_finite_covariance_capture,
    require_current_finite_covariance_sources,
)
from .native_reference.source_replay import build_source_replay
""",
            ),
            (
                b"""    if retained_capture_profile != "finite-covariance":
        raise ValueError("Retained comparison source profile must be finite-covariance")
    capture = validated_finite_covariance_capture(repository)
    expected = capture.source_context["protected_science_sha256"]
    if (
""",
                b"""    if retained_capture_profile != "finite-covariance":
        raise ValueError("Retained comparison source profile must be finite-covariance")
    capture = historical_finite_covariance_capture(repository)
    expected = capture.source_context["protected_science_sha256"]
    if (
""",
            ),
            (
                b"""            "Retained comparison source routes or sealed source hashes differ"
        )


""",
                b"""            "Retained comparison source routes or sealed source hashes differ"
        )
    require_current_finite_covariance_sources(repository, capture)


""",
            ),
        ),
    ),
    "packages/bijux-pollenomics-lra/tests/reference/lra_oracle/run_source_domains.py": (
        11567,
        "661b0eb311708a9f116de6d7784702aefbe35cbb165d66d884fce0e30e0b85f7",
        (
            (
                b"""@dataclass(frozen=True)
class DomainCase:
    id: str
    kind: str
""",
                b'''@dataclass(frozen=True)
class DomainCase:
    """Describe one declared source-domain numerical case."""

    id: str
    kind: str
''',
            ),
            (
                b"""
def cases() -> list[DomainCase]:
    result = [
        DomainCase(
""",
                b'''
def cases() -> list[DomainCase]:
    """Declare the complete fixed source-domain case inventory."""
    result = [
        DomainCase(
''',
            ),
            (
                b"""
def parameters() -> pd.DataFrame:
    return pd.DataFrame(
        {
""",
                b'''
def parameters() -> pd.DataFrame:
    """Return the declared two-taxon physical parameter table."""
    return pd.DataFrame(
        {
''',
            ),
            (
                b"""
def geometry(case: DomainCase) -> pd.DataFrame:
    edges = np.array(
        [case.radius, 3 * case.radius, 10 * case.radius, 50 * case.radius, 100000.0]
""",
                b'''
def geometry(case: DomainCase) -> pd.DataFrame:
    """Build the declared ring geometry for one source-domain case."""
    edges = np.array(
        [case.radius, 3 * case.radius, 10 * case.radius, 50 * case.radius, 100000.0]
''',
            ),
            (
                b"""
def expectation(case: DomainCase) -> np.ndarray:
    p = parameters().iloc[: case.taxa_count]
    rings = geometry(case)
""",
                b'''
def expectation(case: DomainCase) -> np.ndarray:
    """Compute the fixed analytical expectation for a declared source-domain case."""
    p = parameters().iloc[: case.taxa_count]
    rings = geometry(case)
''',
            ),
            (
                b"""
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
""",
                b'''
def main(argv: list[str] | None = None) -> int:
    """Parse arguments for the source-bound evidence consumer."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
''',
            ),
            (
                b"""        source = Path(__file__).with_name(name)
        content = source.read_bytes()
        (output / name).write_bytes(content)
        retained_sources[name] = hashlib.sha256(content).hexdigest()
    archive_hash = hashlib.sha256(
""",
                b"""        source = Path(__file__).with_name(name)
        content = source.read_bytes()
        retained_sources[name] = hashlib.sha256(content).hexdigest()
    archive_hash = hashlib.sha256(
""",
            ),
            (
                b"""        "Rscript",
        "--vanilla",
        str(output / "source_domains.R"),
        str(output),
        str(args.library.resolve()),
        str(output / "r_support.R"),
        archive_hash,
    ]
""",
                b"""        "Rscript",
        "--vanilla",
        str(Path(__file__).with_name("source_domains.R")),
        str(output),
        str(args.library.resolve()),
        str(Path(__file__).with_name("r_support.R")),
        archive_hash,
    ]
""",
            ),
        ),
    ),
}

NATIVE_REFERENCE_TRANSPORT_SOURCES = frozenset(_NATIVE_REFERENCE_TRANSPORT_CONTRACTS)

_NATIVE_REFERENCE_TRANSPORT_CAPTURES = {
    "data/method-certification/author-optimizer-diagnostic-source-capture": (
        "f865795aac7585e56c4cf44faac84496d339e1c176fc6ee111cba3cbc9b4ce93",
        "executions/optimizer-diagnostics/first-party-inputs/",
    ),
    "data/method-certification/linux-r-source-capture": (
        "fa6e9a4fa9c12013a04cc461fef52d0fd54044d517e132e802a9c176def2a913",
        "source/",
    ),
}


_CANONICAL_REFERENCE_IO_SPANS: dict[str, tuple[tuple[bytes, bytes], ...]] = {
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/lra_reference/evidence.py": (
        (
            b"""from __future__ import annotations

import csv
import hashlib
""",
            b"""from __future__ import annotations

from collections.abc import Callable
import csv
import hashlib
""",
        ),
        (
            b'''    expected_run: tuple[str, int, int] | None = None,
    source_transport: SourceCapsule | None = None,
) -> dict[str, Any]:
    """Check source/runtime/case/member closure; transport authenticity is external."""
''',
            b'''    expected_run: tuple[str, int, int] | None = None,
    source_transport: SourceCapsule | None = None,
    current_repository: Path | None = None,
) -> dict[str, Any]:
    """Check source/runtime/case/member closure; transport authenticity is external."""
''',
        ),
        (
            b"""        if certificate.get("required_profiles") != required_profiles:
            raise ReferenceRefusal("Required reference profile denominators differ")
        from .profiles import validate_source_domains

        validate_source_domains(
            root / "source-domains",
            lock.payload["reference"]["sha256"],
            read_source=(
                None if source_transport is None else source_transport.read_source
            ),
        )
        python_runtime = certificate.get("python_runtime")
""",
            b"""        if certificate.get("required_profiles") != required_profiles:
            raise ReferenceRefusal("Required reference profile denominators differ")
        from .profiles import canonical_domain_source_reader, validate_source_domains

        if source_transport is not None and current_repository is not None:
            raise ReferenceRefusal(
                "Historical and current source readers must remain distinct"
            )
        domain_source: Callable[[str], bytes] | None = None
        retained_sources = (
            root / "source-domains" / name
            for name in ("run_source_domains.py", "source_domains.R", "r_support.R")
        )
        # Retained bundles keep their own complete source contract. A checkout
        # supplies sources only for bundles that retain no script members.
        if current_repository is not None and not any(
            path.exists() or path.is_symlink() for path in retained_sources
        ):
            domain_source = canonical_domain_source_reader(
                current_repository, certificate["source_files"]
            )
        elif source_transport is not None:
            domain_source = source_transport.read_source

        validate_source_domains(
            root / "source-domains",
            lock.payload["reference"]["sha256"],
            read_source=domain_source,
        )
        python_runtime = certificate.get("python_runtime")
""",
        ),
    ),
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/lra_reference/profiles.py": (
        (
            b"""from __future__ import annotations

from collections.abc import Callable
import csv
import hashlib
from pathlib import Path
from typing import Any

from .contracts import ReferenceRefusal, read_json

SOURCE_DOMAIN_PROFILE = "disqover-source-domains-and-corrected-forward-v1"
""",
            b"""from __future__ import annotations

from collections.abc import Callable, Mapping
import csv
import hashlib
from pathlib import Path
import re
from typing import Any

from .contracts import ReferenceRefusal, read_json
from .paths import local_path

SOURCE_DOMAIN_PROFILE = "disqover-source-domains-and-corrected-forward-v1"
""",
        ),
        (
            b"""    "F013": "corrected-matrix-rounded-cover",
}


""",
            b'''    "F013": "corrected-matrix-rounded-cover",
}


def canonical_domain_source_reader(
    repository: Path, source_files: Mapping[str, str]
) -> Callable[[str], bytes]:
    """Authenticate the three executed scripts in their canonical source owner."""
    repository = local_path(repository)
    owner = Path("packages/bijux-pollenomics-lra/tests/reference/lra_oracle")
    allowed = {
        "source-domains/" + name
        for name in ("run_source_domains.py", "source_domains.R", "r_support.R")
    }

    def read_source(name: str) -> bytes:
        if name not in allowed:
            raise ReferenceRefusal("Unlisted canonical source-domain script")
        relative = owner / name.removeprefix("source-domains/")
        expected = source_files.get(relative.as_posix())
        if (
            not isinstance(expected, str)
            or re.fullmatch(r"[0-9a-f]{64}", expected) is None
        ):
            raise ReferenceRefusal("Canonical source-domain identity is missing")
        path = local_path(repository / relative)
        if not path.is_file() or path.stat().st_nlink != 1:
            raise ReferenceRefusal(
                "Canonical source-domain script is not independently owned"
            )
        payload = path.read_bytes()
        if hashlib.sha256(payload).hexdigest() != expected:
            raise ReferenceRefusal("Canonical source-domain script changed")
        return payload

    return read_source


''',
        ),
    ),
}


def _canonical_reference_reader_basis(name: str, current: bytes) -> bytes:
    """Reverse only the declared canonical IO layer before the existing byte law."""
    spans = _CANONICAL_REFERENCE_IO_SPANS.get(name)
    if spans is None:
        return current
    body = current
    for previous, inserted in spans:
        if body.count(inserted) != 1:
            return current
        body = body.replace(inserted, previous, 1)
    return body


def native_reference_transport_extension_matches(
    name: str, historical: bytes, current: bytes
) -> bool:
    """Recover the whole old reader by reversing only its declared transport seams."""
    contract = _NATIVE_REFERENCE_TRANSPORT_CONTRACTS.get(name)
    if contract is None:
        return False
    size, checksum, spans = contract
    if (
        len(historical) != size
        or hashlib.sha256(historical).hexdigest() != checksum
        or not 0 < len(current) <= 128 * 1024
    ):
        return False
    restored = _canonical_reference_reader_basis(name, current)
    for old, new in spans:
        if historical.count(old) != 1 or restored.count(new) != 1:
            return False
        restored = restored.replace(new, old, 1)
    return restored == historical


def validated_native_reference_transport_source(
    repository: Path,
    historical: JsonObject,
    logical: str,
    source_buffer: SourceCapsule,
) -> JsonObject:
    """Bind finite IO extensions to their two original captured source contexts."""
    name = historical.get("path")
    contract = (
        _NATIVE_REFERENCE_TRANSPORT_CONTRACTS.get(name)
        if isinstance(name, str)
        else None
    )
    binding = _NATIVE_REFERENCE_TRANSPORT_CAPTURES.get(source_buffer.prefix)
    if contract is None or binding is None or not isinstance(name, str):
        raise ReportRebuildError(
            "Native reference transport source is outside its fixed scope"
        )
    size, checksum, _ = contract
    expected = {"bytes": size, "sha256": checksum}
    if (
        repository != repository.resolve()
        or source_buffer.repository != repository
        or source_buffer.descriptor.capture.get("sha256") != binding[0]
        or set(historical) != {"path", "bytes", "sha256"}
        or type(historical.get("bytes")) is not int
        or historical != {"path": name, **expected}
        or logical != binding[1] + name
        or logical not in source_buffer.detached
        or source_buffer.descriptor.members.get(logical) != expected
        or [
            path
            for group in source_buffer.descriptor.groups
            for member, path in group["resolved_paths"]
            if member == logical
        ]
        != [name]
    ):
        raise ReportRebuildError("Native reference transport source binding differs")
    source_buffer.fresh()
    captured = source_buffer.read_source(logical)
    path = _regular_confined_file(repository, name, "current native reference reader")
    before = path.stat()
    if before.st_nlink != 1 or not 0 < before.st_size <= 128 * 1024:
        raise ReportRebuildError(
            "Current native reference reader must be bounded and single-link"
        )
    current = path.read_bytes()
    if not native_reference_transport_extension_matches(name, captured, current):
        raise ReportRebuildError(
            "Native reference reader differs beyond its finite transport seams"
        )
    source_buffer.fresh()
    again = _regular_confined_file(repository, name, "current native reference reader")
    after = again.stat()
    fields = (
        "st_dev",
        "st_ino",
        "st_mode",
        "st_nlink",
        "st_size",
        "st_mtime_ns",
        "st_ctime_ns",
    )
    if (
        any(getattr(before, field) != getattr(after, field) for field in fields)
        or again.read_bytes() != current
    ):
        raise ReportRebuildError(
            "Current native reference reader changed during correspondence"
        )
    return {
        "path": name,
        "classification": "finite_native_reference_transport_extension",
        "original_member": logical,
        "original_sha256": checksum,
        "original_bytes": size,
        "whole_old_module_reconstructed": True,
        "current_regular_single_link_and_stable": True,
        "native_math_runtime_and_count_predicates_preserved": True,
        "historical_native_execution_equal_current_claimed": False,
        "historical_outputs_regenerated": False,
    }
