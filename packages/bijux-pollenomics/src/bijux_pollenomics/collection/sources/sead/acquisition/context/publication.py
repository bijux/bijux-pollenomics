"""Retain private refused epochs and attach complete owned context without replace."""

from __future__ import annotations

from collections.abc import Callable, Sequence
import hashlib
import os
from pathlib import Path
import secrets
import time
from typing import Any

from bijux_pollenomics.core.errors.cleanup import add_cleanup_note
from bijux_pollenomics.core.filesystem import (
    DirectoryAnchor,
    OwnedTreeWriter,
    publish_owned_replacement,
)

from ..full.serialization import canonical_bytes
from .contracts import DEFAULT_CONTEXT_LIMITS, SeadContextLimits, SeadContextSite
from .reading import (
    MANIFEST_MAX_BYTES,
    PACKET_MAX_BYTES,
    PACKET_MAX_FILES,
    read_sead_context,
)
from .transport import ContextResponse
from .workflow import ContextCollector


def _write_packet(writer: OwnedTreeWriter, collector: ContextCollector) -> str:
    """Persist immutable bounded responses plus context-only member authority."""
    files = collector.files()
    manifest = collector.manifest()
    manifest["files"] = [
        {
            "path": name,
            "byte_count": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
        }
        for name, body in sorted(files.items())
    ]
    raw = canonical_bytes(manifest)
    if len(raw) > MANIFEST_MAX_BYTES:
        raise ValueError("Context manifest exceeds its finite byte budget")
    for name, body in sorted(files.items()):
        writer.write_bytes(name, body)
    writer.write_bytes("manifest.json", raw)
    return hashlib.sha256(raw).hexdigest()


def acquire_unresolved_sead_context(
    output_root: Path,
    *,
    recovery_root: Path,
    sites: Sequence[SeadContextSite],
    run_id: str,
    parent_run_id: str,
    build_id: str,
    opener: Callable[..., ContextResponse],
    limits: SeadContextLimits = DEFAULT_CONTEXT_LIMITS,
    clock: Callable[[], float] = time.monotonic,
) -> Path:
    """Acquire one new private context epoch, never country-assigned evidence.

    The caller explicitly supplies a no-retry/no-redirect response opener; there
    is no default network operation. Existing outputs refuse before transport.
    A separate private recovery root retains partial packets after every refusal.
    """
    collector = ContextCollector(
        sites=sites,
        run_id=run_id,
        parent_run_id=parent_run_id,
        build_id=build_id,
        opener=opener,
        limits=limits,
        clock=clock,
    )
    final, recovery_root = Path(output_root), Path(recovery_root)
    if (
        not final.is_absolute()
        or not recovery_root.is_absolute()
        or final.is_relative_to(recovery_root)
        or recovery_root.is_relative_to(final)
    ):
        raise ValueError(
            "Context output and private recovery must be separate absolute trees"
        )
    with DirectoryAnchor(final.parent, create=True) as parent:
        if os.path.lexists(final):
            raise FileExistsError("Context output already exists; no source refetch")
        with DirectoryAnchor(recovery_root, create=True):
            run = recovery_root / ("context-" + secrets.token_hex(12))
            with (
                OwnedTreeWriter(run, max_bytes=1, max_files=1),
                DirectoryAnchor(run) as recovery,
                OwnedTreeWriter(
                    run / "candidate",
                    max_bytes=PACKET_MAX_BYTES,
                    max_files=PACKET_MAX_FILES,
                ) as writer,
            ):
                try:
                    collector.acquire()
                except BaseException as primary:
                    try:
                        _write_packet(writer, collector)
                    except BaseException:
                        add_cleanup_note(
                            primary,
                            lambda: (
                                "Context partial receipt write failed; owned evidence retained"
                            ),
                        )
                    add_cleanup_note(
                        primary,
                        lambda: (
                            f"Context recovery originally allocated at {run}; current location unverified"
                        ),
                    )
                    raise
                pin = _write_packet(writer, collector)
                parent.check()

                def validate(root: Path) -> dict[str, Any]:
                    parent.check()
                    result = read_sead_context(root, expected_manifest_sha256=pin)
                    parent.check()
                    return result

                publish_owned_replacement(
                    writer,
                    final=final,
                    prior=None,
                    recovery=recovery,
                    validate=validate,
                )
    return final / "manifest.json"
