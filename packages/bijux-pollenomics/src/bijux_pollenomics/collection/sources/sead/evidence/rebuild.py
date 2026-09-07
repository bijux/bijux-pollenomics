"""Rebuild the exact governed SEAD evidence materialization without network access."""

from __future__ import annotations

import argparse
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import socket
import sys
from typing import Final

from bijux_pollenomics.collection.sources.sead.acquisition.governed import (
    governed_sead_expected_identity,
    validate_governed_sead_admission,
)
from bijux_pollenomics.evidence.sources.sead import (
    SEAD_GOVERNED_ACQUISITION_MANIFEST_SHA256,
    SEAD_GOVERNED_BUILD_ID,
    SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256,
    SEAD_GOVERNED_EVIDENCE_RUN_ID,
)

from .bundle import (
    validate_sead_source_native_evidence_materialization,
    write_sead_source_native_evidence_bundle,
)

_MANIFEST_NAME: Final = "evidence_materialization_manifest.json"
_EXPECTED_FILE_COUNT: Final = 54


class NetworkAccessRefused(RuntimeError):
    """Raised when a governed local rebuild attempts network access."""


AdmissionValidator = Callable[..., object]
BundleWriter = Callable[..., tuple[Path, ...]]
BundleValidator = Callable[[Path], object]


def _blocked_network_call(*args: object, **kwargs: object) -> object:
    del args, kwargs
    raise NetworkAccessRefused("network access is forbidden during SEAD rebuild")


def _audit_offline_operation(event: str, args: tuple[object, ...]) -> None:
    """Refuse socket and child-process audit events in the command process."""
    del args
    if event.startswith("socket.") or event in {
        "subprocess.Popen",
        "os.system",
        "os.posix_spawn",
        "os.posix_spawnp",
    }:
        raise NetworkAccessRefused(f"offline SEAD rebuild refused operation: {event}")


@contextmanager
def network_disabled() -> Iterator[None]:
    """Refuse DNS, connected sockets, and datagram sends for one rebuild."""
    replacements = (
        (socket, "create_connection", _blocked_network_call),
        (socket, "getaddrinfo", _blocked_network_call),
        (socket, "gethostbyname", _blocked_network_call),
        (socket, "gethostbyname_ex", _blocked_network_call),
        (socket.socket, "connect", _blocked_network_call),
        (socket.socket, "connect_ex", _blocked_network_call),
        (socket.socket, "sendto", _blocked_network_call),
    )
    originals = tuple(
        (owner, name, getattr(owner, name)) for owner, name, _ in replacements
    )
    try:
        for owner, name, replacement in replacements:
            setattr(owner, name, replacement)
        yield
    finally:
        for owner, name, original in originals:
            setattr(owner, name, original)


def _reject_symlink_ancestors(path: Path) -> None:
    for candidate in (path, *path.parents):
        if candidate.exists() and candidate.is_symlink():
            raise ValueError(f"SEAD rebuild path traverses a symlink: {candidate}")


def _validated_repository_root(path: Path) -> Path:
    root = Path(path)
    if not root.is_absolute() or root == Path(root.anchor):
        raise ValueError("repository root must be a safe absolute path")
    _reject_symlink_ancestors(root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("repository root must be a regular directory")
    return root.resolve()


def _validated_output_root(path: Path, *, repository_root: Path) -> Path:
    output = Path(path)
    if not output.is_absolute() or output == Path(output.anchor):
        raise ValueError("SEAD rebuild output must be a safe absolute path")
    _reject_symlink_ancestors(output.parent)
    resolved_parent = output.parent.resolve()
    artifacts_root = (repository_root / "artifacts").resolve()
    try:
        resolved_parent.relative_to(artifacts_root)
    except ValueError as error:
        raise ValueError(
            "SEAD rebuild output must be below repository artifacts"
        ) from error
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"SEAD rebuild output already exists: {output}")
    if not resolved_parent.is_dir():
        raise ValueError("SEAD rebuild output parent must exist")
    return resolved_parent / output.name


def _regular_file_count(root: Path) -> int:
    count = 0
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"symlink found in governed SEAD output: {path}")
        if path.is_file():
            count += 1
        elif not path.is_dir():
            raise ValueError(f"unsupported file type in governed SEAD output: {path}")
    return count


def rebuild_governed_sead_evidence(
    repository_root: Path,
    output_root: Path,
    *,
    admission_validator: AdmissionValidator = validate_governed_sead_admission,
    bundle_writer: BundleWriter = write_sead_source_native_evidence_bundle,
    bundle_validator: BundleValidator = validate_sead_source_native_evidence_materialization,
) -> dict[str, object]:
    """Reconstruct and validate one governed evidence candidate below artifacts."""
    root = _validated_repository_root(repository_root)
    output = _validated_output_root(output_root, repository_root=root)
    data_root = root / "data"
    acquisition_root = (
        data_root / "sead" / "raw" / "acquisitions" / SEAD_GOVERNED_EVIDENCE_RUN_ID
    )
    expected_identity = governed_sead_expected_identity(data_root)
    with network_disabled():
        admission_validator(acquisition_root, data_root=data_root)
        written = bundle_writer(
            acquisition_root,
            output,
            expected_identity=expected_identity,
        )
        bundle_validator(output)
    file_count = _regular_file_count(output)
    if len(written) != _EXPECTED_FILE_COUNT or file_count != _EXPECTED_FILE_COUNT:
        raise ValueError(
            "governed SEAD evidence must contain exactly "
            f"{_EXPECTED_FILE_COUNT} regular files"
        )
    manifest_path = output / _MANIFEST_NAME
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise ValueError("governed SEAD evidence manifest is missing or unsafe")
    manifest_sha256 = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    if manifest_sha256 != SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256:
        raise ValueError("governed SEAD evidence manifest identity changed")
    return {
        "schema_version": "sead-governed-evidence-rebuild.v1",
        "status": "PASS",
        "source_run_id": SEAD_GOVERNED_EVIDENCE_RUN_ID,
        "build_id": SEAD_GOVERNED_BUILD_ID,
        "acquisition_manifest_sha256": SEAD_GOVERNED_ACQUISITION_MANIFEST_SHA256,
        "evidence_manifest_sha256": manifest_sha256,
        "file_count": file_count,
        "network_policy": "forbidden",
        "output_root": str(output),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Rebuild the governed SEAD evidence bundle without network access."
    )
    parser.add_argument("--repository-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the governed local SEAD rebuild command."""
    args = _parser().parse_args(argv)
    sys.addaudithook(_audit_offline_operation)
    try:
        result = rebuild_governed_sead_evidence(
            args.repository_root,
            args.output_root,
        )
    except (
        FileExistsError,
        NetworkAccessRefused,
        OSError,
        TypeError,
        ValueError,
    ) as error:
        print(
            f"SEAD governed evidence rebuild failed: {error}",
            file=sys.stderr,
            flush=True,
        )
        return 2
    print(
        json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
