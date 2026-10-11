"""Prepare compact source-index windows without native extraction or semantic admission."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import tempfile
import zipfile

from .....core.owned_tree import publish_new_output_tree
from ...quarantine import IntakeRefusal
from ..local import read_local_hyde_inventory, select_local_hyde_archive_member
from ..local.contracts import checked_path, encode, implementation_identity, sha256
from .contracts import (
    FORMAT,
    POSTURE,
    SCHEMA,
    AsciiWindowLimits,
    AsciiWindowSelection,
    NativeAsciiWindow,
)
from .parsing import number
from .streaming import source_unchanged, stream_window


def producer_identity() -> dict[str, str]:
    """Bind the ASCII producer plus shared custody/source/publication authorities."""
    result = implementation_identity()
    owner = Path(__file__).resolve().parent
    package = owner.parents[3]
    result.update(
        {
            path.relative_to(package).as_posix(): sha256(path.read_bytes())
            for path in sorted(owner.glob("*.py"))
        }
    )
    return dict(sorted(result.items()))


def prepare_hyde_ascii_window(
    custody_directory: Path,
    *,
    expected_custody_manifest_sha256: str,
    source_root: Path,
    selection: AsciiWindowSelection,
    destination: Path,
    limits: AsciiWindowLimits | None = None,
) -> NativeAsciiWindow:
    """Verify selected native archive/member bytes and retain an uninterpreted index window."""
    limits = AsciiWindowLimits() if limits is None else limits
    if not isinstance(limits, AsciiWindowLimits) or not isinstance(
        selection, AsciiWindowSelection
    ):
        raise IntakeRefusal(
            "hyde_ascii_request_invalid", "Typed selection/limits required"
        )
    source_root, target = checked_path(source_root), checked_path(destination)
    if not source_root.is_dir() or target.exists():
        raise IntakeRefusal("hyde_ascii_paths_invalid", str(target))
    if target.is_relative_to(source_root) or source_root.is_relative_to(target):
        raise IntakeRefusal("hyde_ascii_output_overlaps_source", str(target))
    stage: Path | None = None
    try:
        producer = producer_identity()
        custody = read_local_hyde_inventory(
            custody_directory, expected_manifest_sha256=expected_custody_manifest_sha256
        )
        selected = select_local_hyde_archive_member(
            custody,
            archive_path=selection.archive_path,
            member_index=selection.member_index,
        )
        result = stream_window(source_root, selected, selection, limits)
        target.parent.mkdir(parents=True, exist_ok=True)
        stage = Path(
            tempfile.mkdtemp(prefix=f".{target.name}.pending-", dir=target.parent)
        )
        window = {
            "header": asdict(result.header),
            "source_tokens": result.tokens,
            "missing_mask": result.missing,
        }
        content = encode(window)
        if len(content) > limits.maximum_retained_bytes:
            raise IntakeRefusal("hyde_ascii_output_limit", str(len(content)))
        (stage / "window.json").write_bytes(content)
        manifest = {
            "schema_version": SCHEMA,
            "format_profile": FORMAT,
            **POSTURE,
            "producer": {
                "files": producer,
                "files_sha256": sha256(encode(producer)),
                "attestation": "source_bytes_not_loaded_runtime",
            },
            "custody_manifest_sha256": custody.manifest_sha256,
            "dataset_inventory_sha256": custody.dataset_inventory_sha256,
            "archive_member": asdict(selected),
            "selection": asdict(selection),
            "limits": asdict(limits),
            "files": {
                "window.json": {"sha256": sha256(content), "bytes": len(content)}
            },
            "member_payload": {
                "sha256": result.member_sha256,
                "bytes": result.member_bytes,
                "crc32": result.member_crc32,
                "complete_eof_verified": True,
            },
            "counts": {
                "source_cells": result.header.rows * result.header.columns,
                "selected_cells": len(result.tokens),
                "selected_missing": sum(result.missing),
                "selected_nonmissing": len(result.tokens) - sum(result.missing),
                "selected_zero": sum(
                    not missing and number(token, limits) == 0
                    for token, missing in zip(
                        result.tokens, result.missing, strict=True
                    )
                ),
            },
        }
        manifest_bytes = encode(manifest)
        (stage / "manifest.json").write_bytes(manifest_bytes)
        from .reading import read_hyde_ascii_window

        read_hyde_ascii_window(stage, expected_manifest_sha256=sha256(manifest_bytes))
        if (
            select_local_hyde_archive_member(
                custody,
                archive_path=selection.archive_path,
                member_index=selection.member_index,
            )
            != selected
        ):
            raise IntakeRefusal("hyde_ascii_custody_changed", selected.archive_path)
        source_unchanged(source_root / selected.archive_path, result.source_stamp)
        checked_path(target)
        if producer_identity() != producer:
            raise IntakeRefusal(
                "hyde_ascii_producer_changed",
                "Source producer bytes changed before publication",
            )
        publish_new_output_tree(final_output_root=target, staging_output_root=stage)
        return read_hyde_ascii_window(
            target, expected_manifest_sha256=sha256(manifest_bytes)
        )
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        OverflowError,
        zipfile.BadZipFile,
        RuntimeError,
    ) as exc:
        if isinstance(exc, IntakeRefusal):
            raise
        raise IntakeRefusal(
            "hyde_ascii_preparation_failed",
            f"{type(exc).__name__}: {exc}; stage={stage}",
        ) from exc
