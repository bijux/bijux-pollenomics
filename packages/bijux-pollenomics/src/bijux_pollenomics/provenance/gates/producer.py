"""Recorded-gate producer and runtime identities."""

from __future__ import annotations

import hashlib
import os
import platform
import stat
import sys
from pathlib import Path

from ..release_evidence import ReleaseEvidenceError
from .codec import _digest_json

_PRODUCER_ID = "bijux-pollenomics.recorded-gate"
_PRODUCER_VERSION = "4"
_PRODUCER_MODULE = "bijux_pollenomics.provenance.gates"
_LOCAL_ATTESTATION = {
    "class": "local_self_attestation",
    "independent_execution_attested": False,
    "external_authority_id": None,
}
_PACKAGE_ROOT = Path(__file__).parent


def _producer_record() -> dict[str, object]:
    source_files = _producer_source_files()
    source_digest = _digest_json(source_files)
    content: dict[str, object] = {
        "identity": _PRODUCER_ID,
        "version": _PRODUCER_VERSION,
        "source_files": source_files,
        "source_digest": source_digest,
    }
    return {**content, "digest": _digest_json(content)}


def _producer_source_files() -> list[dict[str, object]]:
    """Return the deterministic identity of every module in this producer package."""
    paths = _source_paths()
    records = [
        {
            "module": _module_name(path),
            "sha256": f"sha256:{hashlib.sha256(payload).hexdigest()}",
            "byte_count": len(payload),
        }
        for path in paths
        for payload in (_read_source_bytes(path),)
    ]
    if _source_paths() != paths:
        raise ReleaseEvidenceError(
            "recorded gate producer source inventory changed while reading"
        )
    return records


def _source_paths() -> list[Path]:
    paths = sorted(
        _PACKAGE_ROOT.rglob("*.py"),
        key=lambda path: path.relative_to(_PACKAGE_ROOT).as_posix(),
    )
    if not paths:
        raise ReleaseEvidenceError("recorded gate producer source is unavailable")
    return paths


def _module_name(path: Path) -> str:
    relative = path.relative_to(_PACKAGE_ROOT)
    components = list(relative.parts)
    if components[-1] == "__init__.py":
        components.pop()
    else:
        components[-1] = path.stem
    return ".".join((_PRODUCER_MODULE, *components))


def _read_executing_source_bytes() -> bytes:
    """Read the compatibility facade that now owns the former module identity."""
    return _read_source_bytes(_PACKAGE_ROOT / "__init__.py")


def _read_source_bytes(path: Path) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise ReleaseEvidenceError("recorded gate producer source is unsafe") from error
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ReleaseEvidenceError(
                "recorded gate producer source is not a regular file"
            )
        with os.fdopen(os.dup(descriptor), "rb") as stream:
            payload = stream.read()
        after = os.fstat(descriptor)
        if (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
        ) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        ):
            raise ReleaseEvidenceError(
                "recorded gate producer source changed while reading"
            )
        return payload
    finally:
        os.close(descriptor)


def _runtime_identity(
    executable: str, node_path: str | None
) -> tuple[tuple[str, str], ...]:
    path = Path(executable).resolve(strict=False)
    identity = {
        "command_executable_path": path.as_posix(),
        "command_executable_sha256": (
            f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"
            if path.is_file()
            else "unavailable"
        ),
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "runner_python": Path(sys.executable).resolve(strict=True).as_posix(),
    }
    if node_path is not None:
        node = Path(node_path).resolve(strict=True)
        identity["node_path"] = node.as_posix()
        identity["node_sha256"] = (
            f"sha256:{hashlib.sha256(node.read_bytes()).hexdigest()}"
        )
    return tuple(sorted(identity.items()))
